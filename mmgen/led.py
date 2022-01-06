#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
led: Control the LED on a single-board computer
"""

import sys,time
from mmgen.common import *
import threading

class LEDControl:

	binfo = namedtuple('board_info',['name','status','trigger','trigger_states'])
	boards = {
		'raspi_pi': binfo(
			name    = 'Raspberry Pi',
			status  = '/sys/class/leds/led0/brightness',
			trigger = '/sys/class/leds/led0/trigger',
			trigger_states = ('none','mmc0') ),
		'orange_pi': binfo(
			name    = 'Orange Pi (Armbian)',
			status  = '/sys/class/leds/orangepi:red:status/brightness',
			trigger = None,
			trigger_states = None ),
		'rock_pi': binfo(
			name    = 'Rock Pi (Armbian)',
			status  = '/sys/class/leds/status/brightness',
			trigger = '/sys/class/leds/status/trigger',
			trigger_states = ('none','heartbeat') ),
		'dummy': binfo(
			name    = 'Fake',
			status  = '/tmp/led_status',
			trigger = '/tmp/led_trigger',
			trigger_states = ('none','original_value') ),
	}

	def __init__(self,enabled,simulate=False,debug=False):

		self.enabled = enabled
		self.debug = debug

		if not enabled:
			self.set = self.stop = self.noop
			return

		self.ev = threading.Event()
		self.led_thread = None

		if simulate:
			type(self).create_dummy_control_files()
			self.debug = True

		for board_id,board in self.boards.items():
			try: os.stat(board.status)
			except: pass
			else: break
		else:
			from mmgen.exception import NoLEDSupport
			raise NoLEDSupport('Control files not found!  LED control not supported on this system')

		msg(f'{board.name} board detected')

		if self.debug:
			msg(fmt(f"""
			Status file:  {board.status}
			Trigger file: {board.trigger}
			""",indent='  ',strip_char='\t'))

		if board_id == 'dummy' and not simulate:
			if g.test_suite:
				msg('Warning: no simulation requested but dummy LED control files detected')
				self.debug = True
			else:
				die(1,fmt(f"""
				No simulation requested but dummy LED control files detected:

				  {board.status}
				  {board.trigger}

				You may wish to remove them and restart
				""",indent='  ',strip_char='\t'))

		def check_access(fn,desc,init_val=None):
			try:
				if not init_val:
					with open(fn) as fp:
						init_val = fp.read().strip()
				with open(fn,'w') as fp:
					fp.write(f'{init_val}\n')
				return True
			except PermissionError:
				ydie(1,'\n'+fmt(f"""
					You do not have access to the {desc} file
					To allow access, run the following command:

					    sudo chmod 0666 {fn}
				""",indent='  ',strip_char='\t'))

		check_access(board.status,desc='status LED control')

		if board.trigger:
			check_access(board.trigger,desc='LED trigger',init_val=board.trigger_states[0])

		self.board = board

	@classmethod
	def create_dummy_control_files(cls):
		db = cls.boards['dummy']
		with open(db.status,'w') as fp:
			fp.write('0\n')
		with open(db.trigger,'w') as fp:
			fp.write(db.trigger_states[1]+'\n')

	def noop(self,*args,**kwargs): pass

	def ev_sleep(self,secs):
		self.ev.wait(secs)
		return self.ev.isSet()

	def led_loop(self,on_secs,off_secs):

		if self.debug:
			msg(f'led_loop({on_secs},{off_secs})')

		if not on_secs:
			with open(self.board.status,'w') as fp:
				fp.write('0\n')
			while True:
				if self.ev_sleep(3600):
					return

		while True:
			for s_time,val in ((on_secs,255),(off_secs,0)):
				if self.debug:
					msg_r(('^','+')[bool(val)])
				with open(self.board.status,'w') as fp:
					fp.write(f'{val}\n')
				if self.ev_sleep(s_time):
					if self.debug:
						msg('\n')
					return

	def set(self,state):
		lt = namedtuple('led_timings',['on_secs','off_secs'])
		timings = {
			'off':     lt( 0, 0 ),
			'standby': lt( 2.2, 0.2 ),
			'busy':    lt( 0.06, 0.06 ),
			'error':   lt( 0.5, 0.5 ) }

		if self.led_thread:
			self.ev.set()
			self.led_thread.join()
			self.ev.clear()

		if self.debug:
			msg(f'Setting LED state to {state!r}')

		self.led_thread = threading.Thread(target=self.led_loop,name='LED loop',args=timings[state])
		self.led_thread.start()

	def stop(self):

		self.set('off')
		self.ev.set()
		self.led_thread.join()

		if self.debug:
			msg('Stopping LED')

		if self.board.trigger:
			with open(self.board.trigger,'w') as fp:
				fp.write(self.board.trigger_states[1]+'\n')

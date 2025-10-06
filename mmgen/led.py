#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
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

import sys, os, threading
from collections import namedtuple
from subprocess import run
from dataclasses import dataclass

from .util import msg, msg_r, die, have_sudo
from .color import blue, orange

class LEDControl:

	orig_trigger_state = None

	@dataclass(frozen=True, kw_only=True)
	class binfo:
		name:            str
		control:         str
		trigger:         str = None
		trigger_dfl:     str = 'heartbeat'
		trigger_disable: str = 'none'
		color:           str = 'colored'

	boards = {
		'raspi_pi': binfo(
			name    = 'Raspberry Pi',
			control = '/sys/class/leds/led0/brightness',
			trigger = '/sys/class/leds/led0/trigger',
			trigger_dfl = 'mmc0',
			color   = 'green'),
		'orange_pi': binfo(
			name    = 'Orange Pi (Armbian)',
			control = '/sys/class/leds/orangepi:red:status/brightness',
			color   = 'green'),
		'orange_pi_5': binfo(
			name    = 'Orange Pi 5 (Armbian)',
			control = '/sys/class/leds/status_led/brightness',
			trigger = '/sys/class/leds/status_led/trigger',
			color   = 'green'),
		'rock_pi': binfo(
			name    = 'Rock Pi (Armbian)',
			control = '/sys/class/leds/status/brightness',
			trigger = '/sys/class/leds/status/trigger',
			color   = 'blue'),
		'rock_5': binfo(
			name    = 'Rock 5 (Armbian) [legacy kernel]',
			control = '/sys/class/leds/user-led2/brightness',
			trigger = '/sys/class/leds/user-led2/trigger',
			color   = 'blue'),
		'rock_5b': binfo(
			name    = 'Rock 5 (Armbian)',
			control = '/sys/class/leds/blue:status/brightness',
			trigger = '/sys/class/leds/blue:status/trigger',
			color   = 'blue'),
		'banana_pi_f3': binfo(
			name    = 'Banana Pi F3 (Armbian)',
			control = '/sys/class/leds/sys-led/brightness',
			trigger = '/sys/class/leds/sys-led/trigger',
			color   = 'green'),
		'nano_pi_m6': binfo(
			name    = 'Nano Pi M6 (Armbian)',
			control = '/sys/class/leds/user_led/brightness',
			trigger = '/sys/class/leds/user_led/trigger',
			color   = 'green'),
		'dummy': binfo(
			name    = 'Fake Board',
			control = '/tmp/led_status',
			trigger = '/tmp/led_trigger')}

	def __init__(self, *, enabled, simulate=False, debug=False):

		self.enabled = enabled
		self.debug = debug or simulate

		if not enabled:
			self.set = self.stop = self.noop
			return

		self.ev = threading.Event()
		self.led_thread = None

		for board_id, board in self.boards.items():
			if board_id == 'dummy' and not simulate:
				continue
			try:
				os.stat(board.control)
				break
			except FileNotFoundError:
				pass
		else:
			die('NoLEDSupport', 'Control files not found!  LED control not supported on this system')

		msg(f'{board.name} board detected')

		if self.debug:
			msg(f'\n  Status file:  {board.control}\n  Trigger file: {board.trigger}')

		def write_init_val(fn, init_val):
			if not init_val:
				with open(fn) as fp:
					init_val = fp.read().strip()
			with open(fn, 'w') as fp:
				fp.write(f'{init_val}\n')

		def permission_error_action(fn, desc):
			cmd = f'sudo chmod 0666 {fn}'
			if have_sudo():
				msg(orange(f'Running ‘{cmd}’'))
				run(cmd.split(), check=True)
			else:
				msg('\n{}\n{}\n{}'.format(
					blue(f'You do not have write access to the {desc}'),
					blue(f'To allow access, run the following command:\n\n    {cmd}'),
					orange('[To prevent this message in the future, enable sudo without a password]')
				))
				sys.exit(1)

		def init_state(fn, *, desc, init_val=None):
			try:
				write_init_val(fn, init_val)
			except PermissionError:
				permission_error_action(fn, desc)
				write_init_val(fn, init_val)

		# Writing to control file can alter trigger file, so read and initialize trigger file first:
		if board.trigger:
			def get_cur_state():
				try:
					with open(board.trigger) as fh:
						states = fh.read()
				except PermissionError:
					permission_error_action(board.trigger, 'status LED trigger file')
					with open(board.trigger) as fh:
						states = fh.read()

				res = [a for a in states.split() if a.startswith('[') and a.endswith(']')]
				return res[0][1:-1] if len(res) == 1 else None

			if cur_state := get_cur_state():
				msg(f'Saving current LED trigger state: [{cur_state}]')
				self.orig_trigger_state = cur_state
			else:
				msg('Unable to determine current LED trigger state')

			init_state(board.trigger, desc='status LED trigger file', init_val=board.trigger_disable)

		init_state(board.control, desc='status LED control file')

		self.board = board

	@classmethod
	def create_dummy_control_files(cls):
		db = cls.boards['dummy']
		with open(db.control, 'w') as fp:
			fp.write('0\n')
		with open(db.trigger, 'w') as fp:
			fp.write(db.trigger_dfl + '\n')

	def noop(self, *args, **kwargs):
		pass

	def ev_sleep(self, secs):
		self.ev.wait(secs)
		return self.ev.is_set()

	def led_loop(self, on_secs, off_secs):

		if self.debug:
			msg(f'led_loop({on_secs}, {off_secs})')

		if not on_secs:
			with open(self.board.control, 'w') as fp:
				fp.write('0\n')
			while True:
				if self.ev_sleep(3600):
					return

		while True:
			for s_time, val in ((on_secs, 255), (off_secs, 0)):
				if self.debug:
					msg_r(('^', '+')[bool(val)])
				with open(self.board.control, 'w') as fp:
					fp.write(f'{val}\n')
				if self.ev_sleep(s_time):
					if self.debug:
						msg('\n')
					return

	def set(self, state):
		lt = namedtuple('led_timings', ['on_secs', 'off_secs'])
		timings = {
			'off':     lt(0,    0),
			'standby': lt(2.2,  0.2),
			'busy':    lt(0.06, 0.06),
			'error':   lt(0.5,  0.5)}

		if self.led_thread:
			self.ev.set()
			self.led_thread.join()
			self.ev.clear()

		if self.debug:
			msg(f'Setting LED state to {state!r}')

		self.led_thread = threading.Thread(
				target = self.led_loop,
				name   = 'LED loop',
				args   = timings[state],
				daemon = True)

		self.led_thread.start()

	def stop(self):

		self.set('off')
		self.ev.set()
		self.led_thread.join()

		if self.debug:
			msg('Stopping LED')

		if self.orig_trigger_state:
			with open(self.board.trigger, 'w') as fp:
				fp.write(self.orig_trigger_state + '\n')

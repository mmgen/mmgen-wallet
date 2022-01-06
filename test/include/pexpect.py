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
test/pexpect.py: pexpect implementation for MMGen test suites
"""

import sys,os,time
from mmgen.globalvars import g
from mmgen.opts import opt
from mmgen.util import msg,msg_r,vmsg,vmsg_r,rmsg,red,yellow,green,cyan,die,rdie
from .common import *

try:
	import pexpect
	from pexpect.popen_spawn import PopenSpawn
except ImportError as e:
	die(2,red(f'Pexpect module is missing.  Cannnot run test suite ({e!r})'))

def debug_pexpect_msg(p):
	if opt.debug_pexpect:
		msg('\n{}{}{}'.format( red('BEFORE ['), p.before, red(']') ))
		msg('{}{}{}'.format( red('MATCH ['), p.after, red(']') ))

NL = '\n'

class MMGenPexpect(object):

	def __init__(self,args,no_output=False,env=None):

		if opt.direct_exec:
			msg('')
			from subprocess import run,DEVNULL
			run([args[0]] + args[1:],check=True,stdout=DEVNULL if no_output else None)
		else:
			timeout = int(opt.pexpect_timeout or 0) or (60,5)[bool(opt.debug_pexpect)]
			if opt.pexpect_spawn:
				self.p = pexpect.spawn(args[0],args[1:],encoding='utf8',timeout=timeout,env=env)
				self.p.delaybeforesend = 0
			else:
				self.p = PopenSpawn(args,encoding='utf8',timeout=timeout,env=env)
#				self.p.delaybeforesend = 0 # TODO: try this here too

			if opt.exact_output:
				self.p.logfile = sys.stdout

		self.req_exit_val = 0
		self.skip_ok = False
		self.sent_value = None

	def do_decrypt_ka_data(self,hp,pw,desc='key-address data',check=True,have_yes_opt=False):
#		self.hash_preset(desc,hp)
		self.passphrase(desc,pw)
		if not have_yes_opt:
			self.expect('Check key-to-address validity? (y/N): ',('n','y')[check])

	def view_tx(self,view):
		self.expect(r'View.* transaction.*\? .*: ',view,regex=True)
		if view not in 'n\n':
			self.expect('to continue: ','\n')

	def do_comment(self,add_comment,has_label=False):
		p = ('Add a comment to transaction','Edit transaction comment')[has_label]
		self.expect(f'{p}? (y/N): ',('n','y')[bool(add_comment)])
		if add_comment:
			self.expect('Comment: ',add_comment+'\n')

	def ok(self):
		self.p.sendeof()
		self.p.read()
		ret = self.p.wait()
		if ret != self.req_exit_val and not opt.coverage:
			die(1,red(f'test.py: spawned program exited with value {ret}'))
		if opt.profile:
			return
		if not self.skip_ok:
			sys.stderr.write(green('OK\n') if opt.exact_output or opt.verbose else (' OK\n'))
		return self

	def license(self):
		if 'MMGEN_NO_LICENSE' in os.environ: return
		self.expect("'w' for conditions and warranty info, or 'c' to continue: ",'c')

	def label(self,label='Test Label (UTF-8) α'):
		self.expect('Enter a wallet label, or hit ENTER for no label: ',label+'\n')

	def usr_rand(self,num_chars):
		if opt.usr_random:
			self.interactive()
			self.send('\n')
		else:
			rand_chars = list(getrandstr(num_chars,no_space=True))
			vmsg_r('SEND ')
			while rand_chars:
				ch = rand_chars.pop(0)
				msg_r(yellow(ch)+' ' if opt.verbose else '+')
				ret = self.expect('left: ',ch,delay=0.005)
			self.expect('ENTER to continue: ','\n')

	def passphrase_new(self,desc,passphrase):
		self.expect(f'Enter passphrase for {desc}: ',passphrase+'\n')
		self.expect('Repeat passphrase: ',passphrase+'\n')

	def passphrase(self,desc,passphrase,pwtype=''):
		if pwtype: pwtype += ' '
		self.expect(f'Enter {pwtype}passphrase for {desc}.*?: ',passphrase+'\n',regex=True)

	def hash_preset(self,desc,preset=''):
		self.expect(f'Enter hash preset for {desc}')
		self.expect('or hit ENTER .*?:',str(preset)+'\n',regex=True)

	def written_to_file(self,desc,overwrite_unlikely=False,query='Overwrite?  ',oo=False):
		s1 = f'{desc} written to file '
		s2 = query + "Type uppercase 'YES' to confirm: "
		ret = self.expect(([s1,s2],s1)[overwrite_unlikely])
		if ret == 1:
			self.send('YES\n')
			return self.expect_getend("Overwriting file '").rstrip("'")
		self.expect(NL,nonl=True)
		outfile = self.p.before.strip().strip("'")
		if opt.debug_pexpect:
			rmsg(f'Outfile [{outfile}]')
		vmsg('{} file: {}'.format( desc, cyan(outfile.replace('"',"")) ))
		return outfile

	def hincog_create(self,hincog_bytes):
		ret = self.expect(['Create? (Y/n): ',"'YES' to confirm: "])
		if ret == 0:
			self.send('\n')
			self.expect('Enter file size: ',str(hincog_bytes)+'\n')
		else:
			self.send('YES\n')
		return ret

	def no_overwrite(self):
		self.expect("Overwrite?  Type uppercase 'YES' to confirm: ",'\n')
		self.expect('Exiting at user request')

	def expect_getend(self,s,regex=False):
		ret = self.expect(s,regex=regex,nonl=True)
		debug_pexpect_msg(self.p)
		# readline() of partial lines doesn't work with PopenSpawn, so do this instead:
		self.expect(NL,nonl=True,silent=True)
		debug_pexpect_msg(self.p)
		end = self.p.before.rstrip()
		if not g.debug:
			vmsg(f' ==> {cyan(end)}')
		return end

	def interactive(self):
		return self.p.interact() # interact() not available with popen_spawn

	def kill(self,signal):
		return self.p.kill(signal)

	def expect(self,s,t='',delay=None,regex=False,nonl=False,silent=False):
		delay = delay or (0,0.3)[bool(opt.buf_keypress)]

		if not silent:
			if opt.verbose:
				msg_r('EXPECT ' + yellow(str(s)))
			elif not opt.exact_output: msg_r('+')

		try:
			if s == '':
				ret = 0
			else:
				f = (self.p.expect_exact,self.p.expect)[bool(regex)]
				ret = f(s)
		except pexpect.TIMEOUT:
			if opt.debug_pexpect: raise
			m1 = red(f'\nERROR.  Expect {s!r} timed out.  Exiting\n')
			m2 = f'before: [{self.p.before}]\n'
			m3 = f'sent value: [{self.sent_value}]' if self.sent_value != None else ''
			rdie(1,m1+m2+m3)

		debug_pexpect_msg(self.p)

		if opt.verbose and type(s) != str:
			msg_r(f' ==> {ret} ')

		if ret == -1:
			rdie(1,f'Error.  Expect returned {ret}')
		else:
			if t == '':
				if not nonl and not silent: vmsg('')
			else:
				self.send(t,delay,s)
			return ret

	def send(self,t,delay=None,s=False):
		self.sent_value = None
		delay = delay or (0,0.3)[bool(opt.buf_keypress)]
		if delay: time.sleep(delay)
		ret = self.p.send(t) # returns num bytes written
		if ret:
			self.sent_value = t
		if delay: time.sleep(delay)
		if opt.verbose:
			ls = '' if opt.debug or not s else ' '
			es = '' if s else '  '
			yt = yellow('{!r}'.format( t.replace('\n',r'\n') ))
			msg(f'{ls}SEND {es}{yt}')
		return ret

	def read(self,n=-1):
		return self.p.read(n)

	def close(self):
		if opt.pexpect_spawn:
			self.p.close()

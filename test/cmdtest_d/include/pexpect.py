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
test.cmdtest_d.include.pexpect: pexpect implementation for MMGen Wallet cmdtest suite
"""

import sys, time

from mmgen.color import red, yellow, green, cyan
from mmgen.util import msg, msg_r, rmsg, die

from ...include.common import cfg, vmsg, vmsg_r, getrandstr, strip_ansi_escapes

try:
	import pexpect
	from pexpect.popen_spawn import PopenSpawn
except ImportError as e:
	die(2, red(f'‘pexpect’ module is missing.  Cannnot run test suite ({e!r})'))

def debug_pexpect_msg(p):
	msg('\n{}{}{}'.format(red('BEFORE ['), p.before, red(']')))
	msg('{}{}{}'.format(red('MATCH ['), p.after, red(']')))

NL = '\n'

class CmdTestPexpect:

	def __init__(
			self,
			args,
			no_output     = False,
			spawn_env     = None,
			pexpect_spawn = False,
			send_delay    = None,
			timeout       = None,
			silent        = False,
			direct_exec   = False):

		self.pexpect_spawn = pexpect_spawn
		self.send_delay = send_delay
		self.skip_ok = False
		self.sent_value = None
		self.spawn_env = spawn_env
		self.exit_val = None

		if direct_exec or cfg.direct_exec:
			from subprocess import Popen, DEVNULL
			redir = DEVNULL if (no_output or not cfg.exact_output) else None
			self.ep = Popen([args[0]] + args[1:], stderr=redir, env=spawn_env)
		else:
			timeout = int(
				timeout
				or cfg.pexpect_timeout
				or cfg.test_suite_pexpect_timeout) or (60, 5)[bool(cfg.debug_pexpect)]
			if pexpect_spawn:
				self.p = pexpect.spawn(args[0], args[1:], encoding='utf8', timeout=timeout, env=spawn_env)
			else:
				self.p = PopenSpawn(args, encoding='utf8', timeout=timeout, env=spawn_env)

			if cfg.exact_output and not silent:
				self.p.logfile = sys.stdout

	def do_decrypt_ka_data(
			self,
			pw,
			desc         = 'key-address data',
			check        = True,
			have_yes_opt = False):
		self.passphrase(desc, pw)
		if not have_yes_opt:
			self.expect('Check key-to-address validity? (y/N): ', ('n', 'y')[check])

	def view_tx(self, view):
		self.expect(r'View.* transaction.*\? .*: ', view, regex=True)
		match view:
			case 'v' if cfg.pexpect_spawn:
				self.expect('END', 'q')
			case 'v' | 'n' | '\n':
				pass
			case _:
				self.expect('to continue: ', '\n')

	def do_comment(self, add_comment, has_label=False):
		p = ('Add a comment to transaction', 'Edit transaction comment')[has_label]
		self.expect(f'{p}? (y/N): ', ('n', 'y')[bool(add_comment)])
		if add_comment:
			self.expect('Comment: ', add_comment+'\n')

	def ok(self, exit_val=None):
		if not self.pexpect_spawn:
			self.p.sendeof()
		self.p.read()
		ret = self.p.wait()
		if ret != (self.exit_val or exit_val or 0) and not cfg.coverage:
			die('TestSuiteSpawnedScriptException', f'Spawned script exited with value {ret}')
		if cfg.profile:
			return
		if not self.skip_ok:
			m = 'OK\n' if ret == 0 else f'OK[{ret}]\n'
			sys.stderr.write(green(m) if cfg.exact_output or cfg.verbose else ' '+m)
		return self

	def license(self):
		if self.spawn_env.get('MMGEN_NO_LICENSE'):
			return
		self.expect("'w' for conditions and warranty info, or 'c' to continue: ", 'c')

	def label(self, label='Test Label (UTF-8) α'):
		self.expect('Enter a wallet label, or hit ENTER for no label: ', label+'\n')

	def usr_rand(self, num_chars):
		if cfg.usr_random:
			self.interactive()
			self.send('\n')
		else:
			rand_chars = list(getrandstr(num_chars, no_space=True))
			vmsg_r('SEND ')
			while rand_chars:
				ch = rand_chars.pop(0)
				msg_r(yellow(ch)+' ' if cfg.verbose else '+')
				self.expect('left: ', ch, delay=0.005)
			self.expect('ENTER to continue: ', '\n')

	def passphrase_new(self, desc, passphrase):
		self.expect(f'Enter passphrase for {desc}: ', passphrase+'\n')
		self.expect('Repeat passphrase: ', passphrase+'\n')

	def passphrase(self, desc, passphrase, pwtype=''):
		if pwtype:
			pwtype += ' '
		self.expect(f'Enter {pwtype}passphrase for {desc}.*?: ', passphrase+'\n', regex=True)

	def hash_preset(self, desc, preset=''):
		self.expect(f'Enter hash preset for {desc}')
		self.expect('or hit ENTER .*?:', str(preset)+'\n', regex=True)

	def written_to_file(self, desc, overwrite_unlikely=False, query='Overwrite?  '):
		s1 = f'{desc} written to file '
		s2 = query + "Type uppercase 'YES' to confirm: "
		ret = self.expect(([s1, s2], s1)[overwrite_unlikely])
		if ret == 1:
			self.send('YES\n')
			return self.expect_getend("Overwriting file '").rstrip("'")
		self.expect(NL, nonl=True)
		outfile = self.p.before.strip().strip("'")
		if cfg.debug_pexpect:
			rmsg(f'Outfile [{outfile}]')
		vmsg('{} file: {}'.format(desc, cyan(outfile.replace('"', ""))))
		return outfile

	def hincog_create(self, hincog_bytes):
		ret = self.expect(['Create? (Y/n): ', "'YES' to confirm: "])
		if ret == 0:
			self.send('\n')
			self.expect('Enter file size: ', str(hincog_bytes)+'\n')
		else:
			self.send('YES\n')
		return ret

	def no_overwrite(self):
		self.expect("Overwrite?  Type uppercase 'YES' to confirm: ", '\n')
		self.expect('Exiting at user request')

	def expect_getend(self, s, regex=False):
		self.expect(s, regex=regex, nonl=True)
		if cfg.debug_pexpect:
			debug_pexpect_msg(self.p)
		# readline() of partial lines doesn't work with PopenSpawn, so do this instead:
		self.expect(NL, nonl=True, silent=True)
		if cfg.debug_pexpect:
			debug_pexpect_msg(self.p)
		end = self.p.before.rstrip()
		if not cfg.debug:
			vmsg(f' ==> {cyan(end)}')
		return end

	def interactive(self):
		return self.p.interact() # interact() not available with popen_spawn

	def kill(self, signal):
		return self.p.kill(signal)

	def match_expect_list(self, expect_list, greedy=False):
		allrep = '.*' if greedy else '.*?'
		expect = (
			r'(\b|\s)' +
			fr'\s{allrep}\s'.join(s.replace(r'.', r'\.').replace(' ', r'\s+') for s in expect_list) +
			r'(\b|\s)')
		import re
		m = re.search(expect, self.read(strip_color=True), re.DOTALL)
		assert m, f'No match found for regular expression {expect!r}'
		return m

	def expect(self, s, t='', delay=None, regex=False, nonl=False, silent=False):

		if not silent:
			if cfg.verbose:
				msg_r('EXPECT ' + yellow(str(s)))
			elif not cfg.exact_output:
				msg_r('+')

		try:
			ret = (self.p.expect_exact, self.p.expect)[bool(regex)](s) if s else 0
		except pexpect.TIMEOUT as e:
			if cfg.debug_pexpect:
				raise
			m1 = f'\nERROR.  Expect {s!r} timed out.  Exiting\n'
			m2 = f'before: [{self.p.before}]\n'
			m3 = f'sent value: [{self.sent_value}]' if self.sent_value is not None else ''
			raise pexpect.TIMEOUT(m1+m2+m3) from e

		if cfg.debug_pexpect:
			debug_pexpect_msg(self.p)

		if cfg.verbose and not isinstance(s, str):
			msg_r(f' ==> {ret} ')

		if ret == -1:
			die(4, f'Error.  Expect returned {ret}')
		else:
			if t:
				self.send(t, delay, s)
			else:
				if not nonl and not silent:
					vmsg('')
			return ret

	def send(self, t, delay=None, s=False):
		delay = delay or self.send_delay
		if delay:
			time.sleep(delay)
			if cfg.demo:
				time.sleep(0.5)
		ret = self.p.send(t) # returns num bytes written
		self.sent_value = t if ret else None
		if cfg.demo and delay:
			time.sleep(delay)
		if cfg.verbose:
			ls = '' if cfg.debug or not s else ' '
			es = '' if s else '  '
			yt = yellow('{!r}'.format(t.replace('\n', r'\n')))
			msg(f'{ls}SEND {es}{yt}')
		return ret

	def read(self, n=-1, strip_color=False):
		return strip_ansi_escapes(self.p.read(n)).replace('\r', '') if strip_color else self.p.read(n)

	def close(self):
		if self.pexpect_spawn:
			self.p.close()

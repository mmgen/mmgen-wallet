#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2017 Philemon <mmgen-py@yandex.com>
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
test/mmgen_pexpect.py: pexpect implementation for MMGen test suites
"""

from mmgen.common import *
from mmgen.test import getrandstr,ok

try:
	import pexpect
	from pexpect.popen_spawn import PopenSpawn
except:
	die(2,red('Pexpect module is missing.  Cannnot run test suite'))

if opt.buf_keypress:
	send_delay = 0.3
else:
	send_delay = 0
	os.environ['MMGEN_DISABLE_HOLD_PROTECT'] = '1'

def my_send(p,t,delay=send_delay,s=False):
	if delay: time.sleep(delay)
	ret = p.send(t) # returns num bytes written
	if delay: time.sleep(delay)
	if opt.verbose:
		ls = (' ','')[bool(opt.debug or not s)]
		es = ('  ','')[bool(s)]
		msg('%sSEND %s%s' % (ls,es,yellow("'%s'"%t.replace('\n',r'\n'))))
	return ret

def my_expect(p,s,t='',delay=send_delay,regex=False,nonl=False):
	quo = ('',"'")[type(s) == str]

	if opt.verbose: msg_r('EXPECT %s' % yellow(quo+str(s)+quo))
	else:       msg_r('+')

	try:
		if s == '': ret = 0
		else:
			f = (p.expect_exact,p.expect)[bool(regex)]
			ret = f(s,timeout=(60,5)[bool(opt.debug_pexpect)])
	except pexpect.TIMEOUT:
		if opt.debug_pexpect: raise
		errmsg(red('\nERROR.  Expect %s%s%s timed out.  Exiting' % (quo,s,quo)))
		sys.exit(1)
	debug_pexpect_msg(p)

	if opt.debug or (opt.verbose and type(s) != str): msg_r(' ==> %s ' % ret)

	if ret == -1:
		errmsg('Error.  Expect returned %s' % ret)
		sys.exit(1)
	else:
		if t == '':
			if not nonl: vmsg('')
		else:
			my_send(p,t,delay,s)
		return ret

def debug_pexpect_msg(p):
	if opt.debug_pexpect:
		errmsg('\n{}{}{}'.format(red('BEFORE ['),p.before,red(']')))
		errmsg('{}{}{}'.format(red('MATCH ['),p.after,red(']')))

class MMGenPexpect(object):

	NL = '\r\n'
	if g.platform == 'linux' and opt.popen_spawn:
		import atexit
		atexit.register(lambda: os.system('stty sane'))
		NL = '\n'

	data_dir = os.path.join('test','data_dir')
	add_spawn_args = ' '.join(['{} {}'.format(
		'--'+k.replace('_','-'),
		getattr(opt,k) if getattr(opt,k) != True else ''
		) for k in ('testnet','rpc_host','rpc_port','regtest') if getattr(opt,k)]).split()
	add_spawn_args += ['--data-dir',data_dir]

	def __init__(self,name,mmgen_cmd,cmd_args,desc,no_output=False):

		cmd_args = self.add_spawn_args + cmd_args
		cmd = (('./','')[bool(opt.system)]+mmgen_cmd,'python')[g.platform=='win']
		args = (cmd_args,[mmgen_cmd]+cmd_args)[g.platform=='win']

		for i in args:
			if type(i) not in (str,unicode):
				m1 = 'Error: missing input files in cmd line?:'
				m2 = '\nName: {}\nCmd: {}\nCmd args: {}'
				die(2,(m1+m2).format(name,cmd,args))
		if opt.popen_spawn:
			args = [("'"+a+"'" if ' ' in a else a) for a in args]
		cmd_str = '{} {}'.format(cmd,' '.join(args))
		if opt.popen_spawn:
			cmd_str = cmd_str.replace('\\','/')

		if opt.log:
			log_fd.write(cmd_str+'\n')
		if opt.verbose or opt.print_cmdline or opt.exact_output:
			clr1,clr2,eol = ((green,cyan,'\n'),(nocolor,nocolor,' '))[bool(opt.print_cmdline)]
			sys.stderr.write(green('Testing: {}\n'.format(desc)))
			sys.stderr.write(clr1('Executing {}{}'.format(clr2(cmd_str),eol)))
		else:
			m = 'Testing %s: ' % desc
			msg_r(m)

		if mmgen_cmd == '': return

		if opt.direct_exec:
			msg('')
			from subprocess import call,check_output
			f = (call,check_output)[bool(no_output)]
			ret = f([cmd] + args)
			if f == call and ret != 0:
				m = 'ERROR: process returned a non-zero exit status (%s)'
				die(1,red(m % ret))
		else:
			if opt.traceback:
				cmd,args = g.traceback_cmd,[cmd]+args
				cmd_str = g.traceback_cmd + ' ' + cmd_str
			if opt.popen_spawn:
				self.p = PopenSpawn(cmd_str)
			else:
				self.p = pexpect.spawn(cmd,args)
			if opt.exact_output: self.p.logfile = sys.stdout

	def ok(self,exit_val=0):
		ret = self.p.wait()
		if ret != exit_val:
			die(1,red('test.py: spawned program exited with value {}'.format(ret)))
		if opt.profile: return
		if opt.verbose or opt.exact_output:
			sys.stderr.write(green('OK\n'))
		else: msg(' OK')

	def cmp_or_die(self,s,t,skip_ok=False,exit_val=0):
		ret = self.p.wait()
		if ret != exit_val:
			die(1,red('test.py: spawned program exited with value {}'.format(ret)))
		if s == t:
			if not skip_ok: ok()
		else:
			sys.stderr.write(red(
				'ERROR: recoded data:\n%s\ndiffers from original data:\n%s\n' %
					(repr(t),repr(s))))
			sys.exit(3)

	def license(self):
		if 'MMGEN_NO_LICENSE' in os.environ: return
		p = "'w' for conditions and warranty info, or 'c' to continue: "
		my_expect(self.p,p,'c')

	def label(self,label='Test Label'):
		p = 'Enter a wallet label, or hit ENTER for no label: '
		my_expect(self.p,p,label+'\n')

	def usr_rand_out(self,saved=False):
		m = '%suser-supplied entropy' % (('','saved ')[saved])
		my_expect(self.p,'Generating encryption key from OS random data plus ' + m)

	def usr_rand(self,num_chars):
		if opt.usr_random:
			self.interactive()
			my_send(self.p,'\n')
		else:
			rand_chars = list(getrandstr(num_chars,no_space=True))
			my_expect(self.p,'symbols left: ','x')
			try:
				vmsg_r('SEND ')
				while self.p.expect('left: ',0.1) == 0:
					ch = rand_chars.pop(0)
					msg_r(yellow(ch)+' ' if opt.verbose else '+')
					self.p.send(ch)
			except:
				vmsg('EOT')
			my_expect(self.p,'ENTER to continue: ','\n')

	def passphrase_new(self,desc,passphrase):
		my_expect(self.p,('Enter passphrase for %s: ' % desc), passphrase+'\n')
		my_expect(self.p,'Repeat passphrase: ', passphrase+'\n')

	def passphrase(self,desc,passphrase,pwtype=''):
		if pwtype: pwtype += ' '
		my_expect(self.p,('Enter %spassphrase for %s.*?: ' % (pwtype,desc)),
				passphrase+'\n',regex=True)

	def hash_preset(self,desc,preset=''):
		my_expect(self.p,('Enter hash preset for %s' % desc))
		my_expect(self.p,('or hit ENTER .*?:'), str(preset)+'\n',regex=True)

	def written_to_file(self,desc,overwrite_unlikely=False,query='Overwrite?  ',oo=False):
		s1 = '%s written to file ' % desc
		s2 = query + "Type uppercase 'YES' to confirm: "
		ret = my_expect(self.p,([s1,s2],s1)[overwrite_unlikely])
		if ret == 1:
			my_send(self.p,'YES\n')
#			if oo:
			outfile = self.expect_getend("Overwriting file '").rstrip("'")
			return outfile
# 			else:
# 				ret = my_expect(self.p,s1)
		self.expect(self.NL,nonl=True)
		outfile = self.p.before.strip().strip("'")
		if opt.debug_pexpect: msgred('Outfile [%s]' % outfile)
		vmsg('%s file: %s' % (desc,cyan(outfile.replace("'",''))))
		return outfile

	def no_overwrite(self):
		self.expect("Overwrite?  Type uppercase 'YES' to confirm: ",'\n')
		self.expect('Exiting at user request')

	def tx_view(self):
		my_expect(self.p,r'View .*?transaction.*? \(y\)es, \(N\)o, pager \(v\)iew.*?: ','\n',regex=True)

	def expect_getend(self,s,regex=False):
		ret = self.expect(s,regex=regex,nonl=True)
		debug_pexpect_msg(self.p)
#		end = self.readline().strip()
		# readline() of partial lines doesn't work with PopenSpawn, so do this instead:
		self.expect(self.NL,nonl=True)
		debug_pexpect_msg(self.p)
		end = self.p.before
		vmsg(' ==> %s' % cyan(end))
		return end

	def interactive(self):
		return self.p.interact()

	def logfile(self,arg):
		self.p.logfile = arg

	def expect(self,*args,**kwargs):
		return my_expect(self.p,*args,**kwargs)

	def send(self,*args,**kwargs):
		return my_send(self.p,*args,**kwargs)

# 	def readline(self):
# 		return self.p.readline()
# 	def readlines(self):
# 		return [l.rstrip()+'\n' for l in self.p.readlines()]

	def read(self,n=None):
		return self.p.read(n)

	def close(self):
		if not opt.popen_spawn:
			self.p.close()

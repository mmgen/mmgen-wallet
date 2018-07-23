#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2018 The MMGen Project <mmgen@tuta.io>
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
from mmgen.test import getrandstr,ok,init_coverage

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

stderr_save = sys.stderr
def errmsg(s): stderr_save.write(s+'\n')
def errmsg_r(s): stderr_save.write(s)

def my_send(p,t,delay=send_delay,s=False):
	if delay: time.sleep(delay)
	ret = p.send(t) # returns num bytes written
	if delay: time.sleep(delay)
	if opt.verbose:
		ls = (' ','')[bool(opt.debug or not s)]
		es = ('  ','')[bool(s)]
		msg(u'{}SEND {}{}'.format(ls,es,yellow(u"'{}'".format(t.decode('utf8').replace('\n',r'\n')))))
	return ret

def my_expect(p,s,t='',delay=send_delay,regex=False,nonl=False,silent=False):

	quo = ('',"'")[type(s) == str]

	if not silent:
		if opt.verbose: msg_r('EXPECT {}'.format(yellow(quo+str(s)+quo)))
		elif not opt.exact_output: msg_r('+')

	try:
		if s == '': ret = 0
		else:
			f = (p.expect_exact,p.expect)[bool(regex)]
			ret = f(s,timeout=(60,5)[bool(opt.debug_pexpect)])
	except pexpect.TIMEOUT:
		if opt.debug_pexpect: raise
		errmsg(red('\nERROR.  Expect {}{}{} timed out.  Exiting'.format(quo,s,quo)))
		sys.exit(1)
	debug_pexpect_msg(p)

	if opt.verbose and type(s) != str:
		msg_r(' ==> {} '.format(ret))

	if ret == -1:
		errmsg('Error.  Expect returned {}'.format(ret))
		sys.exit(1)
	else:
		if t == '':
			if not nonl and not silent: vmsg('')
		else:
			my_send(p,t,delay,s)
		return ret

def debug_pexpect_msg(p):
	if opt.debug_pexpect:
		errmsg('\n{}{}{}'.format(red('BEFORE ['),p.before,red(']')))
		errmsg('{}{}{}'.format(red('MATCH ['),p.after,red(']')))

data_dir = os.path.join('test','data_dir'+('',u'-α')[bool(os.getenv('MMGEN_DEBUG_UTF8'))])

class MMGenPexpect(object):

	NL = '\r\n'
	if g.platform == 'linux' and opt.popen_spawn:
		import atexit
		atexit.register(lambda: os.system('stty sane'))
		NL = '\n'

	def __init__(self,name,mmgen_cmd,cmd_args,desc,no_output=False,passthru_args=[],msg_only=False,no_msg=False):
		cmd_args = ['--{}{}'.format(k.replace('_','-'),
			'='+getattr(opt,k) if getattr(opt,k) != True else ''
			) for k in passthru_args if getattr(opt,k)] \
			+ ['--data-dir='+data_dir] + cmd_args

		if g.platform == 'win': cmd,args = 'python',[mmgen_cmd]+cmd_args
		else:                   cmd,args = mmgen_cmd,cmd_args

		for i in args:
			if type(i) not in (str,unicode):
				m1 = 'Error: missing input files in cmd line?:'
				m2 = '\nName: {}\nCmd: {}\nCmd args: {}'
				die(2,(m1+m2).format(name,cmd,args))

		if opt.popen_spawn:
			args = [u'{q}{}{q}'.format(a,q="'" if ' ' in a else '') for a in args]

		cmd_str = u'{} {}'.format(cmd,u' '.join(args)).replace('\\','/')
		if opt.coverage:
			fs = 'python -m trace --count --coverdir={} --file={} {c}'
			cmd_str = fs.format(*init_coverage(),c=cmd_str)

		if opt.log:
			log_fd.write(cmd_str+'\n')

		if not no_msg:
			if opt.verbose or opt.print_cmdline or opt.exact_output:
				clr1,clr2,eol = ((green,cyan,'\n'),(nocolor,nocolor,' '))[bool(opt.print_cmdline)]
				sys.stderr.write(green('Testing: {}\n'.format(desc)))
				if not msg_only:
					s = repr(cmd_str) if g.platform == 'win' else cmd_str
					sys.stderr.write(clr1(u'Executing {}{}'.format(clr2(s),eol)))
			else:
				m = 'Testing {}: '.format(desc)
				msg_r(m)

		if msg_only: return

		if opt.direct_exec:
			msg('')
			from subprocess import call,check_output
			f = (call,check_output)[bool(no_output)]
			ret = f([cmd] + args)
			if f == call and ret != 0:
				die(1,red('ERROR: process returned a non-zero exit status ({})'.format(ret)))
		else:
			if opt.traceback:
				cmd,args = g.traceback_cmd,[cmd]+args
				cmd_str = g.traceback_cmd + ' ' + cmd_str
#			Msg('\ncmd_str: {}'.format(cmd_str))
			if opt.popen_spawn:
				# PopenSpawn() requires cmd string to be bytes.  However, it autoconverts unicode
				# input to bytes, though this behavior seems to be undocumented.  Setting 'encoding'
				# to 'UTF-8' will cause pexpect to reject non-unicode string input.
				self.p = PopenSpawn(cmd_str.encode('utf8'))
			else:
				self.p = pexpect.spawn(cmd,args)
			if opt.exact_output: self.p.logfile = sys.stdout

	def do_decrypt_ka_data(self,hp,pw,desc='key-address data',check=True):
		self.hash_preset(desc,hp)
		self.passphrase(desc,pw)
		self.expect('Check key-to-address validity? (y/N): ',('n','y')[check])

	def view_tx(self,view):
		self.expect('View.* transaction.*\? .*: ',view,regex=True)
		if view not in 'n\n':
			self.expect('to continue: ','\n')

	def do_comment(self,add_comment,has_label=False):
		p = ('Add a comment to transaction','Edit transaction comment')[has_label]
		self.expect('{}? (y/N): '.format(p),('n','y')[bool(add_comment)])
		if add_comment:
			self.expect('Comment: ',add_comment+'\n')

	def ok(self,exit_val=0):
		ret = self.p.wait()
#		Msg('expect: {} got: {}'.format(exit_val,ret))
		if ret != exit_val and not opt.coverage:
			die(1,red('test.py: spawned program exited with value {}'.format(ret)))
		if opt.profile: return
		if opt.verbose or opt.exact_output:
			sys.stderr.write(green('OK\n'))
		else: msg(' OK')

	def cmp_or_die(self,s,t,skip_ok=False,exit_val=0):
		ret = self.p.wait()
		if ret != exit_val:
			rdie(1,'test.py: spawned program exited with value {}'.format(ret))
		if s == t:
			if not skip_ok: ok()
		else:
			fs = 'ERROR: recoded data:\n{}\ndiffers from original data:\n{}'
			rdie(3,fs.format(repr(t),repr(s)))

	def license(self):
		if 'MMGEN_NO_LICENSE' in os.environ: return
		p = "'w' for conditions and warranty info, or 'c' to continue: "
		my_expect(self.p,p,'c')

	def label(self,label=u'Test Label (UTF-8) α'):
		p = 'Enter a wallet label, or hit ENTER for no label: '
		my_expect(self.p,p,label+'\n')

	def usr_rand_out(self,saved=False):
		fs = 'Generating encryption key from OS random data plus {}user-supplied entropy'
		my_expect(self.p,fs.format(('','saved ')[saved]))

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
		my_expect(self.p,'Enter passphrase for {}: '.format(desc),passphrase+'\n')
		my_expect(self.p,'Repeat passphrase: ',passphrase+'\n')

	def passphrase(self,desc,passphrase,pwtype=''):
		if pwtype: pwtype += ' '
		my_expect(self.p,
				'Enter {}passphrase for {}.*?: '.format(pwtype,desc),
				passphrase+'\n',regex=True)

	def hash_preset(self,desc,preset=''):
		my_expect(self.p,'Enter hash preset for {}'.format(desc))
		my_expect(self.p,'or hit ENTER .*?:',str(preset)+'\n',regex=True)

	def written_to_file(self,desc,overwrite_unlikely=False,query='Overwrite?  ',oo=False):
		s1 = '{} written to file '.format(desc)
		s2 = query + "Type uppercase 'YES' to confirm: "
		ret = my_expect(self.p,([s1,s2],s1)[overwrite_unlikely])
		if ret == 1:
			my_send(self.p,'YES\n')
#			if oo:
			outfile = self.expect_getend("Overwriting file '").rstrip("'").decode('utf8')
			return outfile
# 			else:
# 				ret = my_expect(self.p,s1)
		self.expect(self.NL,nonl=True)
		outfile = self.p.before.strip().strip("'").decode('utf8')
		if opt.debug_pexpect: rmsg('Outfile [{}]'.format(outfile))
		vmsg(u'{} file: {}'.format(desc,cyan(outfile.replace("'",''))))
		return outfile

	def no_overwrite(self):
		self.expect("Overwrite?  Type uppercase 'YES' to confirm: ",'\n')
		self.expect('Exiting at user request')

	def expect_getend(self,s,regex=False):
		ret = self.expect(s,regex=regex,nonl=True)
		debug_pexpect_msg(self.p)
#		end = self.readline().strip()
		# readline() of partial lines doesn't work with PopenSpawn, so do this instead:
		self.expect(self.NL,nonl=True,silent=True)
		debug_pexpect_msg(self.p)
		end = self.p.before
		if not g.debug:
			vmsg(' ==> {}'.format(cyan(end)))
		return end

	def interactive(self):
		return self.p.interact() # interact() not available with popen_spawn

	def kill(self,signal):
		return self.p.kill(signal)

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

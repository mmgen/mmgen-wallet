#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2019 The MMGen Project <mmgen@tuta.io>
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
test/tooltest.py:  Tests for the 'mmgen-tool' utility
"""

import sys,os,subprocess,binascii

repo_root = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]),os.pardir)))
os.chdir(repo_root)
sys.path.__setitem__(0,repo_root)
os.environ['MMGEN_TEST_SUITE'] = '1'

# Import this _after_ local path's been added to sys.path
from mmgen.common import *
from test.common import *

opts_data = lambda: {
	'desc': "Test suite for the 'mmgen-tool' utility",
	'usage':'[options] [command]',
	'options': """
-h, --help          Print this help message
-C, --coverage      Produce code coverage info using trace module
-d, --debug         Produce debugging output (stderr from spawned script)
--, --longhelp      Print help message for long options (common options)
-l, --list-cmds     List and describe the tests and commands in this test suite
-L, --list-names    List the names of all tested 'mmgen-tool' commands
-s, --system        Test scripts and modules installed on system rather than
                    those in the repo root
-t, --type=t        Specify address type (valid options: 'zcash_z')
-v, --verbose       Produce more verbose output
""",
	'notes': """

If no command is given, the whole suite of tests is run.
"""
}

sys.argv = [sys.argv[0]] + ['--skip-cfg-file'] + sys.argv[1:]

cmd_args = opts.init(opts_data,add_opts=['exact_output','profile'])

from collections import OrderedDict
cmd_data = OrderedDict([
	('util', {
			'desc': 'base conversion, hashing and file utilities',
			'cmd_data': OrderedDict([
				('strtob58',     ()),
				('b58tostr',     ('strtob58','io')),
				('hextob58',     ()),
				('b58tohex',     ('hextob58','io')),
				('b58randenc',   ()),
				('hextob32',     ()),
				('b32tohex',     ('hextob32','io')),
				('randhex',      ()),
				('id6',          ()),
				('id8',          ()),
				('str2id6',      ()),
				('hash160',      ()),
				('hash256',      ()),
				('hexreverse',   ()),
				('hexlify',      ()),
				('hexdump',      ()),
				('unhexdump',    ('hexdump','io')),
				('rand2file',    ()),
			])
		}
	),
	('cryptocoin', {
			'desc': 'Cryptocoin address/key commands',
			'cmd_data': OrderedDict([
				('randwif',        ()),
				('randpair',       ()), # create 4 pairs: uncomp,comp,segwit,bech32
				('wif2addr',       ('randpair','o4')),
				('wif2hex',        ('randpair','o4')),

				('privhex2pubhex', ('wif2hex','o3')),        # segwit only
				('pubhex2addr',    ('privhex2pubhex','o3')), # segwit only
				('hex2wif',        ('wif2hex','io2')),       # uncomp, comp
				('addr2hexaddr',   ('randpair','o4'))] +     # uncomp, comp, bech32
			([],[
				('pubhash2addr',   ('addr2hexaddr','io4'))   # uncomp, comp, bech32
			])[opt.type != 'zcash_z'] +
			([],[
				('pubhex2redeem_script', ('privhex2pubhex','o3')),
				('wif2redeem_script', ('randpair','o3')),
				('wif2segwit_pair',   ('randpair','o2')),
				('privhex2addr',   ('wif2hex','o4')), # compare with output of randpair
				('pipetest',       ('randpair','o3'))
			])[g.coin in ('BTC','LTC')]
			)
		}
	),
	('mnemonic', {
			'desc': 'mnemonic commands',
			'cmd_data': OrderedDict([
				('hex2mn',       ()),
				('mn2hex',       ('hex2mn','io3')),
				('mn_rand128',   ()),
				('mn_rand192',   ()),
				('mn_rand256',   ()),
				('mn_stats',     ()),
				('mn_printlist', ()),
			])
		}
	),
])

cfg = {
	'name':          'the tool utility',
	'enc_passwd':    'Ten Satoshis',
	'tmpdir':        'test/tmp10',
	'tmpdir_num':    10,
	'refdir':        'test/ref',
	'txfile': {
		'btc': ('0B8D5A[15.31789,14,tl=1320969600].rawtx',
				'0C7115[15.86255,14,tl=1320969600].testnet.rawtx'),
		'bch': ('460D4D-BCH[10.19764,tl=1320969600].rawtx',
				'359FD5-BCH[6.68868,tl=1320969600].testnet.rawtx'),
		'ltc': ('AF3CDF-LTC[620.76194,1453,tl=1320969600].rawtx',
				'A5A1E0-LTC[1454.64322,1453,tl=1320969600].testnet.rawtx'),
	},
	'addrfile': '98831F3A{}[1,31-33,500-501,1010-1011]{}.addrs',
	'addrfile_chk':  {
		'btc': ('6FEF 6FB9 7B13 5D91','424E 4326 CFFE 5F51'),
		'bch': ('6FEF 6FB9 7B13 5D91','424E 4326 CFFE 5F51'),
		'ltc': ('AD52 C3FE 8924 AAF0','4EBE 2E85 E969 1B30'),
	}
}

ref_subdir  = '' if g.proto.base_coin == 'BTC' else g.proto.name
altcoin_pfx = '' if g.proto.base_coin == 'BTC' else '-'+g.proto.base_coin
tn_ext = ('','.testnet')[g.testnet]

mmgen_cmd = 'mmgen-tool'

if not opt.system:
	os.environ['PYTHONPATH'] = repo_root
	mmgen_cmd = os.path.relpath(os.path.join(repo_root,'cmds',mmgen_cmd))

spawn_cmd = [mmgen_cmd]
if opt.coverage:
	d,f = init_coverage()
	spawn_cmd = ['python','-m','trace','--count','--coverdir='+d,'--file='+f] + spawn_cmd
elif g.platform == 'win':
	spawn_cmd = ['python'] + spawn_cmd

add_spawn_args = ['--data-dir='+cfg['tmpdir']] + ['--{}{}'.format(
		k.replace('_','-'),'='+getattr(opt,k) if getattr(opt,k) != True else '')
			for k in ('testnet','rpc_host','regtest','coin','type') if getattr(opt,k)]

if opt.list_cmds:
	fs = '  {:<{w}} - {}'
	Msg('Available commands:')
	w = max(map(len,cmd_data))
	for cmd in cmd_data:
		Msg(fs.format(cmd,cmd_data[cmd]['desc'],w=w))
	Msg('\nAvailable utilities:')
	Msg(fs.format('clean','Clean the tmp directory',w=w))
	sys.exit(0)
if opt.list_names:
	tested_in = {
		'tooltest.py': [],
		'test.py': (
			'encrypt','decrypt','find_incog_data',
			'addrfile_chksum','keyaddrfile_chksum','passwdfile_chksum',
			'add_label','remove_label','remove_address','twview',
			'getbalance','listaddresses','listaddress'),
		'test-release.sh': ('keyaddrlist2monerowallets','syncmonerowallets'),
		'tooltest2.py': subprocess.check_output(['test/tooltest2.py','--list-tested-cmds']).decode().split()
	}
	for v in cmd_data.values():
		tested_in['tooltest.py'] += list(v['cmd_data'].keys())

	msg(green("TESTED 'MMGEN-TOOL' COMMANDS"))
	for l in ('tooltest.py','tooltest2.py','test.py','test-release.sh'):
		msg(blue(l+':'))
		msg('  '+'\n  '.join(sorted(tested_in[l])))

	ignore = ()
	from mmgen.tool import MMGenToolCmd
	uc = sorted(
		set(MMGenToolCmd.user_commands()) -
		set(ignore) -
		set(tested_in['tooltest.py']) -
		set(tested_in['tooltest2.py']) -
		set(tested_in['test.py']) -
		set(tested_in['test-release.sh'])
	)
	die(0,'\n{}\n  {}'.format(yellow('Untested commands:'),'\n  '.join(uc)))

from mmgen.tx import is_wif,is_coin_addr

msg_w = 33
def test_msg(m):
	m2 = 'Testing {}'.format(m)
	msg_r(green(m2+'\n') if opt.verbose else '{:{w}}'.format(m2,w=msg_w+8))

maybe_compressed = ('','compressed')['C' in g.proto.mmtypes]
maybe_segwit     = ('','segwit')['S' in g.proto.mmtypes]
maybe_bech32     = ('','bech32')['B' in g.proto.mmtypes]
maybe_type_compressed = ([],['--type=compressed'])['C' in g.proto.mmtypes]
maybe_type_segwit     = ([],['--type=segwit'])['S' in g.proto.mmtypes]
maybe_type_bech32     = ([],['--type=bech32'])['B' in g.proto.mmtypes]

class MMGenToolTestUtils(object):

	def run_cmd(self,name,tool_args,kwargs='',extra_msg='',silent=False,strip=True,add_opts=[],binary=False):
		sys_cmd = (
			spawn_cmd +
			add_spawn_args +
			['-r0','-d',cfg['tmpdir']] +
			add_opts +
			[name.lower()] +
			tool_args +
			kwargs.split()
		)
		if extra_msg: extra_msg = '({})'.format(extra_msg)
		full_name = ' '.join([name.lower()]+add_opts+kwargs.split()+extra_msg.split())
		if not silent:
			if opt.verbose:
				sys.stderr.write(green('Testing {}\nExecuting '.format(full_name)))
				sys.stderr.write(cyan(' '.join(sys_cmd)+'\n'))
			else:
				msg_r('Testing {:{w}}'.format(full_name+':',w=msg_w))

		p = subprocess.Popen(sys_cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		a,b = p.communicate()
		if opt.debug:
			try: dmsg(b.decode())
			except: dmsg(repr(b))
		if not binary: a = a.decode()
		retcode = p.wait()
		if retcode != 0:
			msg('{}\n{}\n{}'.format(red('FAILED'),yellow('Command stderr output:'),b.decode()))
			rdie(1,'Called process returned with an error (retcode {})'.format(retcode))
		return (a,a.rstrip())[bool(strip)]

	def run_cmd_chk(self,name,f1,f2,kwargs='',extra_msg='',strip_hex=False,add_opts=[]):
		idata = read_from_file(f1).rstrip()
		odata = read_from_file(f2).rstrip()
		ret = self.run_cmd(name,[odata],kwargs=kwargs,extra_msg=extra_msg,add_opts=add_opts)
		vmsg('In:   ' + repr(odata))
		vmsg('Out:  ' + repr(ret))
		def cmp_equal(a,b):
			return (a.lstrip('0') == b.lstrip('0')) if strip_hex else (a == b)
		if cmp_equal(ret,idata): ok()
		else:
			fs = "Error: values don't match:\nIn:  {!r}\nOut: {!r}"
			rdie(3,fs.format(idata,ret))
		return ret

	def run_cmd_nochk(self,name,f1,kwargs='',add_opts=[]):
		odata = read_from_file(f1).rstrip()
		ret = self.run_cmd(name,[odata],kwargs=kwargs,add_opts=add_opts)
		vmsg('In:   ' + repr(odata))
		vmsg('Out:  ' + repr(ret))
		return ret

	def run_cmd_out(self,name,carg=None,Return=False,kwargs='',fn_idx='',extra_msg='',
						literal=False,chkdata='',hush=False,add_opts=[]):
		if carg: write_to_tmpfile(cfg,'{}{}.in'.format(name,fn_idx),carg+'\n')
		ret = self.run_cmd(name,([],[carg])[bool(carg)],kwargs=kwargs,
								extra_msg=extra_msg,add_opts=add_opts)
		if carg: vmsg('In:   ' + repr(carg))
		vmsg('Out:  ' + (repr(ret),ret)[literal])
		if ret or ret == '':
			write_to_tmpfile(cfg,'{}{}.out'.format(name,fn_idx),ret+'\n')
			if chkdata:
				cmp_or_die(ret,chkdata)
				return
			if Return: return ret
			else:
				if not hush: ok()
		else:
			rdie(3,"Error for command '{}'".format(name))

	def run_cmd_randinput(self,name,strip=True,add_opts=[]):
		s = os.urandom(128)
		fn = name+'.in'
		write_to_tmpfile(cfg,fn,s,binary=True)
		ret = self.run_cmd(name,[get_tmpfile(cfg,fn)],strip=strip,add_opts=add_opts)
		fn = name+'.out'
		write_to_tmpfile(cfg,fn,ret+'\n')
		ok()
		vmsg('Returned: {}'.format(ret))

tu = MMGenToolTestUtils()

def ok_or_die(val,chk_func,s,skip_ok=False):
	try: ret = chk_func(val)
	except: ret = False
	if ret:
		if not skip_ok: ok()
	else:
		rdie(3,"Returned value '{}' is not a {}".format((val,s)))

class MMGenToolTestCmds(object):

	# Util
	def strtob58(self,name):       tu.run_cmd_out(name,getrandstr(16))
	def b58tostr(self,name,f1,f2): tu.run_cmd_chk(name,f1,f2)
	def hextob58(self,name):       tu.run_cmd_out(name,getrandhex(32))
	def b58tohex(self,name,f1,f2): tu.run_cmd_chk(name,f1,f2,strip_hex=True)
	def b58randenc(self,name):
		ret = tu.run_cmd_out(name,Return=True)
		ok_or_die(ret,is_b58_str,'base 58 string')
	def hextob32(self,name):       tu.run_cmd_out(name,getrandhex(24))
	def b32tohex(self,name,f1,f2): tu.run_cmd_chk(name,f1,f2,strip_hex=True)
	def randhex(self,name):
		ret = tu.run_cmd_out(name,Return=True)
		ok_or_die(ret,binascii.unhexlify,'hex string')
	def id6(self,name):     tu.run_cmd_randinput(name)
	def id8(self,name):     tu.run_cmd_randinput(name)
	def str2id6(self,name):
		s = getrandstr(120,no_space=True)
		s2 = ' {} {} {} {} {} '.format(s[:3],s[3:9],s[9:29],s[29:50],s[50:120])
		ret1 = tu.run_cmd(name,[s],extra_msg='unspaced input'); ok()
		ret2 = tu.run_cmd(name,[s2],extra_msg='spaced input')
		cmp_or_die(ret1,ret2)
		vmsg('Returned: {}'.format(ret1))
		ok()
	def hash160(self,name):        tu.run_cmd_out(name,getrandhex(16))
	def hash256(self,name):        tu.run_cmd_out(name,getrandstr(16))
	def hexreverse(self,name):     tu.run_cmd_out(name,getrandhex(24))
	def hexlify(self,name):        tu.run_cmd_out(name,getrandstr(24))
	def hexdump(self,name): tu.run_cmd_randinput(name,strip=False)
	def unhexdump(self,name,fn1,fn2):
		ret = tu.run_cmd(name,[fn2],strip=False,binary=True)
		orig = read_from_file(fn1,binary=True)
		cmp_or_die(orig,ret)
		ok()
	def rand2file(self,name):
		of = name + '.out'
		dlen = 1024
		tu.run_cmd(name,[of,str(1024),'threads=4','silent=1'],strip=False)
		d = read_from_tmpfile(cfg,of,binary=True)
		cmp_or_die(dlen,len(d))
		ok()

	# Cryptocoin
	def randwif(self,name):
		for n,k in enumerate(['',maybe_compressed]):
			ao = ['--type='+k] if k else []
			ret = tu.run_cmd_out(name,add_opts=ao,Return=True,fn_idx=n+1)
			ok_or_die(ret,is_wif,'WIF key')
	def randpair(self,name):
		for n,k in enumerate(['',maybe_compressed,maybe_segwit,maybe_bech32]):
			ao = ['--type='+k] if k else []
			wif,addr = tu.run_cmd_out(name,add_opts=ao,Return=True,fn_idx=n+1).split()
			ok_or_die(wif,is_wif,'WIF key',skip_ok=True)
			ok_or_die(addr,is_coin_addr,'Coin address')
	def wif2addr(self,name,f1,f2,f3,f4):
		for n,f,k,m in (
			(1,f1,'',''),
			(2,f2,'',maybe_compressed),
			(3,f3,maybe_segwit,''),
			(4,f4,maybe_bech32,'')
			):
			ao = ['--type='+k] if k else []
			wif = read_from_file(f).split()[0]
			tu.run_cmd_out(name,wif,add_opts=ao,fn_idx=n,extra_msg=m)
	def wif2hex(self,name,f1,f2,f3,f4):
		for n,f,m in (
			(1,f1,''),
			(2,f2,maybe_compressed),
			(3,f3,'{} for {}'.format(maybe_compressed,maybe_segwit)),
			(4,f4,'{} for {}'.format(maybe_compressed,maybe_bech32))
			):
			wif = read_from_file(f).split()[0]
			tu.run_cmd_out(name,wif,fn_idx=n,extra_msg=m)
	def privhex2addr(self,name,f1,f2,f3,f4):
		keys = [read_from_file(f).rstrip() for f in (f1,f2,f3,f4)]
		for n,k in enumerate(('',maybe_compressed,maybe_segwit,maybe_bech32)):
			ao = ['--type='+k] if k else []
			ret = tu.run_cmd(name,[keys[n]],add_opts=ao).rstrip()
			iaddr = read_from_tmpfile(cfg,'randpair{}.out'.format(n+1)).split()[-1]
			vmsg('Out: {}'.format(ret))
			cmp_or_die(iaddr,ret)
			ok()
	def hex2wif(self,name,f1,f2,f3,f4):
		for n,fi,fo,k in ((1,f1,f2,''),(2,f3,f4,maybe_compressed)):
			ao = ['--type='+k] if k else []
			ret = tu.run_cmd_chk(name,fi,fo,add_opts=ao)
	def addr2hexaddr(self,name,f1,f2,f3,f4):
		for n,f,m,ao in (
			(1,f1,'',[]),
			(2,f2,'from {}'.format(maybe_compressed),[]),
			(4,f4,'',maybe_type_bech32),
			):
			addr = read_from_file(f).split()[-1]
			tu.run_cmd_out(name,addr,fn_idx=n,add_opts=ao,extra_msg=m)
	def pubhash2addr(self,name,f1,f2,f3,f4,f5,f6,f7,f8):
		for n,fi,fo,m,ao in (
			(1,f1,f2,'',[]),
			(2,f3,f4,'from {}'.format(maybe_compressed),[]),
			(4,f7,f8,'',maybe_type_bech32)
			):
			tu.run_cmd_chk(name,fi,fo,add_opts=ao,extra_msg=m)
	def privhex2pubhex(self,name,f1,f2,f3): # from Hex2wif
		addr = read_from_file(f3).strip()
		tu.run_cmd_out(name,addr,add_opts=maybe_type_compressed,fn_idx=3) # what about uncompressed?
	def pubhex2redeem_script(self,name,f1,f2,f3): # from above
		addr = read_from_file(f3).strip()
		tu.run_cmd_out(name,addr,fn_idx=3)
		rs = read_from_tmpfile(cfg,name+'3.out').strip()
		tu.run_cmd_out('pubhex2addr',rs,add_opts=maybe_type_segwit,fn_idx=3,hush=True)
		addr1 = read_from_tmpfile(cfg,'pubhex2addr3.out').strip()
		addr2 = read_from_tmpfile(cfg,'randpair3.out').split()[1]
		cmp_or_die(addr1,addr2)
		ok()
	def wif2redeem_script(self,name,f1,f2,f3): # compare output with above
		wif = read_from_file(f3).split()[0]
		ret1 = tu.run_cmd_out(name,wif,add_opts=maybe_type_segwit,fn_idx=3,Return=True)
		ret2 = read_from_tmpfile(cfg,'pubhex2redeem_script3.out').strip()
		cmp_or_die(ret1,ret2)
		ok()
	def wif2segwit_pair(self,name,f1,f2): # does its own checking, so just run
		wif = read_from_file(f2).split()[0]
		tu.run_cmd_out(name,wif,add_opts=maybe_type_segwit,fn_idx=2)
	def pubhex2addr(self,name,f1,f2,f3):
		addr = read_from_file(f3).strip()
		tu.run_cmd_out(name,addr,add_opts=maybe_type_segwit,fn_idx=3)

	def pipetest(self,name,f1,f2,f3):
		wif = read_from_file(f3).split()[0]
		cmd = ( '{c} {a} wif2hex {wif} | ' +
				'{c} {a} --type=compressed privhex2pubhex - | ' +
				'{c} {a} pubhex2redeem_script - | ' +
				'{c} {a} --type=segwit pubhex2addr -').format(
					c=' '.join(spawn_cmd),
					a=' '.join(add_spawn_args),
					wif=wif)
		test_msg('command piping')
		if opt.verbose:
			sys.stderr.write(green('Executing ') + cyan(cmd) + '\n')
		p = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
		res = p.stdout.read().decode().strip()
		addr = read_from_tmpfile(cfg,'wif2addr3.out').strip()
		cmp_or_die(res,addr)
		ok()

	# Mnemonic
	def hex2mn(self,name):
		for n,size,m in ((1,16,'128-bit'),(2,24,'192-bit'),(3,32,'256-bit')):
			hexnum = getrandhex(size)
			tu.run_cmd_out(name,hexnum,fn_idx=n,extra_msg=m)
	def mn2hex(self,name,f1,f2,f3,f4,f5,f6):
		for f_i,f_o,m in ((f1,f2,'128-bit'),(f3,f4,'192-bit'),(f5,f6,'256-bit')):
			tu.run_cmd_chk(name,f_i,f_o,extra_msg=m,strip_hex=True)
	def mn_rand128(self,name): tu.run_cmd_out(name)
	def mn_rand192(self,name): tu.run_cmd_out(name)
	def mn_rand256(self,name): tu.run_cmd_out(name)
	def mn_stats(self,name):   tu.run_cmd_out(name)
	def mn_printlist(self,name):
		tu.run_cmd(name,[])
		ok()

# main()
import time
start_time = int(time.time())
mk_tmpdir(cfg['tmpdir'])

def gen_deps_for_cmd(cmd,cdata):
	fns = []
	if cdata:
		name,code = cdata
		io,count = (code[:-1],int(code[-1])) if code[-1] in '0123456789' else (code,1)
		for c in range(count):
			fns += ['{}{}{}'.format(name,('',c+1)[count > 1],('.out','.in')[ch=='i']) for ch in io]
	return fns

def do_cmds(cmd_group):
	tc = MMGenToolTestCmds()
	gdata = cmd_data[cmd_group]['cmd_data']
	for cmd in gdata:
		fns = gen_deps_for_cmd(cmd,gdata[cmd])
		cmdline = [cmd] + [os.path.join(cfg['tmpdir'],fn) for fn in fns]
		getattr(tc,cmd)(*cmdline)

try:
	if cmd_args:
		if len(cmd_args) != 1:
			die(1,'Only one command may be specified')
		cmd = cmd_args[0]
		if cmd in cmd_data:
			msg('Running tests for {}:'.format(cmd_data[cmd]['desc']))
			do_cmds(cmd)
		elif cmd == 'clean':
			cleandir(cfg['tmpdir'],do_msg=True)
			sys.exit(0)
		else:
			die(1,"'{}': unrecognized command".format(cmd))
	else:
		cleandir(cfg['tmpdir'],do_msg=True)
		for cmd in cmd_data:
			msg('Running tests for {}:'.format(cmd_data[cmd]['desc']))
			do_cmds(cmd)
			if cmd is not list(cmd_data.keys())[-1]: msg('')
except KeyboardInterrupt:
	die(1,green('\nExiting at user request'))

t = int(time.time()) - start_time
gmsg('All requested tests finished OK, elapsed time: {:02}:{:02}'.format(t//60,t%60))

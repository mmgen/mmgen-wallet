#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
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
test/tooltest.py: Tests for the 'mmgen-tool' utility
"""

import sys, os, time
from subprocess import run, PIPE

try:
	from include.test_init import repo_root
except ImportError:
	from test.include.test_init import repo_root

from mmgen.cfg import Config
from mmgen.color import red, yellow, green, blue, cyan
from mmgen.util import msg, msg_r, Msg, die

opts_data = {
	'text': {
		'desc': "Test suite for the 'mmgen-tool' utility",
		'usage':'[options] [command]',
		'options': """
-h, --help          Print this help message
-C, --coverage      Produce code coverage info using trace module
-d, --debug         Produce debugging output (stderr from spawned script)
--, --longhelp      Print help message for long (global) options
-l, --list-cmds     List and describe the tests and commands in this test suite
-s, --testing-status  List the testing status of all 'mmgen-tool' commands
-t, --type=t        Specify address type (valid choices: 'zcash_z')
-v, --verbose       Produce more verbose output
""",
	'notes': """

If no command is given, the whole suite of tests is run.
"""
	}
}

sys.argv = [sys.argv[0]] + ['--skip-cfg-file'] + sys.argv[1:]

cfg = Config(opts_data=opts_data)

from test.include.common import (
	set_globals,
	mk_tmpdir,
	cleandir,
	write_to_tmpfile,
	ok,
	read_from_file,
	read_from_tmpfile,
	cmp_or_die,
	getrand,
	getrandhex,
	end_msg,
	init_coverage,
	get_tmpfile,
)
set_globals(cfg)

vmsg = cfg._util.vmsg

proto = cfg._proto

assert cfg.type in (None, 'zcash_z'), 'Only zcash-z permitted for --type argument'

cmd_data = {
	'cryptocoin': {
		'desc': 'Cryptocoin address/key commands',
		'cmd_data': {
			'randwif':        (),
			'randpair':       (), # create 4 pairs: uncomp, comp, segwit, bech32
			'wif2addr':       ('randpair', 'o4'),
			'wif2hex':        ('randpair', 'o4'),
			'privhex2pubhex': ('wif2hex', 'o3'),        # segwit only
			'pubhex2addr':    ('privhex2pubhex', 'o3'), # segwit only
			'hex2wif':        ('wif2hex', 'io2'),       # uncomp, comp
			'addr2pubhash':   ('randpair', 'o4'),       # uncomp, comp, bech32
			'pubhash2addr':   ('addr2pubhash', 'io4'),  # uncomp, comp, bech32
		},
	},
	'mnemonic': {
		'desc': 'mnemonic commands',
		'cmd_data': {
			'hex2mn':       (),
			'mn2hex':       ('hex2mn', 'io3'),
			'mn_rand128':   (),
			'mn_rand192':   (),
			'mn_rand256':   (),
			'mn_stats':     (),
			'mn_printlist': (),
		},
	},
}

if proto.coin in ('BTC', 'LTC'):
	cmd_data['cryptocoin']['cmd_data'].update({
		'pubhex2redeem_script': ('privhex2pubhex', 'o3'),
		'wif2redeem_script':    ('randpair', 'o3'),
		'wif2segwit_pair':      ('randpair', 'o2'),
		'privhex2addr':         ('wif2hex', 'o4'), # compare with output of randpair
		'pipetest':             ('randpair', 'o3')
	})

if proto.coin == 'XMR' or cfg.type == 'zcash_z':
	del cmd_data['cryptocoin']['cmd_data']['pubhash2addr']
	del cmd_data['cryptocoin']['cmd_data']['addr2pubhash']

tcfg = {
	'name':          'the tool utility',
	'enc_passwd':    'Ten Satoshis',
	'tmpdir':        'test/tmp/10',
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

ref_subdir  = '' if proto.base_coin == 'BTC' else proto.name.lower()
altcoin_pfx = '' if proto.base_coin == 'BTC' else '-'+proto.base_coin
tn_ext = ('', '.testnet')[proto.testnet]

spawn_cmd = [
	'scripts/exec_wrapper.py',
	os.path.relpath(os.path.join(repo_root, 'cmds', 'mmgen-tool'))]

if cfg.coverage:
	d, f = init_coverage()
	spawn_cmd = ['python3', '-m', 'trace', '--count', '--coverdir='+d, '--file='+f] + spawn_cmd
elif sys.platform == 'win32':
	spawn_cmd = ['python3'] + spawn_cmd

add_spawn_args = ['--data-dir='+tcfg['tmpdir']] + ['--{}{}'.format(
		k.replace('_', '-'),
		'='+getattr(cfg, k) if getattr(cfg, k) is not True else '')
			for k in ('testnet', 'rpc_host', 'regtest', 'coin', 'type') if getattr(cfg, k)]

if cfg.list_cmds:
	fs = '  {:<{w}} - {}'
	Msg('Available commands:')
	w = max(map(len, cmd_data))
	for cmd in cmd_data:
		Msg(fs.format(cmd, cmd_data[cmd]['desc'], w=w))
	Msg('\nAvailable utilities:')
	Msg(fs.format('clean', 'Clean the tmp directory', w=w))
	sys.exit(0)

if cfg.testing_status:
	tested_in = {
		'tooltest.py': [],
		'cmdtest.py': (
			'encrypt', 'decrypt', 'find_incog_data',
			'addrfile_chksum', 'keyaddrfile_chksum', 'passwdfile_chksum',
			'add_label', 'remove_label', 'remove_address', 'twview',
			'getbalance', 'listaddresses', 'listaddress',
			'daemon_version', 'decrypt_keystore', 'decrypt_geth_keystore',
			'mn2hex_interactive', 'rand2file',
			'rescan_address', 'rescan_blockchain', 'resolve_address',
			'twexport', 'twimport', 'txhist'
		),
		'tooltest2.py': run(
			['python3', 'test/tooltest2.py', '--list-tested-cmds'],
			stdout = PIPE,
			check = True
		).stdout.decode().split()
	}
	for v in cmd_data.values():
		tested_in['tooltest.py'] += list(v['cmd_data'].keys())

	Msg(green("Testing status of 'mmgen-tool' commands:"))
	for l in ('tooltest.py', 'tooltest2.py', 'cmdtest.py'):
		Msg('\n  ' + blue(l+':'))
		Msg('    '+'\n    '.join(sorted(tested_in[l])))

	ignore = ()
	from mmgen.main_tool import get_cmds
	uc = sorted(
		set(get_cmds()) -
		set(ignore) -
		set(tested_in['tooltest.py']) -
		set(tested_in['tooltest2.py']) -
		set(tested_in['cmdtest.py'])
	)
	if uc:
		Msg(yellow('\n  {}\n    {}'.format('Untested commands:', '\n    '.join(uc))))
	sys.exit(0)

from mmgen.key import is_wif
from mmgen.addr import is_coin_addr

def is_wif_loc(s):
	return is_wif(proto, s)

def is_coin_addr_loc(s):
	return is_coin_addr(proto, s)

msg_w = 35

def test_msg(m):
	msg_r(green(f'Testing {m}\n') if cfg.verbose else '{:{w}}'.format(f'Testing {m}', w=msg_w+8))

compressed = cfg.type or ('', 'compressed')['C' in proto.mmtypes]
segwit     = ('', 'segwit')['S' in proto.mmtypes]
bech32     = ('', 'bech32')['B' in proto.mmtypes]
type_compressed_arg = ([], ['--type=' + (cfg.type or 'compressed')])[bool(cfg.type) or 'C' in proto.mmtypes]
type_segwit_arg     = ([], ['--type=segwit'])['S' in proto.mmtypes]
type_bech32_arg     = ([], ['--type=bech32'])['B' in proto.mmtypes]

class MMGenToolTestUtils:

	def run_cmd(
			self,
			name,
			tool_args,
			kwargs    = '',
			extra_msg = '',
			silent    = False,
			strip     = True,
			add_opts  = [],
			binary    = False):
		sys_cmd = (
			spawn_cmd +
			add_spawn_args +
			['-r0', '-d', tcfg['tmpdir']] +
			add_opts +
			[name.lower()] +
			tool_args +
			kwargs.split()
		)
		if extra_msg:
			extra_msg = f'({extra_msg})'
		full_name = ' '.join([name.lower()]+add_opts+kwargs.split()+extra_msg.split())
		if not silent:
			if cfg.verbose:
				sys.stderr.write(green(f'Testing {full_name}\nExecuting '))
				sys.stderr.write(cyan(' '.join(sys_cmd)+'\n'))
			else:
				msg_r('Testing {:{w}}'.format(full_name+':', w=msg_w))

		cp = run(sys_cmd, stdout=PIPE, stderr=PIPE)
		out = cp.stdout
		err = cp.stderr
		if cfg.debug:
			from test.include.common import dmsg
			try:
				dmsg(err.decode())
			except:
				dmsg(repr(err))
		if not binary:
			out = out.decode()
		if cp.returncode != 0:
			msg('{}\n{}\n{}'.format(
				red('FAILED'),
				yellow('Command stderr output:'),
				err.decode()))
			die(2, f'Called process returned with an error (retcode {cp.returncode})')
		return (out, out.rstrip())[bool(strip)]

	def run_cmd_chk(self, name, f1, f2, kwargs='', extra_msg='', strip_hex=False, add_opts=[]):
		idata = read_from_file(f1).rstrip()
		odata = read_from_file(f2).rstrip()
		ret = self.run_cmd(name, [odata], kwargs=kwargs, extra_msg=extra_msg, add_opts=add_opts)
		vmsg('In:   ' + repr(odata))
		vmsg('Out:  ' + repr(ret))
		def cmp_equal(a, b):
			return (a.lstrip('0') == b.lstrip('0')) if strip_hex else (a == b)
		if cmp_equal(ret, idata):
			ok()
		else:
			die(4, f"Error: values don't match:\nIn:  {idata!r}\nOut: {ret!r}")
		return ret

	def run_cmd_nochk(self, name, f1, kwargs='', add_opts=[]):
		odata = read_from_file(f1).rstrip()
		ret = self.run_cmd(name, [odata], kwargs=kwargs, add_opts=add_opts)
		vmsg('In:   ' + repr(odata))
		vmsg('Out:  ' + repr(ret))
		return ret

	def run_cmd_out(
			self,
			name,
			carg      = None,
			Return    = False,
			kwargs    = '',
			fn_idx    = '',
			extra_msg = '',
			literal   = False,
			chkdata   = '',
			hush      = False,
			add_opts  = []):
		if carg:
			write_to_tmpfile(tcfg, f'{name}{fn_idx}.in', carg+'\n')
		ret = self.run_cmd(
				name,
				([], [carg])[bool(carg)],
				kwargs    = kwargs,
				extra_msg = extra_msg,
				add_opts  = add_opts)
		if carg:
			vmsg('In:   ' + repr(carg))
		vmsg('Out:  ' + (repr(ret), ret)[literal])
		if ret or ret == '':
			write_to_tmpfile(tcfg, f'{name}{fn_idx}.out', ret+'\n')
			if chkdata:
				cmp_or_die(ret, chkdata)
				return
			if Return:
				return ret
			elif not hush:
				ok()
		else:
			die(4, f'Error for command {name!r}')

	def run_cmd_randinput(self, name, strip=True, add_opts=[]):
		s = getrand(128)
		fn = name+'.in'
		write_to_tmpfile(tcfg, fn, s, binary=True)
		ret = self.run_cmd(name, [get_tmpfile(tcfg, fn)], strip=strip, add_opts=add_opts)
		fn = name+'.out'
		write_to_tmpfile(tcfg, fn, ret+'\n')
		ok()
		vmsg(f'Returned: {ret}')

tu = MMGenToolTestUtils()

def ok_or_die(val, chk_func, s, skip_ok=False):
	try:
		ret = chk_func(val)
	except:
		ret = False
	if ret:
		if not skip_ok:
			ok()
	else:
		die(4, f'Returned value {val!r} is not a {s}')

class MMGenToolTestCmds:

	# Cryptocoin
	def randwif(self, name):
		for n, k in enumerate(['', compressed]):
			ao = ['--type='+k] if k else []
			ret = tu.run_cmd_out(name, add_opts=ao, Return=True, fn_idx=n+1)
			ok_or_die(ret, is_wif_loc, 'WIF key')
	def randpair(self, name):
		for n, k in enumerate(['', compressed, segwit, bech32]):
			ao = ['--type='+k] if k else []
			wif, addr = tu.run_cmd_out(name, add_opts=ao, Return=True, fn_idx=n+1, literal=True).split()
			ok_or_die(wif, is_wif_loc, 'WIF key', skip_ok=True)
			ok_or_die(addr, is_coin_addr_loc, 'Coin address')
	def wif2addr(self, name, f1, f2, f3, f4):
		for n, f, k in (
				(1, f1, ''),
				(2, f2, compressed),
				(3, f3, segwit),
				(4, f4, bech32)):
			ao = ['--type='+k] if k else []
			wif = read_from_file(f).split()[0]
			tu.run_cmd_out(name, wif, add_opts=ao, fn_idx=n)
	def wif2hex(self, name, f1, f2, f3, f4):
		for n, f, m in (
				(1, f1, ''),
				(2, f2, compressed),
				(3, f3, '{} for {}'.format(compressed or 'uncompressed', segwit or 'p2pkh')),
				(4, f4, '{} for {}'.format(compressed or 'uncompressed', bech32 or 'p2pkh'))):
			wif = read_from_file(f).split()[0]
			tu.run_cmd_out(name, wif, fn_idx=n, extra_msg=m)
	def privhex2addr(self, name, f1, f2, f3, f4):
		keys = [read_from_file(f).rstrip() for f in (f1, f2, f3, f4)]
		for n, k in enumerate(('', compressed, segwit, bech32)):
			ao = ['--type='+k] if k else []
			ret = tu.run_cmd(name, [keys[n]], add_opts=ao).rstrip()
			iaddr = read_from_tmpfile(tcfg, f'randpair{n+1}.out').split()[-1]
			vmsg(f'Out: {ret}')
			cmp_or_die(iaddr, ret)
			ok()
	def hex2wif(self, name, f1, f2, f3, f4):
		for fi, fo, k in (
				(f1, f2, ''),
				(f3, f4, compressed)):
			ao = ['--type='+k] if k else []
			tu.run_cmd_chk(name, fi, fo, add_opts=ao)
	def addr2pubhash(self, name, f1, f2, f3, f4):
		for n, f, m, ao in (
				(1, f1, '', []),
				(2, f2, 'from {}'.format(compressed or 'uncompressed'), []),
				(4, f4, '', type_bech32_arg)):
			addr = read_from_file(f).split()[-1]
			tu.run_cmd_out(name, addr, fn_idx=n, add_opts=ao, extra_msg=m)
	def pubhash2addr(self, name, f1, f2, f3, f4, f5, f6, f7, f8):
		for _, fi, fo, m, ao in (
				(1, f1, f2, '', []),
				(2, f3, f4, 'from {}'.format(compressed or 'uncompressed'), []),
				(4, f7, f8, '', type_bech32_arg)):
			tu.run_cmd_chk(name, fi, fo, add_opts=ao, extra_msg=m)
	def privhex2pubhex(self, name, f1, f2, f3): # from Hex2wif
		addr = read_from_file(f3).strip()
		tu.run_cmd_out(name, addr, add_opts=type_compressed_arg, fn_idx=3) # what about uncompressed?
	def pubhex2redeem_script(self, name, f1, f2, f3): # from above
		addr = read_from_file(f3).strip()
		tu.run_cmd_out(name, addr, add_opts=type_segwit_arg, fn_idx=3)
		rs = read_from_tmpfile(tcfg, 'privhex2pubhex3.out').strip()
		tu.run_cmd_out('pubhex2addr', rs, add_opts=type_segwit_arg, fn_idx=3, hush=True)
		addr1 = read_from_tmpfile(tcfg, 'pubhex2addr3.out').strip()
		addr2 = read_from_tmpfile(tcfg, 'randpair3.out').split()[1]
		cmp_or_die(addr1, addr2)
		ok()
	def wif2redeem_script(self, name, f1, f2, f3): # compare output with above
		wif = read_from_file(f3).split()[0]
		ret1 = tu.run_cmd_out(name, wif, add_opts=type_segwit_arg, fn_idx=3, Return=True)
		ret2 = read_from_tmpfile(tcfg, 'pubhex2redeem_script3.out').strip()
		cmp_or_die(ret1, ret2)
		ok()
	def wif2segwit_pair(self, name, f1, f2): # does its own checking, so just run
		wif = read_from_file(f2).split()[0]
		tu.run_cmd_out(name, wif, add_opts=type_segwit_arg, fn_idx=2)
	def pubhex2addr(self, name, f1, f2, f3):
		addr = read_from_file(f3).strip()
		tu.run_cmd_out(name, addr, add_opts=type_segwit_arg, fn_idx=3)

	def pipetest(self, name, f1, f2, f3):
		wif = read_from_file(f3).split()[0]
		cmd = (
			'{c} {a} wif2hex {wif}' +
			' | {c} {a} --type=compressed privhex2pubhex -' +
			' | {c} {a} --type=segwit pubhex2redeem_script -' +
			' | {c} {a} --type=segwit redeem_script2addr -').format(
					c   = ' '.join(spawn_cmd),
					a   = ' '.join(add_spawn_args),
					wif = wif)
		test_msg('command piping')
		if cfg.verbose:
			sys.stderr.write(green('Executing ') + cyan(cmd) + '\n')
		res = run(cmd, stdout=PIPE, shell=True).stdout.decode().strip()
		addr = read_from_tmpfile(tcfg, 'wif2addr3.out').strip()
		cmp_or_die(addr, res)
		ok()

	# Mnemonic
	def hex2mn(self, name):
		for n, size, m in (
				(1, 16, '128-bit'),
				(2, 24, '192-bit'),
				(3, 32, '256-bit')):
			hexnum = getrandhex(size)
			tu.run_cmd_out(name, hexnum, fn_idx=n, extra_msg=m)
	def mn2hex(self, name, f1, f2, f3, f4, f5, f6):
		for f_i, f_o, m in ((f1, f2, '128-bit'), (f3, f4, '192-bit'), (f5, f6, '256-bit')):
			tu.run_cmd_chk(name, f_i, f_o, extra_msg=m, strip_hex=True)
	def mn_rand128(self, name):
		tu.run_cmd_out(name)
	def mn_rand192(self, name):
		tu.run_cmd_out(name)
	def mn_rand256(self, name):
		tu.run_cmd_out(name)
	def mn_stats(self, name):
		tu.run_cmd_out(name)
	def mn_printlist(self, name):
		tu.run_cmd(name, [])
		ok()

# main()
start_time = int(time.time())
mk_tmpdir(tcfg['tmpdir'])

def gen_deps_for_cmd(cdata):
	fns = []
	if cdata:
		name, code = cdata
		io, count = (code[:-1], int(code[-1])) if code[-1] in '0123456789' else (code, 1)
		for c in range(count):
			fns += ['{}{}{}'.format(
				name,
				(c+1 if count > 1 else ''),
				('.in' if ch == 'i' else '.out'),
			) for ch in io]
	return fns

def do_cmds(cmd_group):
	tc = MMGenToolTestCmds()
	gdata = cmd_data[cmd_group]['cmd_data']
	for cmd in gdata:
		fns = gen_deps_for_cmd(gdata[cmd])
		cmdline = [cmd] + [os.path.join(tcfg['tmpdir'], fn) for fn in fns]
		getattr(tc, cmd)(*cmdline)

def main():
	if cfg._args:
		if len(cfg._args) != 1:
			die(1, 'Only one command may be specified')
		cmd = cfg._args[0]
		if cmd in cmd_data:
			cleandir(tcfg['tmpdir'], do_msg=True)
			msg('Running tests for {}:'.format(cmd_data[cmd]['desc']))
			do_cmds(cmd)
		elif cmd == 'clean':
			cleandir(tcfg['tmpdir'], do_msg=True)
			sys.exit(0)
		else:
			die(1, f'{cmd!r}: unrecognized command')
	else:
		cleandir(tcfg['tmpdir'], do_msg=True)
		for cmd in cmd_data:
			msg('Running tests for {}:'.format(cmd_data[cmd]['desc']))
			do_cmds(cmd)
			if cmd is not list(cmd_data.keys())[-1]:
				msg('')
	end_msg(int(time.time()) - start_time)

from mmgen.main import launch
launch(func=main)

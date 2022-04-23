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
common.py: Shared routines and data for the MMGen test suites
"""

class TestSuiteException(Exception): pass
class TestSuiteFatalException(Exception): pass

import os
from subprocess import run,PIPE
from mmgen.common import *
from mmgen.devtools import *
from mmgen.fileutil import write_data_to_file,get_data_from_file

def strip_ansi_escapes(s):
	import re
	return re.sub('\x1b' + r'\[[;0-9]+?m','',s)

ascii_uc   = ''.join(map(chr,list(range(65,91))))   # 26 chars
ascii_lc   = ''.join(map(chr,list(range(97,123))))  # 26 chars
lat_accent = ''.join(map(chr,list(range(192,383)))) # 191 chars, L,S
ru_uc = ''.join(map(chr,list(range(1040,1072)))) # 32 chars
gr_uc = ''.join(map(chr,list(range(913,930)) + list(range(931,940)))) # 26 chars (930 is ctrl char)
gr_uc_w_ctrl = ''.join(map(chr,list(range(913,940)))) # 27 chars, L,C
lat_cyr_gr = lat_accent[:130:5] + ru_uc + gr_uc # 84 chars
ascii_cyr_gr = ascii_uc + ru_uc + gr_uc # 84 chars

utf8_text      = '[α-$ample UTF-8 text-ω]' * 10   # 230 chars, L,N,P,S,Z
utf8_combining = '[α-$ámple UTF-8 téxt-ω]' * 10   # L,N,P,S,Z,M
utf8_ctrl      = '[α-$ample\nUTF-8\ntext-ω]' * 10 # L,N,P,S,Z,C

text_jp = '必要なのは、信用ではなく暗号化された証明に基づく電子取引システムであり、これにより希望する二者が信用できる第三者機関を介さずに直接取引できるよう' # 72 chars ('W'ide)
text_zh = '所以，我們非常需要這樣一種電子支付系統，它基於密碼學原理而不基於信用，使得任何達成一致的雙方，能夠直接進行支付，從而不需要協力廠商仲介的參與。。' # 72 chars ('F'ull + 'W'ide)

sample_text = 'The Times 03/Jan/2009 Chancellor on brink of second bailout for banks'
sample_mn = {
	'mmgen': { # 'able': 0, 'youth': 1625, 'after' == 'afternoon'[:5]
		'mn': 'able cast forgive master funny gaze after afternoon million paint moral youth',
		'hex': '0005685ab4e94cbe3b228cf92112bc5f',
	},
	'bip39': { # len('sun') < uniq_ss_len
		'mn': 'vessel ladder alter error federal sibling chat ability sun glass valve picture',
		'hex': 'f30f8c1da665478f49b001d94c5fc452',
	},
	'xmrseed': {
		'mn': 'viewpoint donuts ardent template unveil agile meant unafraid urgent athlete rustled mime azure jaded hawk baby jagged haystack baby jagged haystack ramped oncoming point template',
		'hex': 'e8164dda6d42bd1e261a3406b2038dcbddadbeefdeadbeefdeadbeefdeadbe0f',
	},
}

ref_kafile_pass = 'kafile password'
ref_kafile_hash_preset = '1'

def getrand(n):
	if g.test_suite_deterministic:
		from mmgen.crypto import fake_urandom
		return fake_urandom(n)
	else:
		return os.urandom(n)

def getrandnum(n):
	return int(getrand(n).hex(),16)

def getrandhex(n):
	return getrand(n).hex()

def getrandnum_range(nbytes,rn_max):
	while True:
		rn = int(getrand(nbytes).hex(),16)
		if rn < rn_max:
			return rn

def getrandstr(num_chars,no_space=False):
	n,m = (94,33) if no_space else (95,32)
	return ''.join( chr(i % n + m) for i in list(getrand(num_chars)) )

def get_data_dir():
	return os.path.join('test','data_dir' + ('','-α')[bool(os.getenv('MMGEN_DEBUG_UTF8'))])

# Windows uses non-UTF8 encodings in filesystem, so use raw bytes here
def cleandir(d,do_msg=False):
	d_enc = d.encode()

	try:    files = os.listdir(d_enc)
	except: return

	from shutil import rmtree
	if do_msg:
		gmsg(f'Cleaning directory {d!r}')
	for f in files:
		try:
			os.unlink(os.path.join(d_enc,f))
		except:
			rmtree(os.path.join(d_enc,f),ignore_errors=True)

def mk_tmpdir(d):
	try: os.mkdir(d,0o755)
	except OSError as e:
		if e.errno != 17:
			raise
	else:
		vmsg(f'Created directory {d!r}')

def get_tmpfile(cfg,fn):
	return os.path.join(cfg['tmpdir'],fn)

def write_to_file(fn,data,binary=False):
	write_data_to_file(
		fn,
		data,
		quiet = True,
		binary = binary,
		ignore_opt_outdir = True )

def write_to_tmpfile(cfg,fn,data,binary=False):
	write_to_file(  os.path.join(cfg['tmpdir'],fn), data=data, binary=binary )

def read_from_file(fn,binary=False):
	return get_data_from_file(fn,quiet=True,binary=binary)

def read_from_tmpfile(cfg,fn,binary=False):
	return read_from_file(os.path.join(cfg['tmpdir'],fn),binary=binary)

def joinpath(*args,**kwargs):
	return os.path.join(*args,**kwargs)

def ok():
	if opt.profile:
		return
	if opt.verbose or opt.exact_output:
		gmsg('OK')
	else:
		msg(' OK')

def cmp_or_die(s,t,desc=None):
	if s != t:
		die( 'TestSuiteFatalException',
			(f'For {desc}:\n' if desc else '') +
			f'ERROR: recoded data:\n{t!r}\ndiffers from original data:\n{s!r}'
		)

def init_coverage():
	coverdir = os.path.join('test','trace')
	acc_file = os.path.join('test','trace.acc')
	try: os.mkdir(coverdir,0o755)
	except: pass
	return coverdir,acc_file

def silence():
	if not (opt.verbose or opt.exact_output):
		devnull_fn = ('/dev/null','null.out')[g.platform == 'win']
		g.stdout = g.stderr = open(devnull_fn,'w')

def end_silence():
	if not (opt.verbose or opt.exact_output):
		g.stdout.close()
		g.stdout = sys.stdout
		g.stderr = sys.stderr

def omsg(s):
	sys.stderr.write(s + '\n')
def omsg_r(s):
	sys.stderr.write(s)
	sys.stderr.flush()

def imsg(s):
	if opt.verbose or opt.exact_output:
		omsg(s)
def imsg_r(s):
	if opt.verbose or opt.exact_output:
		omsg_r(s)

def iqmsg(s):
	if not opt.quiet:
		omsg(s)
def iqmsg_r(s):
	if not opt.quiet:
		omsg_r(s)

def oqmsg(s):
	if not (opt.verbose or opt.exact_output):
		omsg(s)
def oqmsg_r(s):
	if not (opt.verbose or opt.exact_output):
		omsg_r(s)

def end_msg(t):
	omsg(green(
		'All requested tests finished OK' +
		('' if g.test_suite_deterministic else f', elapsed time: {t//60:02d}:{t%60:02d}')
	))

def start_test_daemons(*network_ids,remove_datadir=False):
	if not opt.no_daemon_autostart:
		return test_daemons_ops(*network_ids,op='start',remove_datadir=remove_datadir)

def stop_test_daemons(*network_ids,force=False,remove_datadir=False):
	if force or not opt.no_daemon_stop:
		return test_daemons_ops(*network_ids,op='stop',remove_datadir=remove_datadir)

def restart_test_daemons(*network_ids,remove_datadir=False):
	if not stop_test_daemons(*network_ids):
		return False
	return start_test_daemons(*network_ids,remove_datadir=remove_datadir)

def test_daemons_ops(*network_ids,op,remove_datadir=False):
	if not opt.no_daemon_autostart:
		from mmgen.daemon import CoinDaemon
		silent = not (opt.verbose or opt.exact_output)
		ret = False
		for network_id in network_ids:
			d = CoinDaemon(network_id,test_suite=True,daemon_id=g.daemon_id)
			if remove_datadir:
				d.stop(silent=True)
				d.remove_datadir()
			ret = d.cmd(op,silent=silent)
		return ret

tested_solc_ver = '0.8.7'

def check_solc_ver():
	cmd = 'python3 scripts/create-token.py --check-solc-version'
	try:
		cp = run(cmd.split(),check=False,stdout=PIPE)
	except Exception as e:
		die(4,f'Unable to execute {cmd!r}: {e}')
	res = cp.stdout.decode().strip()
	if cp.returncode == 0:
		omsg(
			orange(f'Found supported solc version {res}') if res == tested_solc_ver else
			yellow(f'WARNING: solc version ({res}) does not match tested version ({tested_solc_ver})')
		)
		return True
	else:
		omsg(yellow('Warning: Solidity compiler (solc) could not be executed or has unsupported version'))
		omsg(res)
		return False

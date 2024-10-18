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
test.include.common: Shared routines and data for the MMGen test suites
"""

import sys, os, re, atexit
from subprocess import run, PIPE, DEVNULL
from pathlib import Path

from mmgen.cfg import gv
from mmgen.color import yellow, green, orange
from mmgen.util import msg, msg_r, Msg, Msg_r, gmsg, die, suf, fmt_list
from mmgen.fileutil import write_data_to_file, get_data_from_file

def noop(*args, **kwargs):
	pass

def set_globals(cfg):
	"""
	make `cfg`, `qmsg`, `vmsg`, etc. available as globals to scripts by setting
	the module attr
	"""
	import test.include.common as this
	this.cfg = cfg

	if cfg.quiet:
		this.qmsg = this.qmsg_r = noop
	else:
		this.qmsg = msg
		this.qmsg_r = msg_r

	if cfg.verbose:
		this.vmsg = msg
		this.vmsg_r = msg_r
		this.Vmsg = Msg
		this.Vmsg_r = Msg_r
	else:
		this.vmsg = this.vmsg_r = this.Vmsg = this.Vmsg_r = noop

	this.dmsg = msg if cfg.debug else noop

def strip_ansi_escapes(s):
	return re.sub('\x1b' + r'\[[;0-9]+?m', '', s)

cmdtest_py_log_fn = 'cmdtest.py.log'
cmdtest_py_error_fn = 'cmdtest.py.err'
parity_dev_amt = 1606938044258990275541962092341162602522202993782792835301376
ascii_uc   = ''.join(map(chr, list(range(65, 91))))   # 26 chars
ascii_lc   = ''.join(map(chr, list(range(97, 123))))  # 26 chars
lat_accent = ''.join(map(chr, list(range(192, 383)))) # 191 chars, L, S
ru_uc = ''.join(map(chr, list(range(1040, 1072)))) # 32 chars
gr_uc = ''.join(map(chr, list(range(913, 930)) + list(range(931, 940)))) # 26 chars (930 is ctrl char)
gr_uc_w_ctrl = ''.join(map(chr, list(range(913, 940)))) # 27 chars, L, C
lat_cyr_gr = lat_accent[:130:5] + ru_uc + gr_uc # 84 chars
ascii_cyr_gr = ascii_uc + ru_uc + gr_uc # 84 chars

utf8_text      = '[α-$ample UTF-8 text-ω]' * 10   # 230 chars, L, N, P, S, Z
utf8_combining = '[α-$ámple UTF-8 téxt-ω]' * 10   # L, N, P, S, Z, M
utf8_ctrl      = '[α-$ample\nUTF-8\ntext-ω]' * 10 # L, N, P, S, Z, C

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

proto_cmds = (
	'addrimport',
	'autosign',
	'msg',
	'regtest',
	'tool',
	'txbump',
	'txcreate',
	'txdo',
	'txsend',
	'txsign',
	'xmrwallet',
)

def getrand(n):
	if cfg.test_suite_deterministic:
		from mmgen.test import fake_urandom
		return fake_urandom(n)
	else:
		return os.urandom(n)

def getrandnum(n):
	return int(getrand(n).hex(), 16)

def getrandhex(n):
	return getrand(n).hex()

def getrandnum_range(nbytes, rn_max):
	while True:
		rn = int(getrand(nbytes).hex(), 16)
		if rn < rn_max:
			return rn

def getrandstr(num_chars, no_space=False):
	n, m = (94, 33) if no_space else (95, 32)
	return ''.join(chr(i % n + m) for i in list(getrand(num_chars)))

# Windows uses non-UTF8 encodings in filesystem, so use raw bytes here
def cleandir(d, do_msg=False):
	d_enc = d.encode()

	try:
		files = os.listdir(d_enc)
	except:
		return None

	if files:
		from shutil import rmtree
		if do_msg:
			gmsg(f'Cleaning directory {d!r}')
		for f in files:
			try:
				os.unlink(os.path.join(d_enc, f))
			except:
				rmtree(os.path.join(d_enc, f), ignore_errors=True)

	return files

def mk_tmpdir(d):
	try:
		os.makedirs(d, mode=0o755, exist_ok=True)
	except OSError as e:
		if e.errno != 17:
			raise
	else:
		vmsg(f'Created directory {d!r}')

def clean(cfgs, tmpdir_ids=None, extra_dirs=[]):

	def clean_tmpdirs():
		cfg_tmpdirs = {k:cfgs[k]['tmpdir'] for k in cfgs}
		for d in map(str, sorted(map(int, (tmpdir_ids or cfg_tmpdirs)))):
			if d in cfg_tmpdirs:
				if cleandir(cfg_tmpdirs[d]):
					yield d
			else:
				die(1, f'{d}: invalid directory number')

	def clean_extra_dirs():
		for d in extra_dirs:
			if os.path.exists(d):
				if cleandir(d):
					yield os.path.relpath(d)

	for clean_func, list_fmt in (
				(clean_tmpdirs, 'no_quotes'),
				(clean_extra_dirs, 'dfl')
			):
		if cleaned := list(clean_func()):
			iqmsg(green('Cleaned director{} {}'.format(
				suf(cleaned, 'ies'),
				fmt_list(cleaned, fmt=list_fmt)
			)))

	for d in extra_dirs:
		if (os.path.exists(d) or os.path.islink(d)) and not os.path.isdir(d):
			print(f'Removing non-directory ‘{d}’')
			os.unlink(d)

def get_tmpfile(cfg, fn):
	return os.path.join(cfg['tmpdir'], fn)

def write_to_file(fn, data, binary=False):
	write_data_to_file(
		cfg,
		fn,
		data,
		quiet = True,
		binary = binary,
		ignore_opt_outdir = True)

def write_to_tmpfile(cfg, fn, data, binary=False):
	write_to_file(os.path.join(cfg['tmpdir'], fn), data=data, binary=binary)

def read_from_file(fn, binary=False):
	return get_data_from_file(cfg, fn, quiet=True, binary=binary)

def read_from_tmpfile(cfg, fn, binary=False):
	return read_from_file(os.path.join(cfg['tmpdir'], fn), binary=binary)

def joinpath(*args, **kwargs):
	return os.path.join(*args, **kwargs)

def ok(text='OK'):
	if cfg.profile:
		return
	if cfg.verbose or cfg.exact_output:
		gmsg(text)
	else:
		msg(f' {text}')

def cmp_or_die(s, t, desc=None):
	if s != t:
		die('TestSuiteFatalException',
			(f'For {desc}:\n' if desc else '') +
			f'ERROR: recoded data:\n{t!r}\ndiffers from original data:\n{s!r}'
		)

def init_coverage():
	coverdir = os.path.join('test', 'trace')
	acc_file = os.path.join('test', 'trace.acc')
	try:
		os.mkdir(coverdir, 0o755)
	except:
		pass
	return coverdir, acc_file

def silence():
	if not (cfg.verbose or cfg.exact_output):
		gv.stdout = gv.stderr = open(os.devnull, 'w')

def end_silence():
	if not (cfg.verbose or cfg.exact_output):
		gv.stdout.close()
		gv.stdout = sys.stdout
		gv.stderr = sys.stderr

def omsg(s):
	sys.stderr.write(s + '\n')
def omsg_r(s):
	sys.stderr.write(s)
	sys.stderr.flush()

def imsg(s):
	if cfg.verbose or cfg.exact_output:
		omsg(s)
def imsg_r(s):
	if cfg.verbose or cfg.exact_output:
		omsg_r(s)

def iqmsg(s):
	if not cfg.quiet:
		omsg(s)
def iqmsg_r(s):
	if not cfg.quiet:
		omsg_r(s)

def oqmsg(s):
	if not (cfg.verbose or cfg.exact_output):
		omsg(s)
def oqmsg_r(s):
	if not (cfg.verbose or cfg.exact_output):
		omsg_r(s)

def end_msg(t):
	omsg(green(
		'All requested tests finished OK' +
		('' if cfg.test_suite_deterministic else f', elapsed time: {t//60:02d}:{t%60:02d}')
	))

def start_test_daemons(*network_ids, remove_datadir=False):
	if not cfg.no_daemon_autostart:
		return test_daemons_ops(*network_ids, op='start', remove_datadir=remove_datadir)

def stop_test_daemons(*network_ids, force=False, remove_datadir=False):
	if force or not cfg.no_daemon_stop:
		return test_daemons_ops(*network_ids, op='stop', remove_datadir=remove_datadir)

def restart_test_daemons(*network_ids, remove_datadir=False):
	if not stop_test_daemons(*network_ids):
		return False
	return start_test_daemons(*network_ids, remove_datadir=remove_datadir)

def test_daemons_ops(*network_ids, op, remove_datadir=False):
	if not cfg.no_daemon_autostart:
		from mmgen.daemon import CoinDaemon
		silent = not (cfg.verbose or cfg.exact_output)
		ret = False
		for network_id in network_ids:
			d = CoinDaemon(cfg, network_id, test_suite=True)
			if remove_datadir:
				d.wait = True
				d.stop(silent=True)
				d.remove_datadir()
			ret = d.cmd(op, silent=silent)
		return ret

tested_solc_ver = '0.8.26'

def check_solc_ver():
	cmd = 'python3 scripts/create-token.py --check-solc-version'
	try:
		cp = run(cmd.split(), check=False, stdout=PIPE)
	except Exception as e:
		die(4, f'Unable to execute {cmd!r}: {e}')
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

def get_ethkey():
	cmdnames = ('ethkey', 'openethereum-ethkey')
	for cmdname in cmdnames:
		try:
			run([cmdname, '--help'], stdout=PIPE)
		except:
			pass
		else:
			return cmdname
	die(1, f'ethkey executable not found (tried {cmdnames})')

def do_run(cmd, check=True):
	return run(cmd, stdout=PIPE, stderr=DEVNULL, check=check)

def VirtBlockDevice(img_path, size):
	if sys.platform == 'linux':
		return VirtBlockDeviceLinux(img_path, size)
	elif sys.platform == 'darwin':
		return VirtBlockDeviceMacOS(img_path, size)

class VirtBlockDeviceBase:

	@property
	def dev(self):
		res = self._get_associations()
		if len(res) < 1:
			die(2, f'No device associated with {self.img_path}')
		elif len(res) > 1:
			die(2, f'More than one device associated with {self.img_path}')
		return res[0]

	def try_detach(self):
		try:
			dev = self.dev
		except:
			pass
		else:
			self.do_detach(dev, check=False)

	def create(self, silent=False):
		for dev in self._get_associations():
			if not silent:
				imsg(f'Detaching associated device {dev}')
			self.do_detach(dev)
		self.img_path.unlink(missing_ok=True)
		if not silent:
			imsg(f'Creating block device image file {self.img_path}')
		self.do_create(self.size, self.img_path)
		atexit.register(self.try_detach)

	def attach(self, dev_mode=None, silent=False):
		if res := self._get_associations():
			die(2, f'Device{suf(res)} {fmt_list(res, fmt="barest")} already associated with {self.img_path}')
		dev = self.get_new_dev()
		if dev_mode:
			self.dev_mode_orig = '0{:o}'.format(os.stat(dev).st_mode & 0xfff)
			if not silent:
				imsg(f'Changing permissions on device {dev} to {dev_mode!r}')
			do_run(['sudo', 'chmod', dev_mode, dev])
		if not silent:
			imsg(f'Attaching {dev or self.img_path!r}')
		self.do_attach(self.img_path, dev)

	def detach(self, silent=False):
		dev = self.dev
		if not silent:
			imsg(f'Detaching {dev!r}')
		self.do_detach(dev)
		if hasattr(self, 'dev_mode_orig'):
			if not silent:
				imsg(f'Resetting permissions on device {dev} to {self.dev_mode_orig!r}')
			do_run(['sudo', 'chmod', self.dev_mode_orig, dev])
			delattr(self, 'dev_mode_orig')

	def __del__(self):
		self.try_detach()

class VirtBlockDeviceLinux(VirtBlockDeviceBase):

	def __init__(self, img_path, size):
		self.img_path = Path(img_path).resolve()
		self.size = size

	def _get_associations(self):
		cmd = ['/sbin/losetup', '-n', '-O', 'NAME', '-j', str(self.img_path)]
		return do_run(cmd).stdout.decode().splitlines()

	def get_new_dev(self):
		return do_run(['sudo', '/sbin/losetup', '-f']).stdout.decode().strip()

	def do_create(self, size, path):
		do_run(['truncate', f'--size={size}', str(path)])

	def do_attach(self, path, dev):
		do_run(['sudo', '/sbin/losetup', dev, str(path)])

	def do_detach(self, dev, check=True):
		do_run(['sudo', '/sbin/losetup', '-d', dev], check=check)

class VirtBlockDeviceMacOS(VirtBlockDeviceBase):

	def __init__(self, img_path, size):
		self.img_path = Path(img_path + '.dmg').resolve()
		self.size = size

	def _get_associations(self):
		cp = run(['hdiutil', 'info'], stdout=PIPE, stderr=PIPE, text=True, check=False)
		if cp.returncode == 0:
			lines = cp.stdout.splitlines()
			out = [re.sub('.* ', '', s.strip()) for s in lines if re.match(r'image-path|/dev/', s)]
			def gen_pairs():
				for n in range(len(out) // 2):
					yield(out[n*2], out[(n*2)+1])
			return [dev for path, dev in gen_pairs() if path == str(self.img_path)]
		else:
			return []

	def get_new_dev(self):
		return None

	def do_create(self, size, path):
		do_run(['hdiutil', 'create', '-size', size, '-layout', 'NONE', str(path)])

	def do_attach(self, path, dev=None):
		do_run(['hdiutil', 'attach', '-nomount', str(path)])

	def do_detach(self, dev, check=True):
		do_run(['hdiutil', 'detach', dev], check=check)

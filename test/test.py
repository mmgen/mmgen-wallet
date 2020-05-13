#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>
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
test/test.py: Test suite for the MMGen wallet system
"""

def check_segwit_opts():
	for k,m in (('segwit','S'),('segwit_random','S'),('bech32','B')):
		if getattr(opt,k) and m not in g.proto.mmtypes:
			die(1,'--{} option incompatible with {}'.format(k.replace('_','-'),type(g.proto).__name__))

def create_shm_dir(data_dir,trash_dir):
	# Laggy flash media can cause pexpect to fail, so create a temporary directory
	# under '/dev/shm' and put datadir and tmpdirs here.
	import shutil
	from subprocess import run
	if g.platform == 'win':
		for tdir in (data_dir,trash_dir):
			try: os.listdir(tdir)
			except: pass
			else:
				try: shutil.rmtree(tdir)
				except: # we couldn't remove data dir - perhaps regtest daemon is running
					try:
						run(['python3',os.path.join('cmds','mmgen-regtest'),'stop'],check=True)
					except:
						rdie(1,"Unable to remove {!r}!".format(tdir))
					else:
						time.sleep(2)
						shutil.rmtree(tdir)
			os.mkdir(tdir,0o755)
		shm_dir = 'test'
	else:
		tdir,pfx = '/dev/shm','mmgen-test-'
		try:
			run('rm -rf {}/{}*'.format(tdir,pfx),shell=True,check=True)
		except Exception as e:
			die(2,'Unable to delete directory tree {}/{}* ({})'.format(tdir,pfx,e.args[0]))
		try:
			import tempfile
			shm_dir = str(tempfile.mkdtemp('',pfx,tdir))
		except Exception as e:
			die(2,'Unable to create temporary directory in {} ({})'.format(tdir,e.args[0]))

		dest = os.path.join(shm_dir,os.path.basename(trash_dir))
		os.mkdir(dest,0o755)

		run(f'rm -rf {trash_dir}',shell=True,check=True)
		os.symlink(dest,trash_dir)

		dest = os.path.join(shm_dir,os.path.basename(data_dir))
		shutil.move(data_dir,dest) # data_dir was created by opts.init()
		os.symlink(dest,data_dir)

	return shm_dir

import sys,os,time
from include.tests_header import repo_root

try: os.unlink(os.path.join(repo_root,'my.err'))
except: pass

from mmgen.common import *
from mmgen.daemon import CoinDaemon
from test.include.common import *
from test.test_py_d.common import *

g.quiet = False # if 'quiet' was set in config file, disable here
os.environ['MMGEN_QUIET'] = '0' # for this script and spawned scripts

opts_data = {
	'sets': [('list_current_cmd_groups',True,'list_cmd_groups',True)],
	'text': {
		'desc': 'Test suite for the MMGen suite',
		'usage':'[options] [command(s) or metacommand(s)]',
		'options': """
-h, --help           Print this help message
--, --longhelp       Print help message for long options (common options)
-A, --no-daemon-autostart Don't start and stop daemons automatically
-B, --bech32         Generate and use Bech32 addresses
-b, --buf-keypress   Use buffered keypresses as with real human input
                     (often required on slow systems, or under emulation)
-c, --print-cmdline  Print the command line of each spawned command
-C, --coverage       Produce code coverage info using trace module
-x, --debug-pexpect  Produce debugging output for pexpect calls
-D, --no-daemon-stop Don't stop auto-started daemons after running tests
-E, --direct-exec    Bypass pexpect and execute a command directly (for
                     debugging only)
-e, --exact-output   Show the exact output of the MMGen script(s) being run
-G, --exclude-groups=G Exclude the specified command groups (comma-separated)
-l, --list-cmds      List and describe the commands in the test suite
-L, --list-cmd-groups Output a list of command groups with descriptions
-g, --list-current-cmd-groups List command groups for current configuration
-n, --names          Display command names instead of descriptions
-o, --log            Log commands to file {lf}
-O, --pexpect-spawn  Use pexpect.spawn instead of popen_spawn (much slower,
                     kut does real terminal emulation)
-p, --pause          Pause between tests, resuming on keypress
-P, --profile        Record the execution time of each script
-q, --quiet          Produce minimal output.  Suppress dependency info
-r, --resume=c       Resume at command 'c' after interrupted run
-R, --resume-after=c Same, but resume at command following 'c'
-s, --system         Test scripts and modules installed on system rather
                     than those in the repo root
-S, --skip-deps      Skip dependency checking for command
-u, --usr-random     Get random data interactively from user
-t, --traceback      Run the command inside the '{tbc}' script
-T, --pexpect-timeout=T Set the timeout for pexpect
-v, --verbose        Produce more verbose output
-W, --no-dw-delete   Don't remove default wallet from data dir after dw tests are done
-X, --exit-after=C   Exit after command 'C'
-y, --segwit         Generate and use Segwit addresses
-Y, --segwit-random  Generate and use a random mix of Segwit and Legacy addrs
""",
		'notes': """

If no command is given, the whole test suite is run.
"""
	},
	'code': {
		'options': lambda s: s.format(
			tbc='scripts/traceback_run.py',
			lf=log_file),
	}
}

data_dir = os.path.join('test','data_dir' + ('','-α')[bool(os.getenv('MMGEN_DEBUG_UTF8'))])

# we need the values of two opts before running opts.init, so parse without initializing:
_uopts = opts.init(opts_data,parse_only=True).user_opts

# step 1: delete data_dir symlink in ./test;
if not ('resume' in _uopts or 'skip_deps' in _uopts):
	try: os.unlink(data_dir)
	except: pass

def get_coin():
	return (_uopts.get('coin') or 'btc').lower()

network_id = get_network_id(get_coin(),bool(_uopts.get('testnet')))

sys.argv.insert(1,'--data-dir=' + data_dir)
sys.argv.insert(1,'--daemon-data-dir=test/daemons/' + get_coin())
sys.argv.insert(1,'--rpc-port={}'.format(CoinDaemon(network_id,test_suite=True).rpc_port))

# step 2: opts.init will create new data_dir in ./test (if not 'resume' or 'skip_deps'):
usr_args = opts.init(opts_data)

# step 3: move data_dir to /dev/shm and symlink it back to ./test:
trash_dir = os.path.join('test','trash')
if not ('resume' in _uopts or 'skip_deps' in _uopts):
	shm_dir = create_shm_dir(data_dir,trash_dir)

check_segwit_opts()

if opt.profile:
	opt.names = True

if opt.exact_output:
	def msg(s): pass
	qmsg = qmsg_r = vmsg = vmsg_r = msg_r = msg

if opt.resume or opt.resume_after:
	opt.skip_deps = True
	resume = opt.resume or opt.resume_after
else:
	resume = False

cfgs = { # addr_idx_lists (except 31,32,33,34) must contain exactly 8 addresses
	'1':  { 'wpasswd':       'Dorian-α',
			'kapasswd':      'Grok the blockchain',
			'addr_idx_list': '12,99,5-10,5,12',
			'dep_generators':  {
				pwfile:        'walletgen',
				'mmdat':       'walletgen',
				'addrs':       'addrgen',
				'rawtx':       'txcreate',
				'txbump':      'txbump',
				'sigtx':       'txsign',
				'mmwords':     'export_mnemonic',
				'mmseed':      'export_seed',
				'mmhex':       'export_hex',
				'mmincog':     'export_incog',
				'mmincox':     'export_incog_hex',
				hincog_fn:     'export_incog_hidden',
				incog_id_fn:   'export_incog_hidden',
				'akeys.mmenc': 'keyaddrgen'
			},
	},
	'2':  { 'wpasswd':       'Hodling away',
			'addr_idx_list': '37,45,3-6,22-23',
			'seed_len':      128,
			'dep_generators': {
				'mmdat':   'walletgen2',
				'addrs':   'addrgen2',
				'rawtx':   'txcreate2',
				'sigtx':   'txsign2',
				'mmwords': 'export_mnemonic2',
			},
	},
	'3':  { 'wpasswd':       'Major miner',
			'addr_idx_list': '73,54,1022-1023,2-5',
			'dep_generators': {
				'mmdat': 'walletgen3',
				'addrs': 'addrgen3',
				'rawtx': 'txcreate3',
				'sigtx': 'txsign3'
			},
	},
	'4':  { 'wpasswd':       'Hashrate good',
			'addr_idx_list': '63,1004,542-544,7-9',
			'seed_len':      192,
			'dep_generators': {
				'mmdat':   'walletgen4',
				'mmbrain': 'walletgen4',
				'addrs':   'addrgen4',
				'rawtx':   'txcreate4',
				'sigtx':   'txsign4',
				'txdo':    'txdo4',
			},
			'bw_filename': 'brainwallet.mmbrain',
			'bw_params':   '192,1',
	},
	'5':  { 'wpasswd':     'My changed password-α',
			'hash_preset': '2',
			'dep_generators': {
				'mmdat': 'passchg',
				pwfile:  'passchg',
			},
	},
	'6':  { 'seed_len':       128,
			'seed_id':        'FE3C6545',
			'ref_bw_seed_id': '33F10310',
			'wpasswd':        'reference password',
			'kapasswd':      '',
			'dep_generators':  {
				'mmdat':       'ref_walletgen_brain_1',
				pwfile:        'ref_walletgen_brain_1',
				'addrs':       'refaddrgen_1',
				'akeys.mmenc': 'refkeyaddrgen_1'
			},
	},
	'7':  { 'seed_len':       192,
			'seed_id':        '1378FC64',
			'ref_bw_seed_id': 'CE918388',
			'wpasswd':        'reference password',
			'kapasswd':      '',
			'dep_generators':  {
				'mmdat':       'ref_walletgen_brain_2',
				pwfile:        'ref_walletgen_brain_2',
				'addrs':       'refaddrgen_2',
				'akeys.mmenc': 'refkeyaddrgen_2'
			},
	},
	'8':  { 'seed_len':       256,
			'seed_id':        '98831F3A',
			'ref_bw_seed_id': 'B48CD7FC',
			'wpasswd':        'reference password',
			'kapasswd':      '',
			'dep_generators':  {
				'mmdat':       'ref_walletgen_brain_3',
				pwfile:        'ref_walletgen_brain_3',
				'addrs':       'refaddrgen_3',
				'akeys.mmenc': 'refkeyaddrgen_3'
			},
	},
	'9':  { 'tool_enc_infn': 'tool_encrypt.in',
			'dep_generators': {
				'tool_encrypt.in':       'tool_encrypt',
				'tool_encrypt.in.mmenc': 'tool_encrypt',
			},
	},
	'14': { 'kapasswd':      'Maxwell',
			'wpasswd':       'The Halving',
			'addr_idx_list': '61,998,502-504,7-9',
			'seed_len':      256,
			'dep_generators': {
				'mmdat':       'walletgen14',
				'addrs':       'addrgen14',
				'akeys.mmenc': 'keyaddrgen14',
			},
	},
	'15': { 'wpasswd':       'Dorian-α',
			'kapasswd':      'Grok the blockchain',
			'addr_idx_list': '12,99,5-10,5,12',
			'dep_generators':  {
				pwfile:       'walletgen_dfl_wallet',
				'addrs':      'addrgen_dfl_wallet',
				'rawtx':      'txcreate_dfl_wallet',
				'sigtx':      'txsign_dfl_wallet',
				'mmseed':     'export_seed_dfl_wallet',
				'del_dw_run': 'delete_dfl_wallet',
			},
	},
	'16': { 'wpasswd':     'My changed password',
			'hash_preset': '2',
			'dep_generators': {
				pwfile: 'passchg_dfl_wallet',
			},
	},
	'17': {},
	'18': {},
	'19': { 'wpasswd':'abc' }, # B2X
	'20': { 'wpasswd':       'Vsize it',
			'addr_idx_list': '1-8',
			'seed_len':      256,
			'dep_generators': {
				'mmdat': 'walletgen5',
				'addrs': 'addrgen5',
				'rawtx': 'txcreate5',
				'sigtx': 'txsign5',
		},
	},
	'21': { 'wpasswd':       'Vsize it',
			'addr_idx_list': '1-8',
			'seed_len':      256,
			'dep_generators': {
				'mmdat': 'walletgen6',
				'addrs': 'addrgen6',
				'rawtx': 'txcreate6',
				'sigtx': 'txsign6',
		},
	},
	'22': {},
	'23': {},
	# 26,27,28 are taken
	'31': {},
	'32': {},
	'33': {},
	'34': {},
	'40': {},
	'41': {},
}

def fixup_cfgs():
	for k in ('6','7','8'):
		cfgs['2'+k] = {}
		cfgs['2'+k].update(cfgs[k])

	for k in cfgs:
		cfgs[k]['tmpdir'] = os.path.join('test','tmp{}'.format(k))
		cfgs[k]['segwit'] = randbool() if opt.segwit_random else bool(opt.segwit or opt.bech32)

	from copy import deepcopy
	for a,b in (('6','11'),('7','12'),('8','13')):
		cfgs[b] = deepcopy(cfgs[a])
		cfgs[b]['tmpdir'] = os.path.join('test','tmp'+b)

	if g.debug_utf8:
		for k in cfgs: cfgs[k]['tmpdir'] += '-α'

fixup_cfgs()

utils = {
#	'check_deps': 'check dependencies for specified command (WIP)', # TODO
	'clean':      'clean specified tmp dir(s) (specify by integer, no arg = all dirs)',
}

def list_cmds():
	gm = CmdGroupMgr()
	cw,d = 0,[]
	Msg(green('AVAILABLE COMMANDS:'))
	for gname in gm.cmd_groups:
		ts = gm.gm_init_group(None,gname,None)
		d.append((gname,ts.__doc__.strip(),gm.cmd_list,gm.dpy_data))
		cw = max(max(len(k) for k in gm.dpy_data),cw)

	for gname,gdesc,clist,dpdata in d:
		Msg('\n'+green('{!r} - {}:'.format(gname,gdesc)))
		for cmd in clist:
			data = dpdata[cmd]
			Msg('    {:{w}} - {}'.format(cmd,data if type(data) == str else data[1],w=cw))

	w = max(map(len,utils))
	Msg('\n'+green('AVAILABLE UTILITIES:'))
	for cmd in sorted(utils):
		Msg('  {:{w}} - {}'.format(cmd,utils[cmd],w=w))

	sys.exit(0)

def do_between():
	if opt.pause:
		confirm_continue()
	elif (opt.verbose or opt.exact_output) and not opt.skip_deps:
		sys.stderr.write('\n')

def list_tmpdirs():
	return {k:cfgs[k]['tmpdir'] for k in cfgs}

def clean(usr_dirs=None):
	if opt.skip_deps:
		return
	all_dirs = list_tmpdirs()
	dirnums = map(int,(usr_dirs if usr_dirs is not None else all_dirs))
	dirlist = list(map(str,sorted(dirnums)))
	for d in dirlist:
		if d in all_dirs:
			cleandir(all_dirs[d])
		else:
			die(1,'{}: invalid directory number'.format(d))
	if dirlist:
		iqmsg(green('Cleaned tmp director{} {}'.format(suf(dirlist,'ies'),' '.join(dirlist))))
	cleandir(data_dir)
	cleandir(trash_dir)
	iqmsg(green("Cleaned directories '{}'".format("' '".join([data_dir,trash_dir]))))

def create_tmp_dirs(shm_dir):
	if g.platform == 'win':
		for cfg in sorted(cfgs):
			mk_tmpdir(cfgs[cfg]['tmpdir'])
	else:
		for cfg in sorted(cfgs):
			src = os.path.join(shm_dir,cfgs[cfg]['tmpdir'].split('/')[-1])
			mk_tmpdir(src)
			try:
				os.unlink(cfgs[cfg]['tmpdir'])
			except OSError as e:
				if e.errno != 2: raise
			finally:
				os.symlink(src,cfgs[cfg]['tmpdir'])

def set_environ_for_spawned_scripts():

	from mmgen.term import get_terminal_size
	os.environ['MMGEN_TERMINAL_WIDTH'] = str(get_terminal_size().width)

	if os.getenv('MMGEN_DEBUG_ALL'):
		for name in g.env_opts:
			if name[:11] == 'MMGEN_DEBUG':
				os.environ[name] = '1'
	if not opt.pexpect_spawn: os.environ['MMGEN_TEST_SUITE_POPEN_SPAWN'] = '1'
	if not opt.system: os.environ['PYTHONPATH'] = repo_root
	if not opt.buf_keypress:
		os.environ['MMGEN_DISABLE_HOLD_PROTECT'] = '1'

	# If test.py itself is running under traceback, the spawned script shouldn't be, so disable this:
	if os.getenv('MMGEN_TRACEBACK') and not opt.traceback:
		os.environ['MMGEN_TRACEBACK'] = ''

	# Disable color in spawned scripts so pexpect can parse their output
	os.environ['MMGEN_DISABLE_COLOR'] = '1'
	os.environ['MMGEN_NO_LICENSE'] = '1'
	os.environ['MMGEN_MIN_URANDCHARS'] = '3'
	os.environ['MMGEN_BOGUS_SEND'] = '1'

def set_restore_term_at_exit():
	import termios,atexit
	fd = sys.stdin.fileno()
	old = termios.tcgetattr(fd)
	def at_exit():
		termios.tcsetattr(fd, termios.TCSADRAIN, old)
	atexit.register(at_exit)

class CmdGroupMgr(object):

	cmd_groups_dfl = {
		'opts':             ('TestSuiteOpts',{'full_data':True}),
		'cfg':              ('TestSuiteCfg',{'full_data':True}),
		'helpscreens':      ('TestSuiteHelp',{'modname':'misc','full_data':True}),
		'main':             ('TestSuiteMain',{'full_data':True}),
		'conv':             ('TestSuiteWalletConv',{'is3seed':True,'modname':'wallet'}),
		'ref':              ('TestSuiteRef',{}),
		'ref3':             ('TestSuiteRef3Seed',{'is3seed':True,'modname':'ref_3seed'}),
		'ref3_addr':        ('TestSuiteRef3Addr',{'is3seed':True,'modname':'ref_3seed'}),
		'ref_altcoin':      ('TestSuiteRefAltcoin',{}),
		'seedsplit':        ('TestSuiteSeedSplit',{}),
		'tool':             ('TestSuiteTool',{'full_data':True}),
		'input':            ('TestSuiteInput',{'full_data':True}),
		'output':           ('TestSuiteOutput',{'modname':'misc','full_data':True}),
		'autosign':         ('TestSuiteAutosign',{}),
		'regtest':          ('TestSuiteRegtest',{}),
#		'chainsplit':       ('TestSuiteChainsplit',{}),
		'ethdev':           ('TestSuiteEthdev',{}),
	}

	cmd_groups_extra = {
		'autosign_btc':     ('TestSuiteAutosignBTC',{'modname':'autosign'}),
		'autosign_live':    ('TestSuiteAutosignLive',{'modname':'autosign'}),
		'autosign_live_simulate': ('TestSuiteAutosignLiveSimulate',{'modname':'autosign'}),
		'create_ref_tx':    ('TestSuiteRefTX',{'modname':'misc','full_data':True}),
	}

	cmd_groups = cmd_groups_dfl.copy()
	cmd_groups.update(cmd_groups_extra)

	def load_mod(self,gname,modname=None):
		clsname,kwargs = self.cmd_groups[gname]
		if modname == None and 'modname' in kwargs:
			modname = kwargs['modname']
		import importlib
		modpath = 'test.test_py_d.ts_{}'.format(modname or gname)
		return getattr(importlib.import_module(modpath),clsname)

	def create_group(self,gname,full_data=False,modname=None,is3seed=False,add_dpy=False):
		"""
		Initializes the list 'cmd_list' and dict 'dpy_data' from module's cmd_group data.
		Alternatively, if called with 'add_dpy=True', updates 'dpy_data' from module data
		without touching 'cmd_list'
		"""

		cls = self.load_mod(gname,modname)
		cdata = []

		def get_shared_deps(cmdname,tmpdir_idx):
			"""
			shared_deps are "implied" dependencies for all cmds in cmd_group that don't appear in
			the cmd_group data or cmds' argument lists.  Supported only for 3seed tests at present.
			"""
			if not hasattr(cls,'shared_deps'):
				return []

			return [k for k,v in cfgs[str(tmpdir_idx)]['dep_generators'].items()
						if k in cls.shared_deps and v != cmdname]

		for a,b in cls.cmd_group:
			if is3seed:
				for n,(i,j) in enumerate(zip(cls.tmpdir_nums,(128,192,256))):
					k = '{}_{}'.format(a,n+1)
					if hasattr(cls,'skip_cmds') and k in cls.skip_cmds:
						continue
					sdeps = get_shared_deps(k,i)
					if type(b) == str:
						cdata.append( (k, (i,'{} ({}-bit)'.format(b,j),[[[]+sdeps,i]])) )
					else:
						cdata.append( (k, (i,'{} ({}-bit)'.format(b[1],j),[[b[0]+sdeps,i]])) )
			else:
				cdata.append( (a, b if full_data else (cls.tmpdir_nums[0],b,[[[],cls.tmpdir_nums[0]]])) )

		if add_dpy:
			self.dpy_data.update(dict(cdata))
		else:
			self.cmd_list = tuple(e[0] for e in cdata)
			self.dpy_data = dict(cdata)

		return cls

	def gm_init_group(self,trunner,gname,spawn_prog):
		kwargs = self.cmd_groups[gname][1]
		cls = self.create_group(gname,**kwargs)
		cls.group_name = gname
		return cls(trunner,cfgs,spawn_prog)

	def list_cmd_groups(self):
		ginfo = []
		for gname in self.cmd_groups:
			clsname,kwargs = self.cmd_groups[gname]
			cls = self.load_mod(gname,kwargs['modname'] if 'modname' in kwargs else None)
			ginfo.append((gname,cls))

		if opt.list_current_cmd_groups:
			exclude = (opt.exclude_groups or '').split(',')
			ginfo = [g for g in ginfo
						if network_id in g[1].networks
							and not g[0] in exclude
							and g[0] in self.cmd_groups_dfl + tuple(usr_args) ]

		for name,cls in ginfo:
			msg('{:17} - {}'.format(name,cls.__doc__))

		Die(0,'\n'+' '.join(e[0] for e in ginfo))

	def find_cmd_in_groups(self,cmd,group=None):
		"""
		Search for a test command in specified group or all configured command groups
		and return it as a string.  Loads modules but alters no global variables.
		"""
		if group:
			if not group in [e[0] for e in self.cmd_groups]:
				die(1,'{!r}: unrecognized group'.format(group))
			groups = [self.cmd_groups[group]]
		else:
			groups = self.cmd_groups

		for gname in groups:
			clsname,kwargs = self.cmd_groups[gname]
			cls = self.load_mod(gname,kwargs['modname'] if 'modname' in kwargs else None)
			if cmd in cls.cmd_group:             # first search the class
				return gname
			if cmd in dir(cls(None,None,None)):  # then a throwaway instance
				return gname # cmd might exist in more than one group - we'll go with the first
		return None

class TestSuiteRunner(object):
	'test suite runner'

	def __init__(self,data_dir,trash_dir):
		self.data_dir = data_dir
		self.trash_dir = trash_dir
		self.cmd_total = 0
		self.rebuild_list = {}
		self.gm = CmdGroupMgr()
		self.repo_root = repo_root
		self.skipped_warnings = []

		if opt.log:
			self.log_fd = open(log_file,'a')
			self.log_fd.write('\nLog started: {} UTC\n'.format(make_timestr()))
			omsg('INFO → Logging to file {!r}'.format(log_file))
		else:
			self.log_fd = None

		if opt.coverage:
			self.coverdir,self.accfile = init_coverage()
			omsg('INFO → Writing coverage files to {!r}'.format(self.coverdir))

	def spawn_wrapper(  self, cmd,
						args       = [],
						extra_desc = '',
						no_output  = False,
						msg_only   = False,
						no_msg     = False,
						cmd_dir    = 'cmds' ):

		desc = self.ts.test_name if opt.names else self.gm.dpy_data[self.ts.test_name][1]
		if extra_desc: desc += ' ' + extra_desc

		if not opt.system:
			cmd = os.path.relpath(os.path.join(repo_root,cmd_dir,cmd))
		elif g.platform == 'win':
			cmd = os.path.join('/mingw64','opt','bin',cmd)

		passthru_opts = ['--{}{}'.format(k.replace('_','-'),
							'=' + getattr(opt,k) if getattr(opt,k) != True else '')
								for k in self.ts.base_passthru_opts + self.ts.passthru_opts if getattr(opt,k)]

		args = [cmd] + passthru_opts + self.ts.extra_spawn_args + args

		if opt.traceback:
			args = ['scripts/traceback_run.py'] + args

		if g.platform == 'win':
			args = ['python3'] + args

		for i in args:
			if type(i) != str:
				m = 'Error: missing input files in cmd line?:\nName: {}\nCmdline: {!r}'
				die(2,m.format(self.ts.test_name,args))

		if opt.coverage:
			args = ['python3','-m','trace','--count','--coverdir='+self.coverdir,'--file='+self.accfile] + args

		qargs = ['{q}{}{q}'.format(a,q=('',"'")[' ' in a]) for a in args]
		cmd_disp = ' '.join(qargs).replace('\\','/') # for mingw

		if not no_msg:
			if opt.verbose or opt.print_cmdline or opt.exact_output:
				clr1,clr2 = ((green,cyan),(nocolor,nocolor))[bool(opt.print_cmdline)]
				omsg(green('Testing: {}'.format(desc)))
				if not msg_only:
					s = repr(cmd_disp) if g.platform == 'win' else cmd_disp
					omsg(clr1('Executing: ') + clr2(s))
			else:
				omsg_r('Testing {}: '.format(desc))

		if msg_only:
			return

		if opt.log:
			self.log_fd.write('[{}][{}:{}] {}\n'.format(
				g.coin.lower(),
				self.ts.group_name,
				self.ts.test_name,
				cmd_disp))

		from test.include.pexpect import MMGenPexpect
		return MMGenPexpect(args,no_output=no_output)

	def end_msg(self):
		t = int(time.time()) - self.start_time
		m = '{} test{} performed.  Elapsed time: {:02d}:{:02d}\n'
		sys.stderr.write(green(m.format(self.cmd_total,suf(self.cmd_total),t//60,t%60)))

	def init_group(self,gname,cmd=None,quiet=False):
		ts_cls = CmdGroupMgr().load_mod(gname)

		for k in ('segwit','segwit_random','bech32'):
			if getattr(opt,k):
				segwit_opt = k
				break
		else:
			segwit_opt = None

		m1 = ('test group {g!r}','{g}:{c}')[bool(cmd)].format(g=gname,c=cmd)
		m2 = ' for {} {}net'.format(g.coin.lower(),'test' if g.testnet else 'main') \
				if len(ts_cls.networks) != 1 else ''
		m3 = ' (--{})'.format(segwit_opt.replace('_','-')) if segwit_opt else ''
		m = m1 + m2 + m3

		if segwit_opt and not ts_cls.segwit_opts_ok:
			iqmsg('INFO → skipping ' + m)
			return False

		# 'networks = ()' means all networks allowed
		nws = [(e.split('_')[0],'testnet') if '_' in e else (e,'mainnet') for e in ts_cls.networks]
		if nws:
			coin = g.coin.lower()
			nw = ('mainnet','testnet')[g.testnet]
			for a,b in nws:
				if a == coin and b == nw:
					break
			else:
				iqmsg('INFO → skipping ' + m)
				return False

		if not quiet:
			bmsg('Executing ' + m)

		self.ts = self.gm.gm_init_group(self,gname,self.spawn_wrapper)

		if opt.resume_after:
			global resume
			resume = self.gm.cmd_list[self.gm.cmd_list.index(resume)+1]
			omsg(f'INFO → Resuming at command {resume!r}')

		if opt.exit_after and opt.exit_after not in self.gm.cmd_list:
			die(1,'{!r}: command not recognized'.format(opt.exit_after))

		return True

	def run_tests(self,usr_args):
		self.start_time = int(time.time())
		gname_save = None
		if usr_args:
			for arg in usr_args:
				if arg in self.gm.cmd_groups:
					if not self.init_group(arg):
						continue
					clean(self.ts.tmpdir_nums)
					for cmd in self.gm.cmd_list:
						self.check_needs_rerun(cmd,build=True)
						do_between()
				elif arg in utils:
					params = usr_args[usr_args.index(arg)+1:]
					globals()[arg](*params)
					sys.exit(0)
				else:
					if ':' in arg:
						gname,arg = arg.split(':')
					else:
						gname = self.gm.find_cmd_in_groups(arg)
					if gname:
						same_grp = gname == gname_save # same group as previous cmd: don't clean, suppress blue msg
						if not self.init_group(gname,arg,quiet=same_grp):
							continue
						if not same_grp:
							clean(self.ts.tmpdir_nums)
						self.check_needs_rerun(arg,build=True)
						do_between()
						gname_save = gname
					else:
						die(1,'{!r}: command not recognized'.format(arg))
		else:
			if opt.exclude_groups:
				exclude = opt.exclude_groups.split(',')
				for e in exclude:
					if e not in self.gm.cmd_groups_dfl:
						die(1,'{!r}: group not recognized'.format(e))
			for gname in self.gm.cmd_groups_dfl:
				if opt.exclude_groups and gname in exclude:
					continue
				if not self.init_group(gname):
					continue
				clean(self.ts.tmpdir_nums)
				for cmd in self.gm.cmd_list:
					self.check_needs_rerun(cmd,build=True)
					do_between()

		self.end_msg()

	def check_needs_rerun(self,
			cmd,
			build=False,
			root=True,
			force_delete=False,
			dpy=False
		):

		rerun = root # force_delete is not passed to recursive call

		fns = []
		if force_delete or not root:
			# does cmd produce a needed dependency(ies)?
			ret = self.get_num_exts_for_cmd(cmd,dpy)
			if ret:
				for ext in ret[1]:
					fn = get_file_with_ext(cfgs[ret[0]]['tmpdir'],ext,delete=build)
					if fn:
						if force_delete: os.unlink(fn)
						else: fns.append(fn)
					else: rerun = True

		fdeps = self.generate_file_deps(cmd)
		cdeps = self.generate_cmd_deps(fdeps)

		for fn in fns:
			my_age = os.stat(fn).st_mtime
			for num,ext in fdeps:
				f = get_file_with_ext(cfgs[num]['tmpdir'],ext,delete=build)
				if f and os.stat(f).st_mtime > my_age:
					rerun = True

		for cdep in cdeps:
			if self.check_needs_rerun(cdep,build=build,root=False,dpy=cmd):
				rerun = True

		if build:
			if rerun:
				for fn in fns:
					if not root: os.unlink(fn)
				if not (dpy and opt.skip_deps):
					self.run_test(cmd)
				if not root: do_between()
		else:
			# If prog produces multiple files:
			if cmd not in self.rebuild_list or rerun == True:
				self.rebuild_list[cmd] = (rerun,fns[0] if fns else '') # FIX

		return rerun

	def run_test(self,cmd):

		d = [(str(num),ext) for exts,num in self.gm.dpy_data[cmd][2] for ext in exts]

		# delete files depended on by this cmd
		arg_list = [get_file_with_ext(cfgs[num]['tmpdir'],ext) for num,ext in d]

		# remove shared_deps from arg list
		if hasattr(self.ts,'shared_deps'):
			arg_list = arg_list[:-len(self.ts.shared_deps)]

		global resume
		if resume:
			if cmd != resume:
				return
			bmsg('Resuming at {!r}'.format(cmd))
			resume = False
			opt.skip_deps = False

		if opt.profile: start = time.time()

		cdata = self.gm.dpy_data[cmd]
		self.ts.test_name = cmd
#		self.ts.test_dpydata = cdata
		self.ts.tmpdir_num = cdata[0]
#		self.ts.cfg = cfgs[str(cdata[0])] # will remove this eventually
		cfg = cfgs[str(cdata[0])]
		for k in (  'seed_len', 'seed_id',
					'wpasswd', 'kapasswd',
					'segwit', 'hash_preset',
					'bw_filename', 'bw_params', 'ref_bw_seed_id',
					'addr_idx_list', 'pass_idx_list' ):
			if k in cfg:
				setattr(self.ts,k,cfg[k])

		ret = getattr(self.ts,cmd)(*arg_list) # run the test
		if type(ret).__name__ == 'coroutine':
			ret = run_session(ret)
		self.process_retval(cmd,ret)

		if opt.profile:
			omsg('\r\033[50C{:.4f}'.format(time.time() - start))

		if cmd == opt.exit_after:
			sys.exit(0)

	def warn_skipped(self):
		if self.skipped_warnings:
			print(yellow('The following tests were skipped and may require attention:'))
			r = '-' * 72 + '\n'
			print(r+('\n'+r).join(self.skipped_warnings))

	def process_retval(self,cmd,ret):
		if type(ret).__name__ == 'MMGenPexpect':
			ret.ok()
			self.cmd_total += 1
		elif ret == 'ok':
			ok()
			self.cmd_total += 1
		elif ret == 'skip':
			pass
		elif type(ret) == tuple and ret[0] == 'skip_warn':
			self.skipped_warnings.append(
				'Test {!r} was skipped:\n  {}'.format(cmd,'\n  '.join(ret[1].split('\n'))))
		else:
			rdie(1,'{!r} returned {}'.format(cmd,ret))

	def check_deps(self,cmds): # TODO: broken
		if len(cmds) != 1:
			die(1,'Usage: {} check_deps <command>'.format(g.prog_name))

		cmd = cmds[0]

		if cmd not in self.gm.cmd_list:
			die(1,'{!r}: unrecognized command'.format(cmd))

		if not opt.quiet:
			omsg('Checking dependencies for {!r}'.format(cmd))

		self.check_needs_rerun(self.ts,cmd,build=False)

		w = max(map(len,self.rebuild_list)) + 1
		for cmd in self.rebuild_list:
			c = self.rebuild_list[cmd]
			m = 'Rebuild' if (c[0] and c[1]) else 'Build' if c[0] else 'OK'
			omsg('cmd {:<{w}} {}'.format(cmd+':', m, w=w))

	def generate_file_deps(self,cmd):
		return [(str(n),e) for exts,n in self.gm.dpy_data[cmd][2] for e in exts]

	def generate_cmd_deps(self,fdeps):
		return [cfgs[str(n)]['dep_generators'][ext] for n,ext in fdeps]

	def get_num_exts_for_cmd(self,cmd,dpy=False): # dpy ignored here
		try:
			num = str(self.gm.dpy_data[cmd][0])
		except KeyError:
			qmsg_r('Missing dependency {!r}'.format(cmd))
			gname = self.gm.find_cmd_in_groups(cmd)
			if gname:
				kwargs = self.gm.cmd_groups[gname][1]
				kwargs.update({'add_dpy':True})
				self.gm.create_group(gname,**kwargs)
				num = str(self.gm.dpy_data[cmd][0])
				qmsg(' found in group {!r}'.format(gname))
			else:
				qmsg(' not found in any command group!')
				raise
		dgl = cfgs[num]['dep_generators']
		if cmd in dgl.values():
			exts = [k for k in dgl if dgl[k] == cmd]
			return (num,exts)
		else:
			return None

# main()

if not opt.skip_deps: # do this before list cmds exit, so we stay in sync with shm_dir
	create_tmp_dirs(shm_dir)

if opt.list_cmd_groups:
	CmdGroupMgr().list_cmd_groups()
elif opt.list_cmds:
	list_cmds()

if opt.pause:
	set_restore_term_at_exit()

set_environ_for_spawned_scripts()
if network_id not in ('eth','etc'):
	start_test_daemons(network_id)

try:
	tr = TestSuiteRunner(data_dir,trash_dir)
	tr.run_tests(usr_args)
	tr.warn_skipped()
	if network_id not in ('eth','etc'):
		stop_test_daemons(network_id)
except KeyboardInterrupt:
	if network_id not in ('eth','etc'):
		stop_test_daemons(network_id)
	tr.warn_skipped()
	die(1,'\ntest.py exiting at user request')
except TestSuiteException as e:
	ydie(1,e.args[0])
except TestSuiteFatalException as e:
	rdie(1,e.args[0])
except Exception:
	if opt.traceback:
		msg(blue('Spawned script exited with error'))
	else:
		import traceback
		print(''.join(traceback.format_exception(*sys.exc_info())))
		msg(blue('Test script exited with error'))
	raise
except:
	raise

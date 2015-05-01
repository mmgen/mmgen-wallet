#!/usr/bin/env python

# Chdir to repo root.
# Since script is not in repo root, fix sys.path so that modules are
# imported from repo, not system.
import sys,os
pn = os.path.dirname(sys.argv[0])
os.chdir(os.path.join(pn,os.pardir))
sys.path.__setitem__(0,os.path.abspath(os.curdir))

scripts = (
	"addrgen", "addrimport", "keygen",
	"passchg", "pywallet", "tool",
	"txcreate", "txsend", "txsign",
	"walletchk", "walletconv", "walletgen"
)

import mmgen.globalvars as g
import mmgen.opt as opt
from mmgen.util import mmsg,mdie,Msg,die,capfirst,write_data_to_file
from mmgen.test import *

if sys.platform[:3] == "win":
	try:
		import colorama
		colorama.init(strip=True,convert=True)
	except:
		def nocolor(s): return s
		red = green = yellow = cyan = nocolor

tb_cmd = "scripts/traceback.py"
hincog_fn      = "rand_data"
hincog_bytes   = 1024*1024
hincog_offset  = 98765
hincog_seedlen = 256

incog_id_fn  = "incog_id"
non_mmgen_fn = "btckey"
pwfile = "passwd_file"

ref_dir = os.path.join("test","ref")

ref_wallet_brainpass = "abc"
ref_wallet_hash_preset = "1"
ref_wallet_incog_offset = 123

ref_bw_hash_preset = "1"
ref_bw_file        = "wallet.mmbrain"
ref_bw_file_spc    = "wallet-spaced.mmbrain"

ref_kafile_pass        = "kafile password"
ref_kafile_hash_preset = "1"

ref_enc_fn = "sample-text.mmenc"
tool_enc_passwd = "Scrypt it, don't hash it!"
sample_text = \
	"The Times 03/Jan/2009 Chancellor on brink of second bailout for banks\n"

cfgs = {
	'1': {
		'tmpdir':        os.path.join("test","tmp1"),
		'wpasswd':       "Dorian",
		'kapasswd':      "Grok the blockchain",
		'addr_idx_list': "12,99,5-10,5,12", # 8 addresses
		'dep_generators':  {
			pwfile:        "walletgen",
			'mmdat':       "walletgen",
			'addrs':       "addrgen",
			'raw':         "txcreate",
			'sig':         "txsign",
			'mmwords':     "export_mnemonic",
			'mmseed':      "export_seed",
			'mmincog':     "export_incog",
			'mmincox':     "export_incog_hex",
			hincog_fn:     "export_incog_hidden",
			incog_id_fn:   "export_incog_hidden",
			'akeys.mmenc': "keyaddrgen"
		},
	},
	'2': {
		'tmpdir':        os.path.join("test","tmp2"),
		'wpasswd':       "Hodling away",
		'addr_idx_list': "37,45,3-6,22-23",  # 8 addresses
		'seed_len':      128,
		'dep_generators': {
			'mmdat':       "walletgen2",
			'addrs':       "addrgen2",
			'raw':         "txcreate2",
			'sig':         "txsign2",
			'mmwords':     "export_mnemonic2",
		},
	},
	'3': {
		'tmpdir':        os.path.join("test","tmp3"),
		'wpasswd':       "Major miner",
		'addr_idx_list': "73,54,1022-1023,2-5", # 8 addresses
		'dep_generators': {
			'mmdat':       "walletgen3",
			'addrs':       "addrgen3",
			'raw':         "txcreate3",
			'sig':         "txsign3"
		},
	},
	'4': {
		'tmpdir':        os.path.join("test","tmp4"),
		'wpasswd':       "Hashrate rising",
		'addr_idx_list': "63,1004,542-544,7-9", # 8 addresses
		'seed_len':      192,
		'dep_generators': {
			'mmdat':       "walletgen4",
			'mmbrain':     "walletgen4",
			'addrs':       "addrgen4",
			'raw':         "txcreate4",
			'sig':         "txsign4",
		},
		'bw_filename': "brainwallet.mmbrain",
		'bw_params':   "192,1",
	},
	'5': {
		'tmpdir':        os.path.join("test","tmp5"),
		'wpasswd':       "My changed password",
		'hash_preset':   '2',
		'dep_generators': {
			'mmdat':       "passchg",
			pwfile:        "passchg",
		},
	},
	'6': {
		'name':            "reference wallet check (128-bit)",
		'seed_len':        128,
		'seed_id':         "FE3C6545",
		'ref_bw_seed_id':  "33F10310",
		'addrfile_chk':    "B230 7526 638F 38CB 8FDC 8B76",
		'keyaddrfile_chk': "CF83 32FB 8A8B 08E2 0F00 D601",
		'wpasswd':         "reference password",
		'ref_wallet':      "FE3C6545-D782B529[128,1].mmdat",
		'ic_wallet':       "FE3C6545-E29303EA-5E229E30[128,1].mmincog",
		'ic_wallet_hex':   "FE3C6545-BC4BE3F2-32586837[128,1].mmincox",

		'hic_wallet':       "FE3C6545-161E495F-BEB7548E[128:1].incog-offset123",
		'hic_wallet_old':   "FE3C6545-161E495F-9860A85B[128:1].incog-old.offset123",

		'tmpdir':        os.path.join("test","tmp6"),
		'kapasswd':      "",
		'addr_idx_list': "1010,500-501,31-33,1,33,500,1011", # 8 addresses
		'dep_generators':  {
			'mmdat':       "refwalletgen1",
			'addrs':       "refaddrgen1",
			'akeys.mmenc': "refkeyaddrgen1"
		},

	},
	'7': {
		'name':            "reference wallet check (192-bit)",
		'seed_len':        192,
		'seed_id':         "1378FC64",
		'ref_bw_seed_id':  "CE918388",
		'addrfile_chk':    "8C17 A5FA 0470 6E89 3A87 8182",
		'keyaddrfile_chk': "9648 5132 B98E 3AD9 6FC3 C5AD",
		'wpasswd':         "reference password",
		'ref_wallet':      "1378FC64-6F0F9BB4[192,1].mmdat",
		'ic_wallet':       "1378FC64-2907DE97-F980D21F[192,1].mmincog",
		'ic_wallet_hex':   "1378FC64-4DCB5174-872806A7[192,1].mmincox",

		'hic_wallet':       "1378FC64-B55E9958-77256FC1[192:1].incog.offset123",
		'hic_wallet_old':   "1378FC64-B55E9958-D85FF20C[192:1].incog-old.offset123",

		'tmpdir':        os.path.join("test","tmp7"),
		'kapasswd':      "",
		'addr_idx_list': "1010,500-501,31-33,1,33,500,1011", # 8 addresses
		'dep_generators':  {
			'mmdat':       "refwalletgen2",
			'addrs':       "refaddrgen2",
			'akeys.mmenc': "refkeyaddrgen2"
		},

	},
	'8': {
		'name':            "reference wallet check (256-bit)",
		'seed_len':        256,
		'seed_id':         "98831F3A",
		'ref_bw_seed_id':  "B48CD7FC",
		'addrfile_chk':    "6FEF 6FB9 7B13 5D91 854A 0BD3",
		'keyaddrfile_chk': "9F2D D781 1812 8BAD C396 9DEB",
		'wpasswd':         "reference password",
		'ref_wallet':      "98831F3A-27F2BF93[256,1].mmdat",
		'ref_addrfile':    "98831F3A[1,31-33,500-501,1010-1011].addrs",
		'ref_keyaddrfile': "98831F3A[1,31-33,500-501,1010-1011].akeys.mmenc",
		'ref_addrfile_chksum':    "6FEF 6FB9 7B13 5D91 854A 0BD3",
		'ref_keyaddrfile_chksum': "9F2D D781 1812 8BAD C396 9DEB",

#		'ref_fake_unspent_data':"98831F3A_unspent.json",
		'ref_tx_file':     "tx_FFB367[1.234].raw",
		'ic_wallet':       "98831F3A-5482381C-18460FB1[256,1].mmincog",
		'ic_wallet_hex':   "98831F3A-1630A9F2-870376A9[256,1].mmincox",

		'hic_wallet':       "98831F3A-F59B07A0-559CEF19[256:1].incog.offset123",
		'hic_wallet_old':   "98831F3A-F59B07A0-848535F3[256:1].incog-old.offset123",

		'tmpdir':        os.path.join("test","tmp8"),
		'kapasswd':      "",
		'addr_idx_list': "1010,500-501,31-33,1,33,500,1011", # 8 addresses
		'dep_generators':  {
			'mmdat':       "refwalletgen3",
			'addrs':       "refaddrgen3",
			'akeys.mmenc': "refkeyaddrgen3"
		},
	},
	'9': {
		'tmpdir':        os.path.join("test","tmp9"),
		'tool_enc_infn':      "tool_encrypt.in",
#		'tool_enc_ref_infn':  "tool_encrypt_ref.in",
		'wpasswd':         "reference password",
		'dep_generators': {
			'tool_encrypt.in':            "tool_encrypt",
			'tool_encrypt.in.mmenc':      "tool_encrypt",
#			'tool_encrypt_ref.in':        "tool_encrypt_ref",
#			'tool_encrypt_ref.in.mmenc':  "tool_encrypt_ref",
		},
	},
}

from copy import deepcopy
for a,b in ('6','11'),('7','12'),('8','13'):
	cfgs[b] = deepcopy(cfgs[a])
	cfgs[b]['tmpdir'] = os.path.join("test","tmp"+b)

from collections import OrderedDict
cmd_data = OrderedDict([
#     test               description                  depends
	['helpscreens',     (1,'help screens',             [],1)],
	['walletgen',       (1,'wallet generation',        [[[],1]],1)],
#	['walletchk',       (1,'wallet check',             [[["mmdat"],1]])],
	['passchg',         (5,'password, label and hash preset change',[[["mmdat",pwfile],1]],1)],
	['walletchk_newpass',(5,'wallet check with new pw, label and hash preset',[[["mmdat",pwfile],5]],1)],
	['addrgen',         (1,'address generation',       [[["mmdat",pwfile],1]],1)],
	['addrimport',      (1,'address import',           [[["addrs"],1]],1)],
	['txcreate',        (1,'transaction creation',     [[["addrs"],1]],1)],
	['txsign',          (1,'transaction signing',      [[["mmdat","raw",pwfile],1]],1)],
	['txsend',          (1,'transaction sending',      [[["sig"],1]])],

	['export_seed',     (1,'seed export to mmseed format',   [[["mmdat"],1]])],
	['export_mnemonic', (1,'seed export to mmwords format',  [[["mmdat"],1]])],
	['export_incog',    (1,'seed export to mmincog format',  [[["mmdat"],1]])],
	['export_incog_hex',(1,'seed export to mmincog hex format', [[["mmdat"],1]])],
	['export_incog_hidden',(1,'seed export to hidden mmincog format', [[["mmdat"],1]])],

	['addrgen_seed',    (1,'address generation from mmseed file', [[["mmseed","addrs"],1]])],
	['addrgen_mnemonic',(1,'address generation from mmwords file',[[["mmwords","addrs"],1]])],
	['addrgen_incog',   (1,'address generation from mmincog file',[[["mmincog","addrs"],1]])],
	['addrgen_incog_hex',(1,'address generation from mmincog hex file',[[["mmincox","addrs"],1]])],
	['addrgen_incog_hidden',(1,'address generation from hidden mmincog file', [[[hincog_fn,"addrs"],1]])],

	['keyaddrgen',    (1,'key-address file generation', [[["mmdat"],1]])],
	['txsign_keyaddr',(1,'transaction signing with key-address file', [[["akeys.mmenc","raw"],1]])],

	['walletgen2',(2,'wallet generation (2), 128-bit seed',     [])],
	['addrgen2',  (2,'address generation (2)',    [[["mmdat"],2]])],
	['txcreate2', (2,'transaction creation (2)',  [[["addrs"],2]])],
	['txsign2',   (2,'transaction signing, two transactions',[[["mmdat","raw"],1],[["mmdat","raw"],2]])],
	['export_mnemonic2', (2,'seed export to mmwords format (2)',[[["mmdat"],2]])],

	['walletgen3',(3,'wallet generation (3)',                  [])],
	['addrgen3',  (3,'address generation (3)',                 [[["mmdat"],3]])],
	['txcreate3', (3,'tx creation with inputs and outputs from two wallets', [[["addrs"],1],[["addrs"],3]])],
	['txsign3',   (3,'tx signing with inputs and outputs from two wallets',[[["mmdat"],1],[["mmdat","raw"],3]])],

	['walletgen4',(4,'wallet generation (4) (brainwallet)',    [])],
	['addrgen4',  (4,'address generation (4)',                 [[["mmdat"],4]])],
	['txcreate4', (4,'tx creation with inputs and outputs from four seed sources, plus non-MMGen inputs and outputs', [[["addrs"],1],[["addrs"],2],[["addrs"],3],[["addrs"],4]])],
	['txsign4',   (4,'tx signing with inputs and outputs from incog file, mnemonic file, wallet and brainwallet, plus non-MMGen inputs and outputs', [[["mmincog"],1],[["mmwords"],2],[["mmdat"],3],[["mmbrain","raw"],4]])],
	['tool_encrypt',     (9,"'mmgen-tool encrypt' (random data)",     [])],
	['tool_decrypt',     (9,"'mmgen-tool decrypt' (random data)", [[[cfgs['9']['tool_enc_infn'],cfgs['9']['tool_enc_infn']+".mmenc"],9]])],
#	['tool_encrypt_ref', (9,"'mmgen-tool encrypt' (reference text)",  [])],
	['tool_find_incog_data', (9,"'mmgen-tool find_incog_data'", [[[hincog_fn],1],[[incog_id_fn],1]])],
	['pywallet', (9,"'mmgen-pywallet'", [],1)],
])

# saved reference data
cmd_data_ref = (
	# reading
	('ref_wallet_chk', ([],'saved reference wallet')),
	('ref_seed_chk',   ([],'saved seed file')),
	('ref_mn_chk',     ([],'saved mnemonic file')),
	('ref_hincog_chk', ([],'saved hidden incog reference wallet')),
	('ref_brain_chk',  ([],'saved brainwallet')),
	# generating new reference ('abc' brainwallet) files:
	('refwalletgen',   ([],'gen new refwallet')),
	('refaddrgen',     (["mmdat"],'new refwallet addr chksum')),
	('refkeyaddrgen',  (["mmdat"],'new refwallet key-addr chksum'))
)

# misc. saved reference data
cmd_data_ref_other = (
	('ref_addrfile_chk',   'saved reference address file'),
	('ref_keyaddrfile_chk','saved reference key-address file'),
#	Create the fake inputs:
#	('txcreate8',          'transaction creation (8)'),
	('ref_tx_chk',         'saved reference tx file'),
	('ref_brain_chk_spc3', 'saved brainwallet (non-standard spacing)'),
	('ref_tool_decrypt',   'decryption of saved MMGen-encrypted file'),
)

# mmgen-walletconv:
cmd_data_conv_in = ( # reading
	('ref_wallet_conv',    'conversion of saved reference wallet'),
	('ref_mn_conv',        'conversion of saved mnemonic'),
	('ref_seed_conv',      'conversion of saved seed file'),
	('ref_brain_conv',     'conversion of ref brainwallet'),
	('ref_incog_conv',     'conversion of saved incog wallet'),
	('ref_incox_conv',     'conversion of saved hex incog wallet'),
	('ref_hincog_conv',    'conversion of saved hidden incog wallet'),
	('ref_hincog_conv_old','conversion of saved hidden incog wallet (old format)')
)
cmd_data_conv_out = ( # writing
	('ref_wallet_conv_out', 'ref seed conversion to wallet'),
	('ref_mn_conv_out',     'ref seed conversion to mnemonic'),
	('ref_seed_conv_out',   'ref seed conversion to seed'),
	('ref_incog_conv_out',  'ref seed conversion to incog data'),
	('ref_incox_conv_out',  'ref seed conversion to hex incog data'),
	('ref_hincog_conv_out', 'ref seed conversion to hidden incog data')
)

cmd_groups = OrderedDict([
	('main',      cmd_data.keys()),
	('ref',       [c[0]+str(i) for c in cmd_data_ref for i in (1,2,3)]),
	('ref_other', [c[0] for c in cmd_data_ref_other]),
	('conv_in',   [c[0]+str(i) for c in cmd_data_conv_in for i in (1,2,3)]),
	('conv_out',  [c[0]+str(i) for c in cmd_data_conv_out for i in (1,2,3)]),
])

for a,b in cmd_data_ref:
	for i,j in (1,128),(2,192),(3,256):
		cmd_data[a+str(i)] = (5+i,"%s (%s-bit)" % (b[1],j),[[b[0],5+i]])

for a,b in cmd_data_ref_other:
	cmd_data[a] = (8,b,[[[],8]])

for a,b in cmd_data_conv_in:
	for i,j in (1,128),(2,192),(3,256):
		cmd_data[a+str(i)] = (10+i,"%s (%s-bit)" % (b,j),[[[],10+i]])

for a,b in cmd_data_conv_out:
	for i,j in (1,128),(2,192),(3,256):
		cmd_data[a+str(i)] = (10+i,"%s (%s-bit)" % (b,j),[[[],10+i]])

utils = {
	'check_deps': 'check dependencies for specified command',
	'clean':      'clean specified tmp dir(s) 1,2,3,4,5 or 6 (no arg = all dirs)',
}

addrs_per_wallet = 8

# total of two outputs must be < 10 BTC
for k in cfgs.keys():
	cfgs[k]['amts'] = [0,0]
	for idx,mod in (0,6),(1,4):
		cfgs[k]['amts'][idx] = "%s.%s" % ((getrandnum(2) % mod), str(getrandnum(4))[:5])

meta_cmds = OrderedDict([
	['ref1', ("refwalletgen1","refaddrgen1","refkeyaddrgen1")],
	['ref2', ("refwalletgen2","refaddrgen2","refkeyaddrgen2")],
	['ref3', ("refwalletgen3","refaddrgen3","refkeyaddrgen3")],
	['gen',  ("walletgen","addrgen")],
	['pass', ("passchg","walletchk_newpass")],
	['tx',   ("addrimport","txcreate","txsign","txsend")],
	['export', [k for k in cmd_data if k[:7] == "export_" and cmd_data[k][0] == 1]],
	['gen_sp', [k for k in cmd_data if k[:8] == "addrgen_" and cmd_data[k][0] == 1]],
	['online', ("keyaddrgen","txsign_keyaddr")],
	['2', [k for k in cmd_data if cmd_data[k][0] == 2]],
	['3', [k for k in cmd_data if cmd_data[k][0] == 3]],
	['4', [k for k in cmd_data if cmd_data[k][0] == 4]],

	['tool', ("tool_encrypt","tool_decrypt","tool_find_incog_data","pywallet")],

	['saved_ref1', [c[0]+"1" for c in cmd_data_ref]],
	['saved_ref2', [c[0]+"2" for c in cmd_data_ref]],
	['saved_ref3', [c[0]+"3" for c in cmd_data_ref]],

	['saved_ref_other', [c[0] for c in cmd_data_ref_other]],

	['saved_ref_conv_in1', [c[0]+"1" for c in cmd_data_conv_in]],
	['saved_ref_conv_in2', [c[0]+"2" for c in cmd_data_conv_in]],
	['saved_ref_conv_in3', [c[0]+"3" for c in cmd_data_conv_in]],

	['saved_ref_conv_out1', [c[0]+"1" for c in cmd_data_conv_out]],
	['saved_ref_conv_out2', [c[0]+"2" for c in cmd_data_conv_out]],
	['saved_ref_conv_out3', [c[0]+"3" for c in cmd_data_conv_out]],
])

opts_data = {
#	'sets': [('non_interactive',bool,'verbose',None)],
	'desc': "Test suite for the MMGen suite",
	'usage':"[options] [command(s) or metacommand(s)]",
	'options': """
-h, --help          Print this help message.
-b, --buf-keypress  Use buffered keypresses as with real human input.
-d, --debug-scripts Turn on debugging output in executed scripts.
-D, --direct-exec   Bypass pexpect and execute a command directly (for
                    debugging only).
-e, --exact-output  Show the exact output of the MMGen script(s) being run.
-l, --list-cmds     List and describe the commands in the test suite.
-n, --names         Display command names instead of descriptions.
-I, --non-interactive Non-interactive operation (MS Windows mode)
-p, --pause         Pause between tests, resuming on keypress.
-q, --quiet         Produce minimal output.  Suppress dependency info.
-s, --system        Test scripts and modules installed on system rather
                    than those in the repo root.
-t, --traceback     Run the command inside the '{tb_cmd}' script.
-v, --verbose       Produce more verbose output.
""".format(tb_cmd=tb_cmd),
	'notes': """

If no command is given, the whole suite of tests is run.
"""
}

cmd_args = opt.opts.init(opts_data)

if opt.system: sys.path.pop(0)
ni = bool(opt.non_interactive)

# temporary
#os.environ["MMGEN_USE_OLD_SCRIPTS"] = "1"

if opt.debug_scripts: os.environ["MMGEN_DEBUG"] = "1"

if opt.buf_keypress:
	send_delay = 0.3
else:
	send_delay = 0
	os.environ["MMGEN_DISABLE_HOLD_PROTECT"] = "1"

if opt.exact_output:
	def msg(s): pass
	vmsg = vmsg_r = msg_r = msg
else:
	def msg(s): sys.stderr.write(s+"\n")
	def vmsg(s):
		if opt.verbose: sys.stderr.write(s+"\n")
	def msg_r(s): sys.stderr.write(s)
	def vmsg_r(s):
		if opt.verbose: sys.stderr.write(s)

stderr_save = sys.stderr

def silence():
	if not (opt.verbose or opt.exact_output):
		f = ("/dev/null","stderr.out")[int(sys.platform[:3] == "win")]
		sys.stderr = open(f,"a")

def end_silence():
	if not (opt.verbose or opt.exact_output):
		sys.stderr = stderr_save

def errmsg(s): stderr_save.write(s+"\n")
def errmsg_r(s): stderr_save.write(s)

if opt.list_cmds:
	fs = "  {:<{w}} - {}"
	Msg("AVAILABLE COMMANDS:")
	w = max([len(i) for i in cmd_data])
	for cmd in cmd_data:
		Msg(fs.format(cmd,cmd_data[cmd][1],w=w))

	w = max([len(i) for i in meta_cmds])
	Msg("\nAVAILABLE METACOMMANDS:")
	for cmd in meta_cmds:
		Msg(fs.format(cmd," ".join(meta_cmds[cmd]),w=w))

	w = max([len(i) for i in cmd_groups.keys()])
	Msg("\nAVAILABLE COMMAND GROUPS:")
	for g in cmd_groups.keys():
		Msg(fs.format(g," ".join(cmd_groups[g]),w=w))

	Msg("\nAVAILABLE UTILITIES:")
	w = max([len(i) for i in utils])
	for cmd in sorted(utils):
		Msg(fs.format(cmd,utils[cmd],w=w))
	sys.exit()

import time,re
try:
	import pexpect
except: # Windows
	msg(red("MS Windows detected (or missing pexpect module).  Running in non-interactive mode"))
	ni = True

from mmgen.util import get_data_from_file,write_to_file,get_lines_from_file

def my_send(p,t,delay=send_delay,s=False):
	if delay: time.sleep(delay)
	ret = p.send(t) # returns num bytes written
	if delay: time.sleep(delay)
	if opt.verbose:
		ls = "" if opt.debug or not s else " "
		es = "" if s else "  "
		msg("%sSEND %s%s" % (ls,es,yellow("'%s'"%t.replace('\n',r'\n'))))
	return ret

def my_expect(p,s,t='',delay=send_delay,regex=False,nonl=False):
	quo = "'" if type(s) == str else ""

	if opt.verbose: msg_r("EXPECT %s" % yellow(quo+str(s)+quo))
	else:       msg_r("+")

	try:
		if s == '': ret = 0
		else:
			f = p.expect if regex else p.expect_exact
			ret = f(s,timeout=3)
	except pexpect.TIMEOUT:
		errmsg(red("\nERROR.  Expect %s%s%s timed out.  Exiting" % (quo,s,quo)))
		sys.exit(1)

	if opt.debug or (opt.verbose and type(s) != str): msg_r(" ==> %s " % ret)

	if ret == -1:
		errmsg("Error.  Expect returned %s" % ret)
		sys.exit(1)
	else:
		if t == '':
			if not nonl: vmsg("")
		else:
			my_send(p,t,delay,s)
		return ret

def get_file_with_ext(ext,mydir,delete=True):

	flist = [os.path.join(mydir,f) for f in os.listdir(mydir)
				if f == ext or f[-(len(ext)+1):] == "."+ext]

	if not flist: return False

	if len(flist) > 1:
		if delete:
			if not opt.quiet:
				msg("Multiple *.%s files in '%s' - deleting" % (ext,mydir))
			for f in flist: os.unlink(f)
		return False
	else:
		return flist[0]

def get_addrfile_checksum(display=False):
	addrfile = get_file_with_ext("addrs",cfg['tmpdir'])
	silence()
	from mmgen.addr import AddrInfo
	chk = AddrInfo(addrfile).checksum
	if opt.verbose and display: msg("Checksum: %s" % cyan(chk))
	end_silence()
	return chk

def verify_checksum_or_exit(checksum,chk):
	if checksum != chk:
		errmsg(red("Checksum error: %s" % chk))
		sys.exit(1)
	vmsg(green("Checksums match: %s") % (cyan(chk)))


class MMGenExpect(object):

	def __init__(self,name,mmgen_cmd,cmd_args=[],extra_desc="",no_output=False):
		if not opt.system:
			mmgen_cmd = os.path.join(os.curdir,mmgen_cmd)
		desc = (cmd_data[name][1],name)[int(bool(opt.names))]
		if extra_desc: desc += " " + extra_desc
		if opt.verbose or opt.exact_output:
			sys.stderr.write(
				green("Testing: %s\nExecuting " % desc) +
				cyan("'%s %s'\n" % (mmgen_cmd," ".join(cmd_args)))
			)
		else:
			msg_r("Testing %s: " % desc)

		if opt.direct_exec or ni:
			msg("")
			from subprocess import check_call,check_output
			f = (check_call,check_output)[int(no_output)]
			f(["python", mmgen_cmd] + cmd_args)
		else:
			if opt.traceback:
				cmd_args = [mmgen_cmd] + cmd_args
				mmgen_cmd = tb_cmd
			self.p = pexpect.spawn(mmgen_cmd,cmd_args)
			if opt.exact_output: self.p.logfile = sys.stdout

	def license(self):
		p = "'w' for conditions and warranty info, or 'c' to continue: "
		my_expect(self.p,p,'c')

	def label(self,label="Test Label"):
		p = "Enter a wallet label, or hit ENTER for no label: "
		my_expect(self.p,p,label+"\n")

	def usr_rand_out(self,saved=False):
		m = "%suser-supplied entropy" % ("saved " if saved else "")
		my_expect(self.p,"Generating encryption key from OS random data plus " + m)

	def usr_rand(self,num_chars):
		rand_chars = list(getrandstr(num_chars,no_space=True))
		my_expect(self.p,'symbols left: ','x')
		try:
			vmsg_r("SEND ")
			while self.p.expect('left: ',0.1) == 0:
				ch = rand_chars.pop(0)
				msg_r(yellow(ch)+" " if opt.verbose else "+")
				self.p.send(ch)
		except:
			vmsg("EOT")
		my_expect(self.p,"ENTER to continue: ",'\n')

	def passphrase_new(self,desc,passphrase):
		my_expect(self.p,("Enter passphrase for %s: " % desc), passphrase+"\n")
		my_expect(self.p,"Repeat passphrase: ", passphrase+"\n")

	def passphrase(self,desc,passphrase,pwtype=""):
		if pwtype: pwtype += " "
		my_expect(self.p,("Enter %spassphrase for %s.*?: " % (pwtype,desc)),
				passphrase+"\n",regex=True)

	def hash_preset(self,desc,preset=''):
		my_expect(self.p,("Enter hash preset for %s" % desc))
		my_expect(self.p,("or hit ENTER .*?:"), str(preset)+"\n",regex=True)

	def written_to_file(self,desc,overwrite_unlikely=False,query="Overwrite?  ",oo=False):
		s1 = "%s written to file " % desc
		s2 = query + "Type uppercase 'YES' to confirm: "
		ret = my_expect(self.p,s1 if overwrite_unlikely else [s1,s2])
		if ret == 1:
			my_send(self.p,"YES\n")
			if oo:
				outfile = self.expect_getend("Overwriting file '").rstrip("'")
				return outfile
			else:
				ret = my_expect(self.p,s1)
		outfile = self.p.readline().strip().strip("'")
		vmsg("%s file: %s" % (desc,cyan(outfile.replace("'",""))))
		return outfile

	def no_overwrite(self):
		self.expect("Overwrite?  Type uppercase 'YES' to confirm: ","\n")
		self.expect("Exiting at user request")

	def tx_view(self):
		my_expect(self.p,r"View .*?transaction.*? \(y\)es, \(N\)o, pager \(v\)iew.*?: ","\n",regex=True)

	def expect_getend(self,s,regex=False):
		ret = self.expect(s,regex=regex,nonl=True)
		end = self.readline().strip()
		vmsg(" ==> %s" % cyan(end))
		return end

	def interactive(self):
		return self.p.interact()

	def logfile(self,arg):
		self.p.logfile = arg

	def expect(self,*args,**kwargs):
		return my_expect(self.p,*args,**kwargs)

	def send(self,*args,**kwargs):
		return my_send(self.p,*args,**kwargs)

	def readline(self):
		return self.p.readline()

	def close(self):
		return self.p.close()

	def readlines(self):
		return [l.rstrip()+"\n" for l in self.p.readlines()]

	def read(self,n=None):
		return self.p.read(n)

from mmgen.rpc.data import TransactionInfo
from decimal import Decimal
from mmgen.bitcoin import verify_addr

def add_fake_unspent_entry(out,address,comment):
	out.append(TransactionInfo(
		account = unicode(comment),
		vout = int(getrandnum(4) % 8),
		txid = unicode(hexlify(os.urandom(32))),
		amount = Decimal("%s.%s" % (10+(getrandnum(4) % 40), getrandnum(4) % 100000000)),
		address = address,
		spendable = False,
		scriptPubKey = ("76a914"+verify_addr(address,return_hex=True)+"88ac"),
		confirmations = getrandnum(4) % 500
	))

def create_fake_unspent_data(adata,unspent_data_file,tx_data,non_mmgen_input=''):

	out = []
	for s in tx_data.keys():
		sid = tx_data[s]['sid']
		a = adata.addrinfo(sid)
		for n,(idx,btcaddr) in enumerate(a.addrpairs(),1):
			lbl = (""," addr %02i" % n)[int(bool(n%3))]
			add_fake_unspent_entry(out,btcaddr,"%s:%s%s" % (sid,idx,lbl))

	if non_mmgen_input:
		from mmgen.bitcoin import privnum2addr,hextowif
		privnum = getrandnum(32)
		btcaddr = privnum2addr(privnum,compressed=True)
		of = os.path.join(cfgs[non_mmgen_input]['tmpdir'],non_mmgen_fn)
		write_to_file(of, hextowif("{:064x}".format(privnum),
					compressed=True)+"\n","compressed bitcoin key")

		add_fake_unspent_entry(out,btcaddr,"Non-MMGen address")

#	msg("\n".join([repr(o) for o in out])); sys.exit()
	write_to_file(unspent_data_file,repr(out),"Unspent outputs",verbose=True)


def add_comments_to_addr_file(addrfile,tfile):
	silence()
	msg(green("Adding comments to address file '%s'" % addrfile))
	from mmgen.addr import AddrInfo
	a = AddrInfo(addrfile)
	for i in a.idxs(): a.set_comment(idx,"Test address %s" % idx)
	write_to_file(tfile,a.fmt_data(),{})
	end_silence()

def make_brainwallet_file(fn):
	# Print random words with random whitespace in between
	from mmgen.mn_tirosh import words
	wl = words.split("\n")
	nwords,ws_list,max_spaces = 10,"    \n",5
	def rand_ws_seq():
		nchars = getrandnum(1) % max_spaces + 1
		return "".join([ws_list[getrandnum(1)%len(ws_list)] for i in range(nchars)])
	rand_pairs = [wl[getrandnum(4) % len(wl)] + rand_ws_seq() for i in range(nwords)]
	d = "".join(rand_pairs).rstrip() + "\n"
	if opt.verbose: msg_r("Brainwallet password:\n%s" % cyan(d))
	write_to_file(fn,d,"brainwallet password")

def do_between():
	if opt.pause:
		from mmgen.util import keypress_confirm
		if keypress_confirm(green("Continue?"),default_yes=True):
			if opt.verbose or opt.exact_output: sys.stderr.write("\n")
		else:
			errmsg("Exiting at user request")
			sys.exit()
	elif opt.verbose or opt.exact_output:
		sys.stderr.write("\n")


rebuild_list = OrderedDict()

def check_needs_rerun(ts,cmd,build=False,root=True,force_delete=False,dpy=False):

	rerun = True if root else False  # force_delete is not passed to recursive call

	fns = []
	if force_delete or not root:
		# does cmd produce a needed dependency(ies)?
		ret = ts.get_num_exts_for_cmd(cmd,dpy)
		if ret:
			for ext in ret[1]:
				fn = get_file_with_ext(ext,cfgs[ret[0]]['tmpdir'],delete=build)
				if fn:
					if force_delete: os.unlink(fn)
					else: fns.append(fn)
				else: rerun = True

	fdeps = ts.generate_file_deps(cmd)
	cdeps = ts.generate_cmd_deps(fdeps)

	for fn in fns:
		my_age = os.stat(fn).st_mtime
		for num,ext in fdeps:
			f = get_file_with_ext(ext,cfgs[num]['tmpdir'],delete=build)
			if f and os.stat(f).st_mtime > my_age: rerun = True

	for cdep in cdeps:
		if check_needs_rerun(ts,cdep,build=build,root=False,dpy=cmd): rerun = True

	if build:
		if rerun:
			for fn in fns:
				if not root: os.unlink(fn)
			ts.do_cmd(cmd)
			if not root: do_between()
	else:
		# If prog produces multiple files:
		if cmd not in rebuild_list or rerun == True:
			rebuild_list[cmd] = (rerun,fns[0] if fns else "") # FIX

	return rerun

def refcheck(desc,chk,refchk):
	vmsg("Comparing %s '%s' to stored reference" % (desc,chk))
	if chk == refchk:
		ok()
	else:
		if not opt.verbose: errmsg("")
		errmsg(red("""
Fatal error - %s '%s' does not match reference value '%s'.  Aborting test
""".strip() % (desc,chk,refchk)))
		sys.exit(3)

def check_deps(cmds):
	if len(cmds) != 1:
		msg("Usage: %s check_deps <command>" % g.prog_name)
		sys.exit(1)

	cmd = cmds[0]

	if cmd not in cmd_data:
		msg("'%s': unrecognized command" % cmd)
		sys.exit(1)

	if not opt.quiet:
		msg("Checking dependencies for '%s'" % (cmd))

	check_needs_rerun(ts,cmd,build=False)

	w = max(len(i) for i in rebuild_list) + 1
	for cmd in rebuild_list:
		c = rebuild_list[cmd]
		m = "Rebuild" if (c[0] and c[1]) else "Build" if c[0] else "OK"
		msg("cmd {:<{w}} {}".format(cmd+":", m, w=w))
#			mmsg(cmd,c)


def clean(dirs=[]):
	ts = MMGenTestSuite()
	dirlist = ts.list_tmp_dirs()
	if not dirs: dirs = dirlist.keys()
	for d in sorted(dirs):
		if d in dirlist:
			cleandir(dirlist[d])
		else:
			msg("%s: invalid directory number" % d)
			sys.exit(1)

class MMGenTestSuite(object):

	def __init__(self):
		pass

	def list_tmp_dirs(self):
		d = {}
		for k in cfgs: d[k] = cfgs[k]['tmpdir']
		return d

	def get_num_exts_for_cmd(self,cmd,dpy=False): # dpy ignored here
		num = str(cmd_data[cmd][0])
		dgl = cfgs[num]['dep_generators']
#	mmsg(num,cmd,dgl)
		if cmd in dgl.values():
			exts = [k for k in dgl if dgl[k] == cmd]
			return (num,exts)
		else:
			return None

	def do_cmd(self,cmd):

		if ni and (len(cmd_data[cmd]) < 4 or cmd_data[cmd][3] != 1): return

		d = [(str(num),ext) for exts,num in cmd_data[cmd][2] for ext in exts]
		al = [get_file_with_ext(ext,cfgs[num]['tmpdir']) for num,ext in d]

		global cfg
		cfg = cfgs[str(cmd_data[cmd][0])]

		self.__class__.__dict__[cmd](*([self,cmd] + al))

	def generate_file_deps(self,cmd):
		return [(str(n),e) for exts,n in cmd_data[cmd][2] for e in exts]

	def generate_cmd_deps(self,fdeps):
		return [cfgs[str(n)]['dep_generators'][ext] for n,ext in fdeps]

	def helpscreens(self,name):
		for s in scripts:
			t = MMGenExpect(name,("mmgen-"+s),["--help"],
				extra_desc="(mmgen-%s)"%s,no_output=True)
			if not ni:
				t.read(); ok()

	def walletgen(self,name,seed_len=None):
		write_to_tmpfile(cfg,pwfile,cfg['wpasswd']+"\n")
		add_args = (["-r10"],
			["-q","-r0","-L","NI Wallet","-P",get_tmpfile_fn(cfg,pwfile)])[int(ni)]
		args = ["-d",cfg['tmpdir'],"-p1"]
		if seed_len: args += ["-l",str(seed_len)]
		t = MMGenExpect(name,"mmgen-walletgen", args + add_args)
		if ni: return
		t.license()
		t.usr_rand(10)
		t.passphrase_new("new MMGen wallet",cfg['wpasswd'])
		t.label()
		t.written_to_file("MMGen wallet")
		ok()

	def brainwalletgen_ref(self,name):
		sl_arg = "-l%s" % cfg['seed_len']
		hp_arg = "-p%s" % ref_wallet_hash_preset
		label = "test.py ref. wallet (pw '%s', seed len %s)" \
				% (ref_wallet_brainpass,cfg['seed_len'])
		args = ["-d",cfg['tmpdir'],hp_arg,"-r10",sl_arg,"-ib","-L",label]
		t = MMGenExpect(name,"mmgen-walletconv", args)
		t.license()
		t.expect("Enter brainwallet: ", ref_wallet_brainpass+"\n")
		t.passphrase_new("new MMGen wallet",cfg['wpasswd'])
		t.usr_rand(10)
		sid = t.written_to_file("MMGen wallet").split("-")[0].split("/")[-1]
		refcheck("seed ID",sid,cfg['seed_id'])

	def refwalletgen(self,name): self.brainwalletgen_ref(name)

	refwalletgen1 = refwalletgen2 = refwalletgen3 = refwalletgen

	def passchg(self,name,wf,pf):
		# ni: reuse password, since there's no way to change it non-interactively
		silence()
		write_to_tmpfile(cfg,pwfile,get_data_from_file(pf))
		end_silence()
		add_args = (["-r16"],["-q","-r0","-P",pf])[int(ni)]
		t = MMGenExpect(name,"mmgen-passchg", add_args +
				["-d",cfg['tmpdir'],"-p","2","-L","New Label",wf])
		if ni: return
		t.license()
		t.passphrase("MMGen wallet",cfgs['1']['wpasswd'],pwtype="old")
		t.expect_getend("Hash preset changed to ")
		t.passphrase("MMGen wallet",cfg['wpasswd'],pwtype="new")
		t.expect("Repeat passphrase: ",cfg['wpasswd']+"\n")
		t.usr_rand(16)
		t.expect_getend("Label changed to ")
#		t.expect_getend("Key ID changed: ")
		t.written_to_file("MMGen wallet")
		ok()

	def walletchk(self,name,wf,pf):
		args = ["-P",pf,"-q"] if ni and pf else []
		hp = cfg['hash_preset'] if 'hash_preset' in cfg else '1'
		t = MMGenExpect(name,"mmgen-walletchk", args + ["-p",hp] + [wf])
		if ni: return
		t.expect("Getting MMGen wallet from file '%s'" % wf)
		t.passphrase("MMGen wallet",cfg['wpasswd'])
		t.expect("Passphrase is OK")
		t.expect_getend("Valid MMGen wallet for seed ID ")
		ok()

	walletchk_newpass = walletchk

	def addrgen(self,name,wf,pf,check_ref=False):
		add_args = ["-P",pf,"-q"] if ni else []
		t = MMGenExpect(name,"mmgen-addrgen", add_args +
				["-d",cfg['tmpdir'],wf,cfg['addr_idx_list']])
		if ni: return
		t.license()
		t.passphrase("MMGen wallet",cfg['wpasswd'])
		t.expect("Passphrase is OK")
		chk = t.expect_getend(r"Checksum for address data .*?: ",regex=True)
		if check_ref:
			refcheck("address data checksum",chk,cfg['addrfile_chk'])
			return
		t.written_to_file("Addresses",oo=True)
		ok()

	def refaddrgen(self,name,wf):
		d = " (%s-bit seed)" % cfg['seed_len']
		self.addrgen(name,wf,pf="",check_ref=True)

	refaddrgen1 = refaddrgen2 = refaddrgen3 = refaddrgen

	def addrimport(self,name,addrfile):
		add_args = ["-q","-t"] if ni else []
		outfile = os.path.join(cfg['tmpdir'],"addrfile_w_comments")
		add_comments_to_addr_file(addrfile,outfile)
		t = MMGenExpect(name,"mmgen-addrimport", add_args + [outfile])
		if ni: return
		t.expect_getend(r"Checksum for address data .*\[.*\]: ",regex=True)
		t.expect_getend("Validating addresses...OK. ")
		t.expect("Type uppercase 'YES' to confirm: ","\n")
		vmsg("This is a simulation, so no addresses were actually imported into the tracking\nwallet")
		ok()

	def txcreate(self,name,addrfile):
		self.txcreate_common(name,sources=['1'])

	def txcreate_common(self,name,sources=['1'],non_mmgen_input=''):
		if opt.verbose or opt.exact_output:
			sys.stderr.write(green("Generating fake transaction info\n"))
		silence()
		from mmgen.addr import AddrInfo,AddrInfoList
		tx_data,ail = {},AddrInfoList()
		from mmgen.util import parse_addr_idxs
		for s in sources:
			afile = get_file_with_ext("addrs",cfgs[s]["tmpdir"])
			ai = AddrInfo(afile)
			ail.add(ai)
			aix = parse_addr_idxs(cfgs[s]['addr_idx_list'])
			if len(aix) != addrs_per_wallet:
				errmsg(red("Address index list length != %s: %s" %
							(addrs_per_wallet,repr(aix))))
				sys.exit()
			tx_data[s] = {
				'addrfile': afile,
				'chk': ai.checksum,
				'sid': ai.seed_id,
				'addr_idxs': aix[-2:],
			}

		unspent_data_file = os.path.join(cfg['tmpdir'],"unspent.json")
		create_fake_unspent_data(ail,unspent_data_file,tx_data,non_mmgen_input)

		# make the command line
		from mmgen.bitcoin import privnum2addr
		btcaddr = privnum2addr(getrandnum(32),compressed=True)

		cmd_args = ["-d",cfg['tmpdir']]
		for num in tx_data.keys():
			s = tx_data[num]
			cmd_args += [
				"%s:%s,%s" % (s['sid'],s['addr_idxs'][0],cfgs[num]['amts'][0]),
			]
			# + one BTC address
			# + one change address and one BTC address
			if num is tx_data.keys()[-1]:
				cmd_args += ["%s:%s" % (s['sid'],s['addr_idxs'][1])]
				cmd_args += ["%s,%s" % (btcaddr,cfgs[num]['amts'][1])]

		for num in tx_data: cmd_args += [tx_data[num]['addrfile']]

		os.environ["MMGEN_BOGUS_WALLET_DATA"] = unspent_data_file
		end_silence()
		if opt.verbose or opt.exact_output: sys.stderr.write("\n")

		add_args = ["-q"] if ni else []
		if ni:
			m = "Answer the interactive prompts as follows:\n" + \
				" 'y', 'y', 'q', '1-8', ENTER, ENTER, ENTER, 'y'"
			msg(green(m))
		t = MMGenExpect(name,"mmgen-txcreate",add_args + cmd_args)
		if ni: return
		t.license()
		for num in tx_data.keys():
			t.expect_getend("Getting address data from file ")
			chk=t.expect_getend(r"Checksum for address data .*?: ",regex=True)
			verify_checksum_or_exit(tx_data[num]['chk'],chk)

		# not in tracking wallet warning, (1 + num sources) times
		if t.expect(["Continue anyway? (y/N): ",
				"Unable to connect to bitcoind"]) == 0:
			t.send("y")
		else:
			errmsg(red("Error: unable to connect to bitcoind.  Exiting"))
			sys.exit(1)

		for num in tx_data.keys():
			t.expect("Continue anyway? (y/N): ","y")
		t.expect(r"'q' = quit sorting, .*?: ","M", regex=True)
		t.expect(r"'q' = quit sorting, .*?: ","q", regex=True)
		outputs_list = [addrs_per_wallet*i + 1 for i in range(len(tx_data))]
		if non_mmgen_input: outputs_list.append(len(tx_data)*addrs_per_wallet + 1)
		t.expect("Enter a range or space-separated list of outputs to spend: ",
				" ".join([str(i) for i in outputs_list])+"\n")
		if non_mmgen_input: t.expect("Accept? (y/N): ","y")
		t.expect("OK? (Y/n): ","y")
		t.expect("Add a comment to transaction? (y/N): ","\n")
		t.tx_view()
		t.expect("Save transaction? (y/N): ","y")
		t.written_to_file("Transaction")
		ok()

	def txsign_end(self,t,tnum=None):
		t.expect("Signing transaction")
		t.expect("Edit transaction comment? (y/N): ","\n")
		t.expect("Save signed transaction? (y/N): ","y")
		add = " #" + tnum if tnum else ""
		t.written_to_file("Signed transaction" + add)

	def txsign(self,name,txfile,wf,pf="",save=True):
		add_args = ["-q","-P",pf] if ni else []
		if ni:
			m = "Answer the interactive prompts as follows:\n  ENTER, ENTER, 'y'"
			msg(green(m))
		t = MMGenExpect(name,"mmgen-txsign", add_args +
				["-d",cfg['tmpdir'],txfile,wf])
		if ni: return
		t.license()
		t.tx_view()
		t.passphrase("MMGen wallet",cfg['wpasswd'])
		if save:
			self.txsign_end(t)
		else:
			t.expect("Edit transaction comment? (y/N): ","\n")
			t.expect("Save signed transaction? (y/N): ","\n")
			t.expect("Signed transaction not saved")
		ok()

	def txsend(self,name,sigfile):
		t = MMGenExpect(name,"mmgen-txsend", ["-d",cfg['tmpdir'],sigfile])
		t.license()
		t.tx_view()
		t.expect("Edit transaction comment? (y/N): ","\n")
		t.expect("broadcast this transaction to the network?")
		t.expect("'YES, I REALLY WANT TO DO THIS' to confirm: ","\n")
		t.expect("Exiting at user request")
		vmsg("This is a simulation; no transaction was sent")
		ok()

	def walletconv_export(self,name,wf,desc,uargs=[],out_fmt="w",pw=False):
		opts = ["-d",cfg['tmpdir'],"-o",out_fmt] + uargs + [wf]
		t = MMGenExpect(name,"mmgen-walletconv",opts)
		t.license()
		t.passphrase("MMGen wallet",cfg['wpasswd'])
		if pw:
			t.passphrase_new("new "+desc,cfg['wpasswd'])
			t.usr_rand(10)
		if " ".join(desc.split()[-2:]) == "incognito data":
			t.expect("Generating encryption key from OS random data ")
			t.expect("Generating encryption key from OS random data ")
			ic_id = t.expect_getend("New Incog Wallet ID: ")
			t.expect("Generating encryption key from OS random data ")
		if desc == "hidden incognito data":
			write_to_tmpfile(cfg,incog_id_fn,ic_id)
			ret = t.expect(["Create? (Y/n): ","'YES' to confirm: "])
			if ret == 0:
				t.send("\n")
				t.expect("Enter file size: ",str(hincog_bytes)+"\n")
			else:
				t.send("YES\n")
		if out_fmt == "w": t.label()
		return t.written_to_file(capfirst(desc),oo=True)

	def export_seed(self,name,wf,desc="seed data",out_fmt="seed"):
		f = self.walletconv_export(name,wf,desc=desc,out_fmt=out_fmt)
		silence()
		msg("%s: %s" % (capfirst(desc),cyan(get_data_from_file(f,desc))))
		end_silence()
		ok()

	def export_mnemonic(self,name,wf):
		self.export_seed(name,wf,desc="mnemonic data",out_fmt="words")

	def export_incog(self,name,wf,desc="incognito data",out_fmt="i",add_args=[]):
		uargs = ["-p1","-r10"] + add_args
		self.walletconv_export(name,wf,desc=desc,out_fmt=out_fmt,uargs=uargs,pw=True)
		ok()

	def export_incog_hex(self,name,wf):
		self.export_incog(name,wf,desc="hex incognito data",out_fmt="xi")

	# TODO: make outdir and hidden incog compatible (ignore --outdir and warn user?)
	def export_incog_hidden(self,name,wf):
		rf = os.path.join(cfg['tmpdir'],hincog_fn)
		add_args = ["-J","%s,%s"%(rf,hincog_offset)]
		self.export_incog(
			name,wf,desc="hidden incognito data",out_fmt="hi",add_args=add_args)

	def addrgen_seed(self,name,wf,foo,desc="seed data",in_fmt="seed"):
		stdout = (False,True)[int(desc=="seed data")] #capture output to screen once
		add_arg = ([],["-S"])[int(stdout)]
		t = MMGenExpect(name,"mmgen-addrgen", add_arg +
				["-i"+in_fmt,"-d",cfg['tmpdir'],wf,cfg['addr_idx_list']])
		t.license()
		t.expect_getend("Valid %s for seed ID " % desc)
		vmsg("Comparing generated checksum with checksum from previous address file")
		chk = t.expect_getend(r"Checksum for address data .*?: ",regex=True)
		if stdout: t.read()
		verify_checksum_or_exit(get_addrfile_checksum(),chk)
#		t.no_overwrite()
		ok()

	def addrgen_mnemonic(self,name,wf,foo):
		self.addrgen_seed(name,wf,foo,desc="mnemonic data",in_fmt="words")

	def addrgen_incog(self,name,wf=[],foo="",in_fmt="i",
						desc="incognito data",args=[]):
		t = MMGenExpect(name,"mmgen-addrgen",
				args+["-i"+in_fmt,"-d",cfg['tmpdir']]+
				([wf] if wf else [])+
				[cfg['addr_idx_list']])
		t.license()
		t.expect_getend("Incog Wallet ID: ")
		t.hash_preset(desc,'1')
		t.passphrase("%s \w{8}" % desc, cfg['wpasswd'])
		vmsg("Comparing generated checksum with checksum from address file")
		chk = t.expect_getend(r"Checksum for address data .*?: ",regex=True)
		t.close()
		verify_checksum_or_exit(get_addrfile_checksum(),chk)
#		t.no_overwrite()
		ok()

	def addrgen_incog_hex(self,name,wf,foo):
		self.addrgen_incog(name,wf,"",in_fmt="xi",desc="hex incognito data")

	def addrgen_incog_hidden(self,name,wf,foo):
		rf = os.path.join(cfg['tmpdir'],hincog_fn)
		self.addrgen_incog(name,[],"",in_fmt="hi",desc="hidden incognito data",
			args=["-H","%s,%s"%(rf,hincog_offset),"-l",str(hincog_seedlen)])

	def keyaddrgen(self,name,wf,check_ref=False):
		t = MMGenExpect(name,"mmgen-keygen",
				["-d",cfg['tmpdir'],wf,cfg['addr_idx_list']])
		t.license()
		t.passphrase("MMGen wallet",cfg['wpasswd'])
		chk = t.expect_getend(r"Checksum for key-address data .*?: ",regex=True)
		if check_ref:
			refcheck("key-address data checksum",chk,cfg['keyaddrfile_chk'])
			return
		t.expect("Encrypt key list? (y/N): ","y")
		t.hash_preset("new key list",'1')
		t.passphrase_new("new key list",cfg['kapasswd'])
		t.written_to_file("Secret keys",oo=True)
		ok()

	def refkeyaddrgen(self,name,wf):
		self.keyaddrgen(name,wf,check_ref=True)

	refkeyaddrgen1 = refkeyaddrgen2 = refkeyaddrgen3 = refkeyaddrgen

	def txsign_keyaddr(self,name,keyaddr_file,txfile):
		t = MMGenExpect(name,"mmgen-txsign", ["-d",cfg['tmpdir'],"-M",keyaddr_file,txfile])
		t.license()
		t.hash_preset("key-address file",'1')
		t.passphrase("key-address file",cfg['kapasswd'])
		t.expect("Check key-to-address validity? (y/N): ","y")
		t.tx_view()
		self.txsign_end(t)
		ok()

	def walletgen2(self,name):
		self.walletgen(name,seed_len=128)

	def addrgen2(self,name,wf):
		self.addrgen(name,wf,pf="")

	def txcreate2(self,name,addrfile):
		self.txcreate_common(name,sources=['2'])

	def txsign2(self,name,txf1,wf1,txf2,wf2):
		t = MMGenExpect(name,"mmgen-txsign", ["-d",cfg['tmpdir'],txf1,wf1,txf2,wf2])
		t.license()
		for cnum in ('1','2'):
			t.tx_view()
			t.passphrase("MMGen wallet",cfgs[cnum]['wpasswd'])
			self.txsign_end(t,cnum)
		ok()

	def export_mnemonic2(self,name,wf):
		self.export_mnemonic(name,wf)

	def walletgen3(self,name):
		self.walletgen(name)

	def addrgen3(self,name,wf):
		self.addrgen(name,wf,pf="")

	def txcreate3(self,name,addrfile1,addrfile2):
		self.txcreate_common(name,sources=['1','3'])

	def txsign3(self,name,wf1,wf2,txf2):
		t = MMGenExpect(name,"mmgen-txsign", ["-d",cfg['tmpdir'],wf1,wf2,txf2])
		t.license()
		t.tx_view()
		for cnum in ('1','3'):
#			t.expect_getend("Getting MMGen wallet data from file ")
			t.passphrase("MMGen wallet",cfgs[cnum]['wpasswd'])
		self.txsign_end(t)
		ok()

	def brainwalletgen_pwfile(self,name):
		bwf = os.path.join(cfg['tmpdir'],cfg['bw_filename'])
		make_brainwallet_file(bwf)
		seed_len = str(cfg['seed_len'])
		args = ["-d",cfg['tmpdir'],"-p1","-r10","-l"+seed_len,"-ib"]
		t = MMGenExpect(name,"mmgen-walletconv", args + [bwf])
		t.license()
		t.passphrase_new("new MMGen wallet",cfg['wpasswd'])
		t.usr_rand(10)
		t.label()
		t.written_to_file("MMGen wallet")
		ok()

	def walletgen4(self,name): self.brainwalletgen_pwfile(name)

	def addrgen4(self,name,wf):
		self.addrgen(name,wf,pf="")

	def txcreate4(self,name,f1,f2,f3,f4):
		self.txcreate_common(name,sources=['1','2','3','4'],non_mmgen_input='4')

	def txsign4(self,name,f1,f2,f3,f4,f5):
		non_mm_fn = os.path.join(cfg['tmpdir'],non_mmgen_fn)
		t = MMGenExpect(name,"mmgen-txsign",
			["-d",cfg['tmpdir'],"-i","brain","-b"+cfg['bw_params'],"-p1","-k",non_mm_fn,f1,f2,f3,f4,f5])
		t.license()
		t.tx_view()

		for cnum,desc in ('1',"incognito data"),('3',"MMGen wallet"):
			t.passphrase(("%s" % desc),cfgs[cnum]['wpasswd'])

		self.txsign_end(t)
		ok()

	def tool_encrypt(self,name,infile=""):
		if infile:
			infn = infile
		else:
			d = os.urandom(1033)
			tmp_fn = cfg['tool_enc_infn']
			write_to_tmpfile(cfg,tmp_fn,d)
			infn = get_tmpfile_fn(cfg,tmp_fn)
		t = MMGenExpect(name,"mmgen-tool",["-d",cfg['tmpdir'],"encrypt",infn])
		t.hash_preset("user data",'1')
		t.passphrase_new("user data",tool_enc_passwd)
		t.written_to_file("Encrypted data")
		ok()
# Generate the reference mmenc file
# 	def tool_encrypt_ref(self,name):
# 		infn = get_tmpfile_fn(cfg,cfg['tool_enc_ref_infn'])
# 		write_to_file(infn,cfg['tool_enc_reftext'],silent=True)
# 		self.tool_encrypt(name,infn)

	def tool_decrypt(self,name,f1,f2):
		of = name + ".out"
		t = MMGenExpect(name,"mmgen-tool",
			["-d",cfg['tmpdir'],"decrypt",f2,"outfile="+of,"hash_preset=1"])
		t.passphrase("user data",tool_enc_passwd)
		t.written_to_file("Decrypted data")
		d1 = read_from_file(f1)
		d2 = read_from_file(get_tmpfile_fn(cfg,of))
		cmp_or_die(d1,d2)

	def tool_find_incog_data(self,name,f1,f2):
		i_id = read_from_file(f2).rstrip()
		vmsg("Incog ID: %s" % cyan(i_id))
		t = MMGenExpect(name,"mmgen-tool",
				["-d",cfg['tmpdir'],"find_incog_data",f1,i_id])
		o = t.expect_getend("Incog data for ID %s found at offset " % i_id)
		os.unlink(f1)
		cmp_or_die(hincog_offset,int(o))

	def pywallet(self,name):  # TODO - check output
		pf = get_tmpfile_fn(cfg,pwfile)
		write_data_to_file(pf,cfg['wpasswd']+"\n",silent=True)
		args = ["-q","-P",pf] if ni else []
		unenc_wf = os.path.join(ref_dir,"wallet-unenc.dat")
		enc_wf   = os.path.join(ref_dir,"wallet-enc.dat")
		for wf,enc in (unenc_wf,False),(enc_wf,True):
			for w,o,pk in (
				("addresses","a",False),
				("private keys","k",True),
				("json dump","j",True)
			):
				ed = "(%sencrypted wallet, %s)" % (("un","")[int(enc)],w)
				t = MMGenExpect(name,"mmgen-pywallet", args +
						["-"+o,"-d",cfg['tmpdir']] + [wf], extra_desc=ed)
				if ni: continue
				if pk and enc and not ni:
					t.expect("Enter password: ",cfg['wpasswd']+"\n")
				t.written_to_file(capfirst(w),oo=True)
				if not ni: ok()

	def walletconv_out(self,name,desc,out_fmt="w",uopts=[],uopts_chk=[],pw=False):
		opts = ["-d",cfg['tmpdir'],"-r10","-p1","-o",out_fmt] + uopts
		infile = os.path.join(ref_dir,cfg['seed_id']+".mmwords")
		t = MMGenExpect(name,"mmgen-walletconv",opts+[infile],extra_desc="(convert)")
		t.license()
		if pw:
			t.passphrase_new("new "+desc,cfg['wpasswd'])
			t.usr_rand(10)
		if " ".join(desc.split()[-2:]) == "incognito data":
			for i in (1,2,3):
				t.expect("Generating encryption key from OS random data ")
		if desc == "hidden incognito data":
			ret = t.expect(["Create? (Y/n): ","'YES' to confirm: "])
			if ret == 0:
				t.send("\n")
				t.expect("Enter file size: ",str(hincog_bytes)+"\n")
			else:
				t.send("YES\n")
		if out_fmt == "w": t.label()
		wf = t.written_to_file(capfirst(desc),oo=True)
		ok()
		if desc == "hidden incognito data":
			self.keygen_chksum_chk_hincog(name,cfg['seed_id'],uopts_chk)
		else:
			self.keygen_chksum_chk(name,wf,cfg['seed_id'],pw=pw)

	def walletconv_in(self,name,infile,desc,uopts=[],pw=False,oo=False):
		opts = ["-d",cfg['tmpdir'],"-o","words","-r10"]
		if_arg = [infile] if infile else []
		d = "(convert)"
		t = MMGenExpect(name,"mmgen-walletconv",opts+uopts+if_arg,extra_desc=d)
		t.license()
		if desc == "brainwallet":
			t.expect("Enter brainwallet: ",ref_wallet_brainpass+"\n")
		if pw:
			t.passphrase(desc,cfg['wpasswd'])
			if name[:19] == "ref_hincog_conv_old":
				t.expect("Is the seed ID correct? (Y/n): ","\n")
			else:
				t.expect(["Passphrase is OK"," are correct"])
		# Output
		wf = t.written_to_file("Mnemonic data",oo=oo)
		t.close()
		ok()
		# back check of result
		d = "(check)"
		self.keygen_chksum_chk(name,wf,cfg['seed_id'])

	# Saved reference file tests
	def ref_wallet_conv(self,name):
		wf = os.path.join(ref_dir,cfg['ref_wallet'])
		self.walletconv_in(name,wf,"MMGen wallet",pw=True,oo=True)

	def ref_mn_conv(self,name,ext="mmwords",desc="Mnemonic data"):
		wf = os.path.join(ref_dir,cfg['seed_id']+"."+ext)
		self.walletconv_in(name,wf,desc,oo=True)

	def ref_seed_conv(self,name):
		self.ref_mn_conv(name,ext="mmseed",desc="Seed data")

	def ref_brain_conv(self,name):
		uopts = ["-i","b","-p","1","-l",str(cfg['seed_len'])]
		self.walletconv_in(name,None,"brainwallet",uopts,oo=True)

	def ref_incog_conv(self,name,wfk="ic_wallet",in_fmt="i",desc="incognito data"):
		uopts = ["-i",in_fmt,"-p","1","-l",str(cfg['seed_len'])]
		wf = os.path.join(ref_dir,cfg[wfk])
		self.walletconv_in(name,wf,desc,uopts,oo=True,pw=True)

	def ref_incox_conv(self,name):
		self.ref_incog_conv(name,in_fmt="xi",wfk="ic_wallet_hex",desc="hex incognito data")

	def ref_hincog_conv(self,name,wfk='hic_wallet',add_uopts=[]):
		ic_f = os.path.join(ref_dir,cfg[wfk])
		uopts = ["-i","hi","-p","1","-l",str(cfg['seed_len'])] + add_uopts
		hi_opt = ["-H","%s,%s" % (ic_f,ref_wallet_incog_offset)]
		self.walletconv_in(name,None,"hidden incognito data",uopts+hi_opt,oo=True,pw=True)

	def ref_hincog_conv_old(self,name):
		self.ref_hincog_conv(name,wfk='hic_wallet_old',add_uopts=["-O"])

	def ref_wallet_conv_out(self,name):
		self.walletconv_out(name,"MMGen wallet","w",pw=True)

	def ref_mn_conv_out(self,name):
		self.walletconv_out(name,"mnemonic data","mn")

	def ref_seed_conv_out(self,name):
		self.walletconv_out(name,"seed data","seed")

	def ref_incog_conv_out(self,name):
		self.walletconv_out(name,"incognito data",out_fmt="i",pw=True)

	def ref_incox_conv_out(self,name):
		self.walletconv_out(name,"hex incognito data",out_fmt="xi",pw=True)

	def ref_hincog_conv_out(self,name,extra_uopts=[]):
		ic_f = os.path.join(cfg['tmpdir'],"rand.data")
		hi_parms = "%s,%s" % (ic_f,ref_wallet_incog_offset)
		sl_parm = "-l" + str(cfg['seed_len'])
		self.walletconv_out(name,
			"hidden incognito data", "hi",
			uopts=["-J",hi_parms,sl_parm] + extra_uopts,
			uopts_chk=["-H",hi_parms,sl_parm],
			pw=True
		)

	ref_wallet_conv1 = ref_wallet_conv2 = ref_wallet_conv3 = ref_wallet_conv
	ref_mn_conv1 = ref_mn_conv2 = ref_mn_conv3 = ref_mn_conv
	ref_seed_conv1 = ref_seed_conv2 = ref_seed_conv3 = ref_seed_conv
	ref_brain_conv1 = ref_brain_conv2 = ref_brain_conv3 = ref_brain_conv
	ref_incog_conv1 = ref_incog_conv2 = ref_incog_conv3 = ref_incog_conv
	ref_incox_conv1 = ref_incox_conv2 = ref_incox_conv3 = ref_incox_conv
	ref_hincog_conv1 = ref_hincog_conv2 = ref_hincog_conv3 = ref_hincog_conv
	ref_hincog_conv_old1 = ref_hincog_conv_old2 = ref_hincog_conv_old3 = ref_hincog_conv_old

	ref_wallet_conv_out1 = ref_wallet_conv_out2 = ref_wallet_conv_out3 = ref_wallet_conv_out
	ref_mn_conv_out1 = ref_mn_conv_out2 = ref_mn_conv_out3 = ref_mn_conv_out
	ref_seed_conv_out1 = ref_seed_conv_out2 = ref_seed_conv_out3 = ref_seed_conv_out
	ref_incog_conv_out1 = ref_incog_conv_out2 = ref_incog_conv_out3 = ref_incog_conv_out
	ref_incox_conv_out1 = ref_incox_conv_out2 = ref_incox_conv_out3 = ref_incox_conv_out
	ref_hincog_conv_out1 = ref_hincog_conv_out2 = ref_hincog_conv_out3 = ref_hincog_conv_out

	def ref_wallet_chk(self,name):
		wf = os.path.join(ref_dir,cfg['ref_wallet'])
		self.walletchk(name,wf,pf="")

	ref_wallet_chk1 = ref_wallet_chk2 = ref_wallet_chk3 = ref_wallet_chk

	def ref_seed_chk(self,name,ext=g.seed_ext):
		wf = os.path.join(ref_dir,"%s.%s" % (cfg['seed_id'],ext))
		desc = "seed data" if ext == g.seed_ext else "mnemonic"
		self.keygen_chksum_chk(name,wf,cfg['seed_id'])

	ref_seed_chk1 = ref_seed_chk2 = ref_seed_chk3 = ref_seed_chk

	def ref_mn_chk(self,name): self.ref_seed_chk(name,ext=g.mn_ext)

	ref_mn_chk1 = ref_mn_chk2 = ref_mn_chk3 = ref_mn_chk

	def ref_brain_chk(self,name,bw_file=ref_bw_file):
		wf = os.path.join(ref_dir,bw_file)
		args = ["-l%s" % cfg['seed_len'], "-p"+ref_bw_hash_preset]
		self.keygen_chksum_chk(name,wf,cfg['ref_bw_seed_id'],args)

	def keygen_chksum_chk_hincog(self,name,seed_id,hincog_parm):
		t = MMGenExpect(name,"mmgen-keygen", ["-p1","-q","-S","-A"]+hincog_parm+["1"],extra_desc="(check)")
		t.passphrase("",cfg['wpasswd'])
		t.expect("Encrypt key list? (y/N): ","\n")
		t.expect("ignored by MMGen.\r\n")
		chk = t.readline()[:8]
		vmsg("Seed ID: %s" % cyan(chk))
		cmp_or_die(seed_id,chk)

	def keygen_chksum_chk(self,name,wf,seed_id,args=[],pw=False):
		hp_arg = ["-p1"] if pw else []
		t = MMGenExpect(name,"mmgen-keygen",
			["-l",str(cfg['seed_len']),"-q","-S","-A"]+args+hp_arg+[wf,"1"],
			extra_desc="(check)")
		if pw:
			t.passphrase("",cfg['wpasswd'])
		t.expect("Encrypt key list? (y/N): ","\n")
		t.expect("ignored by MMGen.\r\n")
		chk = t.readline()[:8]
		vmsg("Seed ID: %s" % cyan(chk))
		cmp_or_die(seed_id,chk)

	# Use this for encrypted wallets instead of keygen_chksum_chk()
	def walletchk_chksum_chk(self,name,wf,seed_id,uopts=[]):
		t = MMGenExpect(name,"mmgen-walletchk",["-v", wf]+uopts,
							extra_desc="(check)")
		t.passphrase("",cfg['wpasswd'])
		chk = t.expect_getend("Seed ID checksum OK (")[:8]
		t.close()
		cmp_or_die(seed_id,chk)

	ref_brain_chk1 = ref_brain_chk2 = ref_brain_chk3 = ref_brain_chk

	def ref_brain_chk_spc3(self,name):
		self.ref_brain_chk(name,bw_file=ref_bw_file_spc)

	def ref_hincog_chk(self,name,desc="hidden incognito data"):
		for wtype,edesc,earg in ('hic_wallet','',[]), \
								('hic_wallet_old','(old format)',["-O"]):
			ic_arg = "%s,%s" % (
						os.path.join(ref_dir,cfg[wtype]),
						ref_wallet_incog_offset
					)
			t = MMGenExpect(name,"mmgen-keygen",["-l",str(cfg['seed_len']),
					"-q","-A"]+earg+["-H"]+[ic_arg]+['1'],extra_desc=edesc)
			t.hash_preset(desc,"1")
			t.passphrase(desc,cfg['wpasswd'])
			if wtype == 'hic_wallet_old':
				t.expect("Is the seed ID correct? (Y/n): ","\n")
			chk = t.expect_getend("Seed ID: ")
			t.expect("Encrypt key list? (y/N): ","\n")
			t.close()
			cmp_or_die(cfg['seed_id'],chk)

	ref_hincog_chk1 = ref_hincog_chk2 = ref_hincog_chk3 = ref_hincog_chk

	def ref_addrfile_chk(self,name,ftype="addr"):
		wf = os.path.join(ref_dir,cfg['ref_'+ftype+'file'])
		t = MMGenExpect(name,"mmgen-tool",[ftype+"file_chksum",wf])
		if ftype == "keyaddr":
			w = "key-address file"
			t.hash_preset(w,ref_kafile_hash_preset)
			t.passphrase(w,ref_kafile_pass)
			t.expect("Check key-to-address validity? (y/N): ","y")
		o = t.expect_getend("Checksum for .*address data .*: ",regex=True)
		cmp_or_die(cfg['ref_'+ftype+'file_chksum'],o)

	def ref_keyaddrfile_chk(self,name):
		self.ref_addrfile_chk(name,ftype="keyaddr")

#	def txcreate8(self,name,addrfile):
#		self.txcreate_common(name,sources=['8'])

	def ref_tx_chk(self,name):
		tf = os.path.join(ref_dir,cfg['ref_tx_file'])
		wf = os.path.join(ref_dir,cfg['ref_wallet'])
		self.txsign(name,tf,wf,save=False)

	def ref_tool_decrypt(self,name):
		f = os.path.join(ref_dir,ref_enc_fn)
		t = MMGenExpect(name,"mmgen-tool",
				["-q","decrypt",f,"outfile=-","hash_preset=1"])
		t.passphrase("user data",tool_enc_passwd)
		t.readline()
		import re
		o = re.sub('\r\n','\n',t.read())
		cmp_or_die(sample_text,o)

# main()
if opt.pause:
	import termios,atexit
	fd = sys.stdin.fileno()
	old = termios.tcgetattr(fd)
	def at_exit():
		termios.tcsetattr(fd, termios.TCSADRAIN, old)
	atexit.register(at_exit)

start_time = int(time.time())
ts = MMGenTestSuite()

for cfg in sorted(cfgs): mk_tmpdir(cfgs[cfg])

try:
	if cmd_args:
		for arg in cmd_args:
			if arg in utils:
				globals()[arg](cmd_args[cmd_args.index(arg)+1:])
				sys.exit()
			elif arg in meta_cmds:
				for cmd in meta_cmds[arg]:
					check_needs_rerun(ts,cmd,build=True)
			elif arg in cmd_groups.keys():
				for cmd in cmd_groups[arg]:
					check_needs_rerun(ts,cmd,build=True)
			elif arg in cmd_data:
				check_needs_rerun(ts,arg,build=True)
			else:
				die(1,"%s: unrecognized command" % arg)
	else:
		clean()
		for cmd in cmd_data:
			ts.do_cmd(cmd)
			if cmd is not cmd_data.keys()[-1]: do_between()
except:
	sys.stderr = stderr_save
	raise

t = int(time.time()) - start_time
sys.stderr.write(green(
	"All requested tests finished OK, elapsed time: %02i:%02i\n"
	% (t/60,t%60)))

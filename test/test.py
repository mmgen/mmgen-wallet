#!/usr/bin/python

# Chdir to repo root.
# Since script is not in repo root, fix sys.path so that modules are
# imported from repo, not system.
import sys,os
pn = os.path.dirname(sys.argv[0])
os.chdir(os.path.join(pn,os.pardir))
sys.path.__setitem__(0,os.path.abspath(os.curdir))

from mmgen.util import msgrepr, msgrepr_exit

hincog_fn = "rand_data"
non_mmgen_fn = "btckey"

from collections import OrderedDict
cmd_data = OrderedDict([
#     test               description                  depends
	['refwalletgen',    (6,'reference wallet seed ID',    [[[],6]])],
	['refaddrgen',      (6,'reference wallet address checksum', [[["mmdat"],6]])],
	['refkeyaddrgen',   (6,'reference wallet key-address checksum', [[["mmdat"],6]])],

	['walletgen',       (1,'wallet generation',        [[[],1]])],
	['walletchk',       (1,'wallet check',             [[["mmdat"],1]])],
	['passchg',         (5,'password, label and hash preset change',[[["mmdat"],1]])],
	['walletchk_newpass',(5,'wallet check with new pw, label and hash preset',[[["mmdat"],5]])],
	['addrgen',         (1,'address generation',       [[["mmdat"],1]])],
	['addrimport',      (1,'address import',           [[["addrs"],1]])],
	['txcreate',        (1,'transaction creation',     [[["addrs"],1]])],
	['txsign',          (1,'transaction signing',      [[["mmdat","raw"],1]])],
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

	['walletgen2',(2,'wallet generation (2)',     [])],
#	['walletgen2',(2,'wallet generation (2), 128-bit seed (WIP)',     [])],
	['addrgen2',  (2,'address generation (2)',    [[["mmdat"],2]])],
	['txcreate2', (2,'transaction creation (2)',  [[["addrs"],2]])],
	['txsign2',   (2,'transaction signing, two transactions',[[["mmdat","raw"],1],[["mmdat","raw"],2]])],
	['export_mnemonic2', (2,'seed export to mmwords format (2)',[[["mmdat"],2]])],
#	['export_mnemonic2', (2,'seed export to mmwords format (2), 128-bit seed (WIP)',[[["mmdat"],2]])],

	['walletgen3',(3,'wallet generation (3)',         [])],
	['addrgen3',  (3,'address generation (3)',        [[["mmdat"],3]])],
	['txcreate3', (3,'tx creation with inputs and outputs from two wallets', [[["addrs"],1],[["addrs"],3]])],
	['txsign3',   (3,'tx signing with inputs and outputs from two wallets',[[["mmdat"],1],[["mmdat","raw"],3]])],

	['walletgen4',(4,'wallet generation (4) (brainwallet)', [])],
#	['walletgen4',(4,'wallet generation (4) (brainwallet, 192-bit seed (WIP))', [])],
	['addrgen4',  (4,'address generation (4)',              [[["mmdat"],4]])],
	['txcreate4', (4,'tx creation with inputs and outputs from four seed sources, plus non-MMGen inputs and outputs', [[["addrs"],1],[["addrs"],2],[["addrs"],3],[["addrs"],4]])],
	['txsign4',   (4,'tx signing with inputs and outputs from incog file, mnemonic file, wallet and brainwallet, plus non-MMGen inputs and outputs', [[["mmincog"],1],[["mmwords"],2],[["mmdat"],3],[["mmbrain","raw"],4]])],
])

tool_cmd_data = OrderedDict([
	['strtob58',   (10, '',   [])],
	['b58tostr',   (10, '',   [[["strtob58.in","strtob58.out"],10]])],
	['hextob58',   (10, '',   [])],
	['b58tohex',   (10, '',   [[["hextob58.in","hextob58.out"],10]])],
# 	"b58randenc":   [],
# 	"randhex":      ['nbytes [int=32]'],
# 	"randwif":      ['compressed [bool=False]'],
# 	"randpair":     ['compressed [bool=False]'],
# 	"wif2hex":      ['<wif> [str]', 'compressed [bool=False]'],
# 	"wif2addr":     ['<wif> [str]', 'compressed [bool=False]'],
# 	"hex2wif":      ['<private key in hex format> [str]', 'compressed [bool=False]'],
# 	"hexdump":      ['<infile> [str]', 'cols [int=8]', 'line_nums [bool=True]'],
# 	"unhexdump":    ['<infile> [str]'],
# 	"hex2mn":       ['<hexadecimal string> [str]','wordlist [str="electrum"]'],
# 	"mn2hex":       ['<mnemonic> [str]', 'wordlist [str="electrum"]'],
# 	"b32tohex":     ['<b32 num> [str]'],
# 	"hextob32":     ['<hex num> [str]'],
# 	"mn_rand128":   ['wordlist [str="electrum"]'],
# 	"mn_rand192":   ['wordlist [str="electrum"]'],
# 	"mn_rand256":   ['wordlist [str="electrum"]'],
# 	"mn_stats":     ['wordlist [str="electrum"]'],
# 	"mn_printlist": ['wordlist [str="electrum"]'],
# 	"id8":          ['<infile> [str]'],
# 	"id6":          ['<infile> [str]'],
# 	"str2id6":      ['<string (spaces are ignored)> [str]'],
])


utils = {
	'check_deps': 'check dependencies for specified command',
	'clean':      'clean specified tmp dir(s) 1, 2, 3 or 4 (no arg = all dirs)',
}

addrs_per_wallet = 8
cfgs = {
	'10': {
		'name':          "test the tool utility",
		'enc_passwd':    "Ten Satoshis",
		'tmpdir':        "test/tmp10",
		'dep_generators':  {
			'strtob58.out': "strtob58",
			'strtob58.in':  "strtob58",
		},

	},
	'6': {
		'name':            "reference wallet check",
		'bw_passwd':       "abc",
		'bw_hashparams':   "256,1",
		'key_id':          "98831F3A",
		'addrfile_chk':    "6FEF 6FB9 7B13 5D91 854A 0BD3",
		'keyaddrfile_chk': "9F2D D781 1812 8BAD C396 9DEB",

		'wpasswd':       "reference password",
		'tmpdir':        "test/tmp6",
		'kapasswd':      "",
		'addr_idx_list': "1010,500-501,31-33,1,33,500,1011", # 8 addresses
		'dep_generators':  {
			'mmdat':       "refwalletgen",
			'addrs':       "refaddrgen",
			'akeys.mmenc': "refkeyaddrgen"
		},

	},
	'1': {
		'tmpdir':        "test/tmp1",
		'wpasswd':       "Dorian",
		'kapasswd':      "Grok the blockchain",
		'addr_idx_list': "12,99,5-10,5,12", # 8 addresses
		'dep_generators':  {
			'mmdat':       "walletgen",
			'addrs':       "addrgen",
			'raw':         "txcreate",
			'sig':         "txsign",
			'mmwords':     "export_mnemonic",
			'mmseed':      "export_seed",
			'mmincog':     "export_incog",
			'mmincox':     "export_incog_hex",
			hincog_fn:    "export_incog_hidden",
			'akeys.mmenc': "keyaddrgen"
		},
	},
	'2': {
		'tmpdir':        "test/tmp2",
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
		'tmpdir':        "test/tmp3",
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
		'tmpdir':        "test/tmp4",
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
		'tmpdir':        "test/tmp5",
		'wpasswd':       "My changed password",
		'dep_generators': {
			'mmdat':       "passchg",
		},
	},
}

from binascii import hexlify
def getrand(n): return int(hexlify(os.urandom(n)),16)
def getrandhex(n): return hexlify(os.urandom(n))

# total of two outputs must be < 10 BTC
for k in cfgs.keys():
	cfgs[k]['amts'] = [0,0]
	for idx,mod in (0,6),(1,4):
		cfgs[k]['amts'][idx] = "%s.%s" % ((getrand(2) % mod), str(getrand(4))[:5])

meta_cmds = OrderedDict([
	['ref',    (6,("refwalletgen","refaddrgen","refkeyaddrgen"))],
	['gen',    (1,("walletgen","walletchk","addrgen"))],
	['pass',   (5,("passchg","walletchk_newpass"))],
	['tx',     (1,("txcreate","txsign","txsend"))],
	['export', (1,[k for k in cmd_data if k[:7] == "export_" and cmd_data[k][0] == 1])],
	['gen_sp', (1,[k for k in cmd_data if k[:8] == "addrgen_" and cmd_data[k][0] == 1])],
	['online', (1,("keyaddrgen","txsign_keyaddr"))],
	['2', (2,[k for k in cmd_data if cmd_data[k][0] == 2])],
	['3', (3,[k for k in cmd_data if cmd_data[k][0] == 3])],
	['4', (4,[k for k in cmd_data if cmd_data[k][0] == 4])],
])

from mmgen.Opts import *
help_data = {
	'prog_name': "test.py",
	'desc': "Test suite for the MMGen suite",
	'usage':"[options] [command or metacommand]",
	'options': """
-h, --help         Print this help message
-b, --buf-keypress Use buffered keypresses as with real human input
-d, --debug        Produce debugging output
-e, --exact-output Show the exact output of the MMGen script(s) being run
-l, --list-cmds    List and describe the tests and commands in the test suite
-p, --pause        Pause between tests, resuming on keypress
-q, --quiet        Produce minimal output.  Suppress dependency info
-s, --system       Test scripts and modules installed on system rather than those in the repo root
-v, --verbose      Produce more verbose output
""",
	'notes': """

If no command is given, the whole suite of tests is run.
"""
}

opts,cmd_args = parse_opts(sys.argv,help_data)

if 'system' in opts: sys.path.pop(0)

env = os.environ
if 'buf_keypress' in opts:
	send_delay = 0.3
else:
	send_delay = 0
	env["MMGEN_DISABLE_HOLD_PROTECT"] = "1"

for k in 'debug','verbose','exact_output','pause','quiet':
	globals()[k] = True if k in opts else False

if debug: verbose = True

if exact_output:
	def msg(s): pass
	vmsg = vmsg_r = msg_r = msg
else:
	def msg(s): sys.stderr.write(s+"\n")
	def vmsg(s):
		if verbose: sys.stderr.write(s+"\n")
	def msg_r(s): sys.stderr.write(s)
	def vmsg_r(s):
		if verbose: sys.stderr.write(s)

stderr_save = sys.stderr

def silence():
	if not (verbose or exact_output):
		sys.stderr = open("/dev/null","a")

def end_silence():
	if not (verbose or exact_output):
		sys.stderr = stderr_save

def errmsg(s): stderr_save.write(s+"\n")
def errmsg_r(s): stderr_save.write(s)

def Msg(s): sys.stdout.write(s+"\n")

if "list_cmds" in opts:
	Msg("Available commands:")
	w = max([len(i) for i in cmd_data])
	for cmd in cmd_data:
		Msg("  {:<{w}} - {}".format(cmd,cmd_data[cmd][1],w=w))
	Msg("\nAvailable metacommands:")
	w = max([len(i) for i in meta_cmds])
	for cmd in meta_cmds:
		Msg("  {:<{w}} - {}".format(cmd," + ".join(meta_cmds[cmd][1]),w=w))
	Msg("\nAvailable utilities:")
	w = max([len(i) for i in utils])
	for cmd in sorted(utils):
		Msg("  {:<{w}} - {}".format(cmd,utils[cmd],w=w))
	sys.exit()

import pexpect,time,re
import mmgen.config as g
from mmgen.util import get_data_from_file,write_to_file,get_lines_from_file

redc,grnc,yelc,cyac,reset = (
	["\033[%sm" % c for c in "31;1","32;1","33;1","36;1","0"]
)
def red(s):    return redc+s+reset
def green(s):  return grnc+s+reset
def yellow(s): return yelc+s+reset
def cyan(s):   return cyac+s+reset

def my_send(p,t,delay=send_delay,s=False):
	if delay: time.sleep(delay)
	ret = p.send(t) # returns num bytes written
	if delay: time.sleep(delay)
	if verbose:
		ls = "" if debug or not s else " "
		es = "" if s else "  "
		msg("%sSEND %s%s" % (ls,es,yellow("'%s'"%t.replace('\n',r'\n'))))
	return ret

def my_expect(p,s,t='',delay=send_delay,regex=False,nonl=False):
	quo = "'" if type(s) == str else ""

	if verbose: msg_r("EXPECT %s" % yellow(quo+str(s)+quo))
	else:       msg_r("+")

	try:
		if s == '': ret = 0
		else:
			f = p.expect if regex else p.expect_exact
			ret = f(s,timeout=3)
	except pexpect.TIMEOUT:
		errmsg(red("\nERROR.  Expect %s%s%s timed out.  Exiting" % (quo,s,quo)))
		sys.exit(1)

	if debug or (verbose and type(s) != str): msg_r(" ==> %s " % ret)

	if ret == -1:
		errmsg("Error.  Expect returned %s" % ret)
		sys.exit(1)
	else:
		if t == '':
			if not nonl: vmsg("")
		else: ret = my_send(p,t,delay,s)
		return ret

def cleandir(d):
	try:    files = os.listdir(d)
	except: return

	msg(green("Cleaning directory '%s'" % d))
	for f in files:
		os.unlink(os.path.join(d,f))

def get_file_with_ext(ext,mydir,delete=True):

	flist = [os.path.join(mydir,f) for f in os.listdir(mydir)
				if f == ext or f[-(len(ext)+1):] == "."+ext]

	if not flist: return False

	if len(flist) > 1:
		if delete:
			if not quiet:
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
	if verbose and display: msg("Checksum: %s" % cyan(chk))
	end_silence()
	return chk

def verify_checksum_or_exit(checksum,chk):
	if checksum != chk:
		errmsg(red("Checksum error: %s" % chk))
		sys.exit(1)
	vmsg(green("Checksums match: %s") % (cyan(chk)))

def get_rand_printable_chars(num_chars,no_punc=False):
	return [chr(ord(i)%94+33) for i in list(os.urandom(num_chars))]


class MMGenExpect(object):

	def __init__(self,name,mmgen_cmd,cmd_args=[],env=env):
		if not 'system' in opts:
			mmgen_cmd = os.path.join(os.curdir,mmgen_cmd)
		desc = cmd_data[name][1]
		if not desc: desc = name
		if verbose or exact_output:
			sys.stderr.write(
				green("Testing %s\nExecuting " % desc) +
				cyan("'%s %s'\n" % (mmgen_cmd," ".join(cmd_args)))
			)
		else:
			msg_r("Testing %s " % (desc+":"))
#		msgrepr(mmgen_cmd,cmd_args); msg("")
		if env: self.p = pexpect.spawn(mmgen_cmd,cmd_args,env=env)
		else:   self.p = pexpect.spawn(mmgen_cmd,cmd_args)
		if exact_output: self.p.logfile = sys.stdout

	def license(self):
		p = "'w' for conditions and warranty info, or 'c' to continue: "
		my_expect(self.p,p,'c')

	def usr_rand(self,num_chars):
		rand_chars = get_rand_printable_chars(num_chars)
		my_expect(self.p,'symbols left: ','x')
		try:
			vmsg_r("SEND ")
			while self.p.expect('left: ',0.1) == 0:
				ch = rand_chars.pop(0)
				msg_r(yellow(ch)+" " if verbose else "+")
				self.p.send(ch)
		except:
			vmsg("EOT")
		my_expect(self.p,"ENTER to continue: ",'\n')

	def passphrase_new(self,what,passphrase):
		my_expect(self.p,("Enter passphrase for new %s: " % what), passphrase+"\n")
		my_expect(self.p,"Repeat passphrase: ", passphrase+"\n")

	def passphrase(self,what,passphrase,pwtype=""):
		if pwtype: pwtype += " "
		my_expect(self.p,("Enter %spassphrase for %s.*?: " % (pwtype,what)),
				passphrase+"\n",regex=True)

	def hash_preset(self,what,preset=''):
		my_expect(self.p,("Enter hash preset for %s, or ENTER .*?:" % what),
				str(preset)+"\n",regex=True)

	def written_to_file(self,what,overwrite_unlikely=False,query="Overwrite?  "):
		s1 = "%s written to file " % what
		s2 = query + "Type uppercase 'YES' to confirm: "
		ret = my_expect(self.p,s1 if overwrite_unlikely else [s1,s2])
		if ret == 1:
			my_send(self.p,"YES\n")
			ret = my_expect(self.p,s1)
		outfile = self.p.readline().strip().strip("'")
		vmsg("%s file: %s" % (what,cyan(outfile.replace("'",""))))
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
		vout = int(getrand(4) % 8),
		txid = unicode(hexlify(os.urandom(32))),
		amount = Decimal("%s.%s" % (10+(getrand(4) % 40), getrand(4) % 100000000)),
		address = address,
		spendable = False,
		scriptPubKey = ("76a914"+verify_addr(address,return_hex=True)+"88ac"),
		confirmations = getrand(4) % 500
	))

def create_fake_unspent_data(adata,unspent_data_file,tx_data,non_mmgen_input=''):

	out = []
	for s in tx_data.keys():
		sid = tx_data[s]['sid']
		a = adata.addrinfo(sid)
		for idx,btcaddr in a.addrpairs():
			add_fake_unspent_entry(out,btcaddr,"%s:%s Test Wallet" % (sid,idx))

	if non_mmgen_input:
		from mmgen.bitcoin import privnum2addr,hextowif
		privnum = getrand(32)
		btcaddr = privnum2addr(privnum,compressed=True)
		of = os.path.join(cfgs[non_mmgen_input]['tmpdir'],non_mmgen_fn)
		write_to_file(of, hextowif("{:064x}".format(privnum),
					compressed=True)+"\n",{},"compressed bitcoin key")

		add_fake_unspent_entry(out,btcaddr,"Non-MMGen address")

#	msg("\n".join([repr(o) for o in out])); sys.exit()
	write_to_file(unspent_data_file,repr(out),{},"Unspent outputs",verbose=True)


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
	from mmgen.mn_tirosh import tirosh_words
	wl = tirosh_words.split("\n")
	nwords,ws_list,max_spaces = 10,"    \n",5
	def rand_ws_seq():
		nchars = getrand(1) % max_spaces + 1
		return "".join([ws_list[getrand(1)%len(ws_list)] for i in range(nchars)])
	rand_pairs = [wl[getrand(4) % len(wl)] + rand_ws_seq() for i in range(nwords)]
	d = "".join(rand_pairs).rstrip() + "\n"
	if verbose: msg_r("Brainwallet password:\n%s" % cyan(d))
	write_to_file(fn,d,{},"brainwallet password")

def do_between():
	if pause:
		from mmgen.util import keypress_confirm
		if keypress_confirm(green("Continue?"),default_yes=True):
			if verbose or exact_output: sys.stderr.write("\n")
		else:
			errmsg("Exiting at user request")
			sys.exit()
	elif verbose or exact_output:
		sys.stderr.write("\n")

def do_cmd(ts,cmd):

	d = [(str(num),ext) for exts,num in cmd_data[cmd][2] for ext in exts]
	al = [get_file_with_ext(ext,cfgs[num]['tmpdir']) for num,ext in d]

	global cfg
	cfg = cfgs[str(cmd_data[cmd][0])]

	ts.__class__.__dict__[cmd](*([ts,cmd] + al))


hincog_bytes   = 1024*1024
hincog_offset  = 98765
hincog_seedlen = 256

rebuild_list = OrderedDict()

def get_num_ext_for_cmd(cmd):
	num = str(cmd_data[cmd][0])
	dgl = cfgs[num]['dep_generators']
#	msgrepr(num,cmd,dgl)
	if cmd in dgl.values():
		ext = [k for k in dgl if dgl[k] == cmd][0]
		return (num,ext)
	else:
		return ('','')

def check_needs_rerun(cmd,build=False,root=True,force_delete=False):

	rerun = True if root else False

	num,ext = get_num_ext_for_cmd(cmd) # does cmd produce a needed dependency?
	if num and (force_delete or not root):
		fn = get_file_with_ext(ext,cfgs[num]['tmpdir'],delete=build)
		if not fn: rerun = True
		if fn and force_delete:
			os.unlink(fn); fn = ""
	else: fn = ""

	fdeps = [(str(n),e) for exts,n in cmd_data[cmd][2] for e in exts]
	cdeps = [cfgs[str(n)]['dep_generators'][e] for n,e in fdeps]

	if fn:
		my_age = os.stat(fn).st_mtime
		for num,ext in fdeps:
			f = get_file_with_ext(ext,cfgs[num]['tmpdir'],delete=build)
			if f and os.stat(f).st_mtime > my_age: rerun = True

	for cdep in cdeps:
		if check_needs_rerun(cdep,build=build,root=False): rerun = True

	if build:
		if rerun:
			if fn and not root:
				os.unlink(fn)
			do_cmd(ts,cmd)
			if not root: do_between()
	else:
		# If prog produces multiple files:
		if cmd not in rebuild_list or rerun == True:
			rebuild_list[cmd] = (rerun,fn)

	return rerun

def mk_tmpdir(cfg):
	try: os.mkdir(cfg['tmpdir'],0755)
	except OSError as e:
		if e.errno != 17: raise
	else: msg("Created directory '%s'" % cfg['tmpdir'])

def refcheck(what,chk,refchk):
	vmsg("Comparing %s '%s' to stored reference" % (what,chk))
	if chk == refchk:
		ok()
	else:
		if not verbose: errmsg("")
		errmsg(red("""
Fatal error - %s '%s' does not match reference value '%s'.  Aborting test
""".strip() % (what,chk,refchk)))
		sys.exit(3)

def ok():
	if verbose or exact_output:
		sys.stderr.write(green("OK\n"))
	else: msg(" OK")

class MMGenTestSuite(object):

	def __init__(self):
		pass

	def check_deps(self,name,cmds):
		if len(cmds) != 1:
			msg("Usage: %s check_deps <command>" % g.prog_name)
			sys.exit(1)

		cmd = cmds[0]

		if cmd not in cmd_data:
			msg("'%s': unrecognized command" % cmd)
			sys.exit(1)

		if not quiet:
			msg("Checking dependencies for '%s'" % (cmd))

		check_needs_rerun(cmd,build=False)

		w = max(len(i) for i in rebuild_list) + 1
		for cmd in rebuild_list:
			c = rebuild_list[cmd]
			m = "Rebuild" if (c[0] and c[1]) else "Build" if c[0] else "OK"
			msg("cmd {:<{w}} {}".format(cmd+":", m, w=w))
#			msgrepr(cmd,c)


	def clean(self,name,dirs=[]):
		dirlist = dirs if dirs else sorted(cfgs.keys())
		for k in dirlist:
			if k in cfgs:
				cleandir(cfgs[k]['tmpdir'])
			else:
				msg("%s: invalid directory index" % k)
				sys.exit(1)

	def walletgen(self,name,brain=False):
		mk_tmpdir(cfg)

		args = ["-d",cfg['tmpdir'],"-p1","-r10"]
#        if 'seed_len' in cfg: args += ["-l",cfg['seed_len']]
		if brain:
			bwf = os.path.join(cfg['tmpdir'],cfg['bw_filename'])
			args += ["-b",cfg['bw_params'],bwf]
			make_brainwallet_file(bwf)

		t = MMGenExpect(name,"mmgen-walletgen", args)
		t.license()

		if brain:
			t.expect(
	"A brainwallet will be secure only if you really know what you're doing")
			t.expect("Type uppercase 'YES' to confirm: ","YES\n")

		t.usr_rand(10)
		for s in "user-supplied entropy","saved user-supplied entropy":
			t.expect("Generating encryption key from OS random data plus %s" % s)
			if brain: break

		t.passphrase_new("MMGen wallet",cfg['wpasswd'])
		t.written_to_file("Wallet")
		ok()

	def refwalletgen(self,name):
		mk_tmpdir(cfg)
		args = ["-q","-d",cfg['tmpdir'],"-p1","-r10","-b"+cfg['bw_hashparams']]
		t = MMGenExpect(name,"mmgen-walletgen", args)
		t.expect("passphrase: ",cfg['bw_passwd']+"\n")
		t.usr_rand(10)
		t.passphrase_new("MMGen wallet",cfg['wpasswd'])
		key_id = t.written_to_file("Wallet").split("-")[0].split("/")[-1]
		refcheck("key id",key_id,cfg['key_id'])

	def passchg(self,name,walletfile):
		mk_tmpdir(cfg)

		t = MMGenExpect(name,"mmgen-passchg",
			["-d",cfg['tmpdir'],"-p","2","-L","New Label","-r","16",walletfile])
		t.passphrase("MMGen wallet",cfgs['1']['wpasswd'],pwtype="old")
		t.expect_getend("Label changed: ")
		t.expect_getend("Hash preset has changed ")
		t.passphrase("MMGen wallet",cfg['wpasswd'],pwtype="new")
		t.expect("Repeat passphrase: ",cfg['wpasswd']+"\n")
		t.usr_rand(16)
		t.expect_getend("Key ID changed: ")
		t.written_to_file("Wallet")
		ok()

	def walletchk_newpass(self,name,walletfile):
		t = self.walletchk_beg(name,[walletfile])
		ok()

	def walletchk_beg(self,name,args):
		t = MMGenExpect(name,"mmgen-walletchk", args)
		t.expect("Getting MMGen wallet data from file '%s'" % args[-1])
		t.passphrase("MMGen wallet",cfg['wpasswd'])
		t.expect("Passphrase is OK")
		t.expect("Wallet is OK")
		return t

	def walletchk(self,name,walletfile):
		t = self.walletchk_beg(name,[walletfile])
		ok()

	def addrgen(self,name,walletfile,check_ref=False):
		t = MMGenExpect(name,"mmgen-addrgen",["-d",cfg['tmpdir'],walletfile,cfg['addr_idx_list']])
		t.license()
		t.passphrase("MMGen wallet",cfg['wpasswd'])
		t.expect("Passphrase is OK")
		t.expect("[0-9]+ addresses generated",regex=True)
		chk = t.expect_getend(r"Checksum for address data .*?: ",regex=True)
		if check_ref:
			refcheck("address data checksum",chk,cfg['addrfile_chk'])
			return
		t.written_to_file("Addresses")
		ok()

	def refaddrgen(self,name,walletfile):
		self.addrgen(name,walletfile,check_ref=True)

	def addrimport(self,name,addrfile):
		outfile = os.path.join(cfg['tmpdir'],"addrfile_w_comments")
		add_comments_to_addr_file(addrfile,outfile)
		t = MMGenExpect(name,"mmgen-addrimport",[outfile])
		t.expect_getend(r"checksum for addr data .*\[.*\]: ",regex=True)
		t.expect_getend("Validating addresses...OK. ")
		t.expect("Type uppercase 'YES' to confirm: ","\n")
		vmsg("This is a simulation, so no addresses were actually imported into the tracking\nwallet")
		ok()

	def txcreate(self,name,addrfile):
		self.txcreate_common(name,sources=['1'])

	def txcreate_common(self,name,sources=['1'],non_mmgen_input=''):
		if verbose or exact_output:
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
				errmsg(red("Addr index list length != %s: %s" %
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
		btcaddr = privnum2addr(getrand(32),compressed=True)

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

		env["MMGEN_BOGUS_WALLET_DATA"] = unspent_data_file
		end_silence()
		if verbose or exact_output: sys.stderr.write("\n")

		t = MMGenExpect(name,"mmgen-txcreate",cmd_args,env)
		t.license()
		for num in tx_data.keys():
			t.expect_getend("Getting address data from file ")
			chk=t.expect_getend(r"Computed checksum for addr data .*?: ",regex=True)
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

	def txsign(self,name,txfile,walletfile):
		t = MMGenExpect(name,"mmgen-txsign", ["-d",cfg['tmpdir'],txfile,walletfile])
		t.license()
		t.tx_view()
		t.passphrase("MMGen wallet",cfg['wpasswd'])
		t.expect("Edit transaction comment? (y/N): ","\n")
		t.written_to_file("Signed transaction")
		ok()

	def txsend(self,name,sigfile):
		t = MMGenExpect(name,"mmgen-txsend", ["-d",cfg['tmpdir'],sigfile])
		t.license()
		t.tx_view()
		t.expect("Edit transaction comment? (y/N): ","\n")
		t.expect("Are you sure you want to broadcast this transaction to the network?")
		t.expect("Type uppercase 'YES, I REALLY WANT TO DO THIS' to confirm: ","\n")
		t.expect("Exiting at user request")
		vmsg("This is a simulation, so no transaction was sent")
		ok()

	def export_seed(self,name,walletfile):
		t = self.walletchk_beg(name,["-s","-d",cfg['tmpdir'],walletfile])
		f = t.written_to_file("Seed data")
		silence()
		msg("Seed data: %s" % cyan(get_data_from_file(f,"seed data")))
		end_silence()
		ok()

	def export_mnemonic(self,name,walletfile):
		t = self.walletchk_beg(name,["-m","-d",cfg['tmpdir'],walletfile])
		f = t.written_to_file("Mnemonic data")
		silence()
		msg_r("Mnemonic data: %s" % cyan(get_data_from_file(f,"mnemonic data")))
		end_silence()
		ok()

	def export_incog(self,name,walletfile,args=["-g"]):
		t = MMGenExpect(name,"mmgen-walletchk",args+["-d",cfg['tmpdir'],"-r","10",walletfile])
		t.passphrase("MMGen wallet",cfg['wpasswd'])
		t.usr_rand(10)
		t.expect_getend("Incog ID: ")
		if args[0] == "-G": return t
		t.written_to_file("Incognito wallet data",overwrite_unlikely=True)
		ok()

	def export_incog_hex(self,name,walletfile):
		self.export_incog(name,walletfile,args=["-X"])

	# TODO: make outdir and hidden incog compatible (ignore --outdir and warn user?)
	def export_incog_hidden(self,name,walletfile):
		rf,rd = os.path.join(cfg['tmpdir'],hincog_fn),os.urandom(hincog_bytes)
		vmsg(green("Writing %s bytes of data to file '%s'" % (hincog_bytes,rf)))
		write_to_file(rf,rd,{},verbose=verbose)
		t = self.export_incog(name,walletfile,args=["-G","%s,%s"%(rf,hincog_offset)])
		t.written_to_file("Data",query="")
		ok()

	def addrgen_seed(self,name,walletfile,foo,what="seed data",arg="-s"):
		t = MMGenExpect(name,"mmgen-addrgen",
				[arg,"-d",cfg['tmpdir'],walletfile,cfg['addr_idx_list']])
		t.license()
		t.expect_getend("Valid %s for seed ID " % what)
		vmsg("Comparing generated checksum with checksum from previous address file")
		chk = t.expect_getend(r"Checksum for address data .*?: ",regex=True)
		verify_checksum_or_exit(get_addrfile_checksum(),chk)
		t.no_overwrite()
		ok()

	def addrgen_mnemonic(self,name,walletfile,foo):
		self.addrgen_seed(name,walletfile,foo,what="mnemonic",arg="-m")

	def addrgen_incog(self,name,walletfile,foo,args=["-g"]):
		t = MMGenExpect(name,"mmgen-addrgen",args+["-d",
				cfg['tmpdir'],walletfile,cfg['addr_idx_list']])
		t.license()
		t.expect_getend("Incog ID: ")
		t.passphrase("MMGen incognito wallet \w{8}", cfg['wpasswd'])
		t.hash_preset("incog wallet",'1')
		vmsg("Comparing generated checksum with checksum from address file")
		chk = t.expect_getend(r"Checksum for address data .*?: ",regex=True)
		verify_checksum_or_exit(get_addrfile_checksum(),chk)
		t.no_overwrite()
		ok()

	def addrgen_incog_hex(self,name,walletfile,foo):
		self.addrgen_incog(name,walletfile,foo,args=["-X"])

	def addrgen_incog_hidden(self,name,walletfile,foo):
		rf = os.path.join(cfg['tmpdir'],hincog_fn)
		self.addrgen_incog(name,walletfile,foo,
				args=["-G","%s,%s,%s"%(rf,hincog_offset,hincog_seedlen)])

	def keyaddrgen(self,name,walletfile,check_ref=False):
		t = MMGenExpect(name,"mmgen-keygen",
				["-d",cfg['tmpdir'],walletfile,cfg['addr_idx_list']])
		t.license()
		t.expect("Type uppercase 'YES' to confirm: ","YES\n")
		t.passphrase("MMGen wallet",cfg['wpasswd'])
		chk = t.expect_getend(r"Checksum for key-address data .*?: ",regex=True)
		if check_ref:
			refcheck("key-address data checksum",chk,cfg['keyaddrfile_chk'])
			return
		t.expect("Encrypt key list? (y/N): ","y")
		t.hash_preset("new key list",'1')
		t.passphrase_new("key list",cfg['kapasswd'])
		t.written_to_file("Keys")
		ok()

	def refkeyaddrgen(self,name,walletfile):
		self.keyaddrgen(name,walletfile,check_ref=True)

	def txsign_keyaddr(self,name,keyaddr_file,txfile):
		t = MMGenExpect(name,"mmgen-txsign", ["-d",cfg['tmpdir'],"-M",keyaddr_file,txfile])
		t.license()
		t.hash_preset("key-address file",'1')
		t.passphrase("key-address file",cfg['kapasswd'])
		t.expect("Check key-to-address validity? (y/N): ","y")
		t.tx_view()
		t.expect("Signing transaction...OK")
		t.expect("Edit transaction comment? (y/N): ","\n")
		t.written_to_file("Signed transaction")
		ok()

	def walletgen2(self,name):
		self.walletgen(name)

	def addrgen2(self,name,walletfile):
		self.addrgen(name,walletfile)

	def txcreate2(self,name,addrfile):
		self.txcreate_common(name,sources=['2'])

	def txsign2(self,name,txf1,wf1,txf2,wf2):
		t = MMGenExpect(name,"mmgen-txsign", ["-d",cfg['tmpdir'],txf1,wf1,txf2,wf2])
		t.license()

		for cnum in ['1','2']:
			t.tx_view()
			t.passphrase("MMGen wallet",cfgs[cnum]['wpasswd'])
			t.expect_getend("Signing transaction ")
			t.expect("Edit transaction comment? (y/N): ","\n")
			t.written_to_file("Signed transaction #%s" % cnum)

		ok()

	def export_mnemonic2(self,name,walletfile):
		self.export_mnemonic(name,walletfile)

	def walletgen3(self,name):
		self.walletgen(name)

	def addrgen3(self,name,walletfile):
		self.addrgen(name,walletfile)

	def txcreate3(self,name,addrfile1,addrfile2):
		self.txcreate_common(name,sources=['1','3'])

	def txsign3(self,name,wf1,wf2,txf2):
		t = MMGenExpect(name,"mmgen-txsign", ["-d",cfg['tmpdir'],wf1,wf2,txf2])
		t.license()
		t.tx_view()

		for s in ['1','3']:
			t.expect_getend("Getting MMGen wallet data from file ")
			t.passphrase("MMGen wallet",cfgs[s]['wpasswd'])

		t.expect_getend("Signing transaction")
		t.expect("Edit transaction comment? (y/N): ","\n")
		t.written_to_file("Signed transaction")
		ok()

	def walletgen4(self,name):
		self.walletgen(name,brain=True)

	def addrgen4(self,name,walletfile):
		self.addrgen(name,walletfile)

	def txcreate4(self,name,f1,f2,f3,f4):
		self.txcreate_common(name,sources=['1','2','3','4'],non_mmgen_input='4')

	def txsign4(self,name,f1,f2,f3,f4,f5):
		non_mm_fn = os.path.join(cfg['tmpdir'],non_mmgen_fn)
		t = MMGenExpect(name,"mmgen-txsign",
			["-d",cfg['tmpdir'],"-b",cfg['bw_params'],"-k",non_mm_fn,f1,f2,f3,f4,f5])
		t.license()
		t.tx_view()

		for cfgnum,what,app in ('1',"incognito"," incognito"),('3',"MMGen",""):
			t.expect_getend("Getting %s wallet data from file " % what)
			t.passphrase("MMGen%s wallet"%app,cfgs[cfgnum]['wpasswd'])
			if cfgnum == '1':
				t.hash_preset("incog wallet",'1')

		t.expect_getend("Signing transaction")
		t.expect("Edit transaction comment? (y/N): ","\n")
		t.written_to_file("Signed transaction")
		ok()


def write_to_tmpfile(fn,data):
	write_to_file(os.path.join(cfg['tmpdir'],fn),data,{},silent=True)

def read_from_tmpfile(fn):
	from mmgen.util import get_data_from_file
	return get_data_from_file(os.path.join(cfg['tmpdir'],fn),silent=True)

def read_from_file(fn):
	from mmgen.util import get_data_from_file
	return get_data_from_file(fn,silent=True)

class MMGenToolTestSuite(object):

	def __init__(self):
		global cmd_data,tool_cmd_data
		cmd_data = tool_cmd_data
		pass

	def clean(self,name):
		cleandir(cfgs['10']['tmpdir'])

	def cmd(self,name,tool_args):
		mk_tmpdir(cfg)
		t = MMGenExpect(name,"mmgen-tool", ["-d",cfg['tmpdir']] + tool_args)
		return t.read()

	def cmd_to_tmpfile(self,name,tool_args,tmpfile):
		ret = self.cmd(name,tool_args)
		if ret:
			write_to_tmpfile(tmpfile,ret)
			ok()

	def strtob58(self,name):
		s = "".join(get_rand_printable_chars(15))
		write_to_tmpfile('strtob58.in',s)
		self.cmd_to_tmpfile(name,["strtob58",s],'strtob58.out')

	def b58tostr(self,name,f1,f2):
		idata = read_from_file(f1)
		odata = read_from_file(f2)[:-2]
		res = self.cmd(name,["b58tostr",odata])[:-2]
		if res == idata: ok()
		else: errmsg(red("Error"))

	def hextob58(self,name):
		hexnum = getrandhex(32)
		write_to_tmpfile('hextob58.in',hexnum)
		self.cmd_to_tmpfile(name,["hextob58",hexnum],'hextob58.out')

	def b58tohex(self,name,f1,f2):
		idata = read_from_file(f1)
		odata = read_from_file(f2)[:-2]
		res = self.cmd(name,["b58tohex",odata])[:-2]
		if res == idata: ok()
		else: errmsg(red("Error"))
# 	"b58randenc":   [],
# 	"randhex":      ['nbytes [int=32]'],
# 	"randwif":      ['compressed [bool=False]'],
# 	"randpair":     ['compressed [bool=False]'],
# 	"wif2hex":      ['<wif> [str]', 'compressed [bool=False]'],
# 	"wif2addr":     ['<wif> [str]', 'compressed [bool=False]'],
# 	"hex2wif":      ['<private key in hex format> [str]', 'compressed [bool=False]'],
# 	"hexdump":      ['<infile> [str]', 'cols [int=8]', 'line_nums [bool=True]'],
# 	"unhexdump":    ['<infile> [str]'],
# 	"hex2mn":       ['<hexadecimal string> [str]','wordlist [str="electrum"]'],
# 	"mn2hex":       ['<mnemonic> [str]', 'wordlist [str="electrum"]'],
# 	"b32tohex":     ['<b32 num> [str]'],
# 	"hextob32":     ['<hex num> [str]'],
# 	"mn_rand128":   ['wordlist [str="electrum"]'],
# 	"mn_rand192":   ['wordlist [str="electrum"]'],
# 	"mn_rand256":   ['wordlist [str="electrum"]'],
# 	"mn_stats":     ['wordlist [str="electrum"]'],
# 	"mn_printlist": ['wordlist [str="electrum"]'],
# 	"id8":          ['<infile> [str]'],
# 	"id6":          ['<infile> [str]'],
# 	"str2id6":      ['<string (spaces are ignored)> [str]'],

# main()
if pause:
	import termios,atexit
	fd = sys.stdin.fileno()
	old = termios.tcgetattr(fd)
	def at_exit():
		termios.tcsetattr(fd, termios.TCSADRAIN, old)
	atexit.register(at_exit)

start_time = int(time.time())

try:
	if cmd_args and cmd_args[0] != "tool":
		arg1 = cmd_args[0]
		if arg1 in utils:
			MMGenTestSuite.__dict__[arg1](ts,arg1,cmd_args[1:])
			sys.exit()
		elif arg1 in meta_cmds:
			ts = MMGenTestSuite()
			if len(cmd_args) == 1:
				for cmd in meta_cmds[arg1][1]:
					check_needs_rerun(cmd,build=True,force_delete=True)
			else:
				msg("Only one meta command may be specified")
				sys.exit(1)
		elif arg1 in cmd_data.keys() + tool_cmd_data.keys():
			ts = MMGenTestSuite() if arg1 in cmd_data else MMGenToolTestSuite()
			if len(cmd_args) == 1:
				check_needs_rerun(arg1,build=True)
			else:
				msg("Only one command may be specified")
				sys.exit(1)
		else:
			errmsg("%s: unrecognized command" % arg1)
			sys.exit(1)
	else:
		if cmd_args: # tool
			if len(cmd_args) != 1:
				msg("Only one command may be specified")
				sys.exit(1)
			ts = MMGenToolTestSuite()
		else:
			ts = MMGenTestSuite()

		ts.clean("clean")
		for cmd in cmd_data:
			do_cmd(ts,cmd)
			if cmd is not cmd_data.keys()[-1]: do_between()
except:
	sys.stderr = stderr_save
	raise

t = int(time.time()) - start_time
msg(green(
	"All requested tests finished OK, elapsed time: %02i:%02i" % (t/60,t%60)))

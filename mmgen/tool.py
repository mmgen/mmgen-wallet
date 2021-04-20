#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2021 The MMGen Project <mmgen@tuta.io>
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
tool.py:  Routines for the 'mmgen-tool' utility
"""

from collections import namedtuple
from .protocol import hash160
from .common import *
from .crypto import *
from .addr import *

NL = ('\n','\r\n')[g.platform=='win']

def _options_annot_str(l):
	return "(valid options: '{}')".format("','".join(l))

def _create_call_sig(cmd,parsed=False):

	m = MMGenToolCmds[cmd]

	if 'varargs_call_sig' in m.__code__.co_varnames: # hack
		flag = 'VAR_ARGS'
		va = m.__defaults__[0]
		args,dfls,ann = va['args'],va['dfls'],va['annots']
	else:
		flag = None
		args = m.__code__.co_varnames[1:m.__code__.co_argcount]
		dfls = m.__defaults__ or ()
		ann  = m.__annotations__

	nargs = len(args) - len(dfls)

	def get_type_from_ann(arg):
		return ann[arg][1:] + (' or STDIN','')[parsed] if ann[arg] == 'sstr' else ann[arg].__name__

	if parsed:
		c_args = [(a,get_type_from_ann(a)) for a in args[:nargs]]
		c_kwargs = [(a,dfls[n]) for n,a in enumerate(args[nargs:])]
		return c_args,dict(c_kwargs),'STDIN_OK' if c_args and ann[args[0]] == 'sstr' else flag
	else:
		c_args = ['{} [{}]'.format(a,get_type_from_ann(a)) for a in args[:nargs]]
		c_kwargs = ['"{}" [{}={!r}{}]'.format(
					a, type(dfls[n]).__name__, dfls[n],
					(' ' + ann[a] if a in ann else ''))
						for n,a in enumerate(args[nargs:])]
		return ' '.join(c_args + c_kwargs)

def _usage(cmd=None,exit_val=1):

	m1=('USAGE INFORMATION FOR MMGEN-TOOL COMMANDS:\n\n'
		'  Unquoted arguments are mandatory\n'
		'  Quoted arguments are optional, default values will be used\n'
		'  Argument types and default values are shown in square brackets\n')

	m2=('  To force a command to read from STDIN instead of file (for commands taking\n'
		'  a filename as their first argument), substitute "-" for the filename.\n\n'
		'EXAMPLES:\n\n'
		'  Generate a random Bech32 public/private keypair for LTC:\n'
		'  $ mmgen-tool -r0 --coin=ltc --type=bech32 randpair\n\n'
		'  Generate a DASH compressed public key address from the supplied WIF key:\n'
		'  $ mmgen-tool --coin=dash --type=compressed wif2addr XJkVRC3eGKurc9Uzx1wfQoio3yqkmaXVqLMTa6y7s3M3jTBnmxfw\n\n'
		'  Generate a well-known burn address:\n'
		'  $ mmgen-tool hextob58chk 000000000000000000000000000000000000000000\n\n'
		'  Generate a random 12-word seed phrase:\n'
		'  $ mmgen-tool -r0 mn_rand128\n\n'
		'  Same as above, but get additional entropy from user:\n'
		'  $ mmgen-tool mn_rand128\n\n'
		'  Encode bytes from a file to base 58:\n'
		'  $ mmgen-tool bytestob58 /etc/timezone pad=20\n\n'
		'  Reverse a hex string:\n'
		'  $ mmgen-tool hexreverse "deadbeefcafe"\n\n'
		'  Same as above, but use a pipe:\n'
		'  $ echo "deadbeefcafe" | mmgen-tool hexreverse -')

	if not cmd:
		Msg(m1)
		for bc in MMGenToolCmds.classes.values():
			cls_info = bc.__doc__.strip().split('\n')[0]
			Msg('  {}{}\n'.format(cls_info[0].upper(),cls_info[1:]))
			max_w = max(map(len,bc.user_commands))
			for cmd in sorted(bc.user_commands):
				Msg('    {:{w}} {}'.format(cmd,_create_call_sig(cmd),w=max_w))
			Msg('')
		Msg(m2)
	elif cmd in MMGenToolCmds:
		p1 = fmt(capfirst(MMGenToolCmds[cmd].__doc__.strip()),strip_char='\t').strip()
		msg('{}{}\nUSAGE: {} {} {}'.format(
			p1,
			('\n' if '\n' in p1 else ''),
			g.prog_name,cmd,
			_create_call_sig(cmd))
		)
	else:
		die(1,"'{}': no such tool command".format(cmd))

	sys.exit(exit_val)

def _process_args(cmd,cmd_args):
	c_args,c_kwargs,flag = _create_call_sig(cmd,parsed=True)
	have_stdin_input = False

	if flag != 'VAR_ARGS':
		if len(cmd_args) < len(c_args):
			m1 = 'Command requires exactly {} non-keyword argument{}'
			msg(m1.format(len(c_args),suf(c_args)))
			_usage(cmd)

		u_args = cmd_args[:len(c_args)]

		# If we're reading from a pipe, replace '-' with output of previous command
		if flag == 'STDIN_OK' and u_args and u_args[0] == '-':
			if sys.stdin.isatty():
				raise BadFilename("Standard input is a TTY.  Can't use '-' as a filename")
			else:
				max_dlen_spec = '10kB' # limit input to 10KB for now
				max_dlen = MMGenToolCmdUtil().bytespec(max_dlen_spec)
				u_args[0] = os.read(0,max_dlen)
				have_stdin_input = True
				if len(u_args[0]) >= max_dlen:
					die(2,'Maximum data input for this command is {}'.format(max_dlen_spec))
				if not u_args[0]:
					die(2,'{}: ERROR: no output from previous command in pipe'.format(cmd))

	u_nkwargs = len(cmd_args) - len(c_args)
	u_kwargs = {}
	if flag == 'VAR_ARGS':
		t = [a.split('=',1) for a in cmd_args if '=' in a]
		tk = [a[0] for a in t]
		tk_bad = [a for a in tk if a not in c_kwargs]
		if set(tk_bad) != set(tk[:len(tk_bad)]): # permit non-kw args to contain '='
			die(1,"'{}': illegal keyword argument".format(tk_bad[-1]))
		u_kwargs = dict(t[len(tk_bad):])
		u_args = cmd_args[:-len(u_kwargs) or None]
	elif u_nkwargs > 0:
		u_kwargs = dict([a.split('=',1) for a in cmd_args[len(c_args):] if '=' in a])
		if len(u_kwargs) != u_nkwargs:
			msg('Command requires exactly {} non-keyword argument{}'.format(len(c_args),suf(c_args)))
			_usage(cmd)
		if len(u_kwargs) > len(c_kwargs):
			msg('Command accepts no more than {} keyword argument{}'.format(len(c_kwargs),suf(c_kwargs)))
			_usage(cmd)

	for k in u_kwargs:
		if k not in c_kwargs:
			msg("'{}': invalid keyword argument".format(k))
			_usage(cmd)

	def conv_type(arg,arg_name,arg_type):
		if arg_type == 'bytes' and type(arg) != bytes:
			die(1,"'Binary input data must be supplied via STDIN")

		if have_stdin_input and arg_type == 'str' and isinstance(arg,bytes):
			arg = arg.decode()
			if arg[-len(NL):] == NL: # rstrip one newline
				arg = arg[:-len(NL)]

		if arg_type == 'bool':
			if arg.lower() in ('true','yes','1','on'): arg = True
			elif arg.lower() in ('false','no','0','off'): arg = False
			else:
				msg("'{}': invalid boolean value for keyword argument".format(arg))
				_usage(cmd)

		try:
			return __builtins__[arg_type](arg)
		except:
			die(1,"'{}': Invalid argument for argument {} ('{}' required)".format(arg,arg_name,arg_type))

	if flag == 'VAR_ARGS':
		args = [conv_type(u_args[i],c_args[0][0],c_args[0][1]) for i in range(len(u_args))]
	else:
		args = [conv_type(u_args[i],c_args[i][0],c_args[i][1]) for i in range(len(c_args))]
	kwargs = {k:conv_type(u_kwargs[k],k,type(c_kwargs[k]).__name__) for k in u_kwargs}

	return args,kwargs

def _process_result(ret,pager=False,print_result=False):
	"""
	Convert result to something suitable for output to screen and return it.
	If result is bytes and not convertible to utf8, output as binary using os.write().
	If 'print_result' is True, send the converted result directly to screen or
	pager instead of returning it.
	"""
	def triage_result(o):
		return o if not print_result else do_pager(o) if pager else Msg(o)

	if ret == True:
		return True
	elif ret in (False,None):
		ydie(1,"tool command returned '{}'".format(ret))
	elif isinstance(ret,str):
		return triage_result(ret)
	elif isinstance(ret,int):
		return triage_result(str(ret))
	elif isinstance(ret,tuple):
		return triage_result('\n'.join([r.decode() if isinstance(r,bytes) else r for r in ret]))
	elif isinstance(ret,bytes):
		try:
			o = ret.decode()
			return o if not print_result else do_pager(o) if pager else Msg(o)
		except:
			# don't add NL to binary data if it can't be converted to utf8
			return ret if not print_result else os.write(1,ret)
	else:
		ydie(1,"tool.py: can't handle return value of type '{}'".format(type(ret).__name__))

from .obj import MMGenAddrType

def conv_cls_bip39():
	from .bip39 import bip39
	return bip39

dfl_mnemonic_fmt = 'mmgen'
mnemonic_fmts = {
	'mmgen': { 'fmt': 'words', 'conv_cls': lambda: baseconv },
	'bip39': { 'fmt': 'bip39', 'conv_cls': conv_cls_bip39 },
	'xmrseed': { 'fmt': 'xmrseed','conv_cls': lambda: baseconv },
}
mn_opts_disp = _options_annot_str(mnemonic_fmts)

class MMGenToolCmdMeta(type):
	classes = {}
	methods = {}
	def __new__(mcls,name,bases,namespace):
		methods = {k:v for k,v in namespace.items() if k[0] != '_' and callable(v) and v.__doc__}
		if g.test_suite:
			if name in mcls.classes:
				raise ValueError(f'Class {name!r} already defined!')
			for m in methods:
				if m in mcls.methods:
					raise ValueError(f'Method {m!r} already defined!')
				if not getattr(m,'__doc__',None):
					raise ValueError(f'Method {m!r} has no doc string!')
		cls = super().__new__(mcls,name,bases,namespace)
		if bases and name != 'tool_api':
			mcls.classes[name] = cls
			mcls.methods.update(methods)
		return cls

	def __iter__(cls):
		return cls.methods.__iter__()

	def __getitem__(cls,val):
		return cls.methods.__getitem__(val)

	def __contains__(cls,val):
		return cls.methods.__contains__(val)

	def classname(cls,cmd_name):
		return cls.methods[cmd_name].__qualname__.split('.')[0]

	def call(cls,cmd_name,*args,**kwargs):
		return getattr(cls.classes[cls.classname(cmd_name)](),cmd_name)(*args,**kwargs)

	@property
	def user_commands(cls):
		return {k:v for k,v in cls.__dict__.items() if k in cls.methods}

class MMGenToolCmds(metaclass=MMGenToolCmdMeta):

	def __init__(self,proto=None,mmtype=None):
		from .protocol import init_proto_from_opts
		self.proto = proto or init_proto_from_opts()
		self.mmtype = MMGenAddrType(self.proto,(mmtype or getattr(opt,'type',None) or self.proto.dfl_mmtype))
		if g.token:
			self.proto.tokensym = g.token.upper()

	def init_generators(self,arg=None):
		gd = namedtuple('generator_data',['at','kg','ag'])

		at = MMGenAddrType(
			proto = self.proto,
			id_str = self.mmtype )

		if arg == 'addrtype_only':
			return gd(at,None,None)
		else:
			return gd(
				at,
				KeyGenerator(self.proto,at),
				AddrGenerator(self.proto,at),
			)


class MMGenToolCmdMisc(MMGenToolCmds):
	"miscellaneous commands"

	def help(self,command_name=''):
		"display usage information for a single command or all commands"
		_usage(command_name,exit_val=0)

	usage = help

class MMGenToolCmdUtil(MMGenToolCmds):
	"general string conversion and hashing utilities"

	def bytespec(self,dd_style_byte_specifier:str):
		"convert a byte specifier such as '1GB' into an integer"
		return parse_bytespec(dd_style_byte_specifier)

	def to_bytespec(self,
			n: int,
			dd_style_byte_specifier: str,
			fmt = '0.2',
			print_sym = True ):
		"convert an integer to a byte specifier such as '1GB'"
		return int2bytespec(n,dd_style_byte_specifier,fmt,print_sym)

	def randhex(self,nbytes='32'):
		"print 'n' bytes (default 32) of random data in hex format"
		return get_random(int(nbytes)).hex()

	def hexreverse(self,hexstr:'sstr'):
		"reverse bytes of a hexadecimal string"
		return bytes.fromhex(hexstr.strip())[::-1].hex()

	def hexlify(self,infile:str):
		"convert bytes in file to hexadecimal (use '-' for stdin)"
		data = get_data_from_file(infile,dash=True,quiet=True,binary=True)
		return data.hex()

	def unhexlify(self,hexstr:'sstr'):
		"convert hexadecimal value to bytes (warning: outputs binary data)"
		return bytes.fromhex(hexstr)

	def hexdump(self,infile:str,cols=8,line_nums='hex'):
		"create hexdump of data from file (use '-' for stdin)"
		data = get_data_from_file(infile,dash=True,quiet=True,binary=True)
		return pretty_hexdump(data,cols=cols,line_nums=line_nums).rstrip()

	def unhexdump(self,infile:str):
		"decode hexdump from file (use '-' for stdin) (warning: outputs binary data)"
		if g.platform == 'win':
			import msvcrt
			msvcrt.setmode(sys.stdout.fileno(),os.O_BINARY)
		hexdata = get_data_from_file(infile,dash=True,quiet=True)
		return decode_pretty_hexdump(hexdata)

	def hash160(self,hexstr:'sstr'):
		"compute ripemd160(sha256(data)) (convert hex pubkey to hex addr)"
		return hash160(hexstr)

	def hash256(self,string_or_bytes:str,file_input=False,hex_input=False): # TODO: handle stdin
		"compute sha256(sha256(data)) (double sha256)"
		from hashlib import sha256
		if file_input:  b = get_data_from_file(string_or_bytes,binary=True)
		elif hex_input: b = decode_pretty_hexdump(string_or_bytes)
		else:           b = string_or_bytes
		return sha256(sha256(b.encode()).digest()).hexdigest()

	def id6(self,infile:str):
		"generate 6-character MMGen ID for a file (use '-' for stdin)"
		return make_chksum_6(
			get_data_from_file(infile,dash=True,quiet=True,binary=True))

	def str2id6(self,string:'sstr'): # retain ignoring of space for backwards compat
		"generate 6-character MMGen ID for a string, ignoring spaces"
		return make_chksum_6(''.join(string.split()))

	def id8(self,infile:str):
		"generate 8-character MMGen ID for a file (use '-' for stdin)"
		return make_chksum_8(
			get_data_from_file(infile,dash=True,quiet=True,binary=True))

	def randb58(self,nbytes=32,pad=0):
		"generate random data (default: 32 bytes) and convert it to base 58"
		return baseconv.frombytes(get_random(nbytes),'b58',pad=pad,tostr=True)

	def bytestob58(self,infile:str,pad=0):
		"convert bytes to base 58 (supply data via STDIN)"
		data = get_data_from_file(infile,dash=True,quiet=True,binary=True)
		return baseconv.frombytes(data,'b58',pad=pad,tostr=True)

	def b58tobytes(self,b58num:'sstr',pad=0):
		"convert a base 58 number to bytes (warning: outputs binary data)"
		return baseconv.tobytes(b58num,'b58',pad=pad)

	def hextob58(self,hexstr:'sstr',pad=0):
		"convert a hexadecimal number to base 58"
		return baseconv.fromhex(hexstr,'b58',pad=pad,tostr=True)

	def b58tohex(self,b58num:'sstr',pad=0):
		"convert a base 58 number to hexadecimal"
		return baseconv.tohex(b58num,'b58',pad=pad)

	def hextob58chk(self,hexstr:'sstr'):
		"convert a hexadecimal number to base58-check encoding"
		from .protocol import _b58chk_encode
		return _b58chk_encode(bytes.fromhex(hexstr))

	def b58chktohex(self,b58chk_num:'sstr'):
		"convert a base58-check encoded number to hexadecimal"
		from .protocol import _b58chk_decode
		return _b58chk_decode(b58chk_num).hex()

	def hextob32(self,hexstr:'sstr',pad=0):
		"convert a hexadecimal number to MMGen's flavor of base 32"
		return baseconv.fromhex(hexstr,'b32',pad,tostr=True)

	def b32tohex(self,b32num:'sstr',pad=0):
		"convert an MMGen-flavor base 32 number to hexadecimal"
		return baseconv.tohex(b32num.upper(),'b32',pad)

	def hextob6d(self,hexstr:'sstr',pad=0,add_spaces=True):
		"convert a hexadecimal number to die roll base6 (base6d)"
		ret = baseconv.fromhex(hexstr,'b6d',pad,tostr=True)
		return block_format(ret,gw=5,cols=None).strip() if add_spaces else ret

	def b6dtohex(self,b6d_num:'sstr',pad=0):
		"convert a die roll base6 (base6d) number to hexadecimal"
		return baseconv.tohex(remove_whitespace(b6d_num),'b6d',pad)

class MMGenToolCmdCoin(MMGenToolCmds):
	"""
	cryptocoin key/address utilities

		May require use of the '--coin', '--type' and/or '--testnet' options

		Examples:
			mmgen-tool --coin=ltc --type=bech32 wif2addr <wif key>
			mmgen-tool --coin=zec --type=zcash_z randpair
	"""
	def randwif(self):
		"generate a random private key in WIF format"
		gd = self.init_generators('addrtype_only')
		return PrivKey(
			self.proto,
			get_random(32),
			pubkey_type = gd.at.pubkey_type,
			compressed  = gd.at.compressed ).wif

	def randpair(self):
		"generate a random private key/address pair"
		gd = self.init_generators()
		privhex = PrivKey(
			self.proto,
			get_random(32),
			pubkey_type = gd.at.pubkey_type,
			compressed  = gd.at.compressed )
		addr = gd.ag.to_addr(gd.kg.to_pubhex(privhex))
		return (privhex.wif,addr)

	def wif2hex(self,wifkey:'sstr'):
		"convert a private key from WIF to hex format"
		return PrivKey(
			self.proto,
			wif = wifkey )

	def hex2wif(self,privhex:'sstr'):
		"convert a private key from hex to WIF format"
		gd = self.init_generators('addrtype_only')
		return PrivKey(
			self.proto,
			bytes.fromhex(privhex),
			pubkey_type = gd.at.pubkey_type,
			compressed  = gd.at.compressed ).wif

	def wif2addr(self,wifkey:'sstr'):
		"generate a coin address from a key in WIF format"
		gd = self.init_generators()
		privhex = PrivKey(
			self.proto,
			wif = wifkey )
		addr = gd.ag.to_addr(gd.kg.to_pubhex(privhex))
		return addr

	def wif2redeem_script(self,wifkey:'sstr'): # new
		"convert a WIF private key to a Segwit P2SH-P2WPKH redeem script"
		assert self.mmtype.name == 'segwit','This command is meaningful only for --type=segwit'
		gd = self.init_generators()
		privhex = PrivKey(
			self.proto,
			wif = wifkey )
		return gd.ag.to_segwit_redeem_script(gd.kg.to_pubhex(privhex))

	def wif2segwit_pair(self,wifkey:'sstr'):
		"generate both a Segwit P2SH-P2WPKH redeem script and address from WIF"
		assert self.mmtype.name == 'segwit','This command is meaningful only for --type=segwit'
		gd = self.init_generators()
		pubhex = gd.kg.to_pubhex(PrivKey(
			self.proto,
			wif = wifkey ))
		addr = gd.ag.to_addr(pubhex)
		rs = gd.ag.to_segwit_redeem_script(pubhex)
		return (rs,addr)

	def privhex2addr(self,privhex:'sstr',output_pubhex=False):
		"generate coin address from raw private key data in hexadecimal format"
		gd = self.init_generators()
		pk = PrivKey(
			self.proto,
			bytes.fromhex(privhex),
			compressed  = gd.at.compressed,
			pubkey_type = gd.at.pubkey_type )
		ph = gd.kg.to_pubhex(pk)
		return ph if output_pubhex else gd.ag.to_addr(ph)

	def privhex2pubhex(self,privhex:'sstr'): # new
		"generate a hex public key from a hex private key"
		return self.privhex2addr(privhex,output_pubhex=True)

	def pubhex2addr(self,pubkeyhex:'sstr'):
		"convert a hex pubkey to an address"
		if self.mmtype.name == 'segwit':
			return self.proto.pubhex2segwitaddr(pubkeyhex)
		else:
			return self.pubhash2addr(hash160(pubkeyhex))

	def pubhex2redeem_script(self,pubkeyhex:'sstr'): # new
		"convert a hex pubkey to a Segwit P2SH-P2WPKH redeem script"
		assert self.mmtype.name == 'segwit','This command is meaningful only for --type=segwit'
		return self.proto.pubhex2redeem_script(pubkeyhex)

	def redeem_script2addr(self,redeem_scripthex:'sstr'): # new
		"convert a Segwit P2SH-P2WPKH redeem script to an address"
		assert self.mmtype.name == 'segwit','This command is meaningful only for --type=segwit'
		assert redeem_scripthex[:4] == '0014','{!r}: invalid redeem script'.format(redeem_scripthex)
		assert len(redeem_scripthex) == 44,'{} bytes: invalid redeem script length'.format(len(redeem_scripthex)//2)
		return self.pubhash2addr(hash160(redeem_scripthex))

	def pubhash2addr(self,pubhashhex:'sstr'):
		"convert public key hash to address"
		if self.mmtype.name == 'bech32':
			return self.proto.pubhash2bech32addr(pubhashhex)
		else:
			gd = self.init_generators('addrtype_only')
			return self.proto.pubhash2addr(pubhashhex,gd.at.addr_fmt=='p2sh')

	def addr2pubhash(self,addr:'sstr'):
		"convert coin address to public key hash"
		from .tx import addr2pubhash
		return addr2pubhash(self.proto,CoinAddr(self.proto,addr))

	def addr2scriptpubkey(self,addr:'sstr'):
		"convert coin address to scriptPubKey"
		from .tx import addr2scriptPubKey
		return addr2scriptPubKey(self.proto,CoinAddr(self.proto,addr))

	def scriptpubkey2addr(self,hexstr:'sstr'):
		"convert scriptPubKey to coin address"
		from .tx import scriptPubKey2addr
		return scriptPubKey2addr(self.proto,hexstr)[0]

class MMGenToolCmdMnemonic(MMGenToolCmds):
	"""
	seed phrase utilities (valid formats: 'mmgen' (default), 'bip39', 'xmrseed')

		IMPORTANT NOTE: MMGen's default seed phrase format uses the Electrum
		wordlist, however seed phrases are computed using a different algorithm
		and are NOT Electrum-compatible!

		BIP39 support is fully compatible with the standard, allowing users to
		import and export seed entropy from BIP39-compatible wallets.  However,
		users should be aware that BIP39 support does not imply BIP32 support!
		MMGen uses its own key derivation scheme differing from the one described
		by the BIP32 protocol.

		For Monero ('xmrseed') seed phrases, input data is reduced to a spendkey
		before conversion so that a canonical seed phrase is produced.  This is
		required because Monero seeds, unlike ordinary wallet seeds, are tied
		to a concrete key/address pair.  To manually generate a Monero spendkey,
		use the 'hex2wif' command.
	"""

	@staticmethod
	def _xmr_reduce(bytestr):
		from .protocol import init_proto
		proto = init_proto('xmr')
		if len(bytestr) != proto.privkey_len:
			m = '{!r}: invalid bit length for Monero private key (must be {})'
			die(1,m.format(len(bytestr*8),proto.privkey_len*8))
		return proto.preprocess_key(bytestr,None)

	def _do_random_mn(self,nbytes:int,fmt:str):
		assert nbytes in (16,24,32), 'nbytes must be 16, 24 or 32'
		randbytes = get_random(nbytes)
		if fmt == 'xmrseed':
			randbytes = self._xmr_reduce(randbytes)
		if opt.verbose:
			msg('Seed: {}'.format(randbytes.hex()))
		return self.hex2mn(randbytes.hex(),fmt=fmt)

	def mn_rand128(self, fmt:mn_opts_disp = dfl_mnemonic_fmt ):
		"generate random 128-bit mnemonic seed phrase"
		return self._do_random_mn(16,fmt)

	def mn_rand192(self, fmt:mn_opts_disp = dfl_mnemonic_fmt ):
		"generate random 192-bit mnemonic seed phrase"
		return self._do_random_mn(24,fmt)

	def mn_rand256(self, fmt:mn_opts_disp = dfl_mnemonic_fmt ):
		"generate random 256-bit mnemonic seed phrase"
		return self._do_random_mn(32,fmt)

	def hex2mn( self, hexstr:'sstr', fmt:mn_opts_disp = dfl_mnemonic_fmt ):
		"convert a 16, 24 or 32-byte hexadecimal number to a mnemonic seed phrase"
		if fmt == 'bip39':
			from .bip39 import bip39
			return ' '.join(bip39.fromhex(hexstr,fmt))
		else:
			bytestr = bytes.fromhex(hexstr)
			if fmt == 'xmrseed':
				bytestr = self._xmr_reduce(bytestr)
			return baseconv.frombytes(bytestr,fmt,'seed',tostr=True)

	def mn2hex( self, seed_mnemonic:'sstr', fmt:mn_opts_disp = dfl_mnemonic_fmt ):
		"convert a mnemonic seed phrase to a hexadecimal number"
		if fmt == 'bip39':
			from .bip39 import bip39
			return bip39.tohex(seed_mnemonic.split(),fmt)
		else:
			return baseconv.tohex(seed_mnemonic.split(),fmt,'seed')

	def mn2hex_interactive( self, fmt:mn_opts_disp = dfl_mnemonic_fmt, mn_len=24, print_mn=False ):
		"convert an interactively supplied mnemonic seed phrase to a hexadecimal number"
		from .mn_entry import mn_entry
		mn = mn_entry(fmt).get_mnemonic_from_user(25 if fmt == 'xmrseed' else mn_len,validate=False)
		if print_mn:
			msg(mn)
		return self.mn2hex(seed_mnemonic=mn,fmt=fmt)

	def mn_stats(self, fmt:mn_opts_disp = dfl_mnemonic_fmt ):
		"show stats for mnemonic wordlist"
		conv_cls = mnemonic_fmts[fmt]['conv_cls']()
		return conv_cls.check_wordlist(fmt)

	def mn_printlist( self, fmt:mn_opts_disp = dfl_mnemonic_fmt, enum=False, pager=False ):
		"print mnemonic wordlist"
		conv_cls = mnemonic_fmts[fmt]['conv_cls']()
		ret = conv_cls.get_wordlist(fmt)
		if enum:
			ret = ['{:>4} {}'.format(n,e) for n,e in enumerate(ret)]
		return '\n'.join(ret)

class MMGenToolCmdFile(MMGenToolCmds):
	"utilities for viewing/checking MMGen address and transaction files"

	def _file_chksum(self,mmgen_addrfile,objname):
		verbose,yes,quiet = [bool(i) for i in (opt.verbose,opt.yes,opt.quiet)]
		opt.verbose,opt.yes,opt.quiet = (False,True,True)
		ret = globals()[objname](self.proto,mmgen_addrfile)
		opt.verbose,opt.yes,opt.quiet = (verbose,yes,quiet)
		if verbose:
			if ret.al_id.mmtype.name == 'password':
				msg('Passwd fmt:  {}\nPasswd len:  {}\nID string:   {}'.format(
					capfirst(ret.pw_info[ret.pw_fmt].desc),
					ret.pw_len,
					ret.pw_id_str ))
			else:
				msg(f'Base coin:   {ret.base_coin} {capfirst(ret.network)}')
				msg(f'MMType:      {capfirst(ret.al_id.mmtype.name)}')
			msg(    f'List length: {len(ret.data)}')
		return ret.chksum

	def addrfile_chksum(self,mmgen_addrfile:str):
		"compute checksum for MMGen address file"
		return self._file_chksum(mmgen_addrfile,'AddrList')

	def keyaddrfile_chksum(self,mmgen_keyaddrfile:str):
		"compute checksum for MMGen key-address file"
		return self._file_chksum(mmgen_keyaddrfile,'KeyAddrList')

	def passwdfile_chksum(self,mmgen_passwdfile:str):
		"compute checksum for MMGen password file"
		return self._file_chksum(mmgen_passwdfile,'PasswordList')

	async def txview( varargs_call_sig = { # hack to allow for multiple filenames
					'args': (
						'mmgen_tx_file(s)',
						'pager',
						'terse',
						'sort',
						'filesort' ),
					'dfls': ( False, False, 'addr', 'mtime' ),
					'annots': {
						'mmgen_tx_file(s)': str,
						'sort': _options_annot_str(['addr','raw']),
						'filesort': _options_annot_str(['mtime','ctime','atime']),
						} },
				*infiles,**kwargs):
		"show raw/signed MMGen transaction in human-readable form"

		terse = bool(kwargs.get('terse'))
		tx_sort = kwargs.get('sort') or 'addr'
		file_sort = kwargs.get('filesort') or 'mtime'

		from .filename import MMGenFileList
		from .tx import MMGenTX
		flist = MMGenFileList(infiles,ftype=MMGenTX)
		flist.sort_by_age(key=file_sort) # in-place sort

		async def process_file(fn):
			if fn.endswith(MMGenTX.Signed.ext):
				tx = MMGenTX.Signed(
					filename   = fn,
					quiet_open = True,
					tw         = await MMGenTX.Signed.get_tracking_wallet(fn) )
			else:
				tx = MMGenTX.Unsigned(
					filename   = fn,
					quiet_open = True )
			return tx.format_view(terse=terse,sort=tx_sort)

		return ('—'*77+'\n').join([await process_file(fn) for fn in flist.names()]).rstrip()

class MMGenToolCmdFileCrypt(MMGenToolCmds):
	"""
	file encryption and decryption

		MMGen encryption suite:
		* Key: Scrypt (user-configurable hash parameters, 32-byte salt)
		* Enc: AES256_CTR, 16-byte rand IV, sha256 hash + 32-byte nonce + data
		* The encrypted file is indistinguishable from random data
	"""
	def encrypt(self,infile:str,outfile='',hash_preset=''):
		"encrypt a file"
		data = get_data_from_file(infile,'data for encryption',binary=True)
		enc_d = mmgen_encrypt(data,'user data',hash_preset)
		if not outfile:
			outfile = '{}.{}'.format(os.path.basename(infile),g.mmenc_ext)
		write_data_to_file(outfile,enc_d,'encrypted data',binary=True)
		return True

	def decrypt(self,infile:str,outfile='',hash_preset=''):
		"decrypt a file"
		enc_d = get_data_from_file(infile,'encrypted data',binary=True)
		while True:
			dec_d = mmgen_decrypt(enc_d,'user data',hash_preset)
			if dec_d: break
			msg('Trying again...')
		if not outfile:
			o = os.path.basename(infile)
			outfile = remove_extension(o,g.mmenc_ext)
			if outfile == o: outfile += '.dec'
		write_data_to_file(outfile,dec_d,'decrypted data',binary=True)
		return True

class MMGenToolCmdFileUtil(MMGenToolCmds):
	"file utilities"

	def find_incog_data(self,filename:str,incog_id:str,keep_searching=False):
		"Use an Incog ID to find hidden incognito wallet data"
		ivsize,bsize,mod = g.aesctr_iv_len,4096,4096*8
		n,carry = 0,b' '*ivsize
		flgs = os.O_RDONLY|os.O_BINARY if g.platform == 'win' else os.O_RDONLY
		f = os.open(filename,flgs)
		for ch in incog_id:
			if ch not in '0123456789ABCDEF':
				die(2,"'{}': invalid Incog ID".format(incog_id))
		while True:
			d = os.read(f,bsize)
			if not d: break
			d = carry + d
			for i in range(bsize):
				if sha256(d[i:i+ivsize]).hexdigest()[:8].upper() == incog_id:
					if n+i < ivsize: continue
					msg('\rIncog data for ID {} found at offset {}'.format(incog_id,n+i-ivsize))
					if not keep_searching: sys.exit(0)
			carry = d[len(d)-ivsize:]
			n += bsize
			if not n % mod:
				msg_r('\rSearched: {} bytes'.format(n))

		msg('')
		os.close(f)
		return True

	def rand2file(self,outfile:str,nbytes:str,threads=4,silent=False):
		"write 'n' bytes of random data to specified file"
		from threading import Thread
		from queue import Queue
		from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
		from cryptography.hazmat.backends import default_backend

		def encrypt_worker(wid):
			ctr_init_val = os.urandom(g.aesctr_iv_len)
			c = Cipher(algorithms.AES(key),modes.CTR(ctr_init_val),backend=default_backend())
			encryptor = c.encryptor()
			while True:
				q2.put(encryptor.update(q1.get()))
				q1.task_done()

		def output_worker():
			while True:
				f.write(q2.get())
				q2.task_done()

		nbytes = parse_bytespec(nbytes)
		if opt.outdir:
			outfile = make_full_path(opt.outdir,outfile)
		f = open(outfile,'wb')

		key = get_random(32)
		q1,q2 = Queue(),Queue()

		for i in range(max(1,threads-2)):
			t = Thread(target=encrypt_worker,args=[i])
			t.daemon = True
			t.start()

		t = Thread(target=output_worker)
		t.daemon = True
		t.start()

		blk_size = 1024 * 1024
		for i in range(nbytes // blk_size):
			if not i % 4:
				msg_r('\rRead: {} bytes'.format(i * blk_size))
			q1.put(os.urandom(blk_size))

		if nbytes % blk_size:
			q1.put(os.urandom(nbytes % blk_size))

		q1.join()
		q2.join()
		f.close()

		fsize = os.stat(outfile).st_size
		if fsize != nbytes:
			die(3,'{}: incorrect random file size (should be {})'.format(fsize,nbytes))

		if not silent:
			msg('\rRead: {} bytes'.format(nbytes))
			qmsg("\r{} byte{} of random data written to file '{}'".format(nbytes,suf(nbytes),outfile))

		return True

class MMGenToolCmdWallet(MMGenToolCmds):
	"key, address or subseed generation from an MMGen wallet"

	def get_subseed(self,subseed_idx:str,wallet=''):
		"get the Seed ID of a single subseed by Subseed Index for default or specified wallet"
		opt.quiet = True
		sf = get_seed_file([wallet] if wallet else [],1)
		from .wallet import Wallet
		return Wallet(sf).seed.subseed(subseed_idx).sid

	def get_subseed_by_seed_id(self,seed_id:str,wallet='',last_idx=g.subseeds):
		"get the Subseed Index of a single subseed by Seed ID for default or specified wallet"
		opt.quiet = True
		sf = get_seed_file([wallet] if wallet else [],1)
		from .wallet import Wallet
		ret = Wallet(sf).seed.subseed_by_seed_id(seed_id,last_idx)
		return ret.ss_idx if ret else None

	def list_subseeds(self,subseed_idx_range:str,wallet=''):
		"list a range of subseed Seed IDs for default or specified wallet"
		opt.quiet = True
		sf = get_seed_file([wallet] if wallet else [],1)
		from .wallet import Wallet
		return Wallet(sf).seed.subseeds.format(*SubSeedIdxRange(subseed_idx_range))

	def list_shares(self,
			share_count:int,
			id_str='default',
			master_share:"(min:1, max:{}, 0=no master share)".format(MasterShareIdx.max_val)=0,
			wallet=''):
		"list the Seed IDs of the shares resulting from a split of default or specified wallet"
		opt.quiet = True
		sf = get_seed_file([wallet] if wallet else [],1)
		from .wallet import Wallet
		return Wallet(sf).seed.split(share_count,id_str,master_share).format()

	def gen_key(self,mmgen_addr:str,wallet=''):
		"generate a single MMGen WIF key from default or specified wallet"
		return self.gen_addr(mmgen_addr,wallet,target='wif')

	def gen_addr(self,mmgen_addr:str,wallet='',target='addr'):
		"generate a single MMGen address from default or specified wallet"
		addr = MMGenID(self.proto,mmgen_addr)
		opt.quiet = True
		sf = get_seed_file([wallet] if wallet else [],1)
		from .wallet import Wallet
		ss = Wallet(sf)
		if ss.seed.sid != addr.sid:
			m = 'Seed ID of requested address ({}) does not match wallet ({})'
			die(1,m.format(addr.sid,ss.seed.sid))
		al = AddrList(
			proto     = self.proto,
			seed      = ss.seed,
			addr_idxs = AddrIdxList(str(addr.idx)),
			mmtype    = addr.mmtype )
		d = al.data[0]
		ret = d.sec.wif if target=='wif' else d.addr
		return ret

from .tw import TwAddrList,TwUnspentOutputs

class MMGenToolCmdRPC(MMGenToolCmds):
	"tracking wallet commands using the JSON-RPC interface"

	async def daemon_version(self):
		"print coin daemon version"
		from .rpc import rpc_init
		r = await rpc_init(self.proto,ignore_daemon_version=True)
		return f'{r.daemon.coind_name} version {r.daemon_version} ({r.daemon_version_str})'

	async def getbalance(self,minconf=1,quiet=False,pager=False):
		"list confirmed/unconfirmed, spendable/unspendable balances in tracking wallet"
		from .tw import TwGetBalance
		return (await TwGetBalance(self.proto,minconf,quiet)).format()

	async def listaddress(self,
					mmgen_addr:str,
					minconf = 1,
					pager = False,
					showempty = True,
					showbtcaddr = True,
					age_fmt: _options_annot_str(TwAddrList.age_fmts) = 'confs',
					):
		"list the specified MMGen address and its balance"
		return await self.listaddresses(  mmgen_addrs = mmgen_addr,
									minconf = minconf,
									pager = pager,
									showempty = showempty,
									showbtcaddrs = showbtcaddr,
									age_fmt = age_fmt,
								)

	async def listaddresses(  self,
						mmgen_addrs:'(range or list)' = '',
						minconf = 1,
						showempty = False,
						pager = False,
						showbtcaddrs = True,
						all_labels = False,
						sort: _options_annot_str(['reverse','age']) = '',
						age_fmt: _options_annot_str(TwAddrList.age_fmts) = 'confs',
						):
		"list MMGen addresses and their balances"
		show_age = bool(age_fmt)

		if sort:
			sort = set(sort.split(','))
			sort_params = {'reverse','age'}
			if not sort.issubset(sort_params):
				die(1,"The sort option takes the following parameters: '{}'".format("','".join(sort_params)))

		usr_addr_list = []
		if mmgen_addrs:
			a = mmgen_addrs.rsplit(':',1)
			if len(a) != 2:
				m = "'{}': invalid address list argument (must be in form <seed ID>:[<type>:]<idx list>)"
				die(1,m.format(mmgen_addrs))
			usr_addr_list = [MMGenID(self.proto,f'{a[0]}:{i}') for i in AddrIdxList(a[1])]

		al = await TwAddrList(self.proto,usr_addr_list,minconf,showempty,showbtcaddrs,all_labels)
		if not al:
			die(0,('No tracked addresses with balances!','No tracked addresses!')[showempty])
		return await al.format(showbtcaddrs,sort,show_age,age_fmt or 'confs')

	async def twview( self,
				pager = False,
				reverse = False,
				wide = False,
				minconf = 1,
				sort = 'age',
				age_fmt: _options_annot_str(TwUnspentOutputs.age_fmts) = 'confs',
				show_mmid = True,
				wide_show_confs = True):
		"view tracking wallet"
		twuo = await TwUnspentOutputs(self.proto,minconf=minconf)
		await twuo.get_unspent_data(reverse_sort=reverse)
		twuo.age_fmt = age_fmt
		twuo.show_mmid = show_mmid
		if wide:
			ret = twuo.format_for_printing(color=True,show_confs=wide_show_confs)
		else:
			ret = twuo.format_for_display()
		del twuo.wallet
		return await ret

	async def add_label(self,mmgen_or_coin_addr:str,label:str):
		"add descriptive label for address in tracking wallet"
		from .tw import TrackingWallet
		await (await TrackingWallet(self.proto,mode='w')).add_label(mmgen_or_coin_addr,label,on_fail='raise')
		return True

	async def remove_label(self,mmgen_or_coin_addr:str):
		"remove descriptive label for address in tracking wallet"
		await self.add_label(mmgen_or_coin_addr,'')
		return True

	async def remove_address(self,mmgen_or_coin_addr:str):
		"remove an address from tracking wallet"
		from .tw import TrackingWallet
		ret = await (await TrackingWallet(self.proto,mode='w')).remove_address(mmgen_or_coin_addr) # returns None on failure
		if ret:
			msg("Address '{}' deleted from tracking wallet".format(ret))
		return ret

class MMGenToolCmdMonero(MMGenToolCmds):
	"""
	Monero wallet operations

	Note that the use of these commands requires private data to be exposed on
	a network-connected machine in order to unlock the Monero wallets.  This is
	a violation of good security practice.
	"""

	def xmrwallet(
		self,
		op:                  str,
		xmr_keyaddrfile:     str,
		blockheight:         '(default: current height)' = 0,
		wallets:             '(integer range or list, or sweep specifier)' = '',
		start_wallet_daemon  = True,
		stop_wallet_daemon   = True,
		monerod_args         = '',
	):

		"""
		perform various Monero wallet operations for addresses in XMR key-address file

		  Supported operations:

		    create - create wallet for all or specified addresses in key-address file
		    sync   - sync wallet for all or specified addresses in key-address file
		    sweep  - sweep funds in specified wallet:account to new address in same
		             account or new account in another wallet

		                               SWEEP OPERATION NOTES

		    For the sweep operation, the parameter to the 'wallets' arg has a different
		    format, known as a 'sweep specifier':

		        SOURCE:ACCOUNT[,DEST]

		    where SOURCE and DEST are wallet numbers and ACCOUNT an account index.

		    If DEST is omitted, a new address will be created in ACCOUNT of SOURCE and
		    all funds from ACCOUNT of SOURCE will be swept into it.

		    If DEST is included, a new account will be created in DEST and all funds
		    from ACCOUNT of SOURCE will be swept into the new account.

		    The user is prompted before addresses are created or funds are transferred.
		"""

		class MoneroWalletOps:

			ops = ('create','sync','sweep')

			class base:

				wallet_exists = True
				_monero_chain_height = None

				def __init__(self,start_daemon=True):

					def wallet_exists(fn):
						try: os.stat(fn)
						except: return False
						else: return True

					def check_wallets():
						for d in self.addr_data:
							fn = self.get_wallet_fn(d)
							exists = wallet_exists(fn)
							if exists and not self.wallet_exists:
								die(1,f'Wallet {fn!r} already exists!')
							elif not exists and self.wallet_exists:
								die(1,f'Wallet {fn!r} not found!')

					from .protocol import init_proto
					self.kal = KeyAddrList(init_proto('xmr',network='mainnet'),xmr_keyaddrfile)
					self.create_addr_data()

					check_wallets()

					from .daemon import MoneroWalletDaemon
					self.wd = MoneroWalletDaemon(
						wallet_dir = opt.outdir or '.',
						test_suite = g.test_suite
					)

					if start_daemon:
						self.wd.restart()

					from .rpc import MoneroWalletRPCClient
					self.c = MoneroWalletRPCClient(
						host   = self.wd.host,
						port   = self.wd.rpc_port,
						user   = self.wd.user,
						passwd = self.wd.passwd
					)

					self.accts_data = {}

				def create_addr_data(self):
					if wallets:
						idxs = AddrIdxList(wallets)
						self.addr_data = [d for d in self.kal.data if d.idx in idxs]
						if len(self.addr_data) != len(idxs):
							die(1,f'List {wallets!r} contains addresses not present in supplied key-address file')
					else:
						self.addr_data = self.kal.data

				def stop_daemon(self):
					self.wd.stop()

				def post_process(self): pass

				def get_wallet_fn(self,d):
					return os.path.join(
						opt.outdir or '.','{}-{}-MoneroWallet{}'.format(
							self.kal.al_id.sid,
							d.idx,
							'-α' if g.debug_utf8 else ''))

				async def process_wallets(self):
					gmsg('\n{}ing {} wallet{}'.format(self.desc,len(self.addr_data),suf(self.addr_data)))
					processed = 0
					for n,d in enumerate(self.addr_data): # [d.sec,d.addr,d.wallet_passwd,d.viewkey]
						fn = self.get_wallet_fn(d)
						gmsg('\n{}ing wallet {}/{} ({})'.format(
							self.desc,
							n+1,
							len(self.addr_data),
							os.path.basename(fn),
						))
						processed += await self.run(d,fn)
					gmsg('\n{} wallet{} {}'.format(processed,suf(processed),self.past))
					return processed

				@property
				def monero_chain_height(self):
					if self._monero_chain_height == None:
						from .daemon import CoinDaemon
						port = CoinDaemon('xmr',test_suite=g.test_suite).rpc_port
						cmd = ['monerod','--rpc-bind-port={}'.format(port)] + monerod_args.split() + ['status']

						from subprocess import run,PIPE,DEVNULL
						cp = run(cmd,stdout=PIPE,stderr=DEVNULL,check=True)
						import re
						m = re.search(r'Height: (\d+)/\d+ ',cp.stdout.decode())
						if not m:
							die(1,'Unable to connect to monerod!')
						self._monero_chain_height = int(m.group(1))
						msg('Chain height: {}'.format(self._monero_chain_height))

					return self._monero_chain_height

			class create(base):
				name    = 'create'
				desc    = 'Creat'
				past    = 'created'
				wallet_exists = False

				async def run(self,d,fn):

					from .baseconv import baseconv
					ret = await self.c.call(
						'restore_deterministic_wallet',
						filename       = os.path.basename(fn),
						password       = d.wallet_passwd,
						seed           = baseconv.fromhex(d.sec,'xmrseed',tostr=True),
						restore_height = blockheight,
						language       = 'English' )

					pp_msg(ret) if opt.debug else msg('  Address: {}'.format(ret['address']))
					return True

			class sync(base):
				name    = 'sync'
				desc    = 'Sync'
				past    = 'synced'

				async def run(self,d,fn):

					chain_height = self.monero_chain_height

					import time
					t_start = time.time()

					msg_r('  Opening wallet...')
					await self.c.call(
						'open_wallet',
						filename=os.path.basename(fn),
						password=d.wallet_passwd )
					msg('done')

					msg_r('  Getting wallet height (be patient, this could take a long time)...')
					wallet_height = (await self.c.call('get_height'))['height']
					msg_r('\r' + ' '*68 + '\r')
					msg(f'  Wallet height: {wallet_height}        ')

					behind = chain_height - wallet_height
					if behind > 1000:
						msg_r(f'  Wallet is {behind} blocks behind chain tip.  Please be patient.  Syncing...')

					ret = await self.c.call('refresh')

					if behind > 1000:
						msg('done')

					if ret['received_money']:
						msg('  Wallet has received funds')

					t_elapsed = int(time.time() - t_start)

					bn = os.path.basename(fn)

					ret = self.accts_data[bn] = await self.c.call('get_accounts')

					msg('  Balance: {} Unlocked balance: {}'.format(
						hlXMRamt(ret['total_balance']),
						hlXMRamt(ret['total_unlocked_balance']),
					))

					msg('  Wallet height: {}'.format( (await self.c.call('get_height'))['height'] ))
					msg('  Sync time: {:02}:{:02}'.format( t_elapsed//60, t_elapsed%60 ))

					await self.c.call('close_wallet')
					return True

				def post_process(self):
					d = self.accts_data

					for n,k in enumerate(d):
						ad = self.addr_data[n]
						xmr_rpc_methods(self,ad).print_accts(d[k],indent='')

					col1_w = max(map(len,d)) + 1
					fs = '{:%s} {} {}' % col1_w
					tbals = [0,0]
					msg('\n'+fs.format('Wallet','Balance           ','Unlocked Balance'))

					for k in d:
						b  = d[k]['total_balance']
						ub = d[k]['total_unlocked_balance']
						msg(fs.format( k + ':', fmtXMRamt(b), fmtXMRamt(ub) ))
						tbals[0] += b
						tbals[1] += ub

					msg(fs.format( '-'*col1_w, '-'*18, '-'*18 ))
					msg(fs.format( 'TOTAL:', fmtXMRamt(tbals[0]), fmtXMRamt(tbals[1]) ))

			class sweep(base):
				name    = 'sweep'
				desc    = 'Sweep'
				past    = 'swept'

				def create_addr_data(self):
					import re
					m = re.match('(\d+):(\d+)(?:,(\d+))?$',wallets,re.ASCII)
					if not m:
						die(1,
							"{!r}: invalid 'wallets' arg: for sweep operation, it must have format {}".format(
							wallets,
							'SOURCE:ACCOUNT[,DEST]'
						))

					def gen():
						for i,k in ( (1,'source'), (3,'dest') ):
							if m[i] == None:
								setattr(self,k,None)
							else:
								idx = int(m[i])
								try:
									res = [d for d in self.kal.data if d.idx == idx][0]
								except:
									die(1,'Supplied key-address file does not contain address {}:{}'.format(
										self.kal.al_id.sid,
										idx ))
								else:
									setattr(self,k,res)
									yield res

					self.addr_data = list(gen())
					self.account = int(m[2])

				async def process_wallets(self):
					gmsg(f'\nSweeping account #{self.account} of wallet {self.source.idx}' + (
						' to new address' if self.dest is None else
						f' to new account in wallet {self.dest.idx}' ))

					h = xmr_rpc_methods(self,self.source)

					await h.open_wallet('source')
					accts_data = await h.get_accts()

					max_acct = len(accts_data['subaddress_accounts']) - 1
					if self.account > max_acct:
						die(1,f'{self.account}: requested account index out of bounds (>{max_acct})')

					await h.get_addrs(accts_data,self.account)

					if self.dest == None:
						if keypress_confirm(f'\nCreate new address for account #{self.account}?'):
							new_addr = await h.create_new_addr(self.account)
						elif keypress_confirm(f'Sweep to last existing address of account #{self.account}?'):
							new_addr = await h.get_last_addr(self.account)
						else:
							die(1,'Exiting at user request')
						await h.get_addrs(accts_data,self.account)
					else:
						bn = os.path.basename(self.get_wallet_fn(self.dest))
						h = xmr_rpc_methods(self,self.dest)
						await h.open_wallet('destination')
						accts_data = await h.get_accts()

						if keypress_confirm(f'\nCreate new account for wallet {bn!r}?'):
							new_addr = await h.create_acct()
							await h.get_accts()
						elif keypress_confirm(f'Sweep to last existing account of wallet {bn!r}?'):
							new_addr = h.get_last_acct(accts_data)
						else:
							die(1,'Exiting at user request')

						h = xmr_rpc_methods(self,self.source)
						await h.open_wallet('source')

					if keypress_confirm(
						'\nSweep balance of wallet {}, account #{} to {}?'.format(
							self.source.idx,
							self.account,
							cyan(new_addr),
						)):
						await h.do_sweep(self.account,new_addr)
					else:
						die(1,'Exiting at user request')

		class xmr_rpc_methods:

			def __init__(self,parent,d):
				self.parent = parent
				self.c = parent.c
				self.d = d
				self.fn = parent.get_wallet_fn(d)

			async def open_wallet(self,desc):
				gmsg_r(f'\n  Opening {desc} wallet...')
				ret = await self.c.call( # returns {}
					'open_wallet',
					filename=os.path.basename(self.fn),
					password=self.d.wallet_passwd )
				gmsg('done')

			def print_accts(self,data,indent='    '):
				d = data['subaddress_accounts']
				msg('\n' + indent + f'Accounts of wallet {os.path.basename(self.fn)}:')
				fs = indent + '  {:6}  {:18}  {:%s}  {}' % max(len(e['label']) for e in d)
				msg(fs.format('Index ','Base Address','Label','Balance'))
				for e in d:
					msg(fs.format(
						str(e['account_index']),
						e['base_address'][:15] + '...',
						e['label'],
						fmtXMRamt(e['balance']),
					))

			async def get_accts(self):
				data = await self.c.call('get_accounts')
				self.print_accts(data)
				return data

			async def create_acct(self):
				msg('\n    Creating new account...')
				ret = await self.c.call(
					'create_account',
					label = f'Sweep from {self.parent.source.idx}:{self.parent.account}'
				)
				msg('      Index:   {}'.format( pink(str(ret['account_index'])) ))
				msg('      Address: {}'.format( cyan(ret['address']) ))
				return ret['address']

			def get_last_acct(self,accts_data):
				msg('\n    Getting last account...')
				data = accts_data['subaddress_accounts'][-1]
				msg('      Index:   {}'.format( pink(str(data['account_index'])) ))
				msg('      Address: {}'.format( cyan(data['base_address']) ))
				return data['base_address']

			async def get_addrs(self,accts_data,account):
				ret = await self.c.call('get_address',account_index=account)
				d = ret['addresses']
				msg('\n      Addresses of account #{} ({}):'.format(
					account,
					accts_data['subaddress_accounts'][account]['label']))
				fs = '        {:6}  {:18}  {:%s}  {}' % max(len(e['label']) for e in d)
				msg(fs.format('Index ','Address','Label','Used'))
				for e in d:
					msg(fs.format(
						str(e['address_index']),
						e['address'][:15] + '...',
						e['label'],
						e['used']
					))
				return ret

			async def create_new_addr(self,account):
				msg_r('\n    Creating new address: ')
				ret = await self.c.call(
					'create_address',
					account_index = account,
					label         = 'Sweep from this account',
				)
				msg(cyan(ret['address']))
				return ret['address']

			async def get_last_addr(self,account):
				msg('\n    Getting last address:')
				ret = (await self.c.call(
					'get_address',
					account_index = account,
				))['addresses'][-1]['address']
				msg('      ' + cyan(ret))
				return ret

			async def do_sweep(self,account,addr):
				msg(f'\n    Sweeping account balance...')
				ret = { # debug
					'amount_list': [322222330000],
					'fee_list': [10600000],
					'tx_hash_list': ['deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef'],
				}
				ret = await self.c.call(
					'sweep_all',
					address = addr,
					account_index = account,
				)
				from .obj import CoinTxID
				msg('    TxID:   {}\n    Amount: {}\n    Fee:    {}'.format(
					CoinTxID(ret['tx_hash_list'][0]).hl(),
					hlXMRamt(ret['amount_list'][0]),
					hlXMRamt(ret['fee_list'][0]),
				))
				return ret

		def fmtXMRamt(amt):
			from .obj import XMRAmt
			return XMRAmt(amt,from_unit='min_coin_unit').fmt(fs='5.12',color=True)

		def hlXMRamt(amt):
			from .obj import XMRAmt
			return XMRAmt(amt,from_unit='min_coin_unit').hl()

		def check_args():
			if op not in MoneroWalletOps.ops:
				die(1,f'{op!r}: unrecognized operation')

			if op == 'sync' and blockheight != 0:
				die(1,'Sync operation does not support blockheight arg')

		# start execution
		check_args()

		if blockheight < 0:
			blockheight = 0 # TODO: handle the non-zero case

		m = getattr(MoneroWalletOps,op)(start_daemon=start_wallet_daemon)

		if run_session(m.process_wallets()):
			m.post_process()

		if stop_wallet_daemon:
			m.stop_daemon()

		return True

class tool_api(
		MMGenToolCmdUtil,
		MMGenToolCmdCoin,
		MMGenToolCmdMnemonic,
	):
	"""
	API providing access to a subset of methods from the mmgen.tool module

	Example:
		from mmgen.tool import tool_api
		tool = tool_api()

		# Set the coin and network:
		tool.init_coin('btc','mainnet')

		# Print available address types:
		tool.print_addrtypes()

		# Set the address type:
		tool.addrtype = 'segwit'

		# Disable user entropy gathering (optional, reduces security):
		tool.usr_randchars = 0

		# Generate a random BTC segwit keypair:
		wif,addr = tool.randpair()

		# Set coin, network and address type:
		tool.init_coin('ltc','testnet')
		tool.addrtype = 'bech32'

		# Generate a random LTC testnet Bech32 keypair:
		wif,addr = tool.randpair()
	"""

	def __init__(self):
		"""
		Initializer - takes no arguments
		"""
		import mmgen.opts
		opts.UserOpts._reset_ok += ('usr_randchars',)
		if not hasattr(opt,'version'):
			opts.init(add_opts=['use_old_ed25519'])
		super().__init__()

	def init_coin(self,coinsym,network):
		"""
		Initialize a coin/network pair
		Valid choices for coins: one of the symbols returned by the 'coins' attribute
		Valid choices for network: 'mainnet','testnet','regtest'
		"""
		from .protocol import init_proto,init_genonly_altcoins
		altcoin_trust_level = init_genonly_altcoins(coinsym,testnet=network in ('testnet','regtest'))
		warn_altcoins(coinsym,altcoin_trust_level)
		self.proto = init_proto(coinsym,network=network)
		return self.proto

	@property
	def coins(self):
		"""The available coins"""
		from .protocol import CoinProtocol
		from .altcoin import CoinInfo
		return sorted(set(
			[c.upper() for c in CoinProtocol.coins]
			+ [c.symbol for c in CoinInfo.get_supported_coins(self.proto.network)]
		))

	@property
	def coin(self):
		"""The currently configured coin"""
		return self.proto.coin

	@property
	def network(self):
		"""The currently configured network"""
		return self.proto.network

	@property
	def addrtypes(self):
		"""
		The available address types for current coin/network pair.  The
		first-listed is the default
		"""
		return [MMGenAddrType(proto=self.proto,id_str=id_str).name for id_str in self.proto.mmtypes]

	def print_addrtypes(self):
		"""
		Print the available address types for current coin/network pair along with
		a description.  The first-listed is the default
		"""
		for t in [MMGenAddrType(proto=self.proto,id_str=id_str) for id_str in self.proto.mmtypes]:
			print('{:<12} - {}'.format(t.name,t.desc))

	@property
	def addrtype(self):
		"""The currently configured address type (is assignable)"""
		return self.mmtype

	@addrtype.setter
	def addrtype(self,val):
		self.mmtype = MMGenAddrType(self.proto,val)

	@property
	def usr_randchars(self):
		"""
		The number of keystrokes of entropy to be gathered from the user.
		Setting to zero disables user entropy gathering.
		"""
		return opt.usr_randchars

	@usr_randchars.setter
	def usr_randchars(self,val):
		opt.usr_randchars = val

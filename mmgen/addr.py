#!/usr/bin/env python
#
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
addr.py:  Address generation/display routines for the MMGen suite
"""

from hashlib import sha256,sha512
from binascii import hexlify,unhexlify
from mmgen.common import *
from mmgen.bitcoin import hex2wif,wif2hex,wif_is_compressed
from mmgen.obj import *
from mmgen.tx import *
from mmgen.tw import *

pnm = g.proj_name

def _test_for_secp256k1(silent=False):
	no_secp256k1_errmsg = """
secp256k1 library unavailable.  Using (slow) native Python ECDSA library for address generation.
"""
	try:
		from mmgen.secp256k1 import priv2pub
		assert priv2pub(os.urandom(32),1)
	except:
		if not silent: msg(no_secp256k1_errmsg.strip())
		return False
	return True

def _pubhex2addr(pubhex,mmtype):
	if mmtype == 'L':
		from mmgen.bitcoin import hexaddr2addr,hash160
		return hexaddr2addr(hash160(pubhex))
	elif mmtype == 'S':
		from mmgen.bitcoin import pubhex2segwitaddr
		return pubhex2segwitaddr(pubhex)
	else:
		die(2,"'{}': mmtype unrecognized".format(mmtype))

def _privhex2addr_python(privhex,compressed,mmtype):
	assert compressed or mmtype != 'S'
	from mmgen.bitcoin import privnum2pubhex
	pubhex = privnum2pubhex(int(privhex,16),compressed=compressed)
	return _pubhex2addr(pubhex,mmtype=mmtype)

def _privhex2addr_secp256k1(privhex,compressed,mmtype):
	assert compressed or mmtype != 'S'
	from mmgen.secp256k1 import priv2pub
	pubhex = hexlify(priv2pub(unhexlify(privhex),int(compressed)))
	return _pubhex2addr(pubhex,mmtype=mmtype)

def _wif2addr_python(wif,mmtype):
	privhex = wif2hex(wif)
	if not privhex: return False
	return _privhex2addr_python(privhex,wif_is_compressed(wif),mmtype=mmtype)

def _wif2addr_secp256k1(wif,mmtype):
	privhex = wif2hex(wif)
	if not privhex: return False
	return _privhex2addr_secp256k1(privhex,wif_is_compressed(wif),mmtype=mmtype)

def keygen_wif2pubhex(wif,selector):
	privhex = wif2hex(wif)
	if not privhex: return False
	if selector == 1:
		from mmgen.secp256k1 import priv2pub
		return hexlify(priv2pub(unhexlify(privhex),int(wif_is_compressed(wif))))
	elif selector == 0:
		from mmgen.bitcoin import privnum2pubhex
		return privnum2pubhex(int(privhex,16),compressed=wif_is_compressed(wif))

def keygen_selector(generator=None):
	if _test_for_secp256k1() and generator != 1:
		if opt.key_generator != 1:
			return 1
	msg('Using (slow) native Python ECDSA library for address generation')
	return 0

def get_wif2addr_f(generator=None):
	gen = keygen_selector(generator=generator)
	return (_wif2addr_python,_wif2addr_secp256k1)[gen]

def get_privhex2addr_f(generator=None):
	gen = keygen_selector(generator=generator)
	return (_privhex2addr_python,_privhex2addr_secp256k1)[gen]


class AddrListEntry(MMGenListItem):
	attrs = 'idx','addr','label','wif','sec'
	idx   = MMGenListItemAttr('idx','AddrIdx')
	wif   = MMGenListItemAttr('wif','WifKey')

class AddrListChksum(str,Hilite):
	color = 'pink'
	trunc_ok = False

	def __new__(cls,addrlist):
		els = ['addr','wif'] if addrlist.has_keys else ['sec'] if addrlist.gen_passwds else ['addr']
		lines = [' '.join([str(e.idx)] + [getattr(e,f) for f in els]) for e in addrlist.data]
#		print '[{}]'.format(' '.join(lines))
		return str.__new__(cls,make_chksum_N(' '.join(lines), nchars=16, sep=True))

class AddrListIDStr(unicode,Hilite):
	color = 'green'
	trunc_ok = False
	def __new__(cls,addrlist,fmt_str=None):
		try: int(addrlist.data[0].idx)
		except:
			s = '(no idxs)'
		else:
			idxs = [e.idx for e in addrlist.data]
			prev = idxs[0]
			ret = prev,
			for i in idxs[1:]:
				if i == prev + 1:
					if i == idxs[-1]: ret += '-', i
				else:
					if prev != ret[-1]: ret += '-', prev
					ret += ',', i
				prev = i
			s = ''.join([unicode(i) for i in ret])

		if fmt_str:
			ret = fmt_str.format(s)
		elif addrlist.al_id.mmtype == 'L':
			ret = '{}[{}]'.format(addrlist.al_id.sid,s)
		else:
			ret = '{}-{}[{}]'.format(addrlist.al_id.sid,addrlist.al_id.mmtype,s)

		return unicode.__new__(cls,ret)

class AddrList(MMGenObject): # Address info for a single seed ID
	msgs = {
	'file_header': """
# {pnm} address file
#
# This file is editable.
# Everything following a hash symbol '#' is a comment and ignored by {pnm}.
# A text label of {n} characters or less may be added to the right of each
# address, and it will be appended to the bitcoind wallet label upon import.
# The label may contain any printable ASCII symbol.
""".strip().format(n=TwComment.max_len,pnm=pnm),
	'record_chksum': """
Record this checksum: it will be used to verify the address file in the future
""".strip(),
	'check_chksum': 'Check this value against your records',
	'removed_dups': """
Removed %s duplicate wif key%s from keylist (also in {pnm} key-address file
""".strip().format(pnm=pnm)
	}
	main_key  = 'addr'
	data_desc = 'address'
	file_desc = 'addresses'
	gen_desc  = 'address'
	gen_desc_pl = 'es'
	gen_addrs = True
	gen_passwds = False
	gen_keys = False
	has_keys = False
	ext      = 'addrs'
	dfl_mmtype = MMGenAddrType('L')
	cook_hash_rounds = 10  # not too many rounds, so hand decoding can still be feasible

	def __init__(self,addrfile='',al_id='',adata=[],seed='',addr_idxs='',src='',
					addrlist='',keylist='',mmtype=None,do_chksum=True,chksum_only=False):

		self.update_msgs()
		mmtype = mmtype or self.dfl_mmtype
		assert mmtype in MMGenAddrType.mmtypes

		if seed and addr_idxs:   # data from seed + idxs
			self.al_id,src = AddrListID(seed.sid,mmtype),'gen'
			adata = self.generate(seed,addr_idxs,compressed=(mmtype=='S'))
		elif addrfile:           # data from MMGen address file
			adata = self.parse_file(addrfile) # sets self.al_id
		elif al_id and adata:    # data from tracking wallet
			self.al_id = al_id
			do_chksum = False
		elif addrlist:           # data from flat address list
			self.al_id = None
			adata = AddrListList([AddrListEntry(addr=a) for a in set(addrlist)])
		elif keylist:            # data from flat key list
			self.al_id = None
			adata = AddrListList([AddrListEntry(wif=k) for k in set(keylist)])
		elif seed or addr_idxs:
			die(3,'Must specify both seed and addr indexes')
		elif al_id or adata:
			die(3,'Must specify both al_id and adata')
		else:
			die(3,'Incorrect arguments for %s' % type(self).__name__)

		# al_id,adata now set
		self.data = adata
		self.num_addrs = len(adata)
		self.fmt_data = ''
		self.chksum = None

		if self.al_id == None: return

		self.id_str = AddrListIDStr(self)

		if type(self) == KeyList: return

		if do_chksum:
			self.chksum = AddrListChksum(self)
			if chksum_only:
				Msg(self.chksum)
			else:
				qmsg('Checksum for %s data %s: %s' %
						(self.data_desc,self.id_str.hl(),self.chksum.hl()))
				qmsg(self.msgs[('check_chksum','record_chksum')[src=='gen']])

	def update_msgs(self):
		if type(self).msgs and type(self) != AddrList:
			for k in AddrList.msgs:
				if k not in self.msgs:
					self.msgs[k] = AddrList.msgs[k]

	def generate(self,seed,addrnums,compressed):
		assert type(addrnums) is AddrIdxList
		assert compressed in (True,False,None)

		seed = seed.get_data()
		seed = self.cook_seed(seed)

		if self.gen_addrs:
			privhex2addr_f = get_privhex2addr_f() # choose internal ECDSA or secp256k1 generator

		t_addrs,num,pos,out = len(addrnums),0,0,AddrListList()

		while pos != t_addrs:
			seed = sha512(seed).digest()
			num += 1 # round

			if num != addrnums[pos]: continue

			pos += 1

			if not g.debug:
				qmsg_r('\rGenerating %s #%s (%s of %s)' % (self.gen_desc,num,pos,t_addrs))

			e = AddrListEntry(idx=num)

			# Secret key is double sha256 of seed hash round /num/
			sec = sha256(sha256(seed).digest()).hexdigest()

			if self.gen_addrs:
				e.addr = privhex2addr_f(sec,compressed=compressed,mmtype=self.al_id.mmtype)

			if self.gen_keys:
				e.wif = hex2wif(sec,compressed=compressed)
				if opt.b16: e.sec = sec

			if self.gen_passwds:
				e.sec = self.make_passwd(sec)
				dmsg('Key {:>03}: {}'.format(pos,sec))

			out.append(e)
			if g.debug: print 'generate():\n', e.pformat()

		qmsg('\r%s: %s %s%s generated%s' % (
				self.al_id.hl(),t_addrs,self.gen_desc,suf(t_addrs,self.gen_desc_pl),' '*15))
		return out

	def is_mainnet(self):
		return self.data[0].addr.is_mainnet()

	def is_for_current_chain(self):
		return self.data[0].addr.is_for_current_chain()

	def chk_addr_or_pw(self,addr):
		return {'L':'p2pkh','S':'p2sh'}[self.al_id.mmtype] == is_btc_addr(addr).addr_fmt

	def cook_seed(self,seed):
		if self.al_id.mmtype == 'L':
			return seed
		else:
			from mmgen.crypto import sha256_rounds
			import hmac
			key = self.al_id.mmtype.name
			cseed = hmac.new(seed,key,sha256).digest()
			dmsg('Seed:  {}\nKey: {}\nCseed: {}\nCseed len: {}'.format(hexlify(seed),key,hexlify(cseed),len(cseed)))
			return sha256_rounds(cseed,self.cook_hash_rounds)

	def encrypt(self,desc='new key list'):
		from mmgen.crypto import mmgen_encrypt
		self.fmt_data = mmgen_encrypt(self.fmt_data.encode('utf8'),desc,'')
		self.ext += '.'+g.mmenc_ext

	def write_to_file(self,ask_tty=True,ask_write_default_yes=False,binary=False,desc=None):
		fn = u'{}.{}'.format(self.id_str,self.ext)
		ask_tty = self.has_keys and not opt.quiet
		write_data_to_file(fn,self.fmt_data,desc or self.file_desc,ask_tty=ask_tty,binary=binary)

	def idxs(self):
		return [e.idx for e in self.data]

	def addrs(self):
		return ['%s:%s'%(self.al_id.sid,e.idx) for e in self.data]

	def addrpairs(self):
		return [(e.idx,e.addr) for e in self.data]

	def btcaddrs(self):
		return [e.addr for e in self.data]

	def comments(self):
		return [e.label for e in self.data]

	def entry(self,idx):
		for e in self.data:
			if idx == e.idx: return e

	def btcaddr(self,idx):
		for e in self.data:
			if idx == e.idx: return e.addr

	def comment(self,idx):
		for e in self.data:
			if idx == e.idx: return e.label

	def set_comment(self,idx,comment):
		for e in self.data:
			if idx == e.idx:
				e.label = comment

	def make_reverse_dict(self,btcaddrs):
		d,b = MMGenDict(),btcaddrs
		for e in self.data:
			try:
				d[b[b.index(e.addr)]] = MMGenID('{}:{}'.format(self.al_id,e.idx)),e.label
			except: pass
		return d

	def flat_list(self):
		class AddrListFlatEntry(AddrListEntry):
			attrs = 'mmid','addr','wif'
		return [AddrListFlatEntry(mmid='{}:{}'.format(self.al_id,e.idx),addr=e.addr,wif=e.wif)
			for e in self.data]

	def remove_dups(self,cmplist,key='wif'):
		pop_list = []
		for n,d in enumerate(self.data):
			if getattr(d,key) == None: continue
			for e in cmplist.data:
				if getattr(e,key) and getattr(e,key) == getattr(d,key):
					pop_list.append(n)
		for n in reversed(pop_list): self.data.pop(n)
		if pop_list:
			vmsg(self.msgs['removed_dups'] % (len(pop_list),suf(removed,'s')))

	def add_wifs(self,al_key):
		if not al_key: return
		for d in self.data:
			for e in al_key.data:
				if e.addr and e.wif and e.addr == d.addr:
					d.wif = e.wif

	def list_missing(self,key):
		return [d.addr for d in self.data if not getattr(d,key)]

	def get(self,key):
		return [getattr(d,key) for d in self.data if getattr(d,key)]

	def get_addrs(self): return self.get('addr')
	def get_wifs(self):  return self.get('wif')
	def get_addr_wif_pairs(self):
		return [(d.addr,d.wif) for d in self.data if hasattr(d,'wif')]

	def generate_addrs_from_keylist(self):
		wif2addr_f = get_wif2addr_f()
		d = self.data
		for n,e in enumerate(d,1):
			qmsg_r('\rGenerating addresses from keylist: %s/%s' % (n,len(d)))
			e.addr = wif2addr_f(e.wif,mmtype='L') # 'L' == p2pkh
		qmsg('\rGenerated addresses from keylist: %s/%s ' % (n,len(d)))

	def format(self,enable_comments=False):

		def check_attrs(key,desc):
			for e in self.data:
				if not getattr(e,key):
					die(3,'missing %s in addr data' % desc)

		if type(self) not in (KeyList,PasswordList): check_attrs('addr','addresses')

		if self.has_keys:
			if opt.b16: check_attrs('sec','hex keys')
			check_attrs('wif','wif keys')

		out = [self.msgs['file_header']+'\n']
		if self.chksum:
			out.append(u'# {} data checksum for {}: {}'.format(
						capfirst(self.data_desc),self.id_str,self.chksum))
			out.append('# Record this value to a secure location.\n')

		if type(self) == PasswordList:
			out.append(u'{} {} {}:{} {{'.format(
				self.al_id.sid,self.pw_id_str,self.pw_fmt,self.pw_len))
		elif self.al_id.mmtype == 'L':
			out.append('{} {{'.format(self.al_id.sid))
		else:
			out.append('{} {} {{'.format(self.al_id.sid,MMGenAddrType.mmtypes[self.al_id.mmtype].upper()))

		fs = '  {:<%s}  {:<34}{}' % len(str(self.data[-1].idx))
		for e in self.data:
			c = ' '+e.label if enable_comments and e.label else ''
			if type(self) == KeyList:
				out.append(fs.format(e.idx, 'wif: '+e.wif,c))
			elif type(self) == PasswordList:
				out.append(fs.format(e.idx, e.sec, c))
			else: # First line with idx
				out.append(fs.format(e.idx, e.addr,c))
				if self.has_keys:
					if opt.b16: out.append(fs.format('', 'hex: '+e.sec,c))
					out.append(fs.format('', 'wif: '+e.wif,c))

		out.append('}')
		self.fmt_data = '\n'.join([l.rstrip() for l in out]) + '\n'

	def parse_file_body(self,lines):

		if self.has_keys and len(lines) % 2:
			return 'Key-address file has odd number of lines'

		ret = AddrListList()

		while lines:
			l = lines.pop(0)
			d = l.split(None,2)

			if not is_mmgen_idx(d[0]):
				return "'%s': invalid address num. in line: '%s'" % (d[0],l)

			if not self.chk_addr_or_pw(d[1]):
				return "'{}': invalid {}".format(d[1],self.data_desc)

			if len(d) != 3: d.append('')

			a = AddrListEntry(**{'idx':int(d[0]),self.main_key:d[1],'label':d[2]})

			if self.has_keys:
				l = lines.pop(0)
				d = l.split(None,2)

				if d[0] != 'wif:':
					return "Invalid key line in file: '%s'" % l
				if not is_wif(d[1]):
					return "'%s': invalid Bitcoin key" % d[1]

				a.wif = d[1]

			ret.append(a)

		if self.has_keys and keypress_confirm('Check key-to-address validity?'):
			wif2addr_f = get_wif2addr_f()
			llen = len(ret)
			for n,e in enumerate(ret):
				msg_r('\rVerifying keys %s/%s' % (n+1,llen))
				if e.addr != wif2addr_f(e.wif,mmtype=self.al_id.mmtype):
					return "Key doesn't match address!\n  %s\n  %s" % (e.wif,e.addr)
			msg(' - done')

		return ret

	def parse_file(self,fn,buf=[],exit_on_error=True):

		def do_error(msg):
			if exit_on_error: die(3,msg)
			msg(msg)
			return False

		lines = get_lines_from_file(fn,self.data_desc+' data',trim_comments=True)

		if len(lines) < 3:
			return do_error("Too few lines in address file (%s)" % len(lines))

		ls = lines[0].split()
		if not 1 < len(ls) < 5:
			return do_error("Invalid first line for {} file: '{}'".format(self.gen_desc,lines[0]))
		if ls.pop() != '{':
			return do_error("'%s': invalid first line" % ls)
		if lines[-1] != '}':
			return do_error("'%s': invalid last line" % lines[-1])

		sid = ls.pop(0)
		if not is_mmgen_seed_id(sid):
			return do_error("'%s': invalid Seed ID" % ls[0])

		if type(self) == PasswordList and len(ls) == 2:
			ss = ls.pop().split(':')
			if len(ss) != 2:
				return do_error("'%s': invalid password length specifier (must contain colon)" % ls[2])
			self.set_pw_fmt(ss[0])
			self.set_pw_len(ss[1])
			self.pw_id_str = MMGenPWIDString(ls.pop())
			mmtype = MMGenPasswordType('P')
		elif len(ls) == 1:
			mmtype = ls.pop().lower()
			try:
				mmtype = MMGenAddrType(mmtype)
			except:
				return do_error(u"'{}': invalid address type in address file. Must be one of: {}".format(
					mmtype.upper(),' '.join(MMGenAddrType.mmtypes.values()).upper()))
		elif len(ls) == 0:
			mmtype = MMGenAddrType('L')
		else:
			return do_error(u"Invalid first line for {} file: '{}'".format(self.gen_desc,lines[0]))

		self.al_id = AddrListID(SeedID(sid=sid),mmtype)

		data = self.parse_file_body(lines[1:-1])
		if not issubclass(type(data),list):
			return do_error(data)

		return data

class KeyAddrList(AddrList):
	data_desc = 'key-address'
	file_desc = 'secret keys'
	gen_desc = 'key/address pair'
	gen_desc_pl = 's'
	gen_addrs = True
	gen_keys = True
	has_keys = True
	ext      = 'akeys'

class KeyList(AddrList):
	msgs = {
	'file_header': """
# {pnm} key file
#
# This file is editable.
# Everything following a hash symbol '#' is a comment and ignored by {pnm}.
""".strip().format(pnm=pnm)
	}
	data_desc = 'key'
	file_desc = 'secret keys'
	gen_desc = 'key'
	gen_desc_pl = 's'
	gen_addrs = False
	gen_keys = True
	has_keys = True
	ext      = 'keys'

class PasswordList(AddrList):
	msgs = {
	'file_header': """
# {pnm} password file
#
# This file is editable.
# Everything following a hash symbol '#' is a comment and ignored by {pnm}.
# A text label of {n} characters or less may be added to the right of each
# password.  The label may contain any printable ASCII symbol.
#
""".strip().format(n=TwComment.max_len,pnm=pnm),
	'record_chksum': """
Record this checksum: it will be used to verify the password file in the future
""".strip()
	}
	main_key    = 'sec'
	data_desc   = 'password'
	file_desc   = 'passwords'
	gen_desc    = 'password'
	gen_desc_pl = 's'
	gen_addrs   = False
	gen_keys    = False
	gen_passwds = True
	has_keys    = False
	ext         = 'pws'
	pw_len      = None
	pw_fmt      = None
	pw_info     = {
		'b58': { 'min_len': 8 , 'max_len': 36 ,'dfl_len': 20, 'desc': 'base-58 password' },
		'b32': { 'min_len': 10 ,'max_len': 42 ,'dfl_len': 24, 'desc': 'base-32 password' }
		}

	def __init__(self,infile=None,seed=None,pw_idxs=None,pw_id_str=None,pw_len=None,pw_fmt=None,
				chksum_only=False,chk_params_only=False):

		self.update_msgs()

		if infile:
			self.data = self.parse_file(infile) # sets self.pw_id_str,self.pw_fmt,self.pw_len
		else:
			for k in seed,pw_idxs: assert chk_params_only or k
			for k in (pw_id_str,pw_fmt): assert k
			self.pw_id_str = MMGenPWIDString(pw_id_str)
			self.set_pw_fmt(pw_fmt)
			self.set_pw_len(pw_len)
			if chk_params_only: return
			self.al_id = AddrListID(seed.sid,MMGenPasswordType('P'))
			self.data = self.generate(seed,pw_idxs,compressed=None)

		self.num_addrs = len(self.data)
		self.fmt_data = ''
		self.chksum = AddrListChksum(self)

		if chksum_only:
			Msg(self.chksum)
		else:
			fs = u'{}-{}-{}-{}[{{}}]'.format(self.al_id.sid,self.pw_id_str,self.pw_fmt,self.pw_len)
			self.id_str = AddrListIDStr(self,fs)
			qmsg(u'Checksum for {} data {}: {}'.format(self.data_desc,self.id_str.hl(),self.chksum.hl()))
			qmsg(self.msgs[('record_chksum','check_chksum')[bool(infile)]])

	def set_pw_fmt(self,pw_fmt):
		assert pw_fmt in self.pw_info
		self.pw_fmt = pw_fmt

	def chk_pw_len(self,passwd=None):
		if passwd is None:
			assert self.pw_len
			pw_len = self.pw_len
			fs = '{l}: invalid user-requested length for {b} ({c}{m})'
		else:
			pw_len = len(passwd)
			fs = '{pw}: {b} has invalid length {l} ({c}{m} characters)'
		d = self.pw_info[self.pw_fmt]
		if pw_len > d['max_len']:
			die(2,fs.format(l=pw_len,b=d['desc'],c='>',m=d['max_len'],pw=passwd))
		elif pw_len < d['min_len']:
			die(2,fs.format(l=pw_len,b=d['desc'],c='<',m=d['min_len'],pw=passwd))

	def set_pw_len(self,pw_len):
		assert self.pw_fmt in self.pw_info
		d = self.pw_info[self.pw_fmt]

		if pw_len is None:
			self.pw_len = d['dfl_len']
			return

		if not is_int(pw_len):
			die(2,"'{}': invalid user-requested password length (not an integer)".format(pw_len,d['desc']))
		self.pw_len = int(pw_len)
		self.chk_pw_len()

	def make_passwd(self,hex_sec):
		assert self.pw_fmt in self.pw_info
		# we take least significant part
		return ''.join(baseconv.fromhex(hex_sec,self.pw_fmt,pad=self.pw_len))[-self.pw_len:]

	def chk_addr_or_pw(self,pw):
		if not (is_b58_str,is_b32_str)[self.pw_fmt=='b32'](pw):
			msg('Password is not a valid {} string'.format(self.pw_fmt))
			return False
		if len(pw) != self.pw_len:
			msg('Password has incorrect length ({} != {})'.format(len(pw),self.pw_len))
			return False
		return True

	def cook_seed(self,seed):
		from mmgen.crypto import sha256_rounds
		# Changing either pw_fmt, pw_len or id_str will cause a different, unrelated set of
		# passwords to be generated: this is what we want
		# NB: In original implementation, pw_id_str was 'baseN', not 'bN'
		fid_str = '{}:{}:{}'.format(self.pw_fmt,self.pw_len,self.pw_id_str.encode('utf8'))
		dmsg(u'Full ID string: {}'.format(fid_str.decode('utf8')))
		# Original implementation was 'cseed = seed + fid_str'; hmac was not used
		import hmac
		cseed = hmac.new(seed,fid_str,sha256).digest()
		dmsg('Seed: {}\nCooked seed: {}\nCooked seed len: {}'.format(hexlify(seed),hexlify(cseed),len(cseed)))
		return sha256_rounds(cseed,self.cook_hash_rounds)


class AddrData(MMGenObject):
	msgs = {
	'too_many_acct_addresses': """
ERROR: More than one address found for account: '%s'.
Your 'wallet.dat' file appears to have been altered by a non-{pnm} program.
Please restore your tracking wallet from a backup or create a new one and
re-import your addresses.
""".strip().format(pnm=pnm)
	}

	def __init__(self,source=None):
		self.al_ids = {}
		if source == 'tw': self.add_tw_data()

	def seed_ids(self):
		return self.al_ids.keys()

	def addrlist(self,al_id):
		# TODO: Validate al_id
		if al_id in self.al_ids:
			return self.al_ids[al_id]

	def mmaddr2btcaddr(self,mmaddr):
		al_id,idx = MMGenID(mmaddr).rsplit(':',1)
		btcaddr = ''
		if al_id in self.al_ids:
			btcaddr = self.addrlist(al_id).btcaddr(int(idx))
		return btcaddr or None

	def btcaddr2mmaddr(self,btcaddr):
		d = self.make_reverse_dict([btcaddr])
		return (d.values()[0][0]) if d else None

	def add_tw_data(self):
		vmsg('Getting address data from tracking wallet')
		c = bitcoin_connection()
		accts = c.listaccounts(0,True)
		data,i = {},0
		alists = c.getaddressesbyaccount([[k] for k in accts],batch=True)
		for acct,addrlist in zip(accts,alists):
			l = TwLabel(acct,on_fail='silent')
			if l and l.mmid.type == 'mmgen':
				obj = l.mmid.obj
				i += 1
				if len(addrlist) != 1:
					die(2,self.msgs['too_many_acct_addresses'] % acct)
				al_id = AddrListID(SeedID(sid=obj.sid),MMGenAddrType(obj.mmtype))
				if al_id not in data:
					data[al_id] = []
				data[al_id].append(AddrListEntry(idx=obj.idx,addr=addrlist[0],label=l.comment))
		vmsg('{n} {pnm} addresses found, {m} accounts total'.format(n=i,pnm=pnm,m=len(accts)))
		for al_id in data:
			self.add(AddrList(al_id=al_id,adata=AddrListList(sorted(data[al_id],key=lambda a: a.idx))))

	def add(self,addrlist):
		if type(addrlist) == AddrList:
			self.al_ids[addrlist.al_id] = addrlist
			return True
		else:
			raise TypeError, 'Error: object %s is not of type AddrList' % repr(addrlist)

	def make_reverse_dict(self,btcaddrs):
		d = MMGenDict()
		for al_id in self.al_ids:
			d.update(self.al_ids[al_id].make_reverse_dict(btcaddrs))
		return d

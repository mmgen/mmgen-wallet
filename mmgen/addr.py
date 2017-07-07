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
from mmgen.bitcoin import privnum2addr,hex2wif,wif2hex
from mmgen.obj import *
from mmgen.tx import *
from mmgen.tw import *

pnm = g.proj_name

def _test_for_keyconv(silent=False):
	no_keyconv_errmsg = """
Executable '{kconv}' unavailable.  Please install '{kconv}' from the {vgen}
package on your system or specify the secp256k1 library.
""".format(kconv=g.keyconv_exec, vgen='vanitygen')
	from subprocess import check_output,STDOUT
	try:
		check_output([g.keyconv_exec, '-G'],stderr=STDOUT)
	except:
		if not silent: msg(no_keyconv_errmsg.strip())
		return False
	return True

def _test_for_secp256k1(silent=False):
	no_secp256k1_errmsg = """
secp256k1 library unavailable.  Will use '{kconv}', or failing that, the (slow)
native Python ECDSA library for address generation.
""".format(kconv=g.keyconv_exec)
	try:
		from mmgen.secp256k1 import priv2pub
		assert priv2pub(os.urandom(32),1)
	except:
		if not silent: msg(no_secp256k1_errmsg.strip())
		return False
	return True

def _wif2addr_python(wif):
	privhex = wif2hex(wif)
	if not privhex: return False
	return privnum2addr(int(privhex,16),wif[0] != ('5','9')[g.testnet])

def _wif2addr_keyconv(wif):
	if wif[0] == ('5','9')[g.testnet]:
		from subprocess import check_output
		return check_output(['keyconv', wif]).split()[1]
	else:
		return _wif2addr_python(wif)

def _wif2addr_secp256k1(wif):
	return _privhex2addr_secp256k1(wif2hex(wif),wif[0] != ('5','9')[g.testnet])

def _privhex2addr_python(privhex,compressed=False):
	return privnum2addr(int(privhex,16),compressed)

def _privhex2addr_keyconv(privhex,compressed=False):
	if compressed:
		return privnum2addr(int(privhex,16),compressed)
	else:
		from subprocess import check_output
		return check_output(['keyconv', hex2wif(privhex,compressed=False)]).split()[1]

def _privhex2addr_secp256k1(privhex,compressed=False):
	from mmgen.secp256k1 import priv2pub
	from mmgen.bitcoin import hexaddr2addr,pubhex2hexaddr
	pubkey = priv2pub(unhexlify(privhex),int(compressed))
	return hexaddr2addr(pubhex2hexaddr(hexlify(pubkey)))

def _keygen_selector(generator=None):
	if generator:
		if generator == 3 and _test_for_secp256k1():             return 2
		elif generator in (2,3) and _test_for_keyconv():         return 1
	else:
		if opt.key_generator == 3 and _test_for_secp256k1():     return 2
		elif opt.key_generator in (2,3) and _test_for_keyconv(): return 1
	msg('Using (slow) native Python ECDSA library for address generation')
	return 0

def get_wif2addr_f(generator=None):
	gen = _keygen_selector(generator=generator)
	return (_wif2addr_python,_wif2addr_keyconv,_wif2addr_secp256k1)[gen]

def get_privhex2addr_f(generator=None):
	gen = _keygen_selector(generator=generator)
	return (_privhex2addr_python,_privhex2addr_keyconv,_privhex2addr_secp256k1)[gen]

class AddrListEntry(MMGenListItem):
	attrs = 'idx','addr','label','wif','sec'
	idx   = MMGenListItemAttr('idx','AddrIdx')

class AddrListChksum(str,Hilite):
	color = 'pink'
	trunc_ok = False

	def __new__(cls,addrlist):
		els = ['addr','wif'] if addrlist.has_keys else ['sec'] if addrlist.gen_passwds else ['addr']
		lines = [' '.join([str(e.idx)] + [getattr(e,f) for f in els]) for e in addrlist.data]
#		print '[{}]'.format(' '.join(lines))
		return str.__new__(cls,make_chksum_N(' '.join(lines), nchars=16, sep=True))

class AddrListID(unicode,Hilite):
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
		return unicode.__new__(cls,fmt_str.format(s) if fmt_str else '{}[{}]'.format(addrlist.seed_id,s))

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
""".strip().format(n=MMGenAddrLabel.max_len,pnm=pnm),
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

	def __init__(self,addrfile='',sid='',adata=[],seed='',addr_idxs='',src='',
					addrlist='',keylist='',do_chksum=True,chksum_only=False):

		self.update_msgs()

		if addrfile:             # data from MMGen address file
			(sid,adata) = self.parse_file(addrfile)
		elif sid and adata:      # data from tracking wallet
			do_chksum = False
		elif seed and addr_idxs: # data from seed + idxs
			sid,src = seed.sid,'gen'
			adata = self.generate(seed,addr_idxs)
		elif addrlist:           # data from flat address list
			sid = None
			adata = [AddrListEntry(addr=a) for a in set(addrlist)]
		elif keylist:            # data from flat key list
			sid,do_chksum = None,False
			adata = [AddrListEntry(wif=k) for k in set(keylist)]
		elif seed or addr_idxs:
			die(3,'Must specify both seed and addr indexes')
		elif sid or adata:
			die(3,'Must specify both seed_id and adata')
		else:
			die(3,'Incorrect arguments for %s' % type(self).__name__)

		# sid,adata now set
		self.seed_id = sid
		self.data = adata
		self.num_addrs = len(adata)
		self.fmt_data = ''
		self.id_str = None
		self.chksum = None
		self.id_str = AddrListID(self)

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

	def generate(self,seed,addrnums):
		assert type(addrnums) is AddrIdxList
		self.seed_id = SeedID(seed=seed)
		seed = seed.get_data()

		seed = self.cook_seed(seed)

		if self.gen_addrs:
			privhex2addr_f = get_privhex2addr_f()

		t_addrs,num,pos,out = len(addrnums),0,0,[]

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
				e.addr = privhex2addr_f(sec,compressed=False)

			if self.gen_keys:
				e.wif = hex2wif(sec,compressed=False)
				if opt.b16: e.sec = sec

			if self.gen_passwds:
				e.sec = self.make_passwd(sec)
				dmsg('Key {:>03}: {}'.format(pos,sec))

			out.append(e)

		qmsg('\r%s: %s %s%s generated%s' % (
				self.seed_id.hl(),t_addrs,self.gen_desc,suf(t_addrs,self.gen_desc_pl),' '*15))
		return out

	def chk_addr_or_pw(self,addr): return is_btc_addr(addr)

	def cook_seed(self,seed): return seed

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
		return ['%s:%s'%(self.seed_id,e.idx) for e in self.data]

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
		d,b = {},btcaddrs
		for e in self.data:
			try:
				d[b[b.index(e.addr)]] = ('%s:%s'%(self.seed_id,e.idx),e.label)
			except: pass
		return d

	def flat_list(self):
		class AddrListFlatEntry(AddrListEntry):
			attrs = 'mmid','addr','wif'
		return [AddrListFlatEntry(
					mmid='{}:{}'.format(self.seed_id,e.idx),
					addr=e.addr,
					wif=e.wif)
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
			vmsg(self.msgs['removed_dups'] % (len(pop_list),suf(removed,'k')))

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

	def generate_addrs(self):
		wif2addr_f = get_wif2addr_f()
		d = self.data
		for n,e in enumerate(d,1):
			qmsg_r('\rGenerating addresses from keylist: %s/%s' % (n,len(d)))
			e.addr = wif2addr_f(e.wif)
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
				self.seed_id,self.pw_id_str,self.pw_fmt,self.pw_len))
		else:
			out.append('{} {{'.format(self.seed_id))

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

		ret = []

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
				if e.addr != wif2addr_f(e.wif):
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
		ls_len = (2,4)[type(self)==PasswordList]
		if len(ls) != ls_len:
			return do_error("Invalid first line for {} file: '{}'".format(self.gen_desc,lines[0]))
		if ls[-1] != '{':
			return do_error("'%s': invalid first line" % ls)
		if lines[-1] != '}':
			return do_error("'%s': invalid last line" % lines[-1])
		if not is_mmgen_seed_id(ls[0]):
			return do_error("'%s': invalid Seed ID" % ls[0])

		if type(self) == PasswordList:
			self.pw_id_str = MMGenPWIDString(ls[1])
			ss = ls[2].split(':')
			if len(ss) != 2:
				return do_error("'%s': invalid password length specifier (must contain colon)" % ls[2])
			self.set_pw_fmt(ss[0])
			self.set_pw_len(ss[1])

		ret = self.parse_file_body(lines[1:-1])
		if type(ret) != list:
			return do_error(ret)

		return ls[0],ret

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
""".strip().format(n=MMGenAddrLabel.max_len,pnm=pnm),
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
	cook_hash_rounds = 10  # not too many rounds, so hand decoding can still be feasible

	def __init__(self,infile=None,seed=None,pw_idxs=None,pw_id_str=None,pw_len=None,pw_fmt=None,
				chksum_only=False,chk_params_only=False):

		self.update_msgs()

		if infile:
			(self.seed_id,self.data) = self.parse_file(infile) # sets self.pw_id_str,self.pw_fmt,self.pw_len
		else:
			for k in seed,pw_idxs: assert chk_params_only or k
			for k in pw_id_str,pw_fmt: assert k
			self.pw_id_str = MMGenPWIDString(pw_id_str)
			self.set_pw_fmt(pw_fmt)
			self.set_pw_len(pw_len)
			if chk_params_only: return
			self.seed_id = seed.sid
			self.data = self.generate(seed,pw_idxs)

		self.num_addrs = len(self.data)
		self.fmt_data = ''
		self.chksum = AddrListChksum(self)

		if chksum_only:
			Msg(self.chksum)
		else:
			self.id_str = AddrListID(self,fmt_str=u'{}-{}-{}-{}[{{}}]'.format(
				self.seed_id,self.pw_id_str,self.pw_fmt,self.pw_len))
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
		self.sids = {}
		if source == 'tw': self.add_tw_data()

	def seed_ids(self):
		return self.sids.keys()

	def addrlist(self,sid):
		# TODO: Validate sid
		if sid in self.sids:
			return self.sids[sid]

	def mmaddr2btcaddr(self,mmaddr):
		btcaddr = ''
		sid,idx = mmaddr.split(':')
		if sid in self.seed_ids():
			btcaddr = self.addrlist(sid).btcaddr(int(idx))
		return btcaddr

	def add_tw_data(self):
		vmsg_r('Getting address data from tracking wallet...')
		c = bitcoin_connection()
		accts = c.listaccounts(0,True)
		data,i = {},0
		alists = c.getaddressesbyaccount([[k] for k in accts],batch=True)
		for acct,addrlist in zip(accts,alists):
			maddr,label = parse_tw_acct_label(acct)
			if maddr:
				i += 1
				if len(addrlist) != 1:
					die(2,self.msgs['too_many_acct_addresses'] % acct)
				seed_id,idx = maddr.split(':')
				if seed_id not in data:
					data[seed_id] = []
				data[seed_id].append(AddrListEntry(idx=idx,addr=addrlist[0],label=label))
		vmsg('{n} {pnm} addresses found, {m} accounts total'.format(
				n=i,pnm=pnm,m=len(accts)))
		for sid in data:
			self.add(AddrList(sid=sid,adata=data[sid]))

	def add(self,addrlist):
		if type(addrlist) == AddrList:
			self.sids[addrlist.seed_id] = addrlist
			return True
		else:
			raise TypeError, 'Error: object %s is not of type AddrList' % repr(addrlist)

	def make_reverse_dict(self,btcaddrs):
		d = {}
		for sid in self.sids:
			d.update(self.sids[sid].make_reverse_dict(btcaddrs))
		return d

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
obj.py: MMGen native classes
"""

import sys
from decimal import *
from mmgen.color import *

def is_mmgen_seed_id(s): return SeedID(sid=s,on_fail='silent')
def is_mmgen_idx(s):     return AddrIdx(s,on_fail='silent')
def is_mmgen_id(s):      return MMGenID(s,on_fail='silent')
def is_btc_addr(s):      return BTCAddr(s,on_fail='silent')
def is_addrlist_id(s):   return AddrListID(s,on_fail='silent')
def is_tw_label(s):      return TwLabel(s,on_fail='silent')
def is_wif(s):           return WifKey(s,on_fail='silent')

class MMGenObject(object):

	# Pretty-print any object subclassed from MMGenObject, recursing into sub-objects - WIP
	def pmsg(self): print(self.pformat())
	def pdie(self): print(self.pformat()); sys.exit(0)
	def pformat(self,lvl=0):
		from decimal import Decimal
		scalars = (str,unicode,int,float,Decimal)
		def do_list(out,e,lvl=0,is_dict=False):
			out.append('\n')
			for i in e:
				el = i if not is_dict else e[i]
				if is_dict:
					out.append('{s}{:<{l}}'.format(i,s=' '*(4*lvl+8),l=10,l2=8*(lvl+1)+8))
				if hasattr(el,'pformat'):
					out.append('{:>{l}}{}'.format('',el.pformat(lvl=lvl+1),l=(lvl+1)*8))
				elif type(el) in scalars:
					if isList(e):
						out.append(u'{:>{l}}{:16}\n'.format('',repr(el),l=lvl*8))
					else:
						out.append(u' {}'.format(repr(el)))
				elif isList(el) or isDict(el):
					indent = 1 if is_dict else lvl*8+4
					out.append(u'{:>{l}}{:16}'.format('','<'+type(el).__name__+'>',l=indent))
					if isList(el) and type(el[0]) in scalars: out.append('\n')
					do_list(out,el,lvl=lvl+1,is_dict=isDict(el))
				else:
					out.append(u'{:>{l}}{:16} {}\n'.format('','<'+type(el).__name__+'>',repr(el),l=(lvl*8)+8))
				out.append('\n')
			if not e: out.append('{}\n'.format(repr(e)))

		from collections import OrderedDict
		def isDict(obj):
			return issubclass(type(obj),dict) or issubclass(type(obj),OrderedDict)
		def isList(obj):
			return issubclass(type(obj),list) and type(obj) != OrderedDict
		def isScalar(obj):
			return any(issubclass(type(obj),t) for t in scalars)

# 		print type(self)
# 		print dir(self)
# 		print self.__dict__
# 		print self.__dict__.keys()
# 		print self.keys()

		out = [u'<{}>{}\n'.format(type(self).__name__,' '+repr(self) if isScalar(self) else '')]
		if isList(self) or isDict(self):
			do_list(out,self,lvl=lvl,is_dict=isDict(self))

#		print repr(self.__dict__.keys())

		for k in self.__dict__:
			if k in ('_OrderedDict__root','_OrderedDict__map'): continue # exclude these because of recursion
			e = getattr(self,k)
			if isList(e) or isDict(e):
				out.append(u'{:>{l}}{:<10} {:16}'.format('',k,'<'+type(e).__name__+'>',l=(lvl*8)+4))
				do_list(out,e,lvl=lvl,is_dict=isDict(e))
			elif hasattr(e,'pformat') and type(e) != type:
				out.append(u'{:>{l}}{:10} {}'.format('',k,e.pformat(lvl=lvl+1),l=(lvl*8)+4))
			else:
				out.append(u'{:>{l}}{:<10} {:16} {}\n'.format(
					'',k,'<'+type(e).__name__+'>',repr(e),l=(lvl*8)+4))

		import re
		return re.sub('\n+','\n',''.join(out))

class MMGenList(list,MMGenObject): pass
class MMGenDict(dict,MMGenObject): pass

# for attrs that are always present in the data instance
# reassignment and deletion forbidden
class MMGenImmutableAttr(object): # Descriptor

	def __init__(self,name,dtype,typeconv=True):
		self.typeconv = typeconv
		assert type(dtype) in (str,type)
		self.name = name
		self.dtype = dtype

	def __get__(self,instance,owner):
		return instance.__dict__[self.name]

	# forbid all reassignment
	def set_attr_ok(self,instance):
		return not hasattr(instance,self.name)

	def __set__(self,instance,value):
		if not self.set_attr_ok(instance):
			m = "Attribute '{}' of {} instance cannot be reassigned"
			raise AttributeError(m.format(self.name,type(instance)))
		if self.typeconv:   # convert type
			instance.__dict__[self.name] = \
				globals()[self.dtype](value) if type(self.dtype) == str else self.dtype(value)
		else:               # check type
			if type(value) != self.dtype:
				m = "Attribute '{}' of {} instance must of type {}"
				raise TypeError(m.format(self.name,type(instance),self.dtype))
			instance.__dict__[self.name] = value

	def __delete__(self,instance):
		m = "Atribute '{}' of {} instance cannot be deleted"
		raise AttributeError(m.format(self.name,type(instance)))

# for attrs that might not be present in the data instance
# reassignment or deletion allowed if specified
class MMGenListItemAttr(MMGenImmutableAttr):

	def __init__(self,name,dtype,typeconv=True,reassign_ok=False,delete_ok=False):
		self.reassign_ok = reassign_ok
		self.delete_ok = delete_ok
		MMGenImmutableAttr.__init__(self,name,dtype,typeconv=typeconv)

	# return None if attribute doesn't exist
	def __get__(self,instance,owner):
		try: return instance.__dict__[self.name]
		except: return None

	def set_attr_ok(self,instance):
		return getattr(instance,self.name) == None or self.reassign_ok

	def __delete__(self,instance):
		if self.delete_ok:
			if self.name in instance.__dict__:
				del instance.__dict__[self.name]
		else:
			MMGenImmutableAttr.__delete__(self,instance)

class MMGenListItem(MMGenObject):

	def __init__(self,*args,**kwargs):
		if args:
			raise ValueError, 'Non-keyword args not allowed'
		for k in kwargs:
			if kwargs[k] != None:
				setattr(self,k,kwargs[k])

	# prevent setting random attributes
	def __setattr__(self,name,value):
		if name not in type(self).__dict__:
			m = "'{}': no such attribute in class {}"
			raise AttributeError(m.format(name,type(self)))
		return object.__setattr__(self,name,value)

class InitErrors(object):

	@staticmethod
	def arg_chk(cls,on_fail):
		assert on_fail in ('die','return','silent','raise'),'arg_chk in class {}'.format(cls.__name__)

	@staticmethod
	def init_fail(m,on_fail,silent=False):
		if silent: m = ''
		from mmgen.util import die,msg
		if on_fail == 'die':      die(1,m)
		elif on_fail == 'return':
			if m: msg(m)
			return None # TODO: change to False
		elif on_fail == 'silent': return None # same here
		elif on_fail == 'raise':  raise ValueError,m

class AddrIdx(int,InitErrors):

	max_digits = 7

	def __new__(cls,num,on_fail='die'):
		cls.arg_chk(cls,on_fail)
		try:
			assert type(num) is not float
			me = int.__new__(cls,num)
		except:
			m = "'%s': value cannot be converted to address index" % num
		else:
			if len(str(me)) > cls.max_digits:
				m = "'%s': too many digits in addr idx" % num
			elif me < 1:
				m = "'%s': addr idx cannot be less than one" % num
			else:
				return me

		return cls.init_fail(m,on_fail)

class AddrIdxList(list,InitErrors,MMGenObject):

	max_len = 1000000

	def __init__(self,fmt_str=None,idx_list=None,on_fail='die',sep=','):
		self.arg_chk(type(self),on_fail)
		assert fmt_str or idx_list
		if idx_list:
			# dies on failure
			return list.__init__(self,sorted(set(AddrIdx(i) for i in idx_list)))
		elif fmt_str:
			desc = fmt_str
			ret,fs = [],"'%s': value cannot be converted to address index"
			from mmgen.util import msg
			for i in (fmt_str.split(sep)):
				j = i.split('-')
				if len(j) == 1:
					idx = AddrIdx(i,on_fail='return')
					if not idx: break
					ret.append(idx)
				elif len(j) == 2:
					beg = AddrIdx(j[0],on_fail='return')
					if not beg: break
					end = AddrIdx(j[1],on_fail='return')
					if not beg: break
					if end < beg:
						msg(fs % "%s-%s (invalid range)" % (beg,end)); break
					ret.extend([AddrIdx(x) for x in range(beg,end+1)])
				else:
					msg((fs % i) + ' list'); break
			else:
				return list.__init__(self,sorted(set(ret))) # fell off end of loop - success

			return self.init_fail((fs + ' list') % desc,on_fail)

class Hilite(object):

	color = 'red'
	color_always = False
	width = 0
	trunc_ok = True

	@classmethod
	def fmtc(cls,s,width=None,color=False,encl='',trunc_ok=None,
				center=False,nullrepl='',app='',appcolor=False):
		if width == None: width = cls.width
		if trunc_ok == None: trunc_ok = cls.trunc_ok
		assert width > 0
		if s == '' and nullrepl:
			s,center = nullrepl,True
		if center: s = s.center(width)
		assert type(encl) is str and len(encl) in (0,2)
		a,b = list(encl) if encl else ('','')
		if trunc_ok and len(s) > width: s = s[:width]
		if app:
			return cls.colorize(a+s+b,color=color) + \
					cls.colorize(app.ljust(width-len(a+s+b)),color=appcolor)
		else:
			return cls.colorize((a+s+b).ljust(width),color=color)

	def fmt(self,*args,**kwargs):
		assert args == () # forbid invocation w/o keywords
		return self.fmtc(self,*args,**kwargs)

	@classmethod
	def hlc(cls,s,color=True):
		return cls.colorize(s,color=color)

	def hl(self,color=True):
		return self.colorize(self,color=color)

	def __str__(self):
		return self.colorize(self,color=False)

	@classmethod
	def colorize(cls,s,color=True):
		k = color if type(color) is str else cls.color # hack: override color with str value
		return globals()[k](s) if (color or cls.color_always) else s

class BTCAmt(Decimal,Hilite,InitErrors):
	color = 'yellow'
	max_prec = 8
	max_amt = 21000000

	def __new__(cls,num,on_fail='die'):
		cls.arg_chk(cls,on_fail)
		try:
			me = Decimal.__new__(cls,str(num))
		except:
			m = "'%s': value cannot be converted to decimal" % num
		else:
			if me.normalize().as_tuple()[-1] < -cls.max_prec:
				from mmgen.globalvars import g
				m = "'{}': too many decimal places in {} amount".format(num,g.coin)
			elif me > cls.max_amt:
				from mmgen.globalvars import g
				m = "'{}': {} amount too large (>{})".format(num,g.coin,cls.max_amt)
#			elif me.as_tuple()[0]:
#				m = "'%s': BTC amount cannot be negative" % num
			else:
				return me
		return cls.init_fail(m,on_fail)

	@classmethod
	def fmtc(cls):
		raise NotImplemented

	def fmt(self,fs='3.8',color=False,suf=''):
		s = self.__str__(color=False)
		if '.' in fs:
			p1,p2 = [int(i) for i in fs.split('.',1)]
			ss = s.split('.',1)
			if len(ss) == 2:
				a,b = ss
				ret = a.rjust(p1) + '.' + (b+suf).ljust(p2+len(suf))
			else:
				ret = s.rjust(p1) + suf + ' ' * (p2+1)
		else:
			ret = s.ljust(int(fs))
		return self.colorize(ret,color=color)

	def hl(self,color=True):
		return self.__str__(color=color)

	def __str__(self,color=False): # format simply, no exponential notation
		if int(self) == self:
			ret = str(int(self))
		else:
			ret = self.normalize().__format__('f')
		return self.colorize(ret,color=color)

	def __repr__(self):
		return "{}('{}')".format(type(self).__name__,self.__str__())

	def __add__(self,other,context=None):
		return type(self)(Decimal.__add__(self,other,context))
	__radd__ = __add__

	def __sub__(self,other,context=None):
		return type(self)(Decimal.__sub__(self,other,context))

	def __mul__(self,other,context=None):
		return type(self)('{:0.8f}'.format(Decimal.__mul__(self,Decimal(other),context)))

	def __div__(self,other,context=None):
		return type(self)('{:0.8f}'.format(Decimal.__div__(self,Decimal(other),context)))

	def __neg__(self,other,context=None):
		return type(self)(Decimal.__neg__(self,other,context))

class BTCAddr(str,Hilite,InitErrors,MMGenObject):
	color = 'cyan'
	width = 35 # max len of testnet p2sh addr
	def __new__(cls,s,on_fail='die'):
		cls.arg_chk(cls,on_fail)
		m = "'%s': value is not a Bitcoin address" % s
		me = str.__new__(cls,s)
		from mmgen.bitcoin import verify_addr,addr_pfxs
		if type(s) in (str,unicode,BTCAddr):
			me.addr_fmt = verify_addr(s,return_type=True)
			me.testnet = s[0] in addr_pfxs['testnet']
			if me.addr_fmt:
				return me
		return cls.init_fail(m,on_fail)

	@classmethod
	def fmtc(cls,s,**kwargs):
		# True -> 'cyan': use the str value override hack
		if 'color' in kwargs and kwargs['color'] == True:
			kwargs['color'] = cls.color
		if not 'width' in kwargs: kwargs['width'] = cls.width
		if kwargs['width'] < len(s):
			s = s[:kwargs['width']-2] +  '..'
		return Hilite.fmtc(s,**kwargs)

	def is_for_current_chain(self):
		from mmgen.globalvars import g
		assert g.chain, 'global chain variable unset'
		from bitcoin import addr_pfxs
		return self[0] in addr_pfxs[g.chain]

	def is_mainnet(self):
		from bitcoin import addr_pfxs
		return self[0] in addr_pfxs['mainnet']

	def is_in_tracking_wallet(self):
		from mmgen.rpc import bitcoin_connection
		d = bitcoin_connection().validateaddress(self)
		return d['iswatchonly'] and 'account' in d

class SeedID(str,Hilite,InitErrors):
	color = 'blue'
	width = 8
	trunc_ok = False
	def __new__(cls,seed=None,sid=None,on_fail='die'):
		cls.arg_chk(cls,on_fail)
		assert seed or sid
		if seed:
			from mmgen.seed import Seed
			from mmgen.util import make_chksum_8
			if type(seed) == Seed:
				return str.__new__(cls,make_chksum_8(seed.get_data()))
		elif sid:
			sid = str(sid)
			from string import hexdigits
			if len(sid) == cls.width and set(sid) <= set(hexdigits.upper()):
				return str.__new__(cls,sid)

		m = "'%s': value cannot be converted to SeedID" % str(seed or sid)
		return cls.init_fail(m,on_fail)

class MMGenID(str,Hilite,InitErrors,MMGenObject):

	color = 'orange'
	width = 0
	trunc_ok = False

	def __new__(cls,s,on_fail='die'):
		cls.arg_chk(cls,on_fail)
		s = str(s)
		try:
			ss = s.split(':')
			assert len(ss) in (2,3)
			sid = SeedID(sid=ss[0],on_fail='silent')
			assert sid
			idx = AddrIdx(ss[-1],on_fail='silent')
			assert idx
			t = MMGenAddrType((MMGenAddrType.dfl_mmtype,ss[1])[len(ss) != 2],on_fail='silent')
			assert t
			me = str.__new__(cls,'{}:{}:{}'.format(sid,t,idx))
			me.sid = sid
			me.mmtype = t
			me.idx = idx
			me.al_id = AddrListID(sid,me.mmtype) # key with colon!
			assert me.al_id
			me.sort_key = '{}:{}:{:0{w}}'.format(sid,t,idx,w=idx.max_digits)
			return me
		except:
			m = "'%s': value cannot be converted to MMGenID" % s
			return cls.init_fail(m,on_fail)

class TwMMGenID(str,Hilite,InitErrors,MMGenObject):

	color = 'orange'
	width = 0
	trunc_ok = False

	def __new__(cls,s,on_fail='die'):
		cls.arg_chk(cls,on_fail)
		obj,sort_key = None,None
		try:
			obj = MMGenID(s,on_fail='silent')
			sort_key,t = obj.sort_key,'mmgen'
		except:
			try:
				assert len(s) > 4 and s[:4] == 'btc:'
				obj,sort_key,t = str(s),'z_'+s,'non-mmgen'
			except:
				pass

		if obj and sort_key:
			me = str.__new__(cls,obj)
			me.obj = obj
			me.sort_key = sort_key
			me.type = t
			return me

		m = "'{}': value cannot be converted to {}".format(s,cls.__name__)
		return cls.init_fail(m,on_fail)

# contains TwMMGenID,TwComment.  Not for display
class TwLabel(str,InitErrors,MMGenObject):

	def __new__(cls,s,on_fail='die'):
		cls.arg_chk(cls,on_fail)
		try:
			ss = s.split(None,1)
			me = str.__new__(cls,s)
			me.mmid = TwMMGenID(ss[0],on_fail='silent')
			assert me.mmid
			me.comment = TwComment(ss[1] if len(ss) == 2 else '',on_fail='silent')
			assert me.comment != None
			return me
		except:
			m = "'{}': value cannot be converted to {}".format(s,cls.__name__)
			return cls.init_fail(m,on_fail)

class HexStr(str,Hilite,InitErrors):
	color = 'red'
	trunc_ok = False
	def __new__(cls,s,on_fail='die',case='lower'):
		assert case in ('upper','lower')
		cls.arg_chk(cls,on_fail)
		from string import hexdigits
		if set(s) <= set(getattr(hexdigits,case)()) and not len(s) % 2:
			return str.__new__(cls,s)
		m = "'{}': value cannot be converted to {}".format(s,cls.__name__)
		return cls.init_fail(m,on_fail)

class MMGenTxID(str,Hilite,InitErrors):
	color = 'red'
	width = 6
	trunc_ok = False
	hexcase = 'upper'
	def __new__(cls,s,on_fail='die'):
		cls.arg_chk(cls,on_fail)
		from string import hexdigits
		if len(s) == cls.width and set(s) <= set(getattr(hexdigits,cls.hexcase)()):
			return str.__new__(cls,s)
		m = "'{}': value cannot be converted to {}".format(s,cls.__name__)
		return cls.init_fail(m,on_fail)

class BitcoinTxID(MMGenTxID):
	color = 'purple'
	width = 64
	hexcase = 'lower'

class WifKey(str,Hilite,InitErrors):
	width = 53
	color = 'blue'
	desc = 'WIF key'
	def __new__(cls,s,on_fail='die',errmsg=None):
		cls.arg_chk(cls,on_fail)
		from mmgen.bitcoin import wif2hex
		if wif2hex(s):
			me = str.__new__(cls,s)
			return me
		m = errmsg or "'{}': invalid value for {}".format(s,cls.desc)
		return cls.init_fail(m,on_fail)

class HexStr(str,Hilite,InitErrors):
	color = 'red'
	trunc_ok = False
	def __new__(cls,s,on_fail='die',case='lower'):
		assert case in ('upper','lower')
		cls.arg_chk(cls,on_fail)
		from string import hexdigits
		if set(s) <= set(getattr(hexdigits,case)()) and not len(s) % 2:
			return str.__new__(cls,s)
		m = "'{}': value cannot be converted to {}".format(s,cls.__name__)
		return cls.init_fail(m,on_fail)

class PubKey(HexStr,MMGenObject):
	def __new__(cls,s,compressed,on_fail='die'):
		assert type(compressed) == bool
		me = HexStr.__new__(cls,s,case='lower')
		me.compressed = compressed
		return me

class PrivKey(str,Hilite,InitErrors,MMGenObject):

	color = 'red'
	width = 64
	trunc_ok = False

	compressed = MMGenImmutableAttr('compressed',bool,typeconv=False)
	wif        = MMGenImmutableAttr('wif',WifKey,typeconv=False)

	def __new__(*args,**kwargs): # initialize with (priv_bin,compressed), WIF or self
		cls = args[0]
		assert set(kwargs) <= set(['on_fail','wif'])
		on_fail = kwargs['on_fail'] if 'on_fail' in kwargs else 'die'
		cls.arg_chk(cls,on_fail)

		if len(args) == 2:
			assert type(args[1]) == cls
			return args[1]

		if 'wif' in kwargs:
			assert len(args) == 1
			try:
				from mmgen.bitcoin import wif2hex,wif_is_compressed # TODO: move these here
				wif = WifKey(kwargs['wif'])
				me = str.__new__(cls,wif2hex(wif))
				me.compressed = wif_is_compressed(wif)
				me.wif = wif
				return me
			except:
				fs = "Value '{}' cannot be converted to WIF key"
				errmsg = fs.format(kwargs['wif'])
				return cls.init_fail(errmsg,on_fail)

		cls,s,compressed = args

		try:
			from binascii import hexlify
			assert len(s) == cls.width / 2
			me = str.__new__(cls,hexlify(s))
			me.compressed = compressed
			me.wif = me.towif()
			return me
		except:
			fs = "Key={}\nCompressed={}\nValue pair cannot be converted to {}"
			errmsg = fs.format(repr(s),compressed,cls.__name__)
			return cls.init_fail(errmsg,on_fail)

	def towif(self):
		from mmgen.bitcoin import hex2wif
		return WifKey(hex2wif(self,compressed=self.compressed))

class MMGenAddrType(str,Hilite,InitErrors):
	width = 1
	trunc_ok = False
	color = 'blue'
	mmtypes = {
		# TODO 'L' is ambiguous: For user, it means MMGen legacy uncompressed address.
		# For generator functions, 'L' means any p2pkh address, and 'S' any ps2h address
		'L': 'legacy',
		'S': 'segwit',
# 		'l': 'litecoin',
# 		'e': 'ethereum',
# 		'E': 'ethereum_classic',
# 		'm': 'monero',
# 		'z': 'zcash',
	}
	dfl_mmtype = 'L'
	def __new__(cls,s,on_fail='die',errmsg=None):
		cls.arg_chk(cls,on_fail)
		for k,v in cls.mmtypes.items():
			if s in (k,v):
				if s == v: s = k
				me = str.__new__(cls,s)
				me.name = cls.mmtypes[s]
				return me
		m = errmsg or "'{}': invalid value for {}".format(s,cls.__name__)
		return cls.init_fail(m,on_fail)

class MMGenPasswordType(MMGenAddrType):
	mmtypes = { 'P': 'password' }

class AddrListID(str,Hilite,InitErrors):
	width = 10
	trunc_ok = False
	color = 'yellow'
	def __new__(cls,sid,mmtype,on_fail='die'):
		cls.arg_chk(cls,on_fail)
		m = "'{}': not a SeedID. Cannot create {}".format(sid,cls.__name__)
		if type(sid) == SeedID:
			m = "'{}': not an MMGenAddrType object. Cannot create {}".format(mmtype,cls.__name__)
			if type(mmtype) in (MMGenAddrType,MMGenPasswordType):
				me = str.__new__(cls,sid+':'+mmtype) # colon in key is OK
				me.sid = sid
				me.mmtype = mmtype
				return me
		return cls.init_fail(m,on_fail)

class MMGenLabel(unicode,Hilite,InitErrors):

	color = 'pink'
	allowed = []
	forbidden = []
	max_len = 0
	min_len = 0
	desc = 'label'

	def __new__(cls,s,on_fail='die',msg=None):
		cls.arg_chk(cls,on_fail)
		for k in cls.forbidden,cls.allowed:
			assert type(k) == list
			for ch in k: assert type(ch) == unicode and len(ch) == 1
		try:
			s = s.strip()
			if type(s) != unicode:
				s = s.decode('utf8')
		except:
			m = "'%s': value is not a valid UTF-8 string" % s
		else:
			from mmgen.util import capfirst
			if len(s) > cls.max_len:
				m = u"'{}': {} too long (>{} symbols)".format(s,capfirst(cls.desc),cls.max_len)
			elif len(s) < cls.min_len:
				m = u"'{}': {} too short (<{} symbols)".format(s,capfirst(cls.desc),cls.min_len)
			elif cls.allowed and not set(list(s)).issubset(set(cls.allowed)):
				m = u"{} '{}' contains non-allowed symbols: {}".format(capfirst(cls.desc),s,
					' '.join(set(list(s)) - set(cls.allowed)))
			elif cls.forbidden and any(ch in s for ch in cls.forbidden):
				m = u"{} '{}' contains one of these forbidden symbols: '{}'".format(capfirst(cls.desc),s,
					"', '".join(cls.forbidden))
			else:
				return unicode.__new__(cls,s)
		return cls.init_fail((msg+'\n' if msg else '') + m,on_fail)

class MMGenWalletLabel(MMGenLabel):
	max_len = 48
	allowed = [unichr(i+32) for i in range(95)]
	desc = 'wallet label'

class TwComment(MMGenLabel):
	max_len = 32
	allowed = [unichr(i+32) for i in range(95)]
	desc = 'tracking wallet comment'

class MMGenTXLabel(MMGenLabel):
	max_len = 72
	desc = 'transaction label'

class MMGenPWIDString(MMGenLabel):
	max_len = 256
	min_len = 1
	desc = 'password ID string'
	forbidden = list(u' :/\\')

class AddrListList(list,MMGenObject): pass

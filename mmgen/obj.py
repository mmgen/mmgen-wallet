#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2018 The MMGen Project <mmgen@tuta.io>
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

import sys,os,unicodedata
from decimal import *
from mmgen.color import *
from string import hexdigits,ascii_letters,digits

def is_mmgen_seed_id(s): return SeedID(sid=s,on_fail='silent')
def is_mmgen_idx(s):     return AddrIdx(s,on_fail='silent')
def is_mmgen_id(s):      return MMGenID(s,on_fail='silent')
def is_coin_addr(s):     return CoinAddr(s,on_fail='silent')
def is_addrlist_id(s):   return AddrListID(s,on_fail='silent')
def is_tw_label(s):      return TwLabel(s,on_fail='silent')
def is_wif(s):           return WifKey(s,on_fail='silent')
def is_viewkey(s):       return ViewKey(s,on_fail='silent')

def truncate_str(s,w):
	wide_count = 0
	w -= 1
	for i in range(len(s)):
		wide_count += unicodedata.east_asian_width(s[i]) in ('F','W')
		if wide_count + i > w:
			return s[:i]

class MMGenObject(object):

	# Pretty-print any object subclassed from MMGenObject, recursing into sub-objects - WIP
	def pmsg(self): print(self.pformat())
	def pdie(self): print(self.pformat()); sys.exit(0)
	def pformat(self,lvl=0):
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
class AddrListList(list,MMGenObject): pass

class InitErrors(object):

	@staticmethod
	def arg_chk(cls,on_fail):
		assert on_fail in ('die','return','silent','raise'),'arg_chk in class {}'.format(cls.__name__)

	@staticmethod
	def init_fail(m,on_fail):
		if os.getenv('MMGEN_TRACEBACK'): on_fail == 'raise'
		from mmgen.util import die,msg
		if   on_fail == 'silent': return None # TODO: return False instead?
		elif on_fail == 'raise':  raise ValueError,m
		elif on_fail == 'die':    die(1,m)
		elif on_fail == 'return':
			if m: msg(m)
			return None                       # TODO: here too?

class Hilite(object):

	color = 'red'
	color_always = False
	width = 0
	trunc_ok = True

	@classmethod
	# 'width' is screen width (greater than len(s) for CJK strings)
	# 'append_chars' and 'encl' must consist of single-width chars only
	def fmtc(cls,s,width=None,color=False,encl='',trunc_ok=None,
				center=False,nullrepl='',append_chars='',append_color=False):
		s = unicode(s)
		s_wide_count = len([1 for ch in s if unicodedata.east_asian_width(ch) in ('F','W')])
		assert type(encl) is str and len(encl) in (0,2),"'encl' must be 2-character str"
		a,b = list(encl) if encl else ('','')
		add_len = len(a) + len(b) + len(append_chars)
		if width == None: width = cls.width
		if trunc_ok == None: trunc_ok = cls.trunc_ok
		assert width >= 2 + add_len,( # 2 because CJK
			"'{!r}': invalid width ({}) (width must be at least 2)".format(s,width))
		if len(s) + s_wide_count + add_len > width:
			assert trunc_ok, "If 'trunc_ok' is false, 'width' must be >= screen width of string"
			s = truncate_str(s,width-add_len)
		if s == '' and nullrepl:
			s = nullrepl.center(width)
		else:
			s = a+s+b
			if center: s = s.center(width)
		if append_chars:
			return cls.colorize(s,color=color) + \
					cls.colorize(append_chars.ljust(width-len(s)-s_wide_count),color=append_color)
		else:
			return cls.colorize(s.ljust(width-s_wide_count),color=color)

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

# For attrs that are always present in the data instance
# Reassignment and deletion forbidden
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
				globals()[self.dtype](value,on_fail='raise') if type(self.dtype) == str else self.dtype(value)
		else:               # check type
			if type(value) != self.dtype:
				m = "Attribute '{}' of {} instance must of type {}"
				raise TypeError(m.format(self.name,type(instance),self.dtype))
			instance.__dict__[self.name] = value

	def __delete__(self,instance):
		m = "Atribute '{}' of {} instance cannot be deleted"
		raise AttributeError(m.format(self.name,type(instance)))

# For attrs that might not be present in the data instance
# Reassignment or deletion allowed if specified
class MMGenListItemAttr(MMGenImmutableAttr): # Descriptor

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

class AddrIdx(int,InitErrors):
	max_digits = 7
	def __new__(cls,num,on_fail='die'):
		cls.arg_chk(cls,on_fail)
		try:
			assert type(num) is not float,'is float'
			me = int.__new__(cls,num)
			assert len(str(me)) <= cls.max_digits,'is more than {} digits'.format(cls.max_digits)
			assert me > 0,'is less than one'
			return me
		except Exception as e:
			m = "{!r}: value cannot be converted to address index ({})"
			return cls.init_fail(m.format(num,e[0]),on_fail)

class AddrIdxList(list,InitErrors,MMGenObject):
	max_len = 1000000
	def __init__(self,fmt_str=None,idx_list=None,on_fail='die',sep=','):
		self.arg_chk(type(self),on_fail)
		try:
			if idx_list:
				return list.__init__(self,sorted(set(AddrIdx(i,on_fail='raise') for i in idx_list)))
			elif fmt_str:
				ret = []
				for i in (fmt_str.split(sep)):
					j = i.split('-')
					if len(j) == 1:
						idx = AddrIdx(i,on_fail='raise')
						if not idx: break
						ret.append(idx)
					elif len(j) == 2:
						beg = AddrIdx(j[0],on_fail='raise')
						if not beg: break
						end = AddrIdx(j[1],on_fail='raise')
						if not beg: break
						if end < beg: break
						ret.extend([AddrIdx(x,on_fail='raise') for x in range(beg,end+1)])
					else: break
				else:
					return list.__init__(self,sorted(set(ret))) # fell off end of loop - success
				raise ValueError,"{!r}: invalid range".format(i)
		except Exception as e:
			m = "{!r}: value cannot be converted to AddrIdxList ({})"
			return type(self).init_fail(m.format(idx_list or fmt_str,e[0]),on_fail)

class BTCAmt(Decimal,Hilite,InitErrors):
	color = 'yellow'
	max_prec = 8
	max_amt = 21000000
	min_coin_unit = Decimal('0.00000001') # satoshi

	def __new__(cls,num,on_fail='die'):
		if type(num) == cls: return num
		cls.arg_chk(cls,on_fail)
		try:
			assert type(num) is not float,'number is floating-point'
			assert type(num) is not long,'number is a long integer'
			me = Decimal.__new__(cls,str(num))
			assert me.normalize().as_tuple()[-1] >= -cls.max_prec,'too many decimal places in coin amount'
			assert me <= cls.max_amt,'coin amount too large (>{})'.format(cls.max_amt)
			assert me >= 0,'coin amount cannot be negative'
			return me
		except Exception as e:
			m = "{!r}: value cannot be converted to {} ({})"
			return cls.init_fail(m.format(num,cls.__name__,e[0]),on_fail)

	@classmethod
	def fmtc(cls):
		raise NotImplementedError

	def fmt(self,fs='4.8',color=False,suf=''):
		s = str(int(self)) if int(self) == self else self.normalize().__format__('f')
		if '.' in fs:
			p1,p2 = map(int,fs.split('.',1))
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
		return self.colorize(
			str(int(self)) if int(self) == self else self.normalize().__format__('f'),
			color=color)

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

class BCHAmt(BTCAmt): pass
class B2XAmt(BTCAmt): pass
class LTCAmt(BTCAmt): max_amt = 84000000

class CoinAddr(str,Hilite,InitErrors,MMGenObject):
	color = 'cyan'
	hex_width = 40
	width = 1
	trunc_ok = False
	def __new__(cls,s,on_fail='die'):
		if type(s) == cls: return s
		cls.arg_chk(cls,on_fail)
		from mmgen.globalvars import g
		try:
			assert set(s) <= set(ascii_letters+digits),'contains non-alphanumeric characters'
			me = str.__new__(cls,s)
			va = g.proto.verify_addr(s,hex_width=cls.hex_width,return_dict=True)
			assert va,'failed verification'
			me.addr_fmt = va['format']
			me.hex = va['hex']
			return me
		except Exception as e:
			m = "{!r}: value cannot be converted to {} address ({})"
			return cls.init_fail(m.format(s,g.proto.__name__,e[0]),on_fail)

	@classmethod
	def fmtc(cls,s,**kwargs):
		# True -> 'cyan': use the str value override hack
		if 'color' in kwargs and kwargs['color'] == True:
			kwargs['color'] = cls.color
		if not 'width' in kwargs: kwargs['width'] = cls.width
		if kwargs['width'] < len(s):
			s = s[:kwargs['width']-2] +  '..'
		return Hilite.fmtc(s,**kwargs)

	def is_for_chain(self,chain):

		def pfx_ok(pfx):
			if type(pfx) == tuple:
				if self[0] in pfx: return True
			elif self[:len(pfx)] == pfx: return True
			return False

		from mmgen.globalvars import g
		proto = g.proto.get_protocol_by_chain(chain)
		vn = proto.addr_ver_num

		if self.addr_fmt == 'bech32':
			return self[:len(proto.bech32_hrp)] == proto.bech32_hrp
		elif self.addr_fmt == 'p2sh' and 'p2sh2' in vn:
			return pfx_ok(vn['p2sh'][1]) or pfx_ok(vn['p2sh2'][1])
		else:
			return pfx_ok(vn[self.addr_fmt][1])

	def is_in_tracking_wallet(self):
		from mmgen.rpc import rpc_init
		d = rpc_init().validateaddress(self)
		return d['iswatchonly'] and 'account' in d

class ViewKey(object):
	def __new__(cls,s,on_fail='die'):
		from mmgen.globalvars import g
		if g.proto.name == 'zcash':
			return ZcashViewKey.__new__(ZcashViewKey,s,on_fail)
		elif g.proto.name == 'monero':
			return MoneroViewKey.__new__(MoneroViewKey,s,on_fail)
		else:
			raise ValueError,'{}: protocol does not support view keys'.format(g.proto.name.capitalize())

class ZcashViewKey(CoinAddr): hex_width = 128

class SeedID(str,Hilite,InitErrors):
	color = 'blue'
	width = 8
	trunc_ok = False
	def __new__(cls,seed=None,sid=None,on_fail='die'):
		if type(sid) == cls: return sid
		cls.arg_chk(cls,on_fail)
		try:
			if seed:
				from mmgen.seed import Seed
				assert type(seed) == Seed,'not a Seed instance'
				from mmgen.util import make_chksum_8
				return str.__new__(cls,make_chksum_8(seed.get_data()))
			elif sid:
				assert set(sid) <= set(hexdigits.upper()),'not uppercase hex digits'
				assert len(sid) == cls.width,'not {} characters wide'.format(cls.width)
				return str.__new__(cls,sid)
			raise ValueError,'no arguments provided'
		except Exception as e:
			m = "{!r}: value cannot be converted to SeedID ({})"
			return cls.init_fail(m.format(seed or sid,e[0]),on_fail)

class MMGenID(str,Hilite,InitErrors,MMGenObject):
	color = 'orange'
	width = 0
	trunc_ok = False
	def __new__(cls,s,on_fail='die'):
		cls.arg_chk(cls,on_fail)
		from mmgen.globalvars import g
		try:
			ss = str(s).split(':')
			assert len(ss) in (2,3),'not 2 or 3 colon-separated items'
			t = MMGenAddrType((ss[1],g.proto.dfl_mmtype)[len(ss)==2],on_fail='raise')
			me = str.__new__(cls,'{}:{}:{}'.format(ss[0],t,ss[-1]))
			me.sid = SeedID(sid=ss[0],on_fail='raise')
			me.idx = AddrIdx(ss[-1],on_fail='raise')
			me.mmtype = t
			assert t in g.proto.mmtypes,'{}: invalid address type for {}'.format(t,g.proto.__name__)
			me.al_id = str.__new__(AddrListID,me.sid+':'+me.mmtype) # checks already done
			me.sort_key = '{}:{}:{:0{w}}'.format(me.sid,me.mmtype,me.idx,w=me.idx.max_digits)
			return me
		except Exception as e:
			m = "{}\n{!r}: value cannot be converted to MMGenID"
			return cls.init_fail(m.format(e[0],s),on_fail)

class TwMMGenID(str,Hilite,InitErrors,MMGenObject):
	color = 'orange'
	width = 0
	trunc_ok = False
	def __new__(cls,s,on_fail='die'):
		if type(s) == cls: return s
		cls.arg_chk(cls,on_fail)
		ret = None
		try:
			ret = MMGenID(s,on_fail='raise')
			sort_key,idtype = ret.sort_key,'mmgen'
		except Exception as e:
			try:
				from mmgen.globalvars import g
				assert s.split(':',1)[0] == g.proto.base_coin.lower(),(
					"not a string beginning with the prefix '{}:'".format(g.proto.base_coin.lower()))
				assert set(s[4:]) <= set(ascii_letters+digits),'contains non-alphanumeric characters'
				assert len(s) > 4,'not more that four characters long'
				ret,sort_key,idtype = str(s),'z_'+s,'non-mmgen'
			except Exception as f:
				m = "{}\nValue is {}\n{!r}: value cannot be converted to TwMMGenID"
				return cls.init_fail(m.format(e[0],f[0],s),on_fail)

		me = str.__new__(cls,ret)
		me.obj = ret
		me.sort_key = sort_key
		me.type = idtype
		return me

# contains TwMMGenID,TwComment.  Not for display
class TwLabel(unicode,InitErrors,MMGenObject):
	def __new__(cls,s,on_fail='die'):
		if type(s) == cls: return s
		cls.arg_chk(cls,on_fail)
		try:
			ss = s.split(None,1)
			mmid = TwMMGenID(ss[0],on_fail='raise')
			comment = TwComment(ss[1] if len(ss) == 2 else '',on_fail='raise')
			me = unicode.__new__(cls,u'{}{}'.format(mmid,u' {}'.format(comment) if comment else ''))
			me.mmid = mmid
			me.comment = comment
			return me
		except Exception as e:
			m = u"{}\n{!r}: value cannot be converted to TwLabel"
			return cls.init_fail(m.format(e[0],s),on_fail)

class HexStr(str,Hilite,InitErrors):
	color = 'red'
	trunc_ok = False
	def __new__(cls,s,on_fail='die',case='lower'):
		if type(s) == cls: return s
		assert case in ('upper','lower')
		cls.arg_chk(cls,on_fail)
		try:
			assert type(s) in (str,unicode,bytes),'not a string'
			assert set(s) <= set(getattr(hexdigits,case)()),'not {}case hexadecimal symbols'.format(case)
			assert not len(s) % 2,'odd-length string'
			return str.__new__(cls,s)
		except Exception as e:
			m = "{!r}: value cannot be converted to {} (value is {})"
			return cls.init_fail(m.format(s,cls.__name__,e[0]),on_fail)

class HexStrWithWidth(HexStr):
	color = 'nocolor'
	trunc_ok = False
	hexcase = 'lower'
	width = None
	def __new__(cls,s,on_fail='die'):
		cls.arg_chk(cls,on_fail)
		try:
			ret = HexStr.__new__(cls,s,case=cls.hexcase,on_fail='raise')
			assert len(s) == cls.width,'Value is not {} characters wide'.format(cls.width)
			return ret
		except Exception as e:
			m = "{}\n{!r}: value cannot be converted to {}"
			return cls.init_fail(m.format(e[0],s,cls.__name__),on_fail)

class MMGenTxID(HexStrWithWidth):      color,width,hexcase = 'red',6,'upper'
class MoneroViewKey(HexStrWithWidth):  color,width,hexcase = 'cyan',64,'lower'
class WalletPassword(HexStrWithWidth): color,width,hexcase = 'blue',32,'lower'
class CoinTxID(HexStrWithWidth):       color,width,hexcase = 'purple',64,'lower'

class WifKey(str,Hilite,InitErrors):
	width = 53
	color = 'blue'
	def __new__(cls,s,on_fail='die'):
		if type(s) == cls: return s
		cls.arg_chk(cls,on_fail)
		try:
			assert set(s) <= set(ascii_letters+digits),'not an ascii string'
			from mmgen.globalvars import g
			g.proto.wif2hex(s) # raises exception on error
			return str.__new__(cls,s)
		except Exception as e:
			m = '{!r}: invalid value for WIF key ({})'.format(s,e[0])
			return cls.init_fail(m,on_fail)

class PubKey(HexStr,MMGenObject): # TODO: add some real checks
	def __new__(cls,s,compressed,on_fail='die'):
		try:
			assert type(compressed) == bool,"'compressed' must be of type bool"
			me = HexStr.__new__(cls,s,case='lower',on_fail='raise')
			me.compressed = compressed
			return me
		except Exception as e:
			m = '{!r}: invalid value for pubkey ({})'.format(s,e[0])
			return cls.init_fail(m,on_fail)

class PrivKey(str,Hilite,InitErrors,MMGenObject):

	color = 'red'
	width = 64
	trunc_ok = False

	compressed = MMGenImmutableAttr('compressed',bool,typeconv=False)
	wif        = MMGenImmutableAttr('wif',WifKey,typeconv=False)

	# initialize with (priv_bin,compressed), WIF or self
	def __new__(cls,s=None,compressed=None,wif=None,pubkey_type=None,on_fail='die'):
		from mmgen.globalvars import g

		if type(s) == cls: return s
		cls.arg_chk(cls,on_fail)

		if wif:
			try:
				assert s == None
				assert set(wif) <= set(ascii_letters+digits),'not an ascii string'
				w2h = g.proto.wif2hex(wif) # raises exception on error
				me = str.__new__(cls,w2h['hex'])
				me.compressed = w2h['compressed']
				me.pubkey_type = w2h['pubkey_type']
				me.wif = str.__new__(WifKey,wif) # check has been done
				me.orig_hex = None
				return me
			except Exception as e:
				fs = "Value {!r} cannot be converted to {} WIF key ({})"
				return cls.init_fail(fs.format(wif,g.coin,e[0]),on_fail)

		try:
			assert s and type(compressed) == bool and pubkey_type,'Incorrect args for PrivKey()'
			assert len(s) == cls.width / 2,'Key length must be {}'.format(cls.width/2)
			me = str.__new__(cls,g.proto.preprocess_key(s.encode('hex'),pubkey_type))
			me.orig_hex = s.encode('hex') # save the non-preprocessed key
			me.compressed = compressed
			me.pubkey_type = pubkey_type
			if pubkey_type != 'password': # skip WIF creation for passwds
				me.wif = WifKey(g.proto.hex2wif(me,pubkey_type,compressed),on_fail='raise')
			return me
		except Exception as e:
			fs = "Key={!r}\nCompressed={}\nValue pair cannot be converted to PrivKey\n({})"
			return cls.init_fail(fs.format(s,compressed,e),on_fail)


class AddrListID(str,Hilite,InitErrors,MMGenObject):
	width = 10
	trunc_ok = False
	color = 'yellow'
	def __new__(cls,sid,mmtype,on_fail='die'):
		cls.arg_chk(cls,on_fail)
		try:
			assert type(sid) == SeedID,"{!r} not a SeedID instance".format(sid)
			t = MMGenAddrType,MMGenPasswordType
			assert type(mmtype) in t,"{!r} not an instance of {}".format(mmtype,','.join([i.__name__ for i in t]))
			me = str.__new__(cls,sid+':'+mmtype)
			me.sid = sid
			me.mmtype = mmtype
			return me
		except Exception as e:
			m = "Cannot create AddrListID ({})".format(e[0])
			return cls.init_fail(m,on_fail)

class MMGenLabel(unicode,Hilite,InitErrors):
	color = 'pink'
	allowed = []
	forbidden = []
	max_len = 0
	min_len = 0
	desc = 'label'
	def __new__(cls,s,on_fail='die',msg=None):
		if type(s) == cls: return s
		cls.arg_chk(cls,on_fail)
		for k in cls.forbidden,cls.allowed:
			assert type(k) == list
			for ch in k: assert type(ch) == unicode and len(ch) == 1
		try:
			s = s.strip()
			if type(s) != unicode:
				s = s.decode('utf8')
			for ch in s:
				# Allow:    (L)etter,(N)umber,(P)unctuation,(S)ymbol,(Z)space
				# Disallow: (C)ontrol,(M)combining
				# Combining characters create width formatting issues, so disallow them for now
				assert unicodedata.category(ch)[0] not in 'CM','{!r}: {} characters not allowed'.format(
					ch,('control','combining')[unicodedata.category(ch)[0]=='M'])
			assert len(s) <= cls.max_len, 'too long (>{} symbols)'.format(cls.max_len)
			assert len(s) >= cls.min_len, 'too short (<{} symbols)'.format(cls.min_len)
			assert not cls.allowed or set(list(s)).issubset(set(cls.allowed)),\
				u'contains non-allowed symbols: {}'.format(' '.join(set(list(s)) - set(cls.allowed)))
			assert not cls.forbidden or not any(ch in s for ch in cls.forbidden),\
				u"contains one of these forbidden symbols: '{}'".format("', '".join(cls.forbidden))
			return unicode.__new__(cls,s)
		except Exception as e:
			m = u"{!r}: value cannot be converted to {} ({})"
			return cls.init_fail(m.format(s,cls.__name__,e),on_fail)

class MMGenWalletLabel(MMGenLabel):
	max_len = 48
	desc = 'wallet label'

class TwComment(MMGenLabel):
	max_len = 40
	desc = 'tracking wallet comment'

class MMGenTXLabel(MMGenLabel):
	max_len = 72
	desc = 'transaction label'

class MMGenPWIDString(MMGenLabel):
	max_len = 256
	min_len = 1
	desc = 'password ID string'
	forbidden = list(u' :/\\')

class MMGenAddrType(str,Hilite,InitErrors,MMGenObject):
	width = 1
	trunc_ok = False
	color = 'blue'
	mmtypes = { # 'name' is used to cook the seed, so it must never change!
		'L': {  'name':'legacy',
				'pubkey_type':'std',
				'compressed':False,
				'gen_method':'p2pkh',
				'addr_fmt':'p2pkh',
				'desc':'Legacy uncompressed address'},
		'C': {  'name':'compressed',
				'pubkey_type':'std',
				'compressed':True,
				'gen_method':'p2pkh',
				'addr_fmt':'p2pkh',
				'desc':'Compressed P2PKH address'},
		'S': {  'name':'segwit',
				'pubkey_type':'std',
				'compressed':True,
				'gen_method':'segwit',
				'addr_fmt':'p2sh',
				'desc':'Segwit P2SH-P2WPKH address' },
		'B': {  'name':'bech32',
				'pubkey_type':'std',
				'compressed':True,
				'gen_method':'bech32',
				'addr_fmt':'bech32',
				'desc':'Native Segwit (Bech32) address' },
		'E': {  'name':'ethereum',
				'pubkey_type':'std',
				'compressed':False,
				'gen_method':'ethereum',
				'addr_fmt':'ethereum',
				'wif_label':'privkey:',
				'extra_attrs': ('wallet_passwd',),
				'desc':'Ethereum address' },
		'Z': {  'name':'zcash_z',
				'pubkey_type':'zcash_z',
				'compressed':False,
				'gen_method':'zcash_z',
				'addr_fmt':'zcash_z',
				'extra_attrs': ('viewkey',),
				'desc':'Zcash z-address' },
		'M': {  'name':'monero',
				'pubkey_type':'monero',
				'compressed':False,
				'gen_method':'monero',
				'addr_fmt':'monero',
				'wif_label':'spendkey:',
				'extra_attrs': ('viewkey','wallet_passwd'),
				'desc':'Monero address'}
	}
	def __new__(cls,s,on_fail='die',errmsg=None):
		if type(s) == cls: return s
		cls.arg_chk(cls,on_fail)
		from mmgen.globalvars import g
		try:
			for k,v in cls.mmtypes.items():
				if s in (k,v['name']):
					if s == v['name']: s = k
					me = str.__new__(cls,s)
					for k in ('name','pubkey_type','compressed','gen_method','addr_fmt','desc'):
						setattr(me,k,v[k])
					assert me in g.proto.mmtypes + ('P',), (
						"'{}': invalid address type for {}".format(me.name,g.proto.__name__))
					me.extra_attrs = v['extra_attrs'] if 'extra_attrs' in v else ()
					me.wif_label   = v['wif_label'] if 'wif_label' in v else 'wif:'
					return me
			raise ValueError,'not found'
		except Exception as e:
			m = '{}{!r}: invalid value for {} ({})'.format(
				('{!r}\n'.format(errmsg) if errmsg else ''),s,cls.__name__,e[0])
			return cls.init_fail(m,on_fail)

	@classmethod
	def get_names(cls):
		return [v['name'] for v in cls.mmtypes.values()]

class MMGenPasswordType(MMGenAddrType):
	mmtypes = {
		'P': {  'name':'password',
				'pubkey_type':'password',
				'compressed':False,
				'gen_method':None,
				'addr_fmt':None,
				'desc':'Password generated from MMGen seed'}
	}

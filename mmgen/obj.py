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
from string import hexdigits,ascii_letters,digits

def is_mmgen_seed_id(s): return SeedID(sid=s,on_fail='silent')
def is_mmgen_idx(s):     return AddrIdx(s,on_fail='silent')
def is_mmgen_id(s):      return MMGenID(s,on_fail='silent')
def is_coin_addr(s):     return CoinAddr(s,on_fail='silent')
def is_addrlist_id(s):   return AddrListID(s,on_fail='silent')
def is_tw_label(s):      return TwLabel(s,on_fail='silent')
def is_wif(s):           return WifKey(s,on_fail='silent')

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
	def init_fail(m,on_fail,silent=False):
		if silent: m = ''
		from mmgen.util import die,msg
		if on_fail == 'die': die(1,m)
		elif on_fail == 'return':
			if m: msg(m)
			return None # TODO: change to False
		elif on_fail == 'silent': return None # same here
		elif on_fail == 'raise':  raise ValueError,m

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
	min_coin_unit = Decimal('0.00000001')

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

class BCHAmt(BTCAmt):
	pass
class LTCAmt(BTCAmt):
	max_amt = 84000000

class CoinAddr(str,Hilite,InitErrors,MMGenObject):
	color = 'cyan'
	width = 35 # max len of testnet p2sh addr
	def __new__(cls,s,on_fail='die'):
		if type(s) == cls: return s
		cls.arg_chk(cls,on_fail)
		from mmgen.globalvars import g
		try:
			assert set(s) <= set(ascii_letters+digits),'contains non-ascii characters'
			me = str.__new__(cls,s)
			va = g.proto.verify_addr(s,return_dict=True)
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
		from mmgen.globalvars import g
		vn = g.proto.get_protocol_by_chain(chain).addr_ver_num
		if self.addr_fmt == 'p2sh' and 'p2sh2' in vn:
			return self[0] in vn['p2sh'][1] or self[0] in vn['p2sh2'][1]
		else:
			return self[0] in vn[self.addr_fmt][1]

	def is_in_tracking_wallet(self):
		from mmgen.rpc import rpc_init
		d = rpc_init().validateaddress(self)
		return d['iswatchonly'] and 'account' in d

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
			t = MMGenAddrType((ss[1],MMGenAddrType.dfl_mmtype)[len(ss)==2],on_fail='raise')
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
				assert set(s[4:]) <= set(ascii_letters+digits),'contains non-ascii characters'
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
class TwLabel(str,InitErrors,MMGenObject):
	def __new__(cls,s,on_fail='die'):
		if type(s) == cls: return s
		cls.arg_chk(cls,on_fail)
		try:
			ss = s.split(None,1)
			mmid = TwMMGenID(ss[0],on_fail='raise')
			comment = TwComment(ss[1] if len(ss) == 2 else '',on_fail='raise')
			me = str.__new__(cls,'{}{}'.format(mmid,' {}'.format(comment) if comment else ''))
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

class MMGenTxID(HexStr,Hilite,InitErrors):
	color = 'red'
	width = 6
	trunc_ok = False
	hexcase = 'upper'
	def __new__(cls,s,on_fail='die'):
		cls.arg_chk(cls,on_fail)
		try:
			ret = HexStr.__new__(cls,s,case=cls.hexcase,on_fail='raise')
			assert len(s) == cls.width,'Value is not {} characters wide'.format(cls.width)
			return ret
		except Exception as e:
			m = "{}\n{!r}: value cannot be converted to {}"
			return cls.init_fail(m.format(e[0],s,cls.__name__),on_fail)

class CoinTxID(MMGenTxID):
	color = 'purple'
	width = 64
	hexcase = 'lower'

class WifKey(str,Hilite,InitErrors):
	width = 53
	color = 'blue'
	def __new__(cls,s,on_fail='die'):
		if type(s) == cls: return s
		cls.arg_chk(cls,on_fail)
		try:
			assert set(s) <= set(ascii_letters+digits),'not an ascii string'
			from mmgen.globalvars import g
			if g.proto.wif2hex(s):
				return str.__new__(cls,s)
			raise ValueError,'failed verification'
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
	def __new__(cls,s=None,compressed=None,wif=None,on_fail='die'):

		if type(s) == cls: return s
		assert wif or (s and type(compressed) == bool),'Incorrect args for PrivKey()'
		cls.arg_chk(cls,on_fail)

		if wif:
			try:
				assert set(wif) <= set(ascii_letters+digits),'not an ascii string'
				from mmgen.globalvars import g
				w2h = g.proto.wif2hex(wif)
				assert w2h,"wif2hex() failed for wif key {!r}".format(wif)
				me = str.__new__(cls,w2h['hex'])
				me.compressed = w2h['compressed']
				me.wif = str.__new__(WifKey,wif) # check has been done
				return me
			except Exception as e:
				fs = "Value {!r} cannot be converted to WIF key ({})"
				return cls.init_fail(fs.format(wif,e[0]),on_fail)

		try:
			from binascii import hexlify
			assert len(s) == cls.width / 2,'Key length must be {}'.format(cls.width/2)
			me = str.__new__(cls,hexlify(s))
			me.compressed = compressed
			me.wif = me.towif()
			return me
		except Exception as e:
			fs = "Key={!r}\nCompressed={}\nValue pair cannot be converted to PrivKey ({!r})"
			return cls.init_fail(fs.format(s,compressed,e),on_fail)

	def towif(self):
		from mmgen.globalvars import g
		return WifKey(g.proto.hex2wif(self,compressed=self.compressed),on_fail='raise')

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
			from mmgen.util import capfirst
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

class MMGenAddrType(str,Hilite,InitErrors,MMGenObject):
	width = 1
	trunc_ok = False
	color = 'blue'
	mmtypes = { # 'name' is used to cook the seed, so it must never change!
		'L': {  'name':'legacy',
				'comp':False,
				'gen':'p2pkh',
				'fmt':'p2pkh',
				'desc':'Legacy uncompressed address'},
		'S': {  'name':'segwit',
				'comp':True,
				'gen':'segwit',
				'fmt':'p2sh',
				'desc':'Segwit P2SH-P2WPKH address' },
		'C': {  'name':'compressed',
				'comp':True,
				'gen':'p2pkh',
				'fmt':'p2pkh',
				'desc':'Compressed P2PKH address'}
	}
	dfl_mmtype = 'L'
	def __new__(cls,s,on_fail='die',errmsg=None):
		if type(s) == cls: return s
		cls.arg_chk(cls,on_fail)
		from mmgen.globalvars import g
		try:
			for k,v in cls.mmtypes.items():
				if s in (k,v['name']):
					if s == v['name']: s = k
					me = str.__new__(cls,s)
					assert me in g.proto.mmtypes + ('P',), (
						"'{}': invalid address type for {}".format(me,g.proto.__name__))
					me.name = v['name']
					me.compressed = v['comp']
					me.gen_method = v['gen']
					me.desc = v['desc']
					me.addr_fmt = v['fmt']
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
				'comp':False,
				'gen':None,
				'fmt':None,
				'desc':'Password generated from MMGen seed'}
	}

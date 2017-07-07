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
obj.py:  MMGen native classes
"""

from decimal import *
from mmgen.color import *
lvl = 0

class MMGenObject(object):

	# Pretty-print any object of type MMGenObject, recursing into sub-objects - WIP
	def pprint(self):  print self.pformat()
	def pformat(self,lvl=0):
		def do_list(out,e,lvl=0):
			add_spc = False
			if e and type(e[0]) not in (str,unicode):
				out.append('\n')
			for i in e:
				if hasattr(i,'pformat'):
					out.append('{:>{l}}{}'.format('',i.pformat(lvl=lvl+1),l=(lvl+1)*8))
				elif type(i) in (str,unicode):
					add_spc = True
					out.append(u' {}'.format(repr(i)))
				elif type(i) == list:
					out.append(u'{:>{l}}{:16}'.format('','<'+type(i).__name__+'>',l=(lvl*8)+4))
					do_list(out,i,lvl=lvl)
				else:
					out.append(u'{:>{l}}{:16} {}\n'.format('','<'+type(i).__name__+'>',repr(i),l=(lvl*8)+8))
			if not e: out.append('{}\n'.format(repr(e)))
			if add_spc: out.append('\n')
		out = []
		out.append(u'<{}>\n'.format(type(self).__name__))
		d = self.__dict__
		for k in d:
			e = getattr(self,k)
			if type(e) == list:
				out.append(u'{:>{l}}{:<10} {:16}'.format('',k,'<'+type(e).__name__+'>',l=(lvl*8)+4))
				do_list(out,e,lvl=lvl)
			elif hasattr(e,'pformat') and type(e) != type:
				out.append(u'{:>{l}}{:10} {}'.format('',k,e.pformat(lvl=lvl+1),l=(lvl*8)+4))
			else:
				out.append(u'{:>{l}}{:<10} {:16} {}\n'.format('',k,'<'+type(e).__name__+'>',repr(e),l=(lvl*8)+4))
		return ''.join(out)

# Descriptor: https://docs.python.org/2/howto/descriptor.html
class MMGenListItemAttr(object):
	def __init__(self,name,dtype):
		self.name = name
		self.dtype = dtype
	def __get__(self,instance,owner):
		return instance.__dict__[self.name]
	def __set__(self,instance,value):
#		if self.name == 'mmid': print repr(instance), repr(value) # DEBUG
		instance.__dict__[self.name] = globals()[self.dtype](value)
	def __delete__(self,instance):
		del instance.__dict__[self.name]

class MMGenListItem(MMGenObject):

	addr = MMGenListItemAttr('addr','BTCAddr')
	amt  = MMGenListItemAttr('amt','BTCAmt')
	mmid = MMGenListItemAttr('mmid','MMGenID')
	label = MMGenListItemAttr('label','MMGenAddrLabel')

	attrs = ()
	attrs_priv = ()
	attrs_reassign = 'label',

	def attr_error(self,arg):
		raise AttributeError, "'{}': invalid attribute for {}".format(arg,type(self).__name__)
	def set_error(self,attr,val):
		raise ValueError, \
			"'{}': attribute '{}' in instance of class '{}' cannot be reassigned".format(
				val,attr,type(self).__name__)

	attrs_base = ('attrs','attrs_priv','attrs_reassign','attrs_base','attr_error','set_error','__dict__','pformat')

	def __init__(self,*args,**kwargs):
		if args:
			raise ValueError, 'Non-keyword args not allowed'
		for k in kwargs:
			if kwargs[k] != None:
				setattr(self,k,kwargs[k])

	def __getattribute__(self,name):
		ga = object.__getattribute__
		if name in ga(self,'attrs') + ga(self,'attrs_priv') + ga(self,'attrs_base'):
			try:
				return ga(self,name)
			except:
				return None
		else:
			self.attr_error(name)

	def __setattr__(self,name,val):
		if name in (self.attrs + self.attrs_priv + self.attrs_base):
			if getattr(self,name) == None or name in self.attrs_reassign:
				object.__setattr__(self,name,val)
			else:
#				object.__setattr__(self,name,val) # DEBUG
				self.set_error(name,val)
		else:
			self.attr_error(name)

	def __delattr__(self,name):
		if name in (self.attrs + self.attrs_priv + self.attrs_base):
			try: # don't know why this is necessary
				object.__delattr__(self,name)
			except:
				pass
		else:
			self.attr_error(name)

class InitErrors(object):

	@staticmethod
	def arg_chk(cls,on_fail):
		assert on_fail in ('die','return','silent','raise'),"'on_fail' in class %s" % cls.__name__

	@staticmethod
	def init_fail(m,on_fail,silent=False):
		if silent: m = ''
		from mmgen.util import die,msg
		if on_fail == 'die':      die(1,m)
		elif on_fail == 'return':
			if m: msg(m)
			return None
		elif on_fail == 'silent': return None
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

class AddrIdxList(list,InitErrors):

	max_len = 1000000

	def __init__(self,fmt_str=None,idx_list=None,on_fail='die',sep=','):
		self.arg_chk(type(self),on_fail)
		assert fmt_str or idx_list
		if idx_list:
			# dies on failure
			return list.__init__(self,sorted(set([AddrIdx(i) for i in idx_list])))
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
				m = "'%s': too many decimal places in BTC amount" % num
			elif me > cls.max_amt:
				m = "'%s': BTC amount too large (>%s)" % (num,cls.max_amt)
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

class BTCAddr(str,Hilite,InitErrors):
	color = 'cyan'
	width = 34
	def __new__(cls,s,on_fail='die'):
		cls.arg_chk(cls,on_fail)
		me = str.__new__(cls,s)
		from mmgen.bitcoin import verify_addr
		if type(s) in (str,unicode,BTCAddr) and verify_addr(s):
			return me
		else:
			m = "'%s': value is not a Bitcoin address" % s
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
			from string import hexdigits
			if len(sid) == cls.width and set(sid) <= set(hexdigits.upper()):
				return str.__new__(cls,sid)

		m = "'%s': value cannot be converted to SeedID" % str(seed or sid)
		return cls.init_fail(m,on_fail)

class MMGenID(str,Hilite,InitErrors):

	color = 'orange'
	width = 0
	trunc_ok = False

	def __new__(cls,s,on_fail='die'):
		cls.arg_chk(cls,on_fail)
		s = str(s)
		if ':' in s:
			a,b = s.split(':',1)
			sid = SeedID(sid=a,on_fail='silent')
			if sid:
				idx = AddrIdx(b,on_fail='silent')
				if idx:
					return str.__new__(cls,'%s:%s' % (sid,idx))

		m = "'%s': value cannot be converted to MMGenID" % s
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
			elif cls.forbidden and any([ch in s for ch in cls.forbidden]):
				m = u"{} '{}' contains one of these forbidden symbols: '{}'".format(capfirst(cls.desc),s,
					"', '".join(cls.forbidden))
			else:
				return unicode.__new__(cls,s)
		return cls.init_fail((msg+'\n' if msg else '') + m,on_fail)

class MMGenWalletLabel(MMGenLabel):
	max_len = 48
	allowed = [unichr(i+32) for i in range(95)]
	desc = 'wallet label'

class MMGenAddrLabel(MMGenLabel):
	max_len = 32
	allowed = [unichr(i+32) for i in range(95)]
	desc = 'address label'

class MMGenTXLabel(MMGenLabel):
	max_len = 72
	desc = 'transaction label'

class MMGenPWIDString(MMGenLabel):
	max_len = 256
	min_len = 1
	desc = 'password ID string'
	forbidden = list(u' :/\\')

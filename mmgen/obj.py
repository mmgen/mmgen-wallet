#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2016 Philemon <mmgen-py@yandex.com>
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
obj.py:  The MMGenObject class and methods
"""

from decimal import *
from mmgen.color import *
lvl = 0

class MMGenObject(object):

	# Pretty-print any object of type MMGenObject, recursing into sub-objects
	def __str__(self):
		global lvl
		indent = lvl * '    '

		def fix_linebreaks(v,fixed_indent=None):
			if '\n' in v:
				i = indent+'    ' if fixed_indent == None else fixed_indent*' '
				return '\n'+i + v.replace('\n','\n'+i)
			else: return repr(v)

		def conv(v,col_w):
			vret = ''
			if type(v) in (str,unicode):
				from string import printable
				if not (set(list(v)) <= set(list(printable))):
					vret = repr(v)
				else:
					vret = fix_linebreaks(v,fixed_indent=0)
			elif type(v) in (int,long,BTCAmt):
				vret = str(v)
			elif type(v) == dict:
				sep = '\n{}{}'.format(indent,' '*4)
				cw = (max(len(k) for k in v) if v else 0) + 2
				t = sep.join(['{:<{w}}: {}'.format(
					repr(k),
	(fix_linebreaks(v[k],fixed_indent=0) if type(v[k]) == str else v[k]),
					w=cw)
				for k in sorted(v)])
				vret = '{' + sep + t + '\n' + indent + '}'
			elif type(v) in (list,tuple):
				sep = '\n{}{}'.format(indent,' '*4)
				t = ' '.join([repr(e) for e in sorted(v)])
				o,c = (('(',')'),('[',']'))[type(v)==list]
				vret = o + sep + t + '\n' + indent + c
			elif repr(v)[:14] == '<bound method ':
				vret = ' '.join(repr(v).split()[0:3]) + '>'
#				vret = repr(v)

			return vret or type(v)

		out = []
		def f(k): return k[:2] != '__'
		keys = filter(f, self.__dict__.keys())
		col_w = max(len(k) for k in keys) if keys else 1
		fs = '{}%-{}s: %s'.format(indent,col_w)

		methods = [k for k in keys if repr(getattr(self,k))[:14] == '<bound method ']

		def f(k): return repr(getattr(self,k))[:14] == '<bound method '
		methods = filter(f,keys)
		def f(k): return repr(getattr(self,k))[:7] == '<mmgen.'
		objects = filter(f,keys)
		other = list(set(keys) - set(methods) - set(objects))

		for k in sorted(methods) + sorted(other) + sorted(objects):
			val = getattr(self,k)
			if str(type(val))[:13] == "<class 'mmgen": # recurse into sub-objects
				out.append('\n%s%s (%s):' % (indent,k,type(val)))
				lvl += 1
				out.append(unicode(getattr(self,k))+'\n')
				lvl -= 1
			else:
				out.append(fs % (k, conv(val,col_w)))

		return repr(self) + '\n    ' + '\n    '.join(out)

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

	attrs_base = ('attrs','attrs_priv','attrs_reassign','attrs_base','attr_error','set_error','__dict__')

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
	def fmtc(cls,s,width=None,color=False,encl='',trunc_ok=None,center=False,nullrepl=''):
		if width == None: width = cls.width
		if trunc_ok == None: trunc_ok = cls.trunc_ok
		assert width > 0
		if s == '' and nullrepl:
			s,center = nullrepl,True
		if center: s = s.center(width)
		assert type(encl) is str and len(encl) in (0,2)
		a,b = list(encl) if encl else ('','')
		if trunc_ok and len(s) > width: s = s[:width]
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

class MMGenLabel(unicode,Hilite,InitErrors):

	color = 'pink'
	allowed = u''
	max_len = 0
	desc = 'label'

	def __new__(cls,s,on_fail='die',msg=None):
		cls.arg_chk(cls,on_fail)
		try:
			s = s.decode('utf8').strip()
		except:
			m = "'%s: value is not a valid UTF-8 string" % s
		else:
			if len(s) > cls.max_len:
				m = '%s too long (>%s symbols)' % (cls.desc.capitalize(),cls.max_len)
			elif cls.allowed and not set(list(s)).issubset(set(list(cls.allowed))):
				m = '%s contains non-permitted symbols: %s' % (cls.desc.capitalize(),
					' '.join(set(list(s)) - set(list(cls.allowed))))
			else:
				return unicode.__new__(cls,s)
		return cls.init_fail((msg+'\n' if msg else '') + m,on_fail)

class MMGenWalletLabel(MMGenLabel):
	max_len = 48
	allowed = [chr(i+32) for i in range(95)]
	desc = 'wallet label'

class MMGenAddrLabel(MMGenLabel):
	max_len = 32
	allowed = [chr(i+32) for i in range(95)]
	desc = 'address label'

class MMGenTXLabel(MMGenLabel):
	max_len = 72
	desc = 'transaction label'

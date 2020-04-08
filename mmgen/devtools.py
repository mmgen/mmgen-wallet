#!/usr/bin/env python3

class MMGenObject(object):
	'placeholder - overridden when testing'
	def immutable_attr_init_check(self): pass

import os
if os.getenv('MMGEN_DEBUG') or os.getenv('MMGEN_TEST_SUITE') or os.getenv('MMGEN_TRACEBACK'):

	import sys,re,traceback,json,pprint
	from decimal import Decimal
	from difflib import unified_diff

	def pmsg(*args,out=sys.stderr):
		d = args if len(args) > 1 else '' if not args else args[0]
		out.write(pprint.PrettyPrinter(indent=4).pformat(d) + '\n')
	def pdie(*args,exit_val=1,out=sys.stderr):
		pmsg(*args,out=out)
		sys.exit(exit_val)
	def pexit(*args,out=sys.stderr):
		pdie(*args,exit_val=0,out=out)

	def Pmsg(*args):
		pmsg(*args,out=sys.stdout)
	def Pdie(*args):
		pdie(*args,out=sys.stdout)
	def Pexit(*args):
		pexit(*args,out=sys.stdout)

	def print_stack_trace(message=None):
		tb1 = traceback.extract_stack()
		tb2 = [t for t in tb1 if t.filename[:1] != '<'][2:-2]
		sys.stderr.write('STACK TRACE {}:\n'.format(message or '(unnamed)'))
		fs = '    {}:{}: in {}:\n        {}\n'
		for t in tb2:
			fn = re.sub(r'^\./','',os.path.relpath(t.filename))
			func = t.name+'()' if t.name[-1] != '>' else t.name
			sys.stderr.write(fs.format(fn,t.lineno,func,t.line or '(none)'))

	class MMGenObject(object):

		# Pretty-print any object subclassed from MMGenObject, recursing into sub-objects - WIP
		def pmsg(self): print(self.pfmt())
		def pdie(self): print(self.pfmt()); sys.exit(0)
		def pfmt(self,lvl=0,id_list=[]):
			scalars = (str,int,float,Decimal)
			def do_list(out,e,lvl=0,is_dict=False):
				out.append('\n')
				for i in e:
					el = i if not is_dict else e[i]
					if is_dict:
						out.append('{s}{:<{l}}'.format(i,s=' '*(4*lvl+8),l=10,l2=8*(lvl+1)+8))
					if hasattr(el,'pfmt'):
						out.append('{:>{l}}{}'.format('',el.pfmt(
							lvl=lvl+1,id_list=id_list+[id(self)]),l=(lvl+1)*8))
					elif isinstance(el,scalars):
						if isList(e):
							out.append('{:>{l}}{:16}\n'.format('',repr(el),l=lvl*8))
						else:
							out.append(' {}'.format(repr(el)))
					elif isList(el) or isDict(el):
						indent = 1 if is_dict else lvl*8+4
						out.append('{:>{l}}{:16}'.format('','<'+type(el).__name__+'>',l=indent))
						if isList(el) and isinstance(el[0],scalars):
							out.append('\n')
						do_list(out,el,lvl=lvl+1,is_dict=isDict(el))
					else:
						out.append('{:>{l}}{:16} {}\n'.format(
							'','<'+type(el).__name__+'>',repr(el),l=(lvl*8)+8))
					out.append('\n')
				if not e: out.append('{}\n'.format(repr(e)))

			from collections import OrderedDict
			def isDict(obj):
				return isinstance(obj,dict)
			def isList(obj):
				return isinstance(obj,list)
			def isScalar(obj):
				return isinstance(obj,scalars)

			out = ['<{}>{}\n'.format(type(self).__name__,' '+repr(self) if isScalar(self) else '')]
			if id(self) in id_list:
				return out[-1].rstrip() + ' [RECURSION]\n'
			if isList(self) or isDict(self):
				do_list(out,self,lvl=lvl,is_dict=isDict(self))

			for k in self.__dict__:
				if k in ('_OrderedDict__root','_OrderedDict__map'): continue # excluded because of recursion
				e = getattr(self,k)
				if isList(e) or isDict(e):
					out.append('{:>{l}}{:<10} {:16}'.format('',k,'<'+type(e).__name__+'>',l=(lvl*8)+4))
					do_list(out,e,lvl=lvl,is_dict=isDict(e))
				elif hasattr(e,'pfmt') and type(e) != type:
					out.append('{:>{l}}{:10} {}'.format(
						'',k,e.pfmt(lvl=lvl+1,id_list=id_list+[id(self)]),l=(lvl*8)+4))
				else:
					out.append('{:>{l}}{:<10} {:16} {}\n'.format(
						'',k,'<'+type(e).__name__+'>',repr(e),l=(lvl*8)+4))

			import re
			return re.sub('\n+','\n',''.join(out))

		# Check that all immutables have been initialized.  Expensive, so do only when testing.
		def immutable_attr_init_check(self):
			from mmgen.globalvars import g
			if g.test_suite:
				from mmgen.util import rdie
				cls = type(self)
				for attrname in sorted({a for a in self.valid_attrs if a[0] != '_'}):
					for o in (cls,cls.__bases__[0]): # assume there's only one base class
						if attrname in o.__dict__:
							attr = o.__dict__[attrname]
							break
					else:
						rdie(3,'unable to find descriptor {}.{}'.format(cls.__name__,attrname))
					if type(attr).__name__ == 'ImmutableAttr':
						if attrname not in self.__dict__:
							fs = 'attribute {!r} of {} has not been initialized in constructor!'
							rdie(3,fs.format(attrname,cls.__name__))

	def print_diff(a,b,from_json=True):
		if from_json:
			a = json.dumps(json.loads(a),indent=4).split('\n') if a else []
			b = json.dumps(json.loads(b),indent=4).split('\n') if b else []
		else:
			a = a.split('\n')
			b = b.split('\n')
		sys.stderr.write('  DIFF:\n    {}\n'.format('\n    '.join(unified_diff(a,b))))

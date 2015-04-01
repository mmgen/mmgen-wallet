#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2015 Philemon <mmgen-py@yandex.com>
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
import mmgen.config as g
from mmgen.util import msgrepr_exit,msgrepr

lvl = 0

class MMGenObject(object):

	# Pretty-print any object of type MMGenObject, recursing into sub-objects
	def __str__(self):
		global lvl
		indent = lvl * "    "

		def fix_linebreaks(v,fixed_indent=None):
			if "\n" in v:
				i = indent+"    " if fixed_indent == None else fixed_indent*" "
				return "\n"+i + v.replace("\n","\n"+i)
			else: return repr(v)

		def conv(v,col_w):
			vret = ""
			if type(v) == str:
				if not (set(list(v)) <= set(list(g.printable))):
					vret = repr(v)
				else:
					vret = fix_linebreaks(v,fixed_indent=0)
			elif type(v) == int or type(v) == long:
				vret = str(v)
			elif type(v) == dict:
				sep = "\n{}{}".format(indent," "*4)
				cw = max(len(k) for k in v) + 2
				t = sep.join(["{:<{w}}: {}".format(
					repr(k),
	(fix_linebreaks(v[k],fixed_indent=0) if type(v[k]) == str else v[k]),
					w=cw)
				for k in sorted(v)])
				vret = "{" + sep + t + "\n" + indent + "}"
			elif type(v) in (list,tuple):
				sep = "\n{}{}".format(indent," "*4)
				t = " ".join([repr(e) for e in sorted(v)])
				o,c = ("[","]") if type(v) == list else ("(",")")
				vret = o + sep + t + "\n" + indent + c
			elif repr(v)[:14] == '<bound method ':
				vret = " ".join(repr(v).split()[0:3]) + ">"
#				vret = repr(v)

			return vret or type(v)

		out = []
		def f(k): return k[:2] != "__"
		keys = filter(f, dir(self))
		col_w = max(len(k) for k in keys)
		fs = "{}%-{}s: %s".format(indent,col_w)

  		methods = [k for k in keys if repr(getattr(self,k))[:14] == '<bound method ']

  		def f(k): return repr(getattr(self,k))[:14] == '<bound method '
  		methods = filter(f,keys)
  		def f(k): return repr(getattr(self,k))[:7] == '<mmgen.'
  		objects = filter(f,keys)
		other = list(set(keys) - set(methods) - set(objects))

		for k in sorted(methods) + sorted(other) + sorted(objects):
			val = getattr(self,k)
			if str(type(val))[:13] == "<class 'mmgen": # recurse into sub-objects
				out.append("\n%s%s (%s):" % (indent,k,repr(type(val))))
				lvl += 1
				out.append(str(getattr(self,k))+"\n")
				lvl -= 1
			else:
				out.append(fs % (k, conv(val,col_w)))
		return "\n".join(out)

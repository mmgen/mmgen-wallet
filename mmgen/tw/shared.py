#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
tw.shared: classes and functions shared by all tracking wallet classes
"""

from ..objmethods import Hilite,InitErrors,MMGenObject
from ..obj import TwComment
from ..addr import MMGenID

class TwMMGenID(str,Hilite,InitErrors,MMGenObject):
	color = 'orange'
	width = 0
	trunc_ok = False
	def __new__(cls,proto,id_str):
		if type(id_str) == cls:
			return id_str
		try:
			ret = addr = disp = MMGenID(proto,id_str)
			sort_key,idtype = (ret.sort_key,'mmgen')
		except Exception as e:
			try:
				coin,addr = id_str.split(':',1)
				assert coin == proto.base_coin.lower(),(
					f'not a string beginning with the prefix {proto.base_coin.lower()!r}:' )
				assert addr.isascii() and addr.isalnum(), 'not an ASCII alphanumeric string'
				ret,sort_key,idtype,disp = (id_str,'z_'+id_str,'non-mmgen','non-MMGen')
				addr = proto.coin_addr(addr)
			except Exception as e2:
				return cls.init_fail(e,id_str,e2=e2)

		me = str.__new__(cls,ret)
		me.obj = ret
		me.disp = disp
		me.addr = addr
		me.sort_key = sort_key
		me.type = idtype
		me.proto = proto
		return me

	@classmethod
	def fmtc(cls,twmmid,*args,**kwargs):
		return super().fmtc(twmmid.disp,*args,**kwargs)

# non-displaying container for TwMMGenID,TwComment
class TwLabel(str,InitErrors,MMGenObject):
	exc = 'BadTwLabel'
	passthru_excs = ('BadTwComment',)
	def __new__(cls,proto,text):
		if type(text) == cls:
			return text
		try:
			ts = text.split(None,1)
			mmid = TwMMGenID(proto,ts[0])
			comment = TwComment(ts[1] if len(ts) == 2 else '')
			me = str.__new__( cls, mmid + (' ' + comment if comment else '') )
			me.mmid = mmid
			me.comment = comment
			me.proto = proto
			return me
		except Exception as e:
			return cls.init_fail(e,text)

def get_tw_label(proto,s):
	"""
	raise an exception on a malformed comment, return None on an empty or invalid label
	"""
	try:
		return TwLabel(proto,s)
	except Exception as e:
		if type(e).__name__ == 'BadTwComment': # do it this way to avoid importing .exception
			raise
		else:
			return None

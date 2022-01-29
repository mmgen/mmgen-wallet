#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
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
tw: Tracking wallet dependency classes for the MMGen suite
"""

import time

from .exception import BadTwLabel,BadTwComment
from .objmethods import Hilite,InitErrors,MMGenObject
from .obj import TwComment
from .addr import MMGenID

# mixin class for TwUnspentOutputs,TwAddrList:
class TwCommon:

	age_fmts = ('confs','block','days','date','date_time')

	date_formatter = {
		'days':      lambda rpc,secs: (rpc.cur_date - secs) // 86400,
		'date':      lambda rpc,secs: '{}-{:02}-{:02}'.format(*time.gmtime(secs)[:3])[2:],
		'date_time': lambda rpc,secs: '{}-{:02}-{:02} {:02}:{:02}'.format(*time.gmtime(secs)[:5]),
	}

	def age_disp(self,o,age_fmt):
		if age_fmt == 'confs':
			return o.confs
		elif age_fmt == 'block':
			return self.rpc.blockcount - (o.confs - 1)
		else:
			return self.date_formatter[age_fmt](self.rpc,o.date)

	@staticmethod
	async def set_dates(rpc,us):
		if rpc.proto.base_proto != 'Bitcoin':
			return
		if us and us[0].date is None:
			# 'blocktime' differs from 'time', is same as getblockheader['time']
			dates = [o['blocktime'] for o in await rpc.gathered_call('gettransaction',[(o.txid,) for o in us])]
			for idx,o in enumerate(us):
				o.date = dates[idx]

class TwMMGenID(str,Hilite,InitErrors,MMGenObject):
	color = 'orange'
	width = 0
	trunc_ok = False
	def __new__(cls,proto,id_str):
		if type(id_str) == cls:
			return id_str
		ret = None
		try:
			ret = MMGenID(proto,id_str)
			sort_key,idtype = ret.sort_key,'mmgen'
		except Exception as e:
			try:
				assert id_str.split(':',1)[0] == proto.base_coin.lower(),(
					f'not a string beginning with the prefix {proto.base_coin.lower()!r}:' )
				assert id_str.isascii() and id_str[4:].isalnum(), 'not an ASCII alphanumeric string'
				assert len(id_str) > 4,'not more that four characters long'
				ret,sort_key,idtype = str(id_str),'z_'+id_str,'non-mmgen'
			except Exception as e2:
				return cls.init_fail(e,id_str,e2=e2)

		me = str.__new__(cls,ret)
		me.obj = ret
		me.sort_key = sort_key
		me.type = idtype
		me.proto = proto
		return me

# non-displaying container for TwMMGenID,TwComment
class TwLabel(str,InitErrors,MMGenObject):
	exc = BadTwLabel
	passthru_excs = (BadTwComment,)
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
	except BadTwComment:
		raise
	except Exception as e:
#		print(e)
		return None

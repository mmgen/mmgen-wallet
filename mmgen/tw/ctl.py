#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
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
tw.ctl: Tracking wallet control class for the MMGen suite
"""

from collections import namedtuple

from ..util import msg, msg_r, ymsg, suf, die
from ..base_obj import AsyncInit
from ..objmethods import MMGenObject
from ..obj import TwComment, get_obj
from ..addr import CoinAddr, is_mmgen_id, is_coin_addr
from ..rpc import rpc_init
from .shared import TwMMGenID, TwLabel

twmmid_addr_pair = namedtuple('addr_info', ['twmmid', 'coinaddr'])
label_addr_pair = namedtuple('label_addr_pair', ['label', 'coinaddr'])

# decorator for TwCtl
def write_mode(orig_func):
	def f(self, *args, **kwargs):
		if self.mode != 'w':
			die(1, '{} opened in read-only mode: cannot execute method {}()'.format(
				type(self).__name__,
				locals()['orig_func'].__name__
			))
		return orig_func(self, *args, **kwargs)
	return f

class TwCtl(MMGenObject, metaclass=AsyncInit):

	caps = ('rescan', 'batch')
	data_key = 'addresses'
	importing = False
	use_cached_balances = False

	def __new__(cls, cfg, proto, *args, **kwargs):
		return MMGenObject.__new__(
			proto.base_proto_subclass(cls, 'tw.ctl', is_token=kwargs.get('token_addr')))

	async def __init__(
			self,
			cfg,
			proto,
			*,
			mode              = 'r',
			token_addr        = None,
			no_rpc            = False,
			rpc_ignore_wallet = False):

		assert mode in ('r', 'w', 'i'), f"{mode!r}: wallet mode must be 'r', 'w' or 'i'"
		if mode == 'i':
			self.importing = True
			mode = 'w'

		self.cfg = cfg
		self.proto = proto
		self.mode = mode
		self.desc = self.base_desc = f'{self.proto.name} tracking wallet'

		if not no_rpc:
			self.rpc = await rpc_init(cfg, proto, ignore_wallet=rpc_ignore_wallet)

	async def resolve_address(self, addrspec):

		twmmid, coinaddr = (None, None)

		pairs = await self.get_label_addr_pairs()

		if is_coin_addr(self.proto, addrspec):
			coinaddr = get_obj(CoinAddr, proto=self.proto, addr=addrspec)
			pair_data = [e for e in pairs if e.coinaddr == coinaddr]
		elif is_mmgen_id(self.proto, addrspec):
			twmmid = TwMMGenID(self.proto, addrspec)
			pair_data = [e for e in pairs if e.label.mmid == twmmid]
		else:
			msg(f'{addrspec!r}: invalid address for this network')
			return None

		if not pair_data:
			msg('{a} address {b!r} not found in tracking wallet'.format(
				a = 'MMGen' if twmmid else 'Coin',
				b = twmmid or coinaddr))
			return None

		return twmmid_addr_pair(
			twmmid or pair_data[0].label.mmid,
			coinaddr or pair_data[0].coinaddr)

	# returns on failure
	@write_mode
	async def set_comment(
			self,
			addrspec,
			comment      = '',
			*,
			trusted_pair = None,
			silent       = False):

		res = twmmid_addr_pair(*trusted_pair) if trusted_pair else await self.resolve_address(addrspec)

		if not res:
			return False

		comment = get_obj(TwComment, s=comment)

		if comment is False:
			return False

		lbl = get_obj(
			TwLabel,
			proto = self.proto,
			text = res.twmmid + (' ' + comment if comment else ''))

		if lbl is False:
			return False

		if await self.set_label(res.coinaddr, lbl):
			if not silent:
				desc = '{t} address {a} in tracking wallet'.format(
					t = res.twmmid.type.replace('mmgen', 'MMGen'),
					a = res.twmmid.addr.hl() if res.twmmid.type == 'mmgen' else
						res.twmmid.addr.hl(res.twmmid.addr.view_pref))
				msg(
					'Added label {} to {}'.format(comment.hl2(encl='‘’'), desc) if comment else
					'Removed label from {}'.format(desc))
			return comment
		else:
			if not silent:
				msg('Label could not be {}'.format('added' if comment else 'removed'))
			return False

	def check_import_mmid(self, addr, old_mmid, new_mmid):
		'returns True if mmid needs update, None otherwise'
		if new_mmid != old_mmid:
			if old_mmid.endswith(':' + addr):
				ymsg(f'Warning: address {new_mmid} was previously imported as non-MMGen!')
				return True
			else:
				fs = (
					'attempting to import MMGen address {a!r} ({b}) as non-MMGen!'
						if new_mmid.endswith(':' + addr) else
					'imported MMGen ID {b!r} does not match tracking wallet MMGen ID {a!r}!')
				die(2, fs.format(a=old_mmid, b=new_mmid))

	async def import_address_common(self, data, *, batch=False, gather=False):

		async def do_import(address, comment, message):
			try:
				res = await self.import_address(address, label=comment)
				self.cfg._util.qmsg(message)
				return res
			except Exception as e:
				die(2, f'\nImport of address {address!r} failed: {e.args[0]!r}')

		_d = namedtuple('formatted_import_data', data[0]._fields + ('mmid_disp',))
		pfx = self.proto.base_coin.lower() + ':'
		fdata = [_d(*d, 'non-MMGen' if d.twmmid.startswith(pfx) else d.twmmid) for d in data]

		fs = '{:%s}: {:%s} {:%s} - OK' % (
			len(str(len(fdata))) * 2 + 1,
			max(len(d.addr) for d in fdata),
			max(len(d.mmid_disp) for d in fdata) + 2
		)

		nAddrs = len(data)
		out = [( # create list, not generator, so we know data is valid before starting import
				CoinAddr(self.proto, d.addr),
				TwLabel(self.proto, d.twmmid + (f' {d.comment}' if d.comment else '')),
				fs.format(f'{n}/{nAddrs}', d.addr, f'({d.mmid_disp})')
			) for n, d in enumerate(fdata, 1)]

		if batch:
			msg_r(f'Batch importing {len(out)} address{suf(data, "es")}...')
			ret = await self.batch_import_address((a, b, False) for a, b, c in out)
			msg(f'done\n{len(ret)} addresses imported')
		else:
			if gather: # this seems to provide little performance benefit
				import asyncio
				await asyncio.gather(*(do_import(*d) for d in out))
			else:
				for d in out:
					await do_import(*d)
			msg('Address import completed OK')

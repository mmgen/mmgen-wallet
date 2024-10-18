#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
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
tool.wallet: Wallet routines for the 'mmgen-tool' utility
"""

from .common import tool_cmd_base

from ..subseed import SubSeedList
from ..seedsplit import MasterShareIdx
from ..wallet import Wallet

class tool_cmd(tool_cmd_base):
	"key, address or subseed generation from an MMGen wallet"

	def __init__(self, cfg, cmdname=None, proto=None, mmtype=None):
		self.need_proto = cmdname in ('gen_key', 'gen_addr')
		super().__init__(cfg, cmdname=cmdname, proto=proto, mmtype=mmtype)

	def _get_seed_file(self, wallet):
		from ..fileutil import get_seed_file
		return get_seed_file(
			cfg     = self.cfg,
			wallets = [wallet] if wallet else [],
			nargs   = 1)

	def get_subseed(self, subseed_idx: str, wallet=''):
		"get the Seed ID of a single subseed by Subseed Index for default or specified wallet"
		self.cfg._set_quiet(True)
		return Wallet(self.cfg, self._get_seed_file(wallet)).seed.subseed(subseed_idx).sid

	def get_subseed_by_seed_id(self, seed_id: str, wallet='', last_idx=SubSeedList.dfl_len):
		"get the Subseed Index of a single subseed by Seed ID for default or specified wallet"
		self.cfg._set_quiet(True)
		ret = Wallet(self.cfg, self._get_seed_file(wallet)).seed.subseed_by_seed_id(seed_id, last_idx)
		return ret.ss_idx if ret else None

	def list_subseeds(self, subseed_idx_range: str, wallet=''):
		"list a range of subseed Seed IDs for default or specified wallet"
		self.cfg._set_quiet(True)
		from ..subseed import SubSeedIdxRange
		return Wallet(self.cfg, self._get_seed_file(wallet)).seed.subseeds.format(
			*SubSeedIdxRange(subseed_idx_range))

	def list_shares(self,
			share_count: int,
			id_str = 'default',
			master_share: f'(min:1, max:{MasterShareIdx.max_val}, 0=no master share)' = 0,
			wallet = ''):
		"list the Seed IDs of the shares resulting from a split of default or specified wallet"
		self.cfg._set_quiet(True)
		return Wallet(self.cfg, self._get_seed_file(wallet)).seed.split(
			share_count, id_str, master_share).format()

	def gen_key(self, mmgen_addr: str, wallet=''):
		"generate a single WIF key for specified MMGen address from default or specified wallet"
		return self._gen_keyaddr(mmgen_addr, 'wif', wallet)

	def gen_addr(self, mmgen_addr: str, wallet=''):
		"generate a single MMGen address from default or specified wallet"
		return self._gen_keyaddr(mmgen_addr, 'addr', wallet)

	def _gen_keyaddr(self, mmgen_addr, target, wallet=''):
		from ..addr import MMGenID
		from ..addrlist import AddrList, AddrIdxList

		addr = MMGenID(self.proto, mmgen_addr)
		self.cfg._set_quiet(True)
		ss = Wallet(self.cfg, self._get_seed_file(wallet))

		if ss.seed.sid != addr.sid:
			from ..util import die
			die(1, f'Seed ID of requested address ({addr.sid}) does not match wallet ({ss.seed.sid})')

		d = AddrList(
			cfg       = self.cfg,
			proto     = self.proto,
			seed      = ss.seed,
			addr_idxs = AddrIdxList(str(addr.idx)),
			mmtype    = addr.mmtype,
			skip_chksum = True).data[0]

		return {'wif': d.sec.wif, 'addr': d.addr}[target]

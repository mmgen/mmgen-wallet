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
tool/wallet.py: Wallet routines for the 'mmgen-tool' utility
"""

from .common import tool_cmd_base

from ..opts import opt
from ..fileutil import get_seed_file
from ..subseed import SubSeedList
from ..seedsplit import MasterShareIdx
from ..wallet import Wallet

class tool_cmd(tool_cmd_base):
	"key, address or subseed generation from an MMGen wallet"

	def __init__(self,proto=None,mmtype=None):
		if proto:
			self.proto = proto
		else:
			from ..protocol import init_proto_from_opts
			self.proto = init_proto_from_opts()

	def get_subseed(self,subseed_idx:str,wallet=''):
		"get the Seed ID of a single subseed by Subseed Index for default or specified wallet"
		opt.quiet = True
		sf = get_seed_file([wallet] if wallet else [],1)
		return Wallet(sf).seed.subseed(subseed_idx).sid

	def get_subseed_by_seed_id(self,seed_id:str,wallet='',last_idx=SubSeedList.dfl_len):
		"get the Subseed Index of a single subseed by Seed ID for default or specified wallet"
		opt.quiet = True
		sf = get_seed_file([wallet] if wallet else [],1)
		ret = Wallet(sf).seed.subseed_by_seed_id( seed_id, last_idx )
		return ret.ss_idx if ret else None

	def list_subseeds(self,subseed_idx_range:str,wallet=''):
		"list a range of subseed Seed IDs for default or specified wallet"
		opt.quiet = True
		sf = get_seed_file([wallet] if wallet else [],1)
		from ..subseed import SubSeedIdxRange
		return Wallet(sf).seed.subseeds.format( *SubSeedIdxRange(subseed_idx_range) )

	def list_shares(self,
			share_count: int,
			id_str = 'default',
			master_share: f'(min:1, max:{MasterShareIdx.max_val}, 0=no master share)' = 0,
			wallet = '' ):
		"list the Seed IDs of the shares resulting from a split of default or specified wallet"
		opt.quiet = True
		sf = get_seed_file([wallet] if wallet else [],1)
		return Wallet(sf).seed.split( share_count, id_str, master_share ).format()

	def gen_key(self,mmgen_addr:str,wallet=''):
		"generate a single MMGen WIF key from default or specified wallet"
		return self.gen_addr( mmgen_addr, wallet, target='wif' )

	def gen_addr(self,mmgen_addr:str,wallet='',target='addr'):
		"generate a single MMGen address from default or specified wallet"
		from ..addr import MMGenID
		from ..addrlist import AddrList,AddrIdxList
		addr = MMGenID( self.proto, mmgen_addr )
		opt.quiet = True
		sf = get_seed_file([wallet] if wallet else [],1)
		ss = Wallet(sf)
		if ss.seed.sid != addr.sid:
			from ..util import die
			die(1,f'Seed ID of requested address ({addr.sid}) does not match wallet ({ss.seed.sid})')
		d = AddrList(
			proto     = self.proto,
			seed      = ss.seed,
			addr_idxs = AddrIdxList(str(addr.idx)),
			mmtype    = addr.mmtype ).data[0]
		return d.sec.wif if target == 'wif' else d.addr

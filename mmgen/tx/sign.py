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
tx.sign: Sign a transaction generated by 'mmgen-txcreate'
"""

from ..common import *
from ..obj import MMGenList
from ..addr import MMGenAddrType
from ..addrlist import AddrIdxList,KeyAddrList
from ..wallet import Wallet,get_wallet_extensions,get_wallet_cls

saved_seeds = {}

def get_seed_for_seed_id(sid,infiles,saved_seeds):

	if sid in saved_seeds:
		return saved_seeds[sid]

	subseeds_checked = False
	while True:
		if infiles:
			seed = Wallet(infiles.pop(0),ignore_in_fmt=True).seed
		elif subseeds_checked == False:
			seed = saved_seeds[list(saved_seeds)[0]].subseed_by_seed_id(sid,print_msg=True)
			subseeds_checked = True
			if not seed: continue
		elif opt.in_fmt:
			qmsg(f'Need seed data for Seed ID {sid}')
			seed = Wallet().seed
			msg(f'User input produced Seed ID {seed.sid}')
			if not seed.sid == sid: # TODO: add test
				seed = seed.subseed_by_seed_id(sid,print_msg=True)

		if seed:
			saved_seeds[seed.sid] = seed
			if seed.sid == sid:
				return seed
		else:
			die(2,f'ERROR: No seed source found for Seed ID: {sid}')

def generate_kals_for_mmgen_addrs(need_keys,infiles,saved_seeds,proto):
	mmids = [e.mmid for e in need_keys]
	sids = remove_dups((i.sid for i in mmids),quiet=True)
	vmsg(f"Need seed{suf(sids)}: {' '.join(sids)}")
	def gen_kals():
		for sid in sids:
			# Returns only if seed is found
			seed = get_seed_for_seed_id(sid,infiles,saved_seeds)
			for id_str in MMGenAddrType.mmtypes:
				idx_list = [i.idx for i in mmids if i.sid == sid and i.mmtype == id_str]
				if idx_list:
					yield KeyAddrList(
						proto     = proto,
						seed      = seed,
						addr_idxs = AddrIdxList(idx_list=idx_list),
						mmtype    = MMGenAddrType(proto,id_str),
						skip_chksum = True )
	return MMGenList(gen_kals())

def add_keys(tx,src,infiles=None,saved_seeds=None,keyaddr_list=None):
	need_keys = [e for e in getattr(tx,src) if e.mmid and not e.have_wif]
	if not need_keys:
		return []
	desc,src_desc = (
		('key-address file','From key-address file:') if keyaddr_list else
		('seed(s)','Generated from seed:') )
	qmsg(f'Checking {g.proj_name} -> {tx.proto.coin} address mappings for {src} (from {desc})')
	d = (
		MMGenList([keyaddr_list]) if keyaddr_list else
		generate_kals_for_mmgen_addrs(need_keys,infiles,saved_seeds,tx.proto) )
	new_keys = []
	for e in need_keys:
		for kal in d:
			for f in kal.data:
				mmid = f'{kal.al_id}:{f.idx}'
				if mmid == e.mmid:
					if f.addr == e.addr:
						e.have_wif = True
						if src == 'inputs':
							new_keys.append(f)
					else:
						die(3,fmt(f"""
							{g.proj_name} -> {tx.proto.coin} address mappings differ!
							{{src_desc:<23}} {{mmid}} -> {{f.addr}}
							{{'tx file:':<23}} {{e.mmid}} -> {{e.addr}}
							""").strip())
	if new_keys:
		vmsg(f'Added {len(new_keys)} wif key{suf(new_keys)} from {desc}')
	return new_keys

def _pop_matching_fns(args,cmplist): # strips found args
	return list(reversed([args.pop(args.index(a)) for a in reversed(args) if get_extension(a) in cmplist]))

def get_tx_files(opt,args):
	from .unsigned import Unsigned
	ret = _pop_matching_fns(args,[Unsigned.ext])
	if not ret:
		die(1,'You must specify a raw transaction file!')
	return ret

def get_seed_files(opt,args):
	# favor unencrypted seed sources first, as they don't require passwords
	ret = _pop_matching_fns( args, get_wallet_extensions('unenc') )
	from ..filename import find_file_in_dir
	wf = find_file_in_dir(get_wallet_cls('mmgen'),g.data_dir) # Make this the first encrypted ss in the list
	if wf:
		ret.append(wf)
	ret += _pop_matching_fns( args, get_wallet_extensions('enc') )
	if not (ret or opt.mmgen_keys_from_file or opt.keys_from_file): # or opt.use_wallet_dat
		die(1,'You must specify a seed or key source!')
	return ret

def get_keyaddrlist(proto,opt):
	if opt.mmgen_keys_from_file:
		return KeyAddrList(proto,opt.mmgen_keys_from_file)
	return None

def get_keylist(proto,opt):
	if opt.keys_from_file:
		from ..fileutil import get_lines_from_file
		return get_lines_from_file(opt.keys_from_file,'key-address data',trim_comments=True)
	return None

async def txsign(tx,seed_files,kl,kal,tx_num_str=''):

	keys = MMGenList() # list of AddrListEntry objects
	non_mmaddrs = tx.get_non_mmaddrs('inputs')

	if non_mmaddrs:
		tx.check_non_mmgen_inputs(caller='txsign',non_mmaddrs=non_mmaddrs)
		tmp = KeyAddrList(
			proto = tx.proto,
			addrlist = non_mmaddrs,
			skip_chksum = True )
		if kl:
			tmp.add_wifs(kl)
		missing = tmp.list_missing('sec')
		if missing:
			sep = '\n    '
			die(2,'ERROR: a key file must be supplied for the following non-{} address{}:{}'.format(
				g.proj_name,
				suf(missing,'es'),
				sep + sep.join(missing) ))
		keys += tmp.data

	if opt.mmgen_keys_from_file:
		keys += add_keys(tx,'inputs',keyaddr_list=kal)
		add_keys(tx,'outputs',keyaddr_list=kal)

	keys += add_keys(tx,'inputs',seed_files,saved_seeds)
	add_keys(tx,'outputs',seed_files,saved_seeds)

	# this (boolean) attr isn't needed in transaction file
	tx.delete_attrs('inputs','have_wif')
	tx.delete_attrs('outputs','have_wif')

	extra_sids = remove_dups(
		(s for s in saved_seeds if s not in tx.get_sids('inputs') + tx.get_sids('outputs')),
		quiet = True )

	if extra_sids:
		msg(f"Unused Seed ID{suf(extra_sids)}: {' '.join(extra_sids)}")

	return await tx.sign(tx_num_str,keys) # returns signed TX object or False
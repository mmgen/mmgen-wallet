#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
tx.keys: transaction keys class for the MMGen suite
"""

from ..cfg import gc
from ..util import msg, suf, fmt, die, remove_dups, get_extension
from ..addr import MMGenAddrType
from ..addrlist import AddrIdxList, KeyAddrList
from ..wallet import Wallet, get_wallet_extensions, get_wallet_cls

def _pop_matching_fns(args, cmplist): # strips found args
	return list(reversed(
		[args.pop(args.index(a)) for a in reversed(args) if get_extension(a) in cmplist]))

def pop_txfiles(cfg):
	from .unsigned import Unsigned, AutomountUnsigned
	ext = (AutomountUnsigned if cfg.autosign else Unsigned).ext
	ret = _pop_matching_fns(cfg._args, [ext])
	if not ret:
		die(1, f'You must specify a raw transaction file with extension ‘.{ext}’')
	return ret

def pop_seedfiles(cfg, *, ignore_dfl_wallet=False, empty_ok=False):
	# favor unencrypted seed sources first, as they don't require passwords
	ret = _pop_matching_fns(cfg._args, get_wallet_extensions('unenc'))
	from ..filename import find_file_in_dir
	if not ignore_dfl_wallet: # Make this the first encrypted ss in the list
		if wf := find_file_in_dir(get_wallet_cls('mmgen'), cfg.data_dir):
			ret.append(wf)
	ret += _pop_matching_fns(cfg._args, get_wallet_extensions('enc'))
	if not (ret
			or empty_ok
			or cfg.mmgen_keys_from_file
			or cfg.keys_from_file):
		die(1, 'You must specify a seed or key source!')
	return ret

def get_keylist(cfg):
	if cfg.keys_from_file:
		from ..fileutil import get_lines_from_file
		return get_lines_from_file(
			cfg,
			cfg.keys_from_file,
			desc = 'key-address data',
			trim_comments = True)

def get_keyaddrlist(cfg, proto):
	if cfg.mmgen_keys_from_file:
		return KeyAddrList(cfg, proto, infile=cfg.mmgen_keys_from_file)

class TxKeys:
	"""
	produce a list of keys to be used for transaction signing

	Keys are taken from a key-address list and/or flat key list, and/or generated
	from provided seed sources.  Seed sources are searched for subseeds to allow
	signing of inputs with subseed addresses by parent seeds.

	In addition, MMGenID-to-address mappings are verified for output addresses, as
	well as the swap destination address, if applicable.  For this reason, seeds or
	key-address files for all MMGen addresses involved in the transaction must be
	provided.

	Verification of the swap memo against TX metadata is also performed.
	"""
	def __init__(
			self,
			cfg,
			tx,
			*,
			seedfiles   = None,
			keylist     = None,
			keyaddrlist = None,
			passwdfile  = None,
			autosign    = False):
		self.cfg         = cfg
		self.tx          = tx
		self.seedfiles   = seedfiles or pop_seedfiles(cfg)
		self.keylist     = keylist if autosign else keylist or get_keylist(cfg)
		self.keyaddrlist = keyaddrlist if autosign else keyaddrlist or get_keyaddrlist(cfg, tx.proto)
		self.passwdfile  = passwdfile
		self.autosign    = autosign
		self.saved_seeds = {}

	def get_keys_for_non_mmgen_inputs(self):
		err_fs = 'ERROR: a key file must be supplied for the following non-{} address{}:{}'
		sep = '\n    '
		if addrs := self.tx.get_non_mmaddrs('inputs'):
			self.tx.check_non_mmgen_inputs(
				caller = 'autosign' if self.autosign and self.keylist else 'txsign',
				non_mmaddrs = addrs)
			kal = KeyAddrList(
				cfg         = self.cfg,
				proto       = self.tx.proto,
				addrlist    = addrs,
				skip_chksum = True)
			if self.keylist:
				kal.add_wifs(self.keylist)
			if missing := kal.list_missing('sec'):
				die(2, err_fs.format(gc.proj_name, suf(missing, 'es'), sep + sep.join(missing)))
			return kal.data
		else:
			return []

	def get_seed_for_seed_id(self, sid):

		if sid in self.saved_seeds:
			return self.saved_seeds[sid]

		subseeds_checked = False
		seed = None

		while True:
			if self.seedfiles:
				seed = Wallet(
					self.cfg,
					fn = self.seedfiles.pop(0),
					ignore_in_fmt = True,
					passwd_file = self.passwdfile).seed
			elif self.saved_seeds and subseeds_checked is False:
				seed = self.saved_seeds[list(self.saved_seeds)[0]].subseed_by_seed_id(sid, print_msg=True)
				subseeds_checked = True
				if not seed:
					continue
			elif self.cfg.in_fmt:
				self.cfg._util.qmsg(f'Need seed data for Seed ID {sid}')
				seed = Wallet(self.cfg, passwd_file=self.passwdfile).seed
				msg(f'User input produced Seed ID {seed.sid}')
				if not seed.sid == sid: # TODO: add test
					seed = seed.subseed_by_seed_id(sid, print_msg=True)

			if seed:
				self.saved_seeds[seed.sid] = seed
				if seed.sid == sid:
					return seed
			else:
				die(2, f'ERROR: No seed source found for Seed ID: {sid}')

	def generate_kals_for_mmgen_addrs(self, need_keys, proto):
		mmids = [e.mmid for e in need_keys]
		sids = remove_dups((i.sid for i in mmids), quiet=True)
		self.cfg._util.vmsg('Need seed{}: {}'.format(suf(sids), ' '.join(sids)))
		for sid in sids:
			seed = self.get_seed_for_seed_id(sid) # raises exception if seed not found
			for id_str in MMGenAddrType.mmtypes:
				idx_list = [i.idx for i in mmids if i.sid == sid and i.mmtype == id_str]
				if idx_list:
					yield KeyAddrList(
						cfg         = self.cfg,
						proto       = proto,
						seed        = seed,
						addr_idxs   = AddrIdxList(idx_list=idx_list),
						mmtype      = MMGenAddrType(proto, id_str),
						skip_chksum = True)

	def add_keys(self, src, io_list, *, from_keyaddrlist=False):

		if not (need_keys := [e for e in io_list if e.mmid and not e.have_wif]):
			return []

		proto = need_keys[0].proto

		if from_keyaddrlist:
			desc = 'key-address file'
			err_desc = 'From key-address file:'
			kals = tuple([self.keyaddrlist])
		else:
			desc = 'seed(s)'
			err_desc = 'Generated from seed:'
			kals = tuple(self.generate_kals_for_mmgen_addrs(need_keys, proto))

		self.cfg._util.qmsg(
			f'Checking {gc.proj_name} -> {proto.coin} address mappings for {src} (from {desc})')

		def gen_keys():
			for e in need_keys:
				for kal in kals:
					for f in kal.data:
						if mmid := f'{kal.al_id}:{f.idx}' == e.mmid:
							if f.addr == e.addr:
								e.have_wif = True
								if src == 'inputs':
									yield f
							else:
								die(3, fmt(f"""
									{gc.proj_name} -> {proto.coin} address mappings differ!
									{err_desc:<23} {mmid} -> {f.addr}
									{'tx file:':<23} {e.mmid} -> {e.addr}
									""").strip())

		if new_keys := list(gen_keys()):
			self.cfg._util.vmsg(f'Added {len(new_keys)} wif key{suf(new_keys)} from {desc}')

		return new_keys

	@property
	def keys(self):
		"""
		produce a list of signing keys and perform checks on output and swap destination
		addresses
		"""
		ret = self.get_keys_for_non_mmgen_inputs()
		memo_output = self.tx.check_swap_memo() # do this for non-swap transactions too!

		if self.keyaddrlist:
			ret += self.add_keys('inputs', self.tx.inputs, from_keyaddrlist=True)
			self.add_keys('outputs', self.tx.outputs, from_keyaddrlist=True)
			if memo_output:
				self.add_keys('swap destination address', [memo_output], from_keyaddrlist=True)

		ret += self.add_keys('inputs', self.tx.inputs)
		self.add_keys('outputs', self.tx.outputs)
		if memo_output:
			self.add_keys('swap destination address', [memo_output])

		# this (boolean) attr isn't needed in transaction file
		self.tx.delete_attrs('inputs', 'have_wif')
		self.tx.delete_attrs('outputs', 'have_wif')

		if extra_sids := remove_dups(
				(s for s in self.saved_seeds
					if s not in self.tx.get_sids('inputs') + self.tx.get_sids('outputs')),
				quiet = True):
			msg('Unused Seed ID{}: {}'.format(suf(extra_sids), ' '.join(extra_sids)))

		return ret

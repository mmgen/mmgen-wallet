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
msg: base message signing classes
"""

import os, importlib, json
from .cfg import gc
from .objmethods import MMGenObject, HiliteStr, InitErrors
from .util import msg, die, make_chksum_6, fmt_list, remove_dups
from .color import red, orange, grnbg
from .protocol import init_proto
from .fileutil import get_data_from_file, write_data_to_file
from .addr import MMGenID, CoinAddr

class MMGenIDRange(HiliteStr, InitErrors, MMGenObject):
	"""
	closely based on MMGenID
	"""
	color = 'orange'
	width = 0
	trunc_ok = False
	def __new__(cls, proto, id_str):
		from .addrlist import AddrIdxList
		from .addr import AddrListID
		from .seed import SeedID
		try:
			match id_str.split(':'):
				case [sid, t, fmt_str]:
					assert t in proto.mmtypes, f'{t}: invalid address type for {proto.cls_name}'
					mmtype = proto.addr_type(t)
				case [sid, fmt_str]:
					mmtype = proto.addr_type(proto.dfl_mmtype)
				case _:
					raise ValueError('not 2 or 3 colon-separated items')
			me = str.__new__(cls, f'{sid}:{mmtype}:{fmt_str}')
			me.sid = SeedID(sid=sid)
			me.idxlist = AddrIdxList(fmt_str=fmt_str)
			me.mmtype = mmtype
			me.al_id = str.__new__(AddrListID, me.sid + ':' + me.mmtype) # checks already done
			me.proto = proto
			return me
		except Exception as e:
			return cls.init_fail(e, id_str)

class coin_msg:

	class base(MMGenObject):

		ext = 'rawmsg.json'
		signed = False
		chksum_keys = ('addrlists', 'message', 'msghash_type', 'network')

		@property
		def desc(self):
			return ('signed' if self.signed else 'unsigned') + ' message data'

		@property
		def chksum(self):
			return make_chksum_6(
				json.dumps(
					{k: self.data[k] for k in self.chksum_keys},
					sort_keys = True,
					separators = (',', ':')
			))

		@property
		def filename_stem(self):
			coin, network = self.data['network'].split('_')
			return '{}[{}]{}'.format(
				self.chksum.upper(),
				coin.upper(),
				('' if network == 'mainnet' else '.'+network))

		@property
		def filename(self):
			return f'{self.filename_stem}.{self.ext}'

		@property
		def signed_filename(self):
			return f'{self.filename_stem}.{coin_msg.signed.ext}'

		@staticmethod
		def get_proto_from_file(cfg, filename):
			data = json.loads(get_data_from_file(cfg, filename))
			network_id = data['metadata']['network'] if 'metadata' in data else data['network'].lower()
			coin, network = network_id.split('_')
			return init_proto(cfg=cfg, coin=coin, network=network)

		def write_to_file(self, *, outdir=None, ask_overwrite=False):
			data = {
				'id': f'{gc.proj_name} {self.desc}',
				'metadata': self.data,
				'signatures': self.sigs}
			write_data_to_file(
				cfg           = self.cfg,
				outfile       = os.path.join(outdir or '', self.filename),
				data          = json.dumps(data, sort_keys=True, indent=4),
				desc          = self.desc,
				ask_overwrite = ask_overwrite)

	class new(base):

		def __init__(self, message, addrlists, msghash_type, *args, **kwargs):

			msghash_type = msghash_type or self.msg_cls.msghash_types[0]

			if msghash_type not in self.msg_cls.msghash_types:
				die(2, f'msghash_type {msghash_type!r} not supported for {self.proto.base_proto} protocol')

			self.data = {
				'network': '{}_{}'.format(self.proto.coin.lower(), self.proto.network),
				'addrlists': [MMGenIDRange(self.proto, i) for i in addrlists.split()],
				'message': message,
				'msghash_type': msghash_type}
			self.sigs = {}

	class completed(base):

		def __init__(self, data, infile, *args, **kwargs):

			if data:
				self.__dict__ = data
				return

			self.data = get_data_from_file(
				cfg    = self.cfg,
				infile = infile,
				desc   = self.desc)

			d = json.loads(self.data)
			self.data = d['metadata']
			self.sigs = d['signatures']
			self.addrlists = [MMGenIDRange(self.proto, i) for i in self.data['addrlists']]

		def format(self, req_addr=None):

			labels = {
				'addr':       'address:',
				'addr_p2pkh': 'addr_p2pkh:',
				'pubhash':    'pubkey hash:',
				'sig':        'signature:'}

			def gen_entry(e):
				for k in labels:
					if e.get(k):
						yield fs_sig.format(labels[k], e[k])

			def gen_all():
				for k, v in hdr_data.items():
					yield fs_hdr.format(v[0], v[1](self.data[k]))
				if self.sigs:
					yield ''
					yield 'Signatures:'
					for n, (k, v) in enumerate(self.sigs.items()):
						yield ''
						yield f'{n+1:>3}) {k}'
						yield from gen_entry(v)

			def gen_single():
				for k, v in hdr_data.items():
					yield fs_hdr.format(v[0], v[1](self.data[k]))
				if self.sigs:
					yield 'Signature data:'
					k = (
						CoinAddr(self.proto, req_addr) if type(self).__name__ == 'exported_sigs' else
						MMGenID(self.proto, req_addr))
					if k not in self.sigs:
						die(1, f'{k}: address not found in signature data')
					yield from gen_entry(self.sigs[k])

			hdr_data = {
				'message':      ('Message:',           grnbg),
				'network':      ('Network:',           lambda v: v.replace('_', ' ').upper()),
				'msghash_type': ('Message Hash Type:', lambda v: v),
				'addrlists':    ('Address Ranges:',    lambda v: fmt_list(v, fmt='bare')),
				'failed_sids':  ('Failed Seed IDs:',   lambda v: red(fmt_list(v, fmt='bare')))}

			if len(self.msg_cls.msghash_types) == 1:
				del hdr_data['msghash_type']

			if req_addr or type(self).__name__ == 'exported_sigs':
				del hdr_data['addrlists']

			if req_addr or not self.data.get('failed_sids'):
				del hdr_data['failed_sids']

			fs_hdr = '{:%s} {}' % max(len(v[0]) for v in hdr_data.values())
			fs_sig = '%s{:%s} %s{}' % (
				' ' * (2 if req_addr else 5),
				max(len(labels[k]) for v in self.sigs.values() for k in v.keys()),
				self.msg_cls.sigdata_pfx or ''
			) if self.sigs else None

			if req_addr:
				return '\n'.join(gen_single())
			else:
				return ('' if self.sigs else 'UN') + 'SIGNED MESSAGE DATA:\n\n  ' + '\n  '.join(gen_all())

	class unsigned(completed):

		async def sign(self, wallet_files, *, passwd_file=None):

			from .addrlist import KeyAddrList

			async def sign_list(al_in, seed):
				al = KeyAddrList(
					cfg         = self.cfg,
					proto       = self.proto,
					seed        = seed,
					addr_idxs   = al_in.idxlist,
					mmtype      = al_in.mmtype,
					skip_chksum = True,
					add_p2pkh   = al_in.mmtype in ('S', 'B'))

				for e in al.data:
					sig = await self.do_sign(
						wif     = e.sec.wif,
						message = self.data['message'],
						msghash_type = self.data['msghash_type'])

					mmid = f'{al_in.sid}:{al_in.mmtype}:{e.idx}'
					data = {
						'addr': e.addr,
						'sig': sig}

					if self.msg_cls.include_pubhash:
						data.update(
							{'pubhash': self.proto.decode_addr(e.addr_p2pkh or e.addr).bytes.hex()})

					if e.addr_p2pkh:
						data.update({'addr_p2pkh': e.addr_p2pkh})

					self.sigs[mmid] = data

			if self.proto.sign_mode == 'daemon':
				from .rpc import rpc_init
				self.rpc = await rpc_init(self.cfg, self.proto, ignore_wallet=True)

			from .wallet import Wallet
			wallet_seeds = [Wallet(cfg=self.cfg, fn=fn, passwd_file=passwd_file).seed for fn in wallet_files]
			need_sids = remove_dups([al.sid for al in self.addrlists], quiet=True)
			saved_seeds = []

			# First try wallet seeds:
			for sid in need_sids:
				for seed in wallet_seeds:
					if sid == seed.sid:
						saved_seeds.append(seed)
						need_sids.remove(sid)
						break

			# Then subseeds:
			for sid in need_sids:
				for seed in wallet_seeds:
					subseed = seed.subseeds.get_subseed_by_seed_id(sid, print_msg=True)
					if subseed:
						saved_seeds.append(subseed)
						need_sids.remove(sid)
						break

			for al in self.addrlists:
				for seed in saved_seeds:
					if al.sid == seed.sid:
						await sign_list(al, seed)
						break

			if need_sids:
				msg('Failed Seed IDs: {}'.format(orange(fmt_list(need_sids, fmt='bare'))))

			self.data['failed_sids'] = need_sids

	class signed(completed):

		ext = 'sigmsg.json'
		signed = True

	class signed_online(signed):

		def get_sigs(self, addr):

			if addr:
				req_addr = (
					CoinAddr(self.proto, addr) if type(self).__name__ == 'exported_sigs' else
					MMGenID(self.proto, addr))
				sigs = {k: v for k, v in self.sigs.items() if k == req_addr}
			else:
				sigs = self.sigs

			if not sigs:
				die(1, 'No signatures')

			return sigs

		async def verify(self, *, addr=None):

			sigs = self.get_sigs(addr)

			if self.proto.sign_mode == 'daemon':
				from .rpc import rpc_init
				self.rpc = await rpc_init(self.cfg, self.proto, ignore_wallet=True)

			for k, v in sigs.items():
				ret = await self.do_verify(
					addr    = v.get('addr_p2pkh') or v['addr'],
					sig     = v['sig'],
					message = self.data['message'],
					msghash_type = self.data['msghash_type'])
				if not ret:
					die(3, f'Invalid signature for address {k} ({v["addr"]})')

			return len(sigs)

		def get_json_for_export(self, *, addr=None):
			sigs = list(self.get_sigs(addr).values())
			pfx = self.msg_cls.sigdata_pfx
			if pfx:
				sigs = [{k: pfx+v for k, v in e.items()} for e in sigs]
			return json.dumps({
					'message': self.data['message'],
					'msghash_type': self.data['msghash_type'],
					'network': self.data['network'].upper(),
					'signatures': sigs},
				sort_keys = True,
				indent = 4)

	class exported_sigs(signed_online):

		def __init__(self, infile, *args, **kwargs):

			self.data = json.loads(
				get_data_from_file(
					cfg    = self.cfg,
					infile = infile,
					desc   = self.desc)
				)

			pfx = self.msg_cls.sigdata_pfx
			self.sigs = {sig_data['addr']: sig_data for sig_data in (
				[{k: v[len(pfx):] for k, v in e.items()} for e in self.data['signatures']]
					if pfx else
				self.data['signatures']
			)}

def _get_obj(clsname, cfg, *args, coin=None, network='mainnet', infile=None, data=None, **kwargs):

	assert not args, 'msg:_get_obj(): only keyword args allowed'

	if clsname == 'signed':
		assert data and not (coin or infile), 'msg:_get_obj(): chk2'
	else:
		assert not data and (coin or infile) and not (coin and infile), 'msg:_get_obj(): chk3'

	proto = (
		data['proto'] if data else
		init_proto(cfg=cfg, coin=coin, network=network) if coin else
		coin_msg.base.get_proto_from_file(cfg, infile))

	try:
		msg_cls = getattr(
			importlib.import_module(f'mmgen.proto.{proto.base_proto_coin.lower()}.msg'),
			'coin_msg')
	except:
		die(1, f'Message signing operations not supported for {proto.base_proto} protocol')

	me = MMGenObject.__new__(getattr(msg_cls, clsname, getattr(coin_msg, clsname)))
	me.msg_cls = msg_cls
	me.cfg = cfg
	me.proto = proto

	me.__init__(infile=infile, data=data, *args, **kwargs)

	return me

def _get(clsname):
	return lambda *args, **kwargs: _get_obj(clsname, *args, **kwargs)

NewMsg          = _get('new')
CompletedMsg    = _get('completed')
UnsignedMsg     = _get('unsigned')
SignedMsg       = _get('signed')
SignedOnlineMsg = _get('signed_online')
ExportedMsgSigs = _get('exported_sigs')

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
msg: base message signing classes
"""

import os,importlib,json
from .globalvars import g
from .objmethods import MMGenObject,Hilite,InitErrors
from .util import msg,vmsg,die,suf,make_chksum_6,fmt_list,remove_dups
from .color import red,orange,grnbg
from .protocol import init_proto
from .fileutil import get_data_from_file,write_data_to_file
from .addr import MMGenID

class MMGenIDRange(str,Hilite,InitErrors,MMGenObject):
	"""
	closely based on MMGenID
	"""
	color = 'orange'
	width = 0
	trunc_ok = False
	def __new__(cls,proto,id_str):
		from .addrlist import AddrIdxList
		from .addr import AddrListID
		from .seed import SeedID
		try:
			ss = str(id_str).split(':')
			assert len(ss) in (2,3),'not 2 or 3 colon-separated items'
			t = proto.addr_type((ss[1],proto.dfl_mmtype)[len(ss)==2])
			me = str.__new__(cls,'{}:{}:{}'.format(ss[0],t,ss[-1]))
			me.sid = SeedID(sid=ss[0])
			me.idxlist = AddrIdxList(ss[-1])
			me.mmtype = t
			assert t in proto.mmtypes, f'{t}: invalid address type for {proto.cls_name}'
			me.al_id = str.__new__(AddrListID,me.sid+':'+me.mmtype) # checks already done
			me.proto = proto
			return me
		except Exception as e:
			return cls.init_fail(e,id_str)

class coin_msg:

	class base(MMGenObject):

		ext = 'rawmsg.json'
		signed = False

		@property
		def desc(self):
			return ('signed' if self.signed else 'unsigned') + ' message data'

		@property
		def chksum(self):
			return make_chksum_6(
				json.dumps( self.data, sort_keys=True, separators=(',', ':') ))

		@property
		def filename_stem(self):
			coin,network = self.data['network'].split('_')
			return '{}[{}]{}'.format(
				self.chksum.upper(),
				coin.upper(),
				('' if network == 'mainnet' else '.'+network) )

		@property
		def filename(self):
			return f'{self.filename_stem}.{self.ext}'

		@property
		def signed_filename(self):
			return f'{self.filename_stem}.{coin_msg.signed.ext}'

		def get_proto_from_file(self,filename):
			coin,network = json.loads(get_data_from_file(filename))['metadata']['network'].split('_')
			return init_proto( coin=coin, network=network )

		def write_to_file(self,outdir=None,ask_overwrite=False):
			data = {
				'id': f'{g.proj_name} {self.desc}',
				'metadata': self.data,
				'signatures': self.sigs,
			}

			if hasattr(self,'failed_sids'):
				data.update({'failed_seed_ids':self.failed_sids})

			write_data_to_file(
				outfile       = os.path.join(outdir or '',self.filename),
				data          = json.dumps(data,sort_keys=True,indent=4),
				desc          = f'{self.desc} data',
				ask_overwrite = ask_overwrite )

	class new(base):

		def __init__(self,message,addrlists,*args,**kwargs):
			self.data = {
				'network': '{}_{}'.format( self.proto.coin.lower(), self.proto.network ),
				'addrlists': [MMGenIDRange(self.proto,i) for i in addrlists.split()],
				'message': message,
			}
			self.sigs = {}

	class completed(base):

		def __init__(self,data,infile,*args,**kwargs):

			if data:
				self.__dict__ = data
				return

			self.infile = infile
			self.data = get_data_from_file(
				infile = self.infile,
				desc   = f'{self.desc} data' )

			d = json.loads(self.data)
			self.data = d['metadata']
			self.sigs = d['signatures']
			self.addrlists = [MMGenIDRange(self.proto,i) for i in self.data['addrlists']]
			if d.get('failed_seed_ids'):
				self.failed_sids = d['failed_seed_ids']

		def format(self,mmid=None):

			def gen_entry(e):
				yield fs2.format( 'addr:', e['addr'] )
				if e.get('addr_p2pkh'):
					yield fs2.format( 'addr_p2pkh:', e['addr_p2pkh'] )
				if e.get('pubhash'):
					yield fs2.format( 'pubkey hash:', e['pubhash'] )
				yield fs2.format('sig:', e['sig'] )

			def gen_all():
				fs = '{:16s} {}'
				for k,v in disp_data.items():
					yield fs.format( v[0]+':', v[1](self.data[k]) )
				if hasattr(self,'failed_sids'):
					yield fs.format(
						'Failed Seed IDs:',
						red(fmt_list(self.failed_sids,fmt='bare')) )
				yield ''
				yield 'Signatures:'
				for n,(k,v) in enumerate(self.sigs.items()):
					yield ''
					yield '{:>3}) {}'.format(n+1,k)
					for res in gen_entry(v):
						yield res

			def gen_single():
				fs = '{:8s} {}'
				for k,v in disp_data.items():
					yield fs.format( v[0]+':', v[1](self.data[k]) )
				yield 'Signature data:'
				k = MMGenID(self.proto,mmid)
				if k not in self.sigs:
					die(1,f'{k}: address not found in signature data')
				for res in gen_entry(self.sigs[k]):
					yield res

			disp_data = {
				'message':   ('Message',        lambda v: grnbg(v) ),
				'network':   ('Network',        lambda v: v.replace('_',' ').upper() ),
				'addrlists': ('Address Ranges', lambda v: fmt_list(v,fmt='bare') ),
			}

			if mmid:
				del disp_data['addrlists']
				fs2 = '  {:12s} {}'
				return '\n'.join(gen_single())
			else:
				fs2 = '     {:12s} {}'
				return 'SIGNED MESSAGE DATA:\n\n  ' + '\n  '.join(gen_all())

	class unsigned(completed):

		async def sign(self,wallet_files):

			async def sign_list(al_in,seed):
				al = KeyAddrList(
					proto       = self.proto,
					seed        = seed,
					addr_idxs   = al_in.idxlist,
					mmtype      = al_in.mmtype,
					skip_chksum = True,
					add_p2pkh   = al_in.mmtype in ('S','B') )

				for e in al.data:
					sig = await self.do_sign(
						wif     = e.sec.wif,
						message = self.data['message'] )

					mmid = '{}:{}:{}'.format( al_in.sid, al_in.mmtype, e.idx )
					data = {
						'addr': e.addr,
						'pubhash': self.proto.parse_addr(e.addr_p2pkh or e.addr).bytes.hex(),
						'sig': sig,
					}

					if e.addr_p2pkh:
						data.update({'addr_p2pkh': e.addr_p2pkh})

					self.sigs[mmid] = data

			from .rpc import rpc_init
			self.rpc = await rpc_init(self.proto)

			from .wallet import Wallet
			from .addrlist import KeyAddrList
			wallet_seeds = [Wallet(fn=fn).seed for fn in wallet_files]
			need_sids = remove_dups([al.sid for al in self.addrlists], quiet=True)
			saved_seeds = list()

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
					subseed = seed.subseeds.get_subseed_by_seed_id(sid,print_msg=True)
					if subseed:
						saved_seeds.append(subseed)
						need_sids.remove(sid)
						break

			for al in self.addrlists:
				for seed in saved_seeds:
					if al.sid == seed.sid:
						await sign_list(al,seed)
						break

			if need_sids:
				msg('Failed Seed IDs: {}'.format(orange(fmt_list(need_sids,fmt='bare'))))

			self.failed_sids = need_sids

	class signed(completed):

		ext = 'sigmsg.json'
		signed = True

	class signed_online(signed):

		async def verify(self,addr=None,summary=False):

			from .rpc import rpc_init
			self.rpc = await rpc_init(self.proto)

			if addr:
				mmaddr = MMGenID(self.proto,addr)
				sigs = {k:v for k,v in self.sigs.items() if k == mmaddr}
			else:
				sigs = self.sigs

			for k,v in sigs.items():
				ret = await self.do_verify(
					addr    = v.get('addr_p2pkh') or v['addr'],
					sig     = v['sig'],
					message = self.data['message'] )
				if not ret:
					die(3,f'Invalid signature for address {k} ({v["addr"]})')

			if summary:
				msg('{} signature{} verified'.format( len(sigs), suf(sigs) ))

def _get_obj(clsname,coin=None,network='mainnet',infile=None,data=None,*args,**kwargs):

	assert not args, 'msg:_get_obj(): only keyword args allowed'

	if clsname == 'signed':
		assert data and not (coin or infile), 'msg:_get_obj(): chk2'
	else:
		assert not data and (coin or infile) and not (coin and infile), 'msg:_get_obj(): chk3'

	proto = (
		data['proto'] if data else
		init_proto( coin=coin, network=network ) if coin else
		coin_msg.base().get_proto_from_file(infile) )

	cls = getattr(
		getattr(importlib.import_module(f'mmgen.base_proto.{proto.base_proto.lower()}.msg'),'coin_msg'),
		clsname )

	me = MMGenObject.__new__(cls)
	me.proto = proto

	me.__init__(infile=infile,data=data,*args,**kwargs)

	return me

def _get(clsname):
	return lambda *args,**kwargs: _get_obj(clsname,*args,**kwargs)

NewMsg          = _get('new')
CompletedMsg    = _get('completed')
UnsignedMsg     = _get('unsigned')
SignedMsg       = _get('signed')
SignedOnlineMsg = _get('signed_online')

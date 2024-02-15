#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
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
xmrwallet.py - MoneroWalletOps class
"""

import re,time,json,atexit
from collections import namedtuple
from pathlib import Path

from .objmethods import MMGenObject,HiliteStr,InitErrors
from .obj import CoinTxID
from .color import red,yellow,green,blue,cyan,pink,orange,purple,gray
from .util import (
	msg,
	msg_r,
	gmsg,
	bmsg,
	ymsg,
	rmsg,
	gmsg_r,
	pp_msg,
	die,
	fmt,
	suf,
	async_run,
	make_timestr,
	make_chksum_N,
	capfirst,
	list_gen,
)
from .fileutil import get_data_from_file
from .seed import SeedID
from .protocol import init_proto
from .proto.btc.common import b58a
from .addr import CoinAddr,AddrIdx
from .addrlist import KeyAddrList,ViewKeyAddrList,AddrIdxList
from .rpc import json_encoder
from .proto.xmr.rpc import MoneroRPCClient,MoneroWalletRPCClient
from .proto.xmr.daemon import MoneroWalletDaemon
from .ui import keypress_confirm
from .autosign import Autosign

xmrwallet_uargs = namedtuple('xmrwallet_uargs',[
	'infile',
	'wallets',
	'spec',
])

xmrwallet_uarg_info = (
	lambda e,hp: {
		'daemon':          e('HOST:PORT', hp),
		'tx_relay_daemon': e('HOST:PORT[:PROXY_HOST:PROXY_PORT]',          rf'({hp})(?::({hp}))?'),
		'newaddr_spec':    e('WALLET_NUM[:ACCOUNT][,"label text"]',         r'(\d+)(?::(\d+))?(?:,(.*))?'),
		'transfer_spec':   e('SOURCE_WALLET_NUM:ACCOUNT:ADDRESS,AMOUNT',   rf'(\d+):(\d+):([{b58a}]+),([0-9.]+)'),
		'sweep_spec':      e('SOURCE_WALLET_NUM:ACCOUNT[,DEST_WALLET_NUM]', r'(\d+):(\d+)(?:,(\d+))?'),
		'label_spec':      e('WALLET_NUM:ACCOUNT:ADDRESS,"label text"',     r'(\d+):(\d+):(\d+),(.*)'),
	})(
		namedtuple('uarg_info_entry',['annot','pat']),
		r'(?:[^:]+):(?:\d+)'
	)

def get_autosign_obj(cfg):
	from .cfg import Config
	return Autosign(
		Config({
			'mountpoint': cfg.autosign_mountpoint,
			'test_suite': cfg.test_suite,
			'coins': 'xmr',
		})
	)

# required to squelch pylint:
def fmt_amt(amt):
	return str(amt)

def hl_amt(amt):
	return str(amt)

class XMRWalletAddrSpec(HiliteStr,InitErrors,MMGenObject):
	color = 'cyan'
	width = 0
	trunc_ok = False
	min_len = 5  # 1:0:0
	max_len = 14 # 9999:9999:9999
	def __new__(cls,arg1,arg2=None,arg3=None):
		if isinstance(arg1,cls):
			return arg1

		try:
			if isinstance(arg1,str):
				me = str.__new__(cls,arg1)
				m = re.fullmatch( '({n}):({n}):({n}|None)'.format(n=r'[0-9]{1,4}'), arg1 )
				assert m is not None, f'{arg1!r}: invalid XMRWalletAddrSpec'
				for e in m.groups():
					if len(e) != 1 and e[0] == '0':
						die(2,f'{e}: leading zeroes not permitted in XMRWalletAddrSpec element')
				me.wallet = AddrIdx(m[1])
				me.account = int(m[2])
				me.account_address = None if m[3] == 'None' else int(m[3])
			else:
				me = str.__new__(cls,f'{arg1}:{arg2}:{arg3}')
				for arg in [arg1,arg2] + ([] if arg3 is None else [arg3]):
					assert isinstance(arg,int), f'{arg}: XMRWalletAddrSpec component not of type int'
					assert arg is None or arg <= 9999, f'{arg}: XMRWalletAddrSpec component greater than 9999'
				me.wallet = AddrIdx(arg1)
				me.account = arg2
				me.account_address = arg3
			return me
		except Exception as e:
			return cls.init_fail(e,me)

def is_xmr_tx_file(cfg,fn):
	try:
		MoneroMMGenTX.Completed(cfg,fn)
		return True
	except Exception as e:
		if not 'MoneroMMGenTXFileParseError' in type(e).__name__:
			ymsg(f'\n{type(e).__name__}: {e}')
		return False

class MoneroMMGenFile:

	silent_load = False

	def make_chksum(self,keys=None):
		res = json.dumps(
			dict( (k,v) for k,v in self.data._asdict().items() if (not keys or k in keys) ),
			cls = json_encoder
		)
		return make_chksum_N( res, rounds=1, nchars=self.chksum_nchars, upper=False )

	@property
	def base_chksum(self):
		return self.make_chksum(self.base_chksum_fields)

	@property
	def full_chksum(self):
		return self.make_chksum(self.full_chksum_fields) if self.full_chksum_fields else None

	def check_checksums(self,d_wrap):
		for k in ('base_chksum','full_chksum'):
			a = getattr(self,k)
			if a is not None:
				b = d_wrap[k]
				assert a == b, f'{k} mismatch: {a} != {b}'

	def make_wrapped_data(self,in_data):
		out = {
			'base_chksum': self.base_chksum,
			'full_chksum': self.full_chksum,
			'data': in_data,
		} if self.full_chksum else {
			'base_chksum': self.base_chksum,
			'data': in_data,
		}
		return json.dumps(
			{ self.data_label: out },
			cls = json_encoder,
			indent = 2,
		)

	def extract_data_from_file(self,cfg,fn):
		return json.loads(
			get_data_from_file( cfg, str(fn), self.desc, silent=self.silent_load )
		)[self.data_label]

class MoneroMMGenTX:

	class Base(MoneroMMGenFile):

		data_label = 'MoneroMMGenTX'

		# both base_chksum and full_chksum are used to make the filename stem, so we must not include
		# fields that change when TX is signed and submitted (e.g. ‘sign_time’, ‘submit_time’)
		base_chksum_fields = {
			'op',
			'create_time',
			'network',
			'seed_id',
			'source',
			'dest',
			'amount' }
		full_chksum_fields = {
			'op',
			'create_time',
			'network',
			'seed_id',
			'source',
			'dest',
			'amount',
			'fee',
			'blob' }
		oneline_fs = '{a:7} {b:8} {c:19} {d:13} {e:8} {f:6} {x:2} {g:6} {h:17} {j}'
		chksum_nchars = 6
		xmrwallet_tx_data = namedtuple('xmrwallet_tx_data',[
			'op',
			'create_time',
			'sign_time',
			'submit_time',
			'network',
			'seed_id',
			'source',
			'dest',
			'dest_address',
			'txid',
			'amount',
			'fee',
			'blob',
			'metadata',
			'unsigned_txset',
			'signed_txset',
			'complete',
		])

		def __init__(self):
			self.name = type(self).__name__

		@property
		def src_wallet_idx(self):
			return int(self.data.source.split(':')[0])

		def get_info_oneline(self,indent='',cols=None):
			d = self.data
			return self.oneline_fs.format(
					a = yellow(d.network),
					b = d.seed_id.hl(),
					c = make_timestr(d.submit_time if d.submit_time is not None else d.create_time),
					d = orange(self.file_id),
					e = purple(capfirst(d.op.ljust(8))),
					f = red('{}:{}'.format(d.source.wallet,d.source.account).ljust(6)),
					g = red('{}:{}'.format(d.dest.wallet,d.dest.account).ljust(6)) if d.dest else cyan('ext   '),
					h = d.amount.fmt( color=True, iwidth=4, prec=12 ),
					j = d.dest_address.fmt(width=cols-95,color=True) if cols else d.dest_address.hl(),
					x = '->'
				)

		def get_info(self,indent='',cols=None):
			d = self.data
			pmt_id = d.dest_address.parsed.payment_id
			fs = '\n'.join(list_gen(
				['Info for transaction {a} [Seed ID: {b}. Network: {c}]:'],
				['  TxID:      {d}'],
				['  Created:   {e:19} [{f}]'],
				['  Signed:    {g:19} [{h}]', d.sign_time],
				['  Submitted: {s:19} [{t}]', d.submit_time],
				['  Type:      {i}{S}'],
				['  From:      Wallet {j}, account {k}'],
				['  To:        Wallet {x}, account {y}, address {z}', d.dest],
				['  Amount:    {m} XMR'],
				['  Fee:       {n} XMR'],
				['  Dest:      {o}'],
				['  Payment ID: {P}', pmt_id],
			))

			from .util2 import format_elapsed_hr
			return fmt(fs,strip_char='\t',indent=indent).format(
					a = orange(self.file_id),
					b = d.seed_id.hl(),
					c = yellow(d.network.upper()),
					d = d.txid.hl(),
					e = make_timestr(d.create_time),
					f = format_elapsed_hr(d.create_time),
					g = make_timestr(d.sign_time) if d.sign_time else None,
					h = format_elapsed_hr(d.sign_time) if d.sign_time else None,
					i = blue(capfirst(d.op)),
					j = d.source.wallet.hl(),
					k = red(f'#{d.source.account}'),
					m = d.amount.hl(),
					n = d.fee.hl(),
					o = d.dest_address.hl(),
					P = pink(pmt_id.hex()) if pmt_id else None,
					s = make_timestr(d.submit_time) if d.submit_time else None,
					S = pink(f" [cold signed{', submitted' if d.complete else ''}]") if d.signed_txset else '',
					t = format_elapsed_hr(d.submit_time) if d.submit_time else None,
					x = d.dest.wallet.hl() if d.dest else None,
					y = red(f'#{d.dest.account}') if d.dest else None,
					z = red(f'#{d.dest.account_address}') if d.dest else None,
				)

		@property
		def file_id(self):
			return (self.base_chksum + ('-' + self.full_chksum if self.full_chksum else '')).upper()

		def write(self,delete_metadata=False,ask_write=True,ask_overwrite=True):
			dict_data = self.data._asdict()
			if delete_metadata:
				dict_data['metadata'] = None

			fn = '{a}-XMR[{b!s}]{c}.{d}'.format(
				a = self.file_id,
				b = self.data.amount,
				c = '' if self.data.network == 'mainnet' else f'.{self.data.network}',
				d = self.ext
			)

			if self.cfg.autosign:
				fn = get_autosign_obj(self.cfg).xmr_tx_dir / fn

			from .fileutil import write_data_to_file
			write_data_to_file(
				cfg                   = self.cfg,
				outfile               = str(fn),
				data                  = self.make_wrapped_data(dict_data),
				desc                  = self.desc,
				ask_write             = ask_write,
				ask_write_default_yes = not ask_write,
				ask_overwrite         = ask_overwrite,
				ignore_opt_outdir     = self.cfg.autosign )

	class New(Base):

		def __init__(self,*args,**kwargs):

			super().__init__()

			assert not args, 'Non-keyword args not permitted'

			if '_in_tx' in kwargs:
				in_data = kwargs.pop('_in_tx').data._asdict()
				in_data.update(kwargs)
			else:
				in_data = kwargs

			d = namedtuple('monero_tx_in_data_tuple',in_data)(**in_data)
			self.cfg = d.cfg

			proto = init_proto( self.cfg, 'xmr', network=d.network, need_amt=True )

			now = int(time.time())

			self.data = self.xmrwallet_tx_data(
				op             = d.op,
				create_time    = now if self.name in ('NewSigned','NewUnsigned') else getattr(d,'create_time',None),
				sign_time      = now if self.name in ('NewSigned','NewColdSigned') else getattr(d,'sign_time',None),
				submit_time    = now if self.name == 'NewSubmitted' else None,
				network        = d.network,
				seed_id        = SeedID(sid=d.seed_id),
				source         = XMRWalletAddrSpec(d.source),
				dest           = None if d.dest is None else XMRWalletAddrSpec(d.dest),
				dest_address   = CoinAddr(proto,d.dest_address),
				txid           = CoinTxID(d.txid),
				amount         = proto.coin_amt(d.amount,from_unit='atomic'),
				fee            = proto.coin_amt(d.fee,from_unit='atomic'),
				blob           = d.blob,
				metadata       = d.metadata,
				unsigned_txset = d.unsigned_txset,
				signed_txset   = getattr(d,'signed_txset',None),
				complete       = self.name in ('NewSigned','NewSubmitted'),
			)

	class NewUnsigned(New):
		desc = 'unsigned transaction'
		ext = 'rawtx'
		signed = False

	class NewSigned(New):
		desc = 'signed transaction'
		ext = 'sigtx'
		signed = True

	class NewColdSigned(NewSigned):
		pass

	class NewSubmitted(NewColdSigned):
		desc = 'submitted transaction'
		ext = 'subtx'

	class Completed(Base):
		desc = 'transaction'
		forbidden_fields = ()

		def __init__(self,cfg,fn):

			super().__init__()

			self.cfg = cfg
			self.fn = Path(fn)

			try:
				d_wrap = self.extract_data_from_file( cfg, fn )
			except Exception as e:
				die( 'MoneroMMGenTXFileParseError', f'{type(e).__name__}: {e}\nCould not load transaction file' )

			if 'unsigned_txset' in d_wrap['data']: # post-autosign
				self.full_chksum_fields &= set(d_wrap['data']) # allow for added chksum fields in future
			else:
				self.full_chksum_fields = set(d_wrap['data']) - {'metadata'}

			for key in self.xmrwallet_tx_data._fields: # backwards compat: fill in missing fields
				if not key in d_wrap['data']:
					d_wrap['data'][key] = None

			d = self.xmrwallet_tx_data(**d_wrap['data'])

			if self.name not in ('View','Completed'):
				assert fn.name.endswith('.'+self.ext), 'TX file {fn} has incorrect extension (not {self.ext!r})'
				assert getattr(d,self.req_field), f'{self.name} TX missing required field {self.req_field!r}'
				assert bool(d.sign_time) == self.signed, '{a} has {b}sign time!'.format(
					a = self.desc,
					b = 'no ' if self.signed else'' )
				for f in self.forbidden_fields:
					assert not getattr(d,f), f'{self.name} TX mismatch: contains forbidden field {f!r}'

			proto = init_proto( cfg, 'xmr', network=d.network, need_amt=True )

			self.data = self.xmrwallet_tx_data(
				op             = d.op,
				create_time    = d.create_time,
				sign_time      = d.sign_time,
				submit_time    = d.submit_time,
				network        = d.network,
				seed_id        = SeedID(sid=d.seed_id),
				source         = XMRWalletAddrSpec(d.source),
				dest           = None if d.dest is None else XMRWalletAddrSpec(d.dest),
				dest_address   = CoinAddr(proto,d.dest_address),
				txid           = CoinTxID(d.txid),
				amount         = proto.coin_amt(d.amount),
				fee            = proto.coin_amt(d.fee),
				blob           = d.blob,
				metadata       = d.metadata,
				unsigned_txset = d.unsigned_txset,
				signed_txset   = d.signed_txset,
				complete       = d.complete,
			)

			self.check_checksums(d_wrap)

	class Unsigned(Completed):
		desc = 'unsigned transaction'
		ext = 'rawtx'
		signed = False
		req_field = 'unsigned_txset'
		forbidden_fields = ('signed_txset',)

	class Signed(Completed):
		desc = 'signed transaction'
		ext = 'sigtx'
		signed = True
		req_field = 'blob'
		forbidden_fields = ('signed_txset','unsigned_txset')

	class ColdSigned(Signed):
		req_field = 'signed_txset'
		forbidden_fields = ()

	class Submitted(ColdSigned):
		desc = 'submitted transaction'
		ext = 'subtx'
		silent_load = True

	class View(Completed):
		silent_load = True

class MoneroWalletOutputsFile:

	class Base(MoneroMMGenFile):

		desc = 'wallet outputs'
		data_label = 'MoneroMMGenWalletOutputsFile'
		base_chksum_fields = {'seed_id','wallet_index','outputs_data_hex',}
		full_chksum_fields = {'seed_id','wallet_index','outputs_data_hex','signed_key_images'}
		fn_fs = '{a}-outputs-{b}.{c}'
		ext_offset = 25 # len('-outputs-') + len(chksum) ({b})
		chksum_nchars = 16
		data_tuple = namedtuple('wallet_outputs_data',[
			'seed_id',
			'wallet_index',
			'outputs_data_hex',
			'signed_key_images',
		])

		def __init__(self,cfg):
			self.name = type(self).__name__
			self.cfg = cfg

		def write(self,add_suf=''):
			from .fileutil import write_data_to_file
			write_data_to_file(
				cfg               = self.cfg,
				outfile           = str(self.get_outfile( self.cfg, self.wallet_fn )) + add_suf,
				data              = self.make_wrapped_data(self.data._asdict()),
				desc              = self.desc,
				ask_overwrite     = False,
				ignore_opt_outdir = True )

		def get_outfile(self,cfg,wallet_fn):
			return (
				get_autosign_obj(cfg).xmr_outputs_dir if cfg.autosign else
				wallet_fn.parent ) / self.fn_fs.format(
					a = wallet_fn.name,
					b = self.base_chksum,
					c = self.ext,
				)

		def get_wallet_fn(self,fn):
			assert fn.name.endswith(f'.{self.ext}'), (
				f'{self.name}: filename does not end with {"."+self.ext!r}'
			)
			return fn.parent / fn.name[:-(len(self.ext)+self.ext_offset+1)]

		def get_info(self,indent=''):
			if self.data.signed_key_images is not None:
				data = self.data.signed_key_images or []
				return f'{indent}{self.wallet_fn.name}: {len(data)} signed key image{suf(data)}'
			else:
				return f'{indent}{self.wallet_fn.name}: no key images'

	class New(Base):
		ext = 'raw'

		def __init__( self, parent, wallet_fn, data, wallet_idx=None ):
			super().__init__(parent.cfg)
			self.wallet_fn = wallet_fn
			init_data = dict.fromkeys(self.data_tuple._fields)
			init_data.update({
				'seed_id':      parent.kal.al_id.sid,
				'wallet_index': wallet_idx or parent.get_idx_from_fn(wallet_fn),
			})
			init_data.update({k:v for k,v in data.items() if k in init_data})
			self.data = self.data_tuple(**init_data)

	class Completed(New):

		def __init__( self, parent, fn=None, wallet_fn=None ):
			def check_equal(desc,a,b):
				assert a == b, f'{desc} mismatch: {a} (from file) != {b} (from filename)'
			fn = fn or self.get_outfile( parent.cfg, wallet_fn )
			wallet_fn = wallet_fn or self.get_wallet_fn(fn)
			d_wrap = self.extract_data_from_file( parent.cfg, fn )
			data = d_wrap['data']
			check_equal( 'Seed ID', data['seed_id'], parent.kal.al_id.sid )
			wallet_idx = parent.get_idx_from_fn(wallet_fn)
			check_equal( 'Wallet index', data['wallet_index'], wallet_idx )
			super().__init__(
				parent     = parent,
				wallet_fn  = wallet_fn,
				data       = data,
				wallet_idx = wallet_idx,
			)
			self.check_checksums(d_wrap)

		@classmethod
		def find_fn_from_wallet_fn(cls,cfg,wallet_fn,ret_on_no_match=False):
			path = get_autosign_obj(cfg).xmr_outputs_dir or Path()
			pat = cls.fn_fs.format(
				a = wallet_fn.name,
				b = f'[0-9a-f]{{{cls.chksum_nchars}}}\\',
				c = cls.ext,
			)
			matches = [f for f in path.iterdir() if re.match(pat,f.name)]
			if not matches and ret_on_no_match:
				return None
			if not matches or len(matches) > 1:
				die(2,"{a} matching pattern {b!r} found in '{c}'!".format(
					a = 'No files' if not matches else 'More than one file',
					b = pat,
					c = path
				))
			return matches[0]

	class Unsigned(Completed):
		pass

	class SignedNew(New):
		desc = 'signed key images'
		ext = 'sig'

	class Signed(Completed,SignedNew):
		pass

class MoneroWalletDumpFile:

	class Base:
		desc = 'Monero wallet dump'
		data_label = 'MoneroMMGenWalletDumpFile'
		base_chksum_fields = {'seed_id','wallet_index','wallet_metadata'}
		full_chksum_fields = None
		ext = 'dump'
		ext_offset = 0
		data_tuple = namedtuple('wallet_dump_data',[
			'seed_id',
			'wallet_index',
			'wallet_metadata',
		])
		def get_outfile(self,cfg,wallet_fn):
			return wallet_fn.parent / f'{wallet_fn.name}.{self.ext}'

	class New(Base,MoneroWalletOutputsFile.New):
		pass

	class Completed(Base,MoneroWalletOutputsFile.Completed):
		pass

class MoneroWalletOps:

	ops = (
		'create',
		'create_offline',
		'sync',
		'list',
		'view',
		'listview',
		'new',
		'transfer',
		'sweep',
		'relay',
		'txview',
		'txlist',
		'label',
		'sign',
		'submit',
		'resubmit',
		'dump',
		'restore',
		'export_outputs',
		'import_key_images' )

	kafile_arg_ops = (
		'create',
		'sync',
		'list',
		'view',
		'listview',
		'label',
		'new',
		'transfer',
		'sweep',
		'dump',
		'restore' )

	opts = (
		'wallet_dir',
		'daemon',
		'tx_relay_daemon',
		'use_internal_keccak_module',
		'hash_preset',
		'restore_height',
		'no_start_wallet_daemon',
		'no_stop_wallet_daemon',
		'no_relay',
		'watch_only',
		'autosign' )

	pat_opts = ('daemon','tx_relay_daemon')

	class base(MMGenObject):

		opts = ('wallet_dir',)
		trust_monerod = False
		do_umount = True

		def __init__(self,cfg,uarg_tuple):

			def gen_classes():
				for cls in type(self).__mro__:
					yield cls
					if cls.__name__ == 'base':
						break

			self.name = type(self).__name__
			self.cfg = cfg
			classes = tuple(gen_classes())
			self.opts = tuple(set(opt for cls in classes for opt in cls.opts))

			if not hasattr(self,'stem'):
				self.stem = self.name

			global uarg, uarg_info, fmt_amt, hl_amt

			uarg = uarg_tuple
			uarg_info = xmrwallet_uarg_info

			def fmt_amt(amt):
				return self.proto.coin_amt(amt,from_unit='atomic').fmt( iwidth=5, prec=12, color=True )
			def hl_amt(amt):
				return self.proto.coin_amt(amt,from_unit='atomic').hl()

			id_cur = None
			for cls in classes:
				if id(cls.check_uopts) != id_cur:
					cls.check_uopts(self)
					id_cur = id(cls.check_uopts)

			self.proto = init_proto( cfg, 'xmr', network=self.cfg.network, need_amt=True )

			if cfg.autosign:
				self.asi = get_autosign_obj(cfg)

			self.pre_init_action()

		def check_uopts(self):

			def check_pat_opt(name):
				val = getattr(self.cfg,name)
				if not re.fullmatch( uarg_info[name].pat, val, re.ASCII ):
					die(1,'{!r}: invalid value for --{}: it must have format {!r}'.format(
						val,
						name.replace('_','-'),
						uarg_info[name].annot
					))

			for attr in self.cfg.__dict__:
				if attr in MoneroWalletOps.opts and not attr in self.opts:
					die(1,'Option --{} not supported for {!r} operation'.format(
						attr.replace('_','-'),
						self.name,
					))

			for opt in MoneroWalletOps.pat_opts:
				if getattr(self.cfg,opt,None):
					check_pat_opt(opt)

		def parse_tx_relay_opt(self):
			return re.fullmatch(
				uarg_info['tx_relay_daemon'].pat,
				self.cfg.tx_relay_daemon,
				re.ASCII )

		def display_tx_relay_info(self,indent=''):
			m = self.parse_tx_relay_opt()
			msg(fmt(f"""
				TX relay info:
				  Host:  {blue(m[1])}
				  Proxy: {blue(m[2] or 'None')}
				""",strip_char='\t',indent=indent))

		def pre_init_action(self):
			pass

		def post_main_success(self):
			pass

		def post_main_failure(self):
			pass

		async def stop_wallet_daemon(self):
			pass

		def post_mount_action(self):
			pass

		def mount_removable_device(self):
			if self.cfg.autosign and not self.cfg.test_suite:
				if not self.asi.get_insert_status():
					die(1,'Removable device not present!')
				if self.do_umount:
					import atexit
					atexit.register(lambda: self.asi.do_umount())
				self.asi.do_mount()
				self.post_mount_action()

	class wallet(base):

		opts = (
			'use_internal_keccak_module',
			'hash_preset',
			'daemon',
			'no_start_wallet_daemon',
			'no_stop_wallet_daemon',
			'autosign',
			'watch_only',
		)
		offline = False
		wallet_offline = False
		wallet_exists = True
		start_daemon = True
		skip_wallet_check = False # for debugging

		def __init__(self,cfg,uarg_tuple):

			def wallet_exists(fn):
				try:
					fn.stat()
				except:
					return False
				else:
					return True

			def check_wallets():
				for d in self.addr_data:
					fn = self.get_wallet_fn(d)
					exists = wallet_exists(fn)
					if exists and not self.wallet_exists:
						die(1,f"Wallet '{fn}' already exists!")
					elif not exists and self.wallet_exists:
						die(1,f"Wallet '{fn}' not found!")

			super().__init__(cfg,uarg_tuple)

			if self.offline or (self.name == 'create' and self.cfg.restore_height is None):
				self.wallet_offline = True

			self.wd = MoneroWalletDaemon(
				cfg         = self.cfg,
				proto       = self.proto,
				wallet_dir  = self.cfg.wallet_dir or '.',
				test_suite  = self.cfg.test_suite,
				monerod_addr = self.cfg.daemon or None,
				trust_monerod = self.trust_monerod,
				test_monerod = not self.wallet_offline,
			)

			if self.wallet_offline:
				self.wd.usr_daemon_args = ['--offline']

			self.c = MoneroWalletRPCClient(
				cfg             = self.cfg,
				daemon          = self.wd,
				test_connection = False,
			)

			if self.offline:
				from .wallet import Wallet
				self.seed_src = Wallet(
					cfg           = cfg,
					fn            = uarg.infile,
					ignore_in_fmt = True )

				gmsg('\nCreating ephemeral key-address list for offline wallets')
				self.kal = KeyAddrList(
					cfg       = cfg,
					proto     = self.proto,
					seed      = self.seed_src.seed,
					addr_idxs = uarg.wallets,
					skip_chksum_msg = True )
			else:
				self.mount_removable_device()
				# with watch_only, make a second attempt to open the file as KeyAddrList:
				for first_try in (True,False):
					try:
						self.kal = (ViewKeyAddrList if (self.cfg.watch_only and first_try) else KeyAddrList)(
							cfg      = cfg,
							proto    = self.proto,
							addrfile = str(self.autosign_viewkey_addr_file) if self.cfg.autosign else uarg.infile,
							key_address_validity_check = True,
							skip_chksum_msg = True )
						break
					except:
						if first_try:
							msg(f"Attempting to open '{uarg.infile}' as key-address list")
							continue
						raise

			self.create_addr_data()

			if not self.skip_wallet_check:
				check_wallets()

			if self.start_daemon and not self.cfg.no_start_wallet_daemon:
				async_run(self.restart_wallet_daemon())

		@classmethod
		def get_idx_from_fn(cls,fn):
			return int( re.match(r'[0-9a-fA-F]{8}-(\d+)-Monero(WatchOnly)?Wallet.*',fn.name)[1] )

		def get_coin_daemon_rpc(self):

			host,port = self.cfg.daemon.split(':') if self.cfg.daemon else ('localhost',self.wd.monerod_port)

			from .daemon import CoinDaemon
			return MoneroRPCClient(
				cfg    = self.cfg,
				proto  = self.proto,
				daemon = CoinDaemon( self.cfg, 'xmr' ),
				host   = host,
				port   = int(port),
				user   = None,
				passwd = None )

		@property
		def autosign_viewkey_addr_file(self):
			from .addrfile import ViewKeyAddrFile
			flist = [f for f in self.asi.xmr_dir.iterdir() if f.name.endswith(ViewKeyAddrFile.ext)]
			if len(flist) != 1:
				die(2,
					"{a} viewkey-address files found in autosign mountpoint directory '{b}'!\n".format(
						a = 'Multiple' if flist else 'No',
						b = self.asi.xmr_dir
					)
					+ 'Have you run ‘mmgen-autosign setup’ on your offline machine with the --xmrwallets option?'
				)
			else:
				return flist[0]

		def create_addr_data(self):
			if uarg.wallets:
				idxs = AddrIdxList(uarg.wallets)
				self.addr_data = [d for d in self.kal.data if d.idx in idxs]
				if len(self.addr_data) != len(idxs):
					die(1,f'List {uarg.wallets!r} contains addresses not present in supplied key-address file')
			else:
				self.addr_data = self.kal.data

		async def restart_wallet_daemon(self):
			atexit.register(lambda: async_run(self.stop_wallet_daemon()))
			await self.c.restart_daemon()

		async def stop_wallet_daemon(self):
			if not self.cfg.no_stop_wallet_daemon:
				try:
					await self.c.stop_daemon()
				except KeyboardInterrupt:
					ymsg('\nForce killing wallet daemon')
					self.c.daemon.force_kill = True
					self.c.daemon.stop()

		def get_wallet_fn(self,data,watch_only=None):
			if watch_only is None:
				watch_only = self.cfg.watch_only
			return Path(
				(self.cfg.wallet_dir or '.'),
				'{a}-{b}-Monero{c}Wallet{d}'.format(
					a = self.kal.al_id.sid,
					b = data.idx,
					c = 'WatchOnly' if watch_only else '',
					d = f'.{self.cfg.network}' if self.cfg.network != 'mainnet' else '')
			)

		@property
		def add_wallet_desc(self):
			return 'offline signing ' if self.offline else 'watch-only ' if self.cfg.watch_only else ''

		async def main(self):
			gmsg('\n{a}ing {b} {c}wallet{d}'.format(
				a = self.stem.capitalize(),
				b = len(self.addr_data),
				c = self.add_wallet_desc,
				d = suf(self.addr_data) ))
			processed = 0
			for n,d in enumerate(self.addr_data): # [d.sec,d.addr,d.wallet_passwd,d.viewkey]
				fn = self.get_wallet_fn(d)
				gmsg('\n{a}ing wallet {b}/{c} ({d})'.format(
					a = self.stem.capitalize(),
					b = n + 1,
					c = len(self.addr_data),
					d = fn.name,
				))
				processed += await self.process_wallet(
					d,
					fn,
					last = n==len(self.addr_data)-1 )
			gmsg(f'\n{processed} wallet{suf(processed)} {self.stem}ed\n')
			return processed

		def head_msg(self,wallet_idx,fn):
			gmsg('\n{a} {b}wallet #{c} ({d})'.format(
				a = self.action.capitalize(),
				b = self.add_wallet_desc,
				c = wallet_idx,
				d = fn.name
			))

		class rpc:

			def __init__(self,parent,d):
				self.parent = parent
				self.cfg = parent.cfg
				self.c = parent.c
				self.d = d
				self.fn = parent.get_wallet_fn(d)
				self.new_tx_cls = (
					MoneroMMGenTX.NewUnsigned if self.cfg.watch_only else
					MoneroMMGenTX.NewSigned )

			def open_wallet(self,desc=None,refresh=True):
				add_desc = desc + ' ' if desc else self.parent.add_wallet_desc
				gmsg_r(f'\n  Opening {add_desc}wallet...')
				self.c.call( # returns {}
					'open_wallet',
					filename = self.fn.name,
					password = self.d.wallet_passwd )
				gmsg('done')

				if refresh:
					gmsg_r(f'  Refreshing {add_desc}wallet...')
					ret = self.c.call('refresh')
					gmsg('done')
					if ret['received_money']:
						msg('  Wallet has received funds')

			def close_wallet(self,desc):
				gmsg_r(f'\n  Closing {desc} wallet...')
				self.c.call('close_wallet')
				gmsg_r('done')

			async def stop_wallet(self,desc):
				msg(f'Stopping {self.c.daemon.desc} on port {self.c.daemon.bind_port}')
				gmsg_r(f'\n  Stopping {desc} wallet...')
				await self.c.stop_daemon(quiet=True) # closes wallet
				gmsg_r('done')

			def gen_accts_info(self, data, addrs_data, indent='    '):
				d = data['subaddress_accounts']
				yield indent + f'Accounts of wallet {self.fn.name}:'
				fs = indent + '  {a:6}  {b:18}  {c:<6} {d:%s}  {e}' % max(len(e['label']) for e in d)
				yield fs.format(a='Index ', b='Base Address', c='nAddrs', d='Label', e='Unlocked Balance')
				for i,e in enumerate(d):
					yield fs.format(
						a = str(e['account_index']),
						b = e['base_address'][:15] + '...',
						c = len(addrs_data[i]['addresses']),
						d = e['label'],
						e = fmt_amt(e['unlocked_balance']))

			def get_accts(self,print=True):
				data = self.c.call('get_accounts')
				addrs_data = [
					self.c.call('get_address',account_index=i)
						for i in range(len(data['subaddress_accounts']))
				]
				if print:
					msg('\n' + '\n'.join(self.gen_accts_info(data, addrs_data)))
				return ( data, addrs_data )

			def create_acct(self,label=None):
				msg('\n    Creating new account...')
				ret = self.c.call('create_account', label=label)
				msg('      Index:   {}'.format( pink(str(ret['account_index'])) ))
				msg('      Address: {}'.format( cyan(ret['address']) ))
				return (ret['account_index'], ret['address'])

			def get_last_acct(self,accts_data):
				msg('\n    Getting last account...')
				ret = accts_data['subaddress_accounts'][-1]
				msg('      Index:   {}'.format( pink(str(ret['account_index'])) ))
				msg('      Address: {}'.format( cyan(ret['base_address']) ))
				return (ret['account_index'], ret['base_address'])

			def print_addrs(self,accts_data,account):
				ret = self.c.call('get_address',account_index=account)
				d = ret['addresses']
				msg('\n      Addresses of account #{} ({}):'.format(
					account,
					accts_data['subaddress_accounts'][account]['label']))
				fs = '        {:6}  {:18}  {:%s}  {}' % max((len(e['label']) for e in d), default=0)
				msg(fs.format('Index ','Address','Label','Used'))
				for e in d:
					msg(fs.format(
						str(e['address_index']),
						e['address'][:15] + '...',
						e['label'],
						e['used']
					))
				return ret

			def create_new_addr(self,account,label=None):
				msg_r('\n    Creating new address: ')
				ret = self.c.call(
					'create_address',
					account_index = account,
					label         = label or f'Sweep from this account [{make_timestr()}]',
				)
				msg(cyan(ret['address']))
				return ret['address']

			def get_last_addr(self,account,display=True):
				if display:
					msg('\n    Getting last address:')
				ret = self.c.call(
					'get_address',
					account_index = account,
				)['addresses']
				addr = ret[-1]['address']
				if display:
					msg('      ' + cyan(addr))
				return ( addr, len(ret) - 1 )

			def set_label(self,account,address_idx,label):
				return self.c.call(
					'label_address',
					index = { 'major': account, 'minor': address_idx },
					label = label
				)

			def make_transfer_tx(self,account,addr,amt):
				res = self.c.call(
					'transfer',
					account_index = account,
					destinations = [{
						'amount':  amt.to_unit('atomic'),
						'address': addr
					}],
					do_not_relay = True,
					get_tx_hex = True,
					get_tx_metadata = True
				)
				return self.new_tx_cls(
					cfg            = self.cfg,
					op             = self.parent.name,
					network        = self.parent.proto.network,
					seed_id        = self.parent.kal.al_id.sid,
					source         = XMRWalletAddrSpec(self.parent.source.idx,self.parent.account,None),
					dest           = None,
					dest_address   = addr,
					txid           = res['tx_hash'],
					amount         = res['amount'],
					fee            = res['fee'],
					blob           = res['tx_blob'],
					metadata       = res['tx_metadata'],
					unsigned_txset = res['unsigned_txset'] if self.cfg.watch_only else None,
				)

			def make_sweep_tx(self,account,dest_acct,dest_addr_idx,addr):
				res = self.c.call(
					'sweep_all',
					address = addr,
					account_index = account,
					do_not_relay = True,
					get_tx_hex = True,
					get_tx_metadata = True
				)

				if len(res['tx_hash_list']) > 1:
					die(3,'More than one TX required.  Cannot perform this sweep')

				return self.new_tx_cls(
					cfg            = self.cfg,
					op             = self.parent.name,
					network        = self.parent.proto.network,
					seed_id        = self.parent.kal.al_id.sid,
					source         = XMRWalletAddrSpec(self.parent.source.idx,self.parent.account,None),
					dest           = XMRWalletAddrSpec(
										(self.parent.dest or self.parent.source).idx,
										dest_acct,
										dest_addr_idx),
					dest_address   = addr,
					txid           = res['tx_hash_list'][0],
					amount         = res['amount_list'][0],
					fee            = res['fee_list'][0],
					blob           = res['tx_blob_list'][0],
					metadata       = res['tx_metadata_list'][0],
					unsigned_txset = res['unsigned_txset'] if self.cfg.watch_only else None,
				)

			def relay_tx(self,tx_hex):
				ret = self.c.call('relay_tx',hex=tx_hex)
				try:
					msg('\n    Relayed {}'.format( CoinTxID(ret['tx_hash']).hl() ))
				except:
					msg(f'\n   Server returned: {ret!s}')

	class create(wallet):
		stem    = 'creat'
		wallet_exists = False
		opts    = ('restore_height',)

		def check_uopts(self):
			if self.cfg.restore_height != 'current':
				if int(self.cfg.restore_height or 0) < 0:
					die(1,f'{self.cfg.restore_height}: invalid value for --restore-height (less than zero)')

		async def process_wallet(self,d,fn,last):
			msg_r('') # for pexpect

			if self.cfg.restore_height == 'current':
				restore_height = self.get_coin_daemon_rpc().call_raw('get_height')['height']
			else:
				restore_height = self.cfg.restore_height

			if self.cfg.watch_only:
				ret = self.c.call(
					'generate_from_keys',
					filename       = fn.name,
					password       = d.wallet_passwd,
					address        = d.addr,
					viewkey        = d.viewkey,
					restore_height = restore_height )
			else:
				from .xmrseed import xmrseed
				ret = self.c.call(
					'restore_deterministic_wallet',
					filename       = fn.name,
					password       = d.wallet_passwd,
					seed           = xmrseed().fromhex(d.sec.wif,tostr=True),
					restore_height = restore_height,
					language       = 'English' )

			pp_msg(ret) if self.cfg.debug else msg(f'  Address: {ret["address"]}')
			return True

	class create_offline(create):
		offline = True

		def __init__(self,cfg,uarg_tuple):

			super().__init__(cfg,uarg_tuple)

			gmsg('\nCreating viewkey-address file for watch-only wallets')
			vkal = ViewKeyAddrList(
				cfg       = self.cfg,
				proto     = self.proto,
				addrfile  = None,
				addr_idxs = uarg.wallets,
				seed      = self.seed_src.seed,
				skip_chksum_msg = True )
			vkf = vkal.file

			# before writing viewkey-address file, shred any old ones in the directory:
			for f in Path(self.cfg.outdir or '.').iterdir():
				if f.name.endswith(vkf.ext):
					from .fileutil import shred_file
					msg(f"\nShredding old viewkey-address file '{f}'")
					shred_file( f, verbose=self.cfg.verbose )

			vkf.write() # write file to self.cfg.outdir

	class restore(create):
		wallet_offline = True

		def check_uopts(self):
			if self.cfg.restore_height is not None:
				die(1,'--restore-height must be unset when running the ‘restore’ command')

		async def process_wallet(self,d,fn,last):

			def get_dump_data():
				def gen():
					for fn in [self.get_wallet_fn(d,watch_only=wo) for wo in (True,False)]:
						ret = fn.parent / (fn.name + '.dump')
						if ret.exists():
							yield ret
				dump_fns = tuple(gen())
				if not dump_fns:
					die(1,f"No suitable dump file found for '{fn}'")
				elif len(dump_fns) > 1:
					ymsg(f"Warning: more than one dump file found for '{fn}' - using the first!")
				return MoneroWalletDumpFile.Completed(
					parent = self,
					fn     = dump_fns[0] ).data._asdict()['wallet_metadata']

			def restore_accounts():
				bmsg('  Restoring accounts:')
				for acct_idx,acct_data in enumerate(data[1:],1):
					msg(fs.format(acct_idx, 0, acct_data['address']))
					self.c.call('create_account')

			def restore_subaddresses():
				bmsg('  Restoring subaddresses:')
				for acct_idx,acct_data in enumerate(data):
					for addr_idx,addr_data in enumerate(acct_data['addresses'][1:],1):
						msg(fs.format(acct_idx, addr_idx, addr_data['address']))
						self.c.call( 'create_address', account_index=acct_idx )

			def restore_labels():
				bmsg('  Restoring labels:')
				for acct_idx,acct_data in enumerate(data):
					for addr_idx,addr_data in enumerate(acct_data['addresses']):
						addr_data['used'] = False # do this so that restored data matches
						msg(fs.format(acct_idx, addr_idx, addr_data['label']))
						self.c.call(
							'label_address',
							index = { 'major': acct_idx, 'minor': addr_idx },
							label = addr_data['label'],
						)

			def make_format_str():
				return '    acct {:O>%s}, addr {:O>%s} [{}]' % (
					len(str( len(data) - 1 )),
					len(str( max(len(acct_data['addresses']) for acct_data in data) - 1))
				)

			def check_restored_data():
				restored_data = h.get_accts(print=False)[1]
				if restored_data != data:
					rmsg('Restored data does not match original dump!  Dumping bad data.')
					MoneroWalletDumpFile.New(
						parent    = self,
						wallet_fn = fn,
						data      = {'wallet_metadata': restored_data} ).write(add_suf='.bad')
					die(3,'Fatal error')

			await super().process_wallet(d,fn,last)

			h = self.rpc(self,d)
			h.open_wallet('newly created')

			msg('')
			data = get_dump_data()
			fs = make_format_str()

			gmsg('\nRestoring accounts, subaddresses and labels from dump file:\n')

			restore_accounts()
			restore_subaddresses()
			restore_labels()

			check_restored_data()

			return True

	class sync(wallet):
		opts = ('rescan_blockchain',)

		def check_uopts(self):
			if self.cfg.rescan_blockchain and self.cfg.watch_only:
				die(1,f'Operation {self.name!r} does not support --rescan-blockchain with watch-only wallets')

		def __init__(self,cfg,uarg_tuple):

			super().__init__(cfg,uarg_tuple)

			if not self.wallet_offline:
				self.dc = self.get_coin_daemon_rpc()

			self.accts_data = {}

		async def process_wallet(self,d,fn,last):

			chain_height = self.dc.call_raw('get_height')['height']
			msg(f'  Chain height: {chain_height}')

			t_start = time.time()

			msg_r('  Opening wallet...')
			self.c.call(
				'open_wallet',
				filename = fn.name,
				password = d.wallet_passwd )
			msg('done')

			msg_r('  Getting wallet height (be patient, this could take a long time)...')
			wallet_height = self.c.call('get_height')['height']
			msg_r('\r' + ' '*68 + '\r')
			msg(f'  Wallet height: {wallet_height}        ')

			behind = chain_height - wallet_height
			if behind > 1000:
				msg_r(f'  Wallet is {behind} blocks behind chain tip.  Please be patient.  Syncing...')

			ret = self.c.call('refresh')

			if behind > 1000:
				msg('done')

			if ret['received_money']:
				msg('  Wallet has received funds')

			for i in range(2):
				wallet_height = self.c.call('get_height')['height']
				if wallet_height >= chain_height:
					break
				ymsg(f'  Wallet failed to sync (wallet height [{wallet_height}] < chain height [{chain_height}])')
				if i or not self.cfg.rescan_blockchain:
					break
				msg_r('  Rescanning blockchain, please be patient...')
				self.c.call('rescan_blockchain')
				self.c.call('refresh')
				msg('done')

			t_elapsed = int(time.time() - t_start)

			a,b = self.rpc(self,d).get_accts(print=False)

			msg('  Balance: {} Unlocked balance: {}'.format(
				hl_amt(a['total_balance']),
				hl_amt(a['total_unlocked_balance']),
			))

			self.accts_data[fn.name] = { 'accts': a, 'addrs': b }

			msg(f'  Wallet height: {wallet_height}')
			msg(f'  Sync time: {t_elapsed//60:02}:{t_elapsed%60:02}')

			if not last:
				self.c.call('close_wallet')

			return wallet_height >= chain_height

		def post_main_success(self):
			d = self.accts_data

			def gen_info():
				for wnum,k in enumerate(d):
					if self.name in ('sync', 'view'):
						yield from self.rpc(self, self.addr_data[wnum]).gen_accts_info(
							d[k]['accts'],
							d[k]['addrs'],
							indent = '')
						yield ''
					elif self.name in ('list', 'listview'):
						fs = '  {:2} {} {} {}'
						yield green(f'Wallet {k}:')
						for acct_num,acct in enumerate(d[k]['addrs']):
							yield ''
							yield '  Account #{a} [{b} {c}]'.format(
								a = acct_num,
								b = self.proto.coin_amt(
									d[k]['accts']['subaddress_accounts'][acct_num]['unlocked_balance'],
									from_unit='atomic').hl(),
								c = self.proto.coin_amt.hlc('XMR')
							)
							yield fs.format('', 'Address'.ljust(95), 'Used ', 'Label')
							for addr in acct['addresses']:
								yield fs.format(
									addr['address_index'],
									CoinAddr(self.proto, addr['address']).hl(),
									(yellow('True ') if addr['used'] else green('False')),
									pink(addr['label']))
						yield ''

				col1_w = max(map(len, d)) + 1
				fs = '{:%s} {} {}' % col1_w
				tbals = [0, 0]
				yield fs.format('Wallet', 'Balance           ', 'Unlocked Balance')

				for k in d:
					b  = d[k]['accts']['total_balance']
					ub = d[k]['accts']['total_unlocked_balance']
					yield fs.format(k + ':', fmt_amt(b), fmt_amt(ub))
					tbals[0] += b
					tbals[1] += ub

				yield fs.format('-'*col1_w, '-'*18, '-'*18)
				yield fs.format('TOTAL:', fmt_amt(tbals[0]), fmt_amt(tbals[1]))

			self.cfg._util.stdout_or_pager('\n'.join(gen_info()) + '\n')

	class list(sync):
		stem = 'sync'

	class view(sync):
		stem = 'open'
		opts = ()
		wallet_offline = True

		def pre_init_action(self):
			ymsg('WARNING: Running in offline mode. Balances and other info may be out of date!')

		async def process_wallet(self,d,fn,last):

			self.c.call(
				'open_wallet',
				filename = fn.name,
				password = d.wallet_passwd)

			wallet_height = self.c.call('get_height')['height']
			msg(f'  Wallet height: {wallet_height}')
			a,b = self.rpc(self, d).get_accts(print=False)
			self.accts_data[fn.name] = {'accts': a, 'addrs': b}

			if not last:
				self.c.call('close_wallet')

			return True

	class listview(view):
		pass

	class spec(wallet): # virtual class

		def create_addr_data(self):
			m = re.fullmatch(uarg_info[self.spec_id].pat,uarg.spec,re.ASCII)
			if not m:
				fs = "{!r}: invalid {!r} arg: for {} operation, it must have format {!r}"
				die(1,fs.format( uarg.spec, self.spec_id, self.name, uarg_info[self.spec_id].annot ))

			def gen():
				for i,k in self.spec_key:
					if m[i] is None:
						setattr(self,k,None)
					else:
						idx = int(m[i])
						try:
							res = self.kal.entry(idx)
						except:
							die(1,f'Supplied key-address file does not contain address {self.kal.al_id.sid}:{idx}')
						else:
							setattr(self,k,res)
							yield res

			self.addr_data = list(gen())
			self.account = None if m[2] is None else int(m[2])

			def strip_quotes(s):
				if s and s[0] in ("'",'"'):
					if s[-1] != s[0] or len(s) < 2:
						die(1,f'{s!r}: unbalanced quotes in label string!')
					return s[1:-1]
				else:
					return s # None or empty string

			if self.name == 'transfer':
				self.dest_addr = CoinAddr(self.proto,m[3])
				self.amount = self.proto.coin_amt(m[4])
			elif self.name == 'new':
				self.label = strip_quotes(m[3])
			elif self.name == 'label':
				self.address_idx = int(m[3])
				self.label = strip_quotes(m[4])

	class sweep(spec):
		spec_id  = 'sweep_spec'
		spec_key = ( (1,'source'), (3,'dest') )
		opts     = ('no_relay','tx_relay_daemon','watch_only')

		def check_uopts(self):
			if self.cfg.tx_relay_daemon and (self.cfg.no_relay or self.cfg.autosign):
				die(1,'--tx-relay-daemon makes no sense in this context!')

		def init_tx_relay_daemon(self):

			m = self.parse_tx_relay_opt()

			wd2 = MoneroWalletDaemon(
				cfg         = self.cfg,
				proto       = self.proto,
				wallet_dir  = self.cfg.wallet_dir or '.',
				test_suite  = self.cfg.test_suite,
				monerod_addr = m[1],
				proxy       = m[2] )

			if self.cfg.test_suite:
				wd2.usr_daemon_args = ['--daemon-ssl-allow-any-cert']

			wd2.start()

			self.c = MoneroWalletRPCClient(
				cfg    = self.cfg,
				daemon = wd2 )

		async def main(self):

			gmsg(f'\n{self.stem.capitalize()}ing account #{self.account} of wallet {self.source.idx}' + (
				f': {self.amount} XMR to {self.dest_addr}' if self.name == 'transfer'
				else ' to new address' if self.dest is None
				else f' to new account in wallet {self.dest.idx}' ))

			h = self.rpc(self,self.source)

			h.open_wallet('source')
			accts_data = h.get_accts()[0]

			max_acct = len(accts_data['subaddress_accounts']) - 1
			if self.account > max_acct:
				die(2, f'{self.account}: requested account index out of bounds (>{max_acct})')

			h.print_addrs(accts_data,self.account)

			if self.name == 'transfer':
				dest_addr = self.dest_addr
			elif self.dest is None:
				dest_acct = self.account
				if keypress_confirm( self.cfg, f'\nCreate new address for account #{self.account}?' ):
					dest_addr_chk = h.create_new_addr(self.account)
				elif keypress_confirm( self.cfg, f'Sweep to last existing address of account #{self.account}?' ):
					dest_addr_chk = None
				else:
					die(1,'Exiting at user request')
				dest_addr,dest_addr_idx = h.get_last_addr(self.account,display=not dest_addr_chk)
				assert dest_addr_chk in (None,dest_addr), 'dest_addr_chk1'
				h.print_addrs(accts_data,self.account)
			else:
				h.close_wallet('source')
				wf = self.get_wallet_fn(self.dest)
				h2 = self.rpc(self,self.dest)
				h2.open_wallet('destination')
				accts_data = h2.get_accts()[0]

				if keypress_confirm( self.cfg, f'\nCreate new account for wallet {wf.name!r}?' ):
					dest_acct,dest_addr = h2.create_acct(
						label = f'Sweep from {self.source.idx}:{self.account} [{make_timestr()}]')
					dest_addr_idx = 0
					h2.get_accts()
				elif keypress_confirm( self.cfg, f'Sweep to last existing account of wallet {wf.name!r}?' ):
					dest_acct,dest_addr_chk = h2.get_last_acct(accts_data)
					dest_addr,dest_addr_idx = h2.get_last_addr(dest_acct,display=False)
					assert dest_addr_chk == dest_addr, 'dest_addr_chk2'
				else:
					die(1,'Exiting at user request')

				h2.close_wallet('destination')
				h.open_wallet('source',refresh=False)

			msg(f'\n    Creating {self.name} transaction...')

			if self.name == 'transfer':
				new_tx = h.make_transfer_tx(self.account,dest_addr,self.amount)
			elif self.name == 'sweep':
				new_tx = h.make_sweep_tx(self.account,dest_acct,dest_addr_idx,dest_addr)

			msg('\n' + new_tx.get_info(indent='    '))

			if self.cfg.tx_relay_daemon:
				self.display_tx_relay_info(indent='    ')

			msg('Saving TX data to file')
			new_tx.write(delete_metadata=True)

			if self.cfg.no_relay or self.cfg.autosign:
				return True

			if keypress_confirm( self.cfg, f'Relay {self.name} transaction?' ):
				if self.cfg.tx_relay_daemon:
					await h.stop_wallet('source')
					msg('')
					self.init_tx_relay_daemon()
					h = self.rpc(self,self.source)
					h.open_wallet('TX-relay-configured source',refresh=False)
				msg_r(f'\n    Relaying {self.name} transaction...')
				h.relay_tx(new_tx.data.metadata)
				gmsg('\nAll done')
				return True
			else:
				die(1,'\nExiting at user request')

	class transfer(sweep):
		stem    = 'transferr'
		spec_id = 'transfer_spec'
		spec_key = ( (1,'source'), )

	class new(spec):
		spec_id = 'newaddr_spec'
		spec_key = ( (1,'source'), )
		wallet_offline = True

		async def main(self):
			h = self.rpc(self,self.source)
			h.open_wallet('Monero')

			desc = 'account' if self.account is None else 'address'
			label = (
				None if self.label == '' else
				'{} [{}]'.format(self.label or f'xmrwallet new {desc}', make_timestr()))

			accts_data = h.get_accts()[0]
			if desc == 'address':
				h.print_addrs(accts_data,self.account)

			if keypress_confirm(
					self.cfg,
					'\nCreating new {a} for wallet {b}{c} with {d}\nOK?'.format(
						a = desc,
						b = red(str(self.source.idx)),
						c = '' if desc == 'account' else f', account {red("#"+str(self.account))}',
						d = 'label ' + pink('‘'+label+'’') if label else 'empty label')
					):

				if desc == 'address':
					h.create_new_addr(self.account,label=label)
				else:
					h.create_acct(label=label)

				accts_data = h.get_accts()[0]
				if desc == 'address':
					h.print_addrs(accts_data,self.account)
			else:
				ymsg('\nOperation cancelled by user request')

			# wallet must be left open: otherwise the 'stop_wallet' RPC call used to stop the daemon will fail
			if self.cfg.no_stop_wallet_daemon:
				h.close_wallet('Monero')

			msg('')

	class label(spec):
		spec_id  = 'label_spec'
		spec_key = ( (1,'source'), )
		opts     = ()
		wallet_offline = True

		async def main(self):

			gmsg('\n{a} label for wallet {b}, account #{c}, address #{d}'.format(
				a = 'Setting' if self.label else 'Removing',
				b = self.source.idx,
				c = self.account,
				d = self.address_idx
			))
			h = self.rpc(self,self.source)

			h.open_wallet('source')
			accts_data = h.get_accts()[0]

			max_acct = len(accts_data['subaddress_accounts']) - 1
			if self.account > max_acct:
				die(2, f'{self.account}: requested account index out of bounds (>{max_acct})')

			ret = h.print_addrs(accts_data,self.account)

			if self.address_idx > len(ret['addresses']) - 1:
				die(2, '{}: requested address index out of bounds (>{})'.format(
					self.address_idx,
					len(ret['addresses']) - 1 ))

			addr = ret['addresses'][self.address_idx]
			new_label = f'{self.label} [{make_timestr()}]' if self.label else ''

			msg('\n  {a} {b}\n  {c} {d}\n  {e} {f}'.format(
					a = 'Address:       ',
					b = cyan(addr['address'][:15] + '...'),
					c = 'Existing label:',
					d = pink(addr['label']) if addr['label'] else gray('[none]'),
					e = 'New label:     ',
					f = pink(new_label) if new_label else gray('[none]') ))

			op = 'remove' if not new_label else 'update' if addr['label'] else 'set'

			if addr['label'] == new_label:
				ymsg('\nLabel is unchanged, operation cancelled')
			elif keypress_confirm(self.cfg, f'  {op.capitalize()} label?'):
				h.set_label(self.account, self.address_idx, new_label)
				accts_data = h.get_accts(print=False)[0]
				ret = h.print_addrs(accts_data,self.account)
				label_chk = ret['addresses'][self.address_idx]['label']
				if label_chk != new_label:
					ymsg(f'Warning: new label {label_chk!r} does not match requested value!')
					return False
				else:
					msg(cyan('\nLabel successfully {}'.format('set' if op == 'set' else op+'d')))
			else:
				ymsg('\nOperation cancelled by user request')

	class sign(wallet):
		action = 'signing transaction with'
		start_daemon = False
		offline = True

		async def main(self,fn,restart_daemon=True):
			if restart_daemon:
				await self.restart_wallet_daemon()
			tx = MoneroMMGenTX.Unsigned( self.cfg, fn )
			h = self.rpc(self,self.addr_data[0])
			self.head_msg(tx.src_wallet_idx,h.fn)
			if restart_daemon:
				h.open_wallet(refresh=False)
			res = self.c.call(
				'sign_transfer',
				unsigned_txset = tx.data.unsigned_txset,
				export_raw = True,
				get_tx_keys = True
			)
			new_tx = MoneroMMGenTX.NewColdSigned(
				cfg            = self.cfg,
				txid           = res['tx_hash_list'][0],
				unsigned_txset = None,
				signed_txset   = res['signed_txset'],
				_in_tx         = tx,
			)
			return new_tx

	class submit(wallet):
		action = 'submitting transaction with'
		opts = ('tx_relay_daemon',)

		def post_mount_action(self):
			self.tx # trigger an exit if no suitable transaction present

		def die_no_tx(self,desc,num_txs,tx_dir):
			die('AutosignTXError', "{a} {b} transaction{c} in '{d}'!".format(
				a = 'More than one' if num_txs else 'No',
				b = desc,
				c = suf(num_txs),
				d = tx_dir,
			))

		@property
		def tx(self):
			if not hasattr(self,'_tx'):
				self._tx = self.get_tx()
			return self._tx

		def get_tx(self):
			if uarg.infile:
				fn = Path(uarg.infile)
			else:
				from .autosign import Signable
				t = Signable.xmr_transaction(self.asi)
				if len(t.unsubmitted) == 1:
					fn = t.unsubmitted[0]
				else:
					self.die_no_tx( 'unsubmitted', len(t.unsubmitted), t.parent.xmr_tx_dir )
			return MoneroMMGenTX.ColdSigned( cfg=self.cfg, fn=fn )

		def get_relay_rpc(self):

			relay_opt = self.parse_tx_relay_opt()

			wd = MoneroWalletDaemon(
				cfg         = self.cfg,
				proto       = self.proto,
				wallet_dir  = self.cfg.wallet_dir or '.',
				test_suite  = self.cfg.test_suite,
				monerod_addr = relay_opt[1],
			)

			u = wd.usr_daemon_args = []
			if self.cfg.test_suite:
				u.append('--daemon-ssl-allow-any-cert')
			if relay_opt[2]:
				u.append(f'--proxy={relay_opt[2]}')

			return MoneroWalletRPCClient(
				cfg             = self.cfg,
				daemon          = wd,
				test_connection = False,
			)

		async def main(self):
			tx = self.tx
			h = self.rpc( self, self.kal.entry(tx.src_wallet_idx) )
			self.head_msg(tx.src_wallet_idx,h.fn)
			h.open_wallet()

			if self.cfg.tx_relay_daemon:
				await self.c.stop_daemon()
				self.c = self.get_relay_rpc()
				self.c.start_daemon()
				h = self.rpc( self, self.kal.entry(tx.src_wallet_idx) )
				h.open_wallet( 'TX-relay-configured watch-only', refresh=False )

			msg('\n' + tx.get_info(indent='    '))

			if self.cfg.tx_relay_daemon:
				self.display_tx_relay_info(indent='    ')

			if keypress_confirm( self.cfg, f'{self.name.capitalize()} transaction?' ):
				if self.cfg.tx_relay_daemon:
					msg_r('Relaying transaction to remote daemon, please be patient...')
				res = self.c.call(
					'submit_transfer',
					tx_data_hex = tx.data.signed_txset )
				assert res['tx_hash_list'][0] == tx.data.txid, 'TxID mismatch in ‘submit_transfer’ result!'
				if self.cfg.tx_relay_daemon:
					msg('success')
			else:
				die(1,'Exiting at user request')

			new_tx = MoneroMMGenTX.NewSubmitted(
				cfg          = self.cfg,
				_in_tx       = tx,
			)
			gmsg('\nOK')
			new_tx.write(
				ask_write     = not self.cfg.autosign,
				ask_overwrite = not self.cfg.autosign )
			return new_tx

	class resubmit(submit):
		action = 'resubmitting transaction with'

		def check_uopts(self):
			if not self.cfg.autosign:
				die(1,'--autosign is required for this operation')

		def get_tx(self):
			files = [f for f in self.asi.xmr_tx_dir.iterdir()
						if f.name.endswith('.'+MoneroMMGenTX.Submitted.ext)]
			txs = sorted(
				(MoneroMMGenTX.Submitted( self.cfg, Path(fn) ) for fn in files),
					key = lambda x: getattr(x.data,'submit_time',None) or x.data.create_time
			)
			if txs:
				return txs[-1]
			else:
				self.die_no_tx('submitted', 0, self.asi.xmr_tx_dir)

	class dump(wallet):
		wallet_offline = True

		async def process_wallet(self,d,fn,last):
			h = self.rpc(self,d)
			h.open_wallet('source')
			_,addr_data = h.get_accts(print=False)
			msg('')
			MoneroWalletDumpFile.New(
				parent    = self,
				wallet_fn = fn,
				data      = {'wallet_metadata': addr_data} ).write()
			return True

	class export_outputs(wallet):
		action = 'exporting outputs from'
		stem = 'process'
		opts = ('rescan_blockchain',)

		async def process_wallet(self,d,fn,last):
			h = self.rpc(self,d)
			h.open_wallet('source')

			if self.cfg.rescan_blockchain:
				gmsg_r('\n  Rescanning blockchain...')
				self.c.call('rescan_blockchain')
				gmsg('done')

			self.head_msg(d.idx,h.fn)
			for ftype in ('Unsigned','Signed'):
				old_fn = getattr(MoneroWalletOutputsFile,ftype).find_fn_from_wallet_fn(
					cfg             = self.cfg,
					wallet_fn       = fn,
					ret_on_no_match = True )
				if old_fn:
					old_fn.unlink()
			m = MoneroWalletOutputsFile.New(
				parent    = self,
				wallet_fn = fn,
				data      = self.c.call('export_outputs', all=True),
			)
			m.write()
			return True

	class export_key_images(wallet):
		action = 'signing wallet outputs file with'
		start_daemon = False
		offline = True

		async def main(self,fn,wallet_idx,restart_daemon=True):
			if restart_daemon:
				await self.restart_wallet_daemon()
			h = self.rpc(self,self.addr_data[0])
			self.head_msg(wallet_idx,fn)
			if restart_daemon:
				h.open_wallet(refresh=False)
			m = MoneroWalletOutputsFile.Unsigned(
				parent = self,
				fn     = fn )
			res = self.c.call(
				'import_outputs',
				outputs_data_hex = m.data.outputs_data_hex )
			idata = res['num_imported']
			bmsg(f'\n  {idata} output{suf(idata)} imported')
			data = m.data._asdict()
			data.update(self.c.call('export_key_images', all=True))
			m = MoneroWalletOutputsFile.SignedNew(
				parent    = self,
				wallet_fn = m.get_wallet_fn(fn),
				data      = data )
			idata = m.data.signed_key_images or []
			bmsg(f'  {len(idata)} key image{suf(idata)} signed')
			return m

	class import_key_images(wallet):
		action = 'importing key images into'
		stem = 'process'
		trust_monerod = True

		def post_main_failure(self):
			rw_msg = ' for requested wallets' if uarg.wallets else ''
			die(2, f'No signed key image files found{rw_msg}!')

		async def process_wallet(self,d,fn,last):
			keyimage_fn = MoneroWalletOutputsFile.Signed.find_fn_from_wallet_fn( self.cfg, fn, ret_on_no_match=True )
			if not keyimage_fn:
				msg(f'No signed key image file found for wallet #{d.idx}')
				return False
			h = self.rpc(self,d)
			h.open_wallet()
			self.head_msg(d.idx,h.fn)
			m = MoneroWalletOutputsFile.Signed( parent=self, fn=keyimage_fn )
			data = m.data.signed_key_images or []
			bmsg(f'\n  {len(data)} signed key image{suf(data)} to import')
			if data:
				res = self.c.call( 'import_key_images', signed_key_images=data )
				bmsg(f'  Success: {res}')
			return True

	class relay(base):
		opts = ('tx_relay_daemon',)

		def __init__(self,cfg,uarg_tuple):

			super().__init__(cfg,uarg_tuple)

			self.mount_removable_device()

			self.tx = MoneroMMGenTX.Signed( self.cfg, Path(uarg.infile) )

			if self.cfg.tx_relay_daemon:
				m = self.parse_tx_relay_opt()
				host,port = m[1].split(':')
				proxy = m[2]
				md = None
			else:
				from .daemon import CoinDaemon
				md = CoinDaemon( self.cfg, 'xmr', test_suite=self.cfg.test_suite )
				host,port = ('localhost', md.rpc_port)
				proxy = None

			self.dc = MoneroRPCClient(
				cfg    = self.cfg,
				proto  = self.proto,
				daemon = md,
				host   = host,
				port   = int(port),
				user   = None,
				passwd = None,
				test_connection = host == 'localhost', # avoid extra connections if relay is a public node
				proxy  = proxy )

		async def main(self):
			msg('\n' + self.tx.get_info(indent='    '))

			if self.cfg.tx_relay_daemon:
				self.display_tx_relay_info(indent='    ')

			if keypress_confirm( self.cfg, 'Relay transaction?' ):
				res = self.dc.call_raw(
					'send_raw_transaction',
					tx_as_hex = self.tx.data.blob
				)
				if res['status'] == 'OK':
					msg('Status: ' + green('OK'))
					if res['not_relayed']:
						ymsg('Transaction not relayed')
					return True
				else:
					die( 'RPCFailure', repr(res) )
			else:
				die(1,'Exiting at user request')

	class txview(base):
		view_method = 'get_info'
		opts = ('watch_only','autosign')
		hdr = ''
		col_hdr = ''
		footer = ''
		cols = None
		do_umount = False

		async def main(self,cols=None):

			self.mount_removable_device()

			if self.cfg.autosign:
				files = [f for f in self.asi.xmr_tx_dir.iterdir()
							if f.name.endswith('.'+MoneroMMGenTX.Submitted.ext)]
			else:
				files = uarg.infile

			txs = sorted(
				(MoneroMMGenTX.View( self.cfg, Path(fn) ) for fn in files),
					# old TX files have no ‘submit_time’ field:
					key = lambda x: getattr(x.data,'submit_time',None) or x.data.create_time
			)

			if self.cfg.autosign:
				self.asi.do_umount()

			self.cfg._util.stdout_or_pager(
				(self.hdr if len(files) > 1 else '')
				+ self.col_hdr
				+ '\n'.join(getattr(tx,self.view_method)(cols=cols) for tx in txs)
				+ self.footer
			)

	class txlist(txview):
		view_method = 'get_info_oneline'
		add_nl = True
		footer = '\n'

		@property
		def hdr(self):
			return ('SUBMITTED ' if self.cfg.autosign else '') + 'MONERO TRANSACTIONS\n'

		@property
		def col_hdr(self):
			return MoneroMMGenTX.View.oneline_fs.format(
				a = 'Network',
				b = 'Seed ID',
				c = 'Submitted' if self.cfg.autosign else 'Date',
				d = 'TxID',
				e = 'Type',
				f = 'Src',
				g = 'Dest',
				h = '  Amount',
				j = 'Dest Address',
				x = '',
			) + '\n'

		async def main(self):
			if self.cfg.pager:
				cols = None
			else:
				from .term import get_terminal_size
				cols = self.cfg.columns or get_terminal_size().width
				if cols < 106:
					die(1, 'A terminal at least 106 columns wide is required to display this output'
						+ ' (or use --columns or --pager)' )
			await super().main(cols=cols)

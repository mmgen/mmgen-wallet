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
test.cmdtest_d.ct_ref_altcoin: Altcoin reference file tests for the cmdtest.py test suite
"""

from mmgen.color import set_vt100

from .common import pwfile, dfl_wpasswd, ref_dir, dfl_words_file, dfl_addr_idx_list
from ..include.common import cfg, joinpath, start_test_daemons, stop_test_daemons, cmp_or_die
from .ct_ref import CmdTestRef
from .ct_base import CmdTestBase

class CmdTestRefAltcoin(CmdTestRef, CmdTestBase):
	'saved and generated altcoin reference files'
	tmpdir_nums = [8]
	networks = ('btc',)
	chk_data = {
		'ref_addrfile_chksum_zec':        '903E 7225 DD86 6E01',
		'ref_addrfile_chksum_zec_z':      '9C7A 72DC 3D4A B3AF',
		'ref_addrfile_chksum_xmr':        '4369 0253 AC2C 0E38',
		'ref_addrfile_chksum_dash':       'FBC1 6B6A 0988 4403',
		'ref_addrfile_chksum_eth':        'E554 076E 7AF6 66A3',
		'ref_addrfile_chksum_etc':        'E97A D796 B495 E8BC',
		'ref_keyaddrfile_chksum_zec':     'F05A 5A5C 0C8E 2617',
		'ref_keyaddrfile_chksum_zec_z':   '6B87 9B2D 0D8D 8D1E',
		'ref_keyaddrfile_chksum_xmr':     'E0D7 9612 3D67 404A',
		'ref_viewkeyaddrfile_chksum_xmr': '40C9 0E61 B743 229C',
		'ref_keyaddrfile_chksum_dash':    'E83D 2C63 FEA2 4142',
		'ref_keyaddrfile_chksum_eth':     'E400 70D9 0AE3 C7C2',
		'ref_keyaddrfile_chksum_etc':     'EF49 967D BD6C FE45',
	}
	cmd_group = (
		('ref_altcoin_tx_chk',          'signing saved reference tx files'),
		('ref_addrfile_gen_eth',        'generate address file (ETH)'),
		('ref_addrfile_gen_etc',        'generate address file (ETC)'),
		('ref_addrfile_gen_dash',       'generate address file (DASH)'),
		('ref_addrfile_gen_zec',        'generate address file (ZEC-T)'),
		('ref_addrfile_gen_zec_z',      'generate address file (ZEC-Z)'),
		('ref_addrfile_gen_xmr',        'generate address file (XMR)'),

		('ref_keyaddrfile_gen_eth',     'generate key-address file (ETH)'),
		('ref_keyaddrfile_gen_etc',     'generate key-address file (ETC)'),
		('ref_keyaddrfile_gen_dash',    'generate key-address file (DASH)'),
		('ref_keyaddrfile_gen_zec',     'generate key-address file (ZEC-T)'),
		('ref_keyaddrfile_gen_zec_z',   'generate key-address file (ZEC-Z)'),
		('ref_keyaddrfile_gen_xmr',     'generate key-address file (XMR)'),
		('ref_viewkeyaddrfile_gen_xmr', 'generate viewkey-address file (XMR)'),

		('ref_addrfile_chk_eth',        'reference address file (ETH)'),
		('ref_addrfile_chk_etc',        'reference address file (ETC)'),
		('ref_addrfile_chk_dash',       'reference address file (DASH)'),
		('ref_addrfile_chk_zec',        'reference address file (ZEC-T)'),
		('ref_addrfile_chk_zec_z',      'reference address file (ZEC-Z)'),
		('ref_addrfile_chk_xmr',        'reference address file (XMR)'),

		('ref_keyaddrfile_chk_eth',     'reference key-address file (ETH)'),
		('ref_keyaddrfile_chk_etc',     'reference key-address file (ETC)'),
		('ref_keyaddrfile_chk_dash',    'reference key-address file (DASH)'),
		('ref_keyaddrfile_chk_zec',     'reference key-address file (ZEC-T)'),
		('ref_keyaddrfile_chk_zec_z',   'reference key-address file (ZEC-Z)'),
		('ref_keyaddrfile_chk_xmr',     'reference key-address file (XMR)'),
		('ref_viewkeyaddrfile_chk_xmr', 'reference viewkey-address file (XMR)'),
	)

	def ref_altcoin_tx_chk(self):
		"""
		Check saved transaction files for *all* configured altcoins
		Though this basically duplicates the autosign test, here we do everything
		via the command line, so it's worth doing
		"""
		self.write_to_tmpfile(pwfile, dfl_wpasswd)
		passfile = joinpath(self.tmpdir, pwfile)
		from mmgen.tx.file import MMGenTxFile
		src = CmdTestRef.sources['ref_tx_file']
		for coin, files in src.items():
			if coin == 'mm1':
				coin = 'eth'
				token_desc = ':MM1'
			else:
				token_desc = ''
			for fn in files:
				if not fn: # no etc testnet TX file
					continue
				txfile = joinpath(
					ref_dir,
					self._get_ref_subdir_by_coin(coin),
					fn)
				proto = MMGenTxFile.get_proto(cfg, txfile, quiet_open=True)
				if proto.sign_mode == 'daemon':
					start_test_daemons(proto.network_id)
					set_vt100()
				t = self.spawn(
					'mmgen-txsign',
					['--outdir=test/trash', '--yes', f'--passwd-file={passfile}', dfl_words_file, txfile],
					extra_desc = f'{proto.coin}{token_desc} {proto.network}')
				t.read()
				t.ok()
				if proto.sign_mode == 'daemon' and not proto.network_id == 'btc':
					stop_test_daemons(proto.network_id)
		return 'ok'

	def ref_altcoin_addrgen(
			self,
			coin,
			mmtype,
			gen_what      = 'addr',
			coin_suf      = '',
			add_args      = [],
			addr_idx_list = None):
		wf = dfl_words_file
		t = self.spawn(
				'mmgen-keygen' if 'key' in gen_what else 'mmgen-addrgen',
				['-Sq', '--coin='+coin] +
				(['--type='+mmtype] if mmtype else []) +
				add_args +
				[wf, addr_idx_list or dfl_addr_idx_list])
		if 'key' in gen_what:
			t.expect('Encrypt key list? (y/N): ', 'N')
		chk = t.expect_getend(r'.* data checksum for \S*: ', regex=True)
		chk_ref = self.chk_data[
			'ref_{}addrfile_chksum_{}{}'.format(
				(gen_what if 'key' in gen_what else ''),
				coin.lower(),
				coin_suf)
		]
		cmp_or_die(chk, chk_ref, desc=f'{gen_what}list data checksum')
		return t

	def ref_addrfile_gen_eth(self):
		return self.ref_altcoin_addrgen(coin='ETH', mmtype='ethereum')

	def ref_addrfile_gen_etc(self):
		return self.ref_altcoin_addrgen(coin='ETC', mmtype='ethereum')

	def ref_addrfile_gen_dash(self):
		return self.ref_altcoin_addrgen(coin='DASH', mmtype='compressed')

	def ref_addrfile_gen_zec(self):
		return self.ref_altcoin_addrgen(coin='ZEC', mmtype='compressed')

	def ref_addrfile_gen_zec_z(self):
		return self.ref_altcoin_addrgen(coin='ZEC', mmtype='zcash_z', coin_suf='_z')

	def ref_addrfile_gen_xmr(self):
		return self.ref_altcoin_addrgen(coin='XMR', mmtype='monero')

	def ref_addrfile_gen_xmr_slow(self):
		return self.ref_altcoin_addrgen(coin='XMR', mmtype='monero', add_args=['--keygen-backend=2'])

	def ref_keyaddrfile_gen_eth(self):
		return self.ref_altcoin_addrgen(coin='ETH', mmtype='ethereum', gen_what='key')

	def ref_keyaddrfile_gen_etc(self):
		return self.ref_altcoin_addrgen(coin='ETC', mmtype='ethereum', gen_what='key')

	def ref_keyaddrfile_gen_dash(self):
		return self.ref_altcoin_addrgen(coin='DASH', mmtype='compressed', gen_what='key')

	def ref_keyaddrfile_gen_zec(self):
		return self.ref_altcoin_addrgen(coin='ZEC', mmtype='compressed', gen_what='key')

	def ref_keyaddrfile_gen_zec_z(self):
		return self.ref_altcoin_addrgen(coin='ZEC', mmtype='zcash_z', coin_suf='_z', gen_what='key')

	def ref_keyaddrfile_gen_xmr(self):
		return self.ref_altcoin_addrgen(coin='XMR', mmtype='monero', gen_what='key')

	def ref_viewkeyaddrfile_gen_xmr(self):
		return self.ref_altcoin_addrgen(
			coin          = 'XMR',
			mmtype        = 'monero',
			gen_what      = 'viewkey',
			add_args      = ['--viewkeys'],
			addr_idx_list = '1-3')

	def ref_addrfile_chk_eth(self):
		return self.ref_addrfile_chk(ftype='addr', coin='ETH', subdir='ethereum', pfx='-ETH',
				pat='ETH Mainnet.*Ethereum')

	def ref_addrfile_chk_etc(self):
		return self.ref_addrfile_chk(ftype='addr', coin='ETC', subdir='ethereum_classic', pfx='-ETC',
				pat='ETH Mainnet.*Ethereum')

	def ref_addrfile_chk_dash(self):
		return self.ref_addrfile_chk(ftype='addr', coin='DASH', subdir='dash', pfx='-DASH-C',
				pat='DASH Mainnet.*Compressed')

	def ref_addrfile_chk_zec(self):
		return self.ref_addrfile_chk(ftype='addr', coin='ZEC', subdir='zcash', pfx='-ZEC-C',
				pat='ZEC Mainnet.*Compressed')

	def ref_addrfile_chk_zec_z(self):
		return self.ref_addrfile_chk(ftype='addr', coin='ZEC', subdir='zcash', pfx='-ZEC-Z', mmtype='z',
				pat='ZEC Mainnet.*Zcash_z')

	def ref_addrfile_chk_xmr(self):
		return self.ref_addrfile_chk(ftype='addr', coin='XMR', subdir='monero', pfx='-XMR-M',
				pat='XMR Mainnet.*Monero')

	def ref_keyaddrfile_chk_eth(self):
		return self.ref_addrfile_chk(ftype='keyaddr', coin='ETH', subdir='ethereum', pfx='-ETH',
				pat='ETH Mainnet.*Ethereum')

	def ref_keyaddrfile_chk_etc(self):
		return self.ref_addrfile_chk(ftype='keyaddr', coin='ETC', subdir='ethereum_classic', pfx='-ETC',
				pat='ETH Mainnet.*Ethereum')

	def ref_keyaddrfile_chk_dash(self):
		return self.ref_addrfile_chk(ftype='keyaddr', coin='DASH', subdir='dash', pfx='-DASH-C',
				pat='DASH Mainnet.*Compressed')

	def ref_keyaddrfile_chk_zec(self):
		return self.ref_addrfile_chk(ftype='keyaddr', coin='ZEC', subdir='zcash', pfx='-ZEC-C',
				pat='ZEC Mainnet.*Compressed')

	def ref_keyaddrfile_chk_zec_z(self):
		return self.ref_addrfile_chk(ftype='keyaddr', coin='ZEC', subdir='zcash', pfx='-ZEC-Z', mmtype='z',
				pat='ZEC Mainnet.*Zcash_z')

	def ref_keyaddrfile_chk_xmr(self):
		return self.ref_addrfile_chk(ftype='keyaddr', coin='XMR', subdir='monero', pfx='-XMR-M',
				pat='XMR Mainnet.*Monero')

	def ref_viewkeyaddrfile_chk_xmr(self):
		return self.ref_addrfile_chk(ftype='viewkeyaddr', coin='XMR', subdir='monero', pfx='-XMR-M',
				pat='XMR Mainnet.*Monero')

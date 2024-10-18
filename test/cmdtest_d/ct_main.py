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
test.cmdtest_d.ct_main: Basic operations tests for the cmdtest.py test suite
"""

import sys, os

from mmgen.util import msg, msg_r, async_run, capfirst, get_extension, die
from mmgen.color import green, cyan, gray
from mmgen.fileutil import get_data_from_file, write_data_to_file
from mmgen.wallet import get_wallet_cls
from mmgen.wallet.mmgen import wallet as MMGenWallet
from mmgen.wallet.incog import wallet as IncogWallet
from mmgen.rpc import rpc_init

from ..include.common import (
	cfg,
	vmsg,
	joinpath,
	silence,
	end_silence,
	getrand,
	getrandnum,
	getrandnum_range,
	getrandhex,
	strip_ansi_escapes
)
from .common import (
	pwfile,
	hincog_fn,
	get_file_with_ext,
	get_comment,
	tx_comment_lat_cyr_gr,
	hincog_offset,
	hincog_bytes,
	hincog_seedlen,
	incog_id_fn,
	non_mmgen_fn
)
from .ct_base import CmdTestBase
from .ct_shared import CmdTestShared

def make_brainwallet_file(fn):
	# Print random words with random whitespace in between
	wl = rwords.split()
	nwords, ws_list, max_spaces = 10, '    \n', 5
	def rand_ws_seq():
		nchars = getrandnum(1) % max_spaces + 1
		return ''.join([ws_list[getrandnum_range(1, 200) % len(ws_list)] for i in range(nchars)])
	rand_pairs = [wl[getrandnum_range(1, 200) % len(wl)] + rand_ws_seq() for i in range(nwords)]
	d = ''.join(rand_pairs).rstrip() + '\n'
	if cfg.verbose:
		msg_r(f'Brainwallet password:\n{cyan(d)}')
	write_data_to_file(cfg, fn, d, 'brainwallet password', quiet=True, ignore_opt_outdir=True)

def verify_checksum_or_exit(checksum, chk):
	chk = strip_ansi_escapes(chk)
	if checksum != chk:
		die('TestSuiteFatalException', f'Checksum error: {chk}')
	vmsg(green('Checksums match: ') + cyan(chk))

addrs_per_wallet = 8

# 100 words chosen randomly from here:
#   https://github.com/bitcoin/bips/pull/432/files/6332230d63149a950d05db78964a03bfd344e6b0
rwords = """
	алфавит алый амнезия амфора артист баян белый биатлон брат бульвар веревка вернуть весть возраст
	восток горло горный десяток дятел ежевика жест жизнь жрать заговор здание зона изделие итог кабина
	кавалер каждый канал керосин класс клятва князь кривой крыша крючок кузнец кукла ландшафт мальчик
	масса масштаб матрос мрак муравей мычать негодяй носок ночной нрав оборот оружие открытие оттенок
	палуба пароход период пехота печать письмо позор полтора понятие поцелуй почему приступ пруд пятно
	ранее режим речь роса рынок рябой седой сердце сквозь смех снимок сойти соперник спичка стон
	сувенир сугроб суть сцена театр тираж толк удивить улыбка фирма читатель эстония эстрада юность
	"""

class CmdTestMain(CmdTestBase, CmdTestShared):
	'basic operations with emulated tracking wallet'
	tmpdir_nums = [1, 2, 3, 4, 5, 14, 15, 16, 20, 21]
	networks = ('btc', 'btc_tn', 'ltc', 'ltc_tn', 'bch', 'bch_tn')
	passthru_opts = ('daemon_data_dir', 'rpc_port', 'coin', 'testnet', 'rpc_backend')
	segwit_opts_ok = True
	color = True
	need_daemon = True
	cmd_group = (
		('walletgen_dfl_wallet',
			(15, 'wallet generation (default wallet)', [[[], 15]])
		),
		('subwalletgen_dfl_wallet',
			(15, 'subwallet generation (default wallet)', [[[pwfile], 15]])
		),
		('export_seed_dfl_wallet',
			(15, 'seed export to mmseed format (default wallet)', [[[pwfile], 15]])),
		('addrgen_dfl_wallet',
			(15, 'address generation (default wallet)', [[[pwfile], 15]])
		),
		('txcreate_dfl_wallet',
			(15, 'transaction creation (default wallet)', [[['addrs'], 15]])
		),
		('txsign_dfl_wallet',
			(15, 'transaction signing (default wallet)', [[['rawtx', pwfile], 15]])
		),
		('passchg_dfl_wallet',
			(16, 'password, label and hash preset change (default wallet)', [[[pwfile], 15]])
		),
		('walletchk_newpass_dfl_wallet',
			(16, 'wallet check with new pw, label and hash preset', [[[pwfile], 16]])
		),
		('delete_dfl_wallet',
			(15, 'delete default wallet', [[[pwfile], 15]])
		),
		('walletgen',
			(1, 'wallet generation', [[['del_dw_run'], 15]])
		),
		('subwalletgen',
			(1, 'subwallet generation', [[['mmdat'], 1]])
		),
		('subwalletgen_mnemonic',
			(1, 'subwallet generation (to mnemonic format)', [[['mmdat'], 1]])
		),
		# ('walletchk', (1, 'wallet check', [[['mmdat'], 1]])),
		('passchg',
			(5, 'password, label and hash preset change', [[['mmdat', pwfile], 1]])
		),
		('passchg_keeplabel',
			(5, 'password, label and hash preset change (keep label)', [[['mmdat', pwfile], 1]])
		),
		('passchg_usrlabel',
			(5, 'password, label and hash preset change (interactive label)', [[['mmdat', pwfile], 1]])
		),
		('walletchk_newpass',
			(5, 'wallet check with new pw, label and hash preset', [[['mmdat', pwfile], 5]])
		),
		('addrgen',
			(1, 'address generation', [[['mmdat'], 1]])
		),
		('txcreate',
			(1, 'transaction creation', [[['addrs'], 1]])
		),
		('txbump',
			(1, 'transaction fee bumping (no send)', [[['rawtx'], 1]])
		),
		('txsign',
			(1, 'transaction signing', [[['mmdat', 'rawtx'], 1]])
		),
		('txsend',
			(1, 'transaction sending', [[['sigtx'], 1]])
		),
		# txdo must go after txsign
		('txdo',
			(1, 'online transaction', [[['sigtx', 'mmdat'], 1]])
		),
		('export_seed',
			(1, 'seed export to mmseed format', [[['mmdat'], 1]])
		),
		('export_hex',
			(1, 'seed export to hexadecimal format', [[['mmdat'], 1]])
		),
		('export_mnemonic',
			(1, 'seed export to mmwords format', [[['mmdat'], 1]])
		),
		('export_bip39',
			(1, 'seed export to bip39 format', [[['mmdat'], 1]])
		),
		('export_incog',
			(1, 'seed export to mmincog format', [[['mmdat'], 1]])
		),
		('export_incog_hex',
			(1, 'seed export to mmincog hex format', [[['mmdat'], 1]])
		),
		('export_incog_hidden',
			(1, 'seed export to hidden mmincog format', [[['mmdat'], 1]])
		),
		('addrgen_seed',
			(1, 'address generation from mmseed file', [[['mmseed', 'addrs'], 1]])
		),
		('addrgen_hex',
			(1, 'address generation from mmhex file', [[['mmhex', 'addrs'], 1]])
		),
		('addrgen_mnemonic',
			(1, 'address generation from mmwords file', [[['mmwords', 'addrs'], 1]])
		),
		('addrgen_incog',
			(1, 'address generation from mmincog file', [[['mmincog', 'addrs'], 1]])
		),
		('addrgen_incog_hex',
			(1, 'address generation from mmincog hex file', [[['mmincox', 'addrs'], 1]])
		),
		('addrgen_incog_hidden',
			(1, 'address generation from hidden mmincog file', [[[hincog_fn, 'addrs'], 1]])
		),
		('keyaddrgen',
			(1, 'key-address file generation', [[['mmdat'], 1]])
		),
		('txsign_keyaddr',
			(1, 'transaction signing with key-address file', [[['akeys.mmenc', 'rawtx'], 1]])
		),
		('txcreate_ni',
			(1, 'transaction creation (non-interactive)', [[['addrs'], 1]])
		),
		('walletgen2',
			(2, 'wallet generation (2), 128-bit seed', [[['del_dw_run'], 15]])
		),
		('addrgen2',
			(2, 'address generation (2)', [[['mmdat'], 2]])
		),
		('txcreate2',
			(2, 'transaction creation (2)', [[['addrs'], 2]])
		),
		('txsign2',
			(2, 'transaction signing, two transactions', [[['mmdat', 'rawtx'], 1], [['mmdat', 'rawtx'], 2]])
		),
		('export_mnemonic2',
			(2, 'seed export to mmwords format (2)', [[['mmdat'], 2]])
		),
		('walletgen3',
			(3, 'wallet generation (3)', [[['del_dw_run'], 15]])
		),
		('addrgen3',
			(3, 'address generation (3)', [[['mmdat'], 3]])
		),
		('txcreate3',
			(3, 'tx creation with inputs and outputs from two wallets', [[['addrs'], 1], [['addrs'], 3]])
			),
		('txsign3',
			(3, 'tx signing with inputs and outputs from two wallets', [[['mmdat'], 1], [['mmdat', 'rawtx'], 3]])
			),
		('walletgen14',
			(14, 'wallet generation (14)', [[['del_dw_run'], 15]], 14)
		),
		('addrgen14',
			(14, 'address generation (14)', [[['mmdat'], 14]])
		),
		('keyaddrgen14',
			(14, 'key-address file generation (14)', [[['mmdat'], 14]], 14)
		),
		('walletgen4',
			(4, 'wallet generation (4) (brainwallet)', [[['del_dw_run'], 15]])
		),
		('addrgen4',
			(4, 'address generation (4)', [[['mmdat'], 4]])
		),
		('txcreate4', (
			4,
			'tx creation with inputs and outputs from four seed sources, key-address file '
			'and non-MMGen inputs and outputs',
			[
				[['addrs'], 1],
				[['addrs'], 2],
				[['addrs'], 3],
				[['addrs'], 4],
				[['addrs', 'akeys.mmenc'], 14]
			])
		),
		('txsign4', (
			4,
			'tx signing with inputs and outputs from incog file, mnemonic file, wallet, '
			'brainwallet, key-address file and non-MMGen inputs and outputs',
			[
				[['mmincog'], 1],
				[['mmwords'], 2],
				[['mmdat'], 3],
				[['mmbrain', 'rawtx'], 4],
				[['akeys.mmenc'], 14]
			])
		),
		('txdo4', (
			4,
			'tx creation, signing and sending with inputs and outputs from four seed sources, '
			'key-address file and non-MMGen inputs and outputs',
			[
				[['addrs'], 1],
				[['addrs'], 2],
				[['addrs'], 3],
				[['addrs'], 4],
				[['addrs', 'akeys.mmenc'], 14],
				[['mmincog'], 1],
				[['mmwords'], 2],
				[['mmdat'], 3],
				[['mmbrain', 'rawtx'], 4],
				[['akeys.mmenc'], 14]
			])
		), # must go after txsign4
		('txbump4', (
			4,
			'tx fee bump + send with inputs and outputs from four seed sources, key-address file '
			'and non-MMGen inputs and outputs',
			[
				[['akeys.mmenc'], 14],
				[['mmincog'], 1],
				[['mmwords'], 2],
				[['mmdat'], 3],
				[['akeys.mmenc'], 14],
				[['mmbrain', 'sigtx', 'mmdat', 'txdo'], 4]
			])
		), # must go after txsign4
		('walletgen5',
			(20, 'wallet generation (5)', [[['del_dw_run'], 15]], 20)
		),
		('addrgen5',
			(20, 'address generation (5)', [[['mmdat'], 20]])
		),
		('txcreate5',
			(20, 'transaction creation with bad vsize (5)', [[['addrs'], 20]])
		),
		('txsign5',
			(20, 'transaction signing with bad vsize', [[['mmdat', 'rawtx'], 20]])
		),
		('walletgen6',
			(21, 'wallet generation (6)', [[['del_dw_run'], 15]], 21)
		),
		('addrgen6',
			(21, 'address generation (6)', [[['mmdat'], 21]])
		),
		('txcreate6',
			(21, 'transaction creation with corrected vsize (6)', [[['addrs'], 21]])
		),
		('txsign6',
			(21, 'transaction signing with corrected vsize', [[['mmdat', 'rawtx'], 21]])
		),
	)
	segwit_do = (
		'walletgen',
		'addrgen',
		'txcreate',
		'txbump',
		'txsign',
		'txsend',
		'txdo',
		'export_incog',
		'keyaddrgen',
		'txsign_keyaddr',
		'txcreate_ni',
		'walletgen2',
		'addrgen2',
		'txcreate2',
		'txsign2',
		'export_mnemonic2',
		'walletgen3',
		'addrgen3',
		'txcreate3',
		'txsign3',
		'walletgen14',
		'addrgen14',
		'keyaddrgen14',
		'walletgen4',
		'addrgen4',
		'txcreate4',
		'txsign4',
		'txdo4',
		'txbump4',
		'walletgen5',
		'addrgen5',
		'txcreate5',
		'txsign5',
		'walletgen6',
		'addrgen6',
		'txcreate6',
		'txsign6',
	)

	def __init__(self, trunner, cfgs, spawn):
		CmdTestBase.__init__(self, trunner, cfgs, spawn)
		if trunner is None or self.coin not in self.networks:
			return
		if self.coin in ('btc', 'bch', 'ltc'):
			self.tx_fee     = {'btc':'0.0001', 'bch':'0.001', 'ltc':'0.01'}[self.coin]
			self.txbump_fee = {'btc':'123s', 'bch':'567s', 'ltc':'12345s'}[self.coin]

		self.unspent_data_file = joinpath('test', 'trash', 'unspent.json')
		self.spawn_env['MMGEN_BOGUS_UNSPENT_DATA'] = self.unspent_data_file

	@property
	def lbl_id(self):
		if not hasattr(self, '_lbl_id'):
			rpc = async_run(rpc_init(cfg, self.proto))
			self._lbl_id = ('account', 'label')['label_api' in rpc.caps]
		return self._lbl_id

	def _get_addrfile_checksum(self, display=False):
		addrfile = self.get_file_with_ext('addrs')
		from mmgen.addrlist import AddrList
		silence()
		chk = AddrList(cfg, self.proto, addrfile).chksum
		end_silence()
		if cfg.verbose and display:
			msg(f'Checksum: {cyan(chk)}')
		return chk

	def walletgen_dfl_wallet(self, seed_len=None):
		return self.walletgen(seed_len=seed_len, gen_dfl_wallet=True)

	def subwalletgen_dfl_wallet(self, pf):
		return self.subwalletgen(wf='default')

	def export_seed_dfl_wallet(self, pf, out_fmt='seed'):
		return self.export_seed(wf=None, out_fmt=out_fmt, pf=pf)

	def addrgen_dfl_wallet(self, pf):
		return self.addrgen(wf=None, dfl_wallet=True)

	def txcreate_dfl_wallet(self, addrfile):
		return self.txcreate_common(sources=['15'])

	def txsign_dfl_wallet(self, txfile, pf='', save=True, has_label=False):
		return self.txsign(None, txfile, save=save, has_label=has_label, dfl_wallet=True)

	def passchg_dfl_wallet(self, pf):
		return self.passchg(wf=None, pf=pf, dfl_wallet=True)

	def walletchk_newpass_dfl_wallet(self, pf):
		return self.walletchk_newpass(wf=None, wcls=MMGenWallet, pf=pf, dfl_wallet=True)

	def delete_dfl_wallet(self, pf):
		self.write_to_tmpfile('del_dw_run', b'', binary=True)
		if cfg.no_dw_delete:
			return 'skip'
		for wf in [f for f in os.listdir(cfg.data_dir) if f[-6:]=='.mmdat']:
			os.unlink(joinpath(cfg.data_dir, wf))
		self.spawn('', msg_only=True)
		self.have_dfl_wallet = False
		return 'ok'

	def walletgen(self, del_dw_run='dummy', seed_len=None, gen_dfl_wallet=False):
		self.write_to_tmpfile(pwfile, self.wpasswd+'\n')
		args = ['-p1']
		if not gen_dfl_wallet:
			args += ['-d', self.tmpdir]
		if seed_len:
			args += ['-l', str(seed_len)]
		t = self.spawn('mmgen-walletgen', self.testnet_opt + args + [self.usr_rand_arg], no_passthru_opts=True)
		t.license()
		t.usr_rand(self.usr_rand_chars)
		wcls = MMGenWallet
		t.passphrase_new('new '+wcls.desc, self.wpasswd)
		t.label()
		if not self.have_dfl_wallet and gen_dfl_wallet:
			t.expect('move it to the data directory? (Y/n): ', 'y')
			self.have_dfl_wallet = True
		t.written_to_file(capfirst(wcls.desc))
		return t

	def subwalletgen(self, wf):
		args = [self.usr_rand_arg, '-p1', '-d', self.tr.trash_dir, '-L', 'Label']
		if wf != 'default':
			args += [wf]
		t = self.spawn('mmgen-subwalletgen', self.testnet_opt + args + ['10s'], no_passthru_opts=True)
		t.license()
		wcls = MMGenWallet
		t.passphrase(wcls.desc, self.cfgs['1']['wpasswd'])
		t.expect(r'Generating subseed.*\D10S', regex=True)
		t.passphrase_new('new '+wcls.desc, 'foo')
		t.usr_rand(self.usr_rand_chars)
		fn = t.written_to_file(capfirst(wcls.desc))
		ext = get_extension(fn)
		assert ext, f'incorrect file extension: {ext}'
		return t

	def subwalletgen_mnemonic(self, wf):
		icls = get_wallet_cls(ext=get_extension(wf))
		ocls = get_wallet_cls('words')
		args = [self.usr_rand_arg, '-p1', '-d', self.tr.trash_dir, '-o', ocls.fmt_codes[0], wf, '3L']
		t = self.spawn('mmgen-subwalletgen', self.testnet_opt + args, no_passthru_opts=True)
		t.license()
		t.passphrase(icls.desc, self.cfgs['1']['wpasswd'])
		t.expect(r'Generating subseed.*\D3L', regex=True)
		fn = t.written_to_file(capfirst(ocls.desc))
		ext = get_extension(fn)
		assert ext == ocls.ext, f'incorrect file extension: {ext}'
		return t

	def passchg(self, wf, pf, label_action='cmdline', dfl_wallet=False, delete=False):
		silence()
		self.write_to_tmpfile(pwfile, get_data_from_file(cfg, pf))
		end_silence()
		add_args = {
			'cmdline': ['-d', self.tmpdir, '-L', 'Changed label (UTF-8) α'],
			'keep':    ['-d', self.tr.trash_dir, '--keep-label'],
			'user':    ['-d', self.tr.trash_dir]
		}[label_action]
		t = self.spawn(
			'mmgen-passchg',
			self.testnet_opt + add_args + [self.usr_rand_arg, '-p2'] + ([wf] if wf else []),
			no_passthru_opts = True)
		t.license()
		wcls = MMGenWallet
		t.passphrase(wcls.desc, self.cfgs['1']['wpasswd'], pwtype='old')
		t.expect_getend('Hash preset changed to ')
		t.passphrase(wcls.desc, self.wpasswd, pwtype='new') # reuse passphrase?
		t.expect('Repeat new passphrase: ', self.wpasswd+'\n')
		t.usr_rand(self.usr_rand_chars)
		if label_action == 'user':
			t.expect('Enter a wallet label.*: ', 'Interactive Label (UTF-8) α\n', regex=True)
		t.expect_getend(('Label changed to ', 'Reusing label ')[label_action=='keep'])
#		t.expect_getend('Key ID changed: ')
		if dfl_wallet:
			t.expect("Type uppercase 'YES' to confirm: ", 'YES\n')
			t.written_to_file('New wallet')
			t.expect('Securely deleting old wallet')
#			t.expect('Okay to WIPE 1 regular file ? (Yes/No)', 'Yes\n')
			t.expect('Wallet passphrase has changed')
			t.expect_getend('has been changed to ')
		else:
			t.written_to_file(capfirst(wcls.desc))
			t.expect('Securely delete .*: ', ('y' if delete else 'n'), regex=True)
			if delete:
				t.expect('Securely deleting')
		return t

	def passchg_keeplabel(self, wf, pf):
		return self.passchg(wf, pf, label_action='keep', delete=True)

	def passchg_usrlabel(self, wf, pf):
		return self.passchg(wf, pf, label_action='user')

	def walletchk_newpass(self, wf, pf, wcls=None, dfl_wallet=False):
		return self.walletchk(wf, wcls=wcls, dfl_wallet=dfl_wallet)

	def _write_fake_data_to_file(self, d):
		write_data_to_file(cfg, self.unspent_data_file, d, 'Unspent outputs', quiet=True, ignore_opt_outdir=True)
		if cfg.verbose or cfg.exact_output:
			sys.stderr.write(f'Fake transaction wallet data written to file {self.unspent_data_file!r}\n')

	def _create_fake_unspent_entry(
			self,
			coinaddr,
			al_id     = None,
			idx       = None,
			comment   = None,
			non_mmgen = False,
			segwit    = False):
		if 'S' not in self.proto.mmtypes:
			segwit = False
		if comment:
			comment = ' ' + comment
		k = coinaddr.addr_fmt
		if not segwit and k == 'p2sh':
			k = 'p2pkh'
		s_beg, s_end = {
			'p2pkh':  ('76a914', '88ac'),
			'p2sh':   ('a914', '87'),
			'bech32': (self.proto.witness_vernum_hex + '14', '')
		}[k]
		amt1, amt2 = {
			'btc': (10, 40),
			'bch': (10, 40),
			'ltc': (1000, 4000)
		}[self.coin]
		ret = {
			self.lbl_id: (
				f'{self.proto.base_coin.lower()}:{coinaddr}' if non_mmgen
				else f'{al_id}:{idx}{comment}'),
			'vout': int(getrandnum(4) % 8),
			'txid': getrandhex(32),
			'amount': self.proto.coin_amt('{}.{}'.format(
				amt1 + getrandnum(4) % amt2,
				getrandnum(4) % 100000000)),
			'address': coinaddr,
			'spendable': False,
			'scriptPubKey': f'{s_beg}{coinaddr.bytes.hex()}{s_end}',
			'confirmations': getrandnum(3) // 20 # max: 838860 (6 digits)
		}
		return ret

	def _create_fake_unspent_data(
			self,
			adata,
			tx_data,
			non_mmgen_input            = '',
			non_mmgen_input_compressed = True):

		out = []
		for d in tx_data.values():
			al = adata.addrlist(al_id=d['al_id'])
			for n, (idx, coinaddr) in enumerate(al.addrpairs()):
				comment = get_comment(do_shuffle=not cfg.test_suite_deterministic)
				out.append(self._create_fake_unspent_entry(
					coinaddr, d['al_id'], idx, comment, segwit=d['segwit']))
				if n == 0:  # create a duplicate address. This means addrs_per_wallet += 1
					out.append(self._create_fake_unspent_entry(
						coinaddr, d['al_id'], idx, comment, segwit=d['segwit']))

		if non_mmgen_input:
			from mmgen.key import PrivKey
			privkey = PrivKey(
				self.proto,
				getrand(32),
				compressed  = non_mmgen_input_compressed,
				pubkey_type = 'std')
			from mmgen.addrgen import KeyGenerator, AddrGenerator
			rand_coinaddr = AddrGenerator(
				cfg,
				self.proto,
				('legacy', 'compressed')[non_mmgen_input_compressed]
				).to_addr(KeyGenerator(cfg, self.proto, 'std').gen_data(privkey))
			of = joinpath(self.cfgs[non_mmgen_input]['tmpdir'], non_mmgen_fn)
			write_data_to_file(
				cfg               = cfg,
				outfile           = of,
				data              = privkey.wif + '\n',
				desc              = f'compressed {self.proto.name} key',
				quiet             = True,
				ignore_opt_outdir = True)
			out.append(self._create_fake_unspent_entry(rand_coinaddr, non_mmgen=True, segwit=False))

		return out

	def _create_tx_data(self, sources, addrs_per_wallet=addrs_per_wallet):
		from mmgen.addrlist import AddrList, AddrIdxList
		from mmgen.addrdata import AddrData
		tx_data, ad = {}, AddrData(self.proto)
		for s in sources:
			addrfile = get_file_with_ext(self.cfgs[s]['tmpdir'], 'addrs')
			al = AddrList(cfg, self.proto, addrfile)
			ad.add(al)
			aix = AddrIdxList(fmt_str=self.cfgs[s]['addr_idx_list'])
			if len(aix) != addrs_per_wallet:
				die('TestSuiteFatalException', f'Address index list length != {addrs_per_wallet}: {repr(aix)}')
			tx_data[s] = {
				'addrfile': addrfile,
				'chk': al.chksum,
				'al_id': al.al_id,
				'addr_idxs': aix[-2:],
				'segwit': self.cfgs[s]['segwit']
			}
		return ad, tx_data

	def _make_txcreate_cmdline(self, tx_data):
		from mmgen.key import PrivKey
		privkey = PrivKey(self.proto, getrand(32), compressed=True, pubkey_type='std')
		t = ('compressed', 'segwit')['S' in self.proto.mmtypes]
		from mmgen.addrgen import KeyGenerator, AddrGenerator
		rand_coinaddr = AddrGenerator(cfg, self.proto, t).to_addr(
			KeyGenerator(cfg, self.proto, 'std').gen_data(privkey)
		)

		# total of two outputs must be < 10 BTC (<1000 LTC)
		mods = {
			'btc': (6, 4),
			'bch': (6, 4),
			'ltc': (600, 400)
		}[self.coin]
		for k in self.cfgs:
			self.cfgs[k]['amts'] = [None, None]
			for idx, mod in enumerate(mods):
				self.cfgs[k]['amts'][idx] = '{}.{}'.format(
					getrandnum(4) % mod,
					str(getrandnum(4))[:5])

		cmd_args = ['--outdir='+self.tmpdir]
		for num in tx_data:
			s = tx_data[num]
			cmd_args += [
				'{}:{},{}'.format(
					s['al_id'],
					s['addr_idxs'][0],
					self.cfgs[num]['amts'][0])]
			# + one change address and one BTC address
			if num is list(tx_data.keys())[-1]:
				cmd_args += [
					'{}:{}'.format(
						s['al_id'],
						s['addr_idxs'][1])]
				cmd_args += [
					'{},{}'.format(
						rand_coinaddr,
						self.cfgs[num]['amts'][1])]

		return cmd_args + [tx_data[num]['addrfile'] for num in tx_data]

	def txcreate_common(
			self,
			sources                    = ['1'],
			non_mmgen_input            = '',
			do_label                   = False,
			txdo_args                  = [],
			add_args                   = [],
			view                       = 'n',
			addrs_per_wallet           = addrs_per_wallet,
			non_mmgen_input_compressed = True,
			cmdline_inputs             = False,
			tweaks                     = []):

		if cfg.verbose or cfg.exact_output:
			sys.stderr.write(green('Generating fake tracking wallet info\n'))

		silence()
		ad, tx_data = self._create_tx_data(sources, addrs_per_wallet)
		dfake = self._create_fake_unspent_data(ad, tx_data, non_mmgen_input, non_mmgen_input_compressed)
		import json
		from mmgen.rpc import json_encoder
		self._write_fake_data_to_file(json.dumps(dfake, cls=json_encoder))
		cmd_args = self._make_txcreate_cmdline(tx_data)

		if cmdline_inputs:
			from mmgen.tw.shared import TwLabel
			cmd_args = [
				'--inputs={},{},{},{},{},{}'.format(
					TwLabel(self.proto, dfake[0][self.lbl_id]).mmid, dfake[1]['address'],
					TwLabel(self.proto, dfake[2][self.lbl_id]).mmid, dfake[3]['address'],
					TwLabel(self.proto, dfake[4][self.lbl_id]).mmid, dfake[5]['address']
				),
				f'--outdir={self.tr.trash_dir}'
			] + cmd_args[1:]

		end_silence()

		if cfg.verbose or cfg.exact_output:
			sys.stderr.write('\n')

		t = self.spawn(
			'mmgen-'+('txcreate', 'txdo')[bool(txdo_args)],
			(['--no-rbf'], [])[self.proto.cap('rbf')] +
			['-f', self.tx_fee, '-B'] + add_args + cmd_args + txdo_args)

		if t.expect([('Get', 'Unsigned transac')[cmdline_inputs], r'Unable to connect to \S+'], regex=True) == 1:
			die('TestSuiteException', '\n'+t.p.after)

		if cmdline_inputs:
			t.written_to_file('tion')
			return t

		t.license()

		for num in tx_data:
			t.expect_getend('ting address data from file ')
			chk=t.expect_getend(r'Checksum for address data .*?: ', regex=True)
			verify_checksum_or_exit(tx_data[num]['chk'], chk)

		# not in tracking wallet warning, (1 + num sources) times
		for num in range(len(tx_data) + 1):
			t.expect('Continue anyway? (y/N): ', 'y')

		outputs_list = [(addrs_per_wallet+1)*i + 1 for i in range(len(tx_data))]
		if non_mmgen_input:
			outputs_list.append(len(tx_data)*(addrs_per_wallet+1) + 1)

		self.txcreate_ui_common(t,
			menu        = (['M'], ['M', 'D', 'D', 'D', 'D', 'm', 'o'])[self.test_name=='txcreate'],
			inputs      = ' '.join(map(str, outputs_list)),
			add_comment = ('', tx_comment_lat_cyr_gr)[do_label],
			view        = view,
			tweaks      = tweaks)

		if txdo_args and add_args: # txdo4
			t.do_decrypt_ka_data(pw=self.cfgs['14']['kapasswd'])

		return t

	def txcreate(self, addrfile):
		return self.txcreate_common(sources=['1'], add_args=['--vsize-adj=1.01'])

	def txbump(self, txfile, prepend_args=[], seed_args=[]):
		if not self.proto.cap('rbf'):
			msg(gray('Skipping RBF'))
			return 'skip'
		args = prepend_args + ['--quiet', '--outdir='+self.tmpdir, txfile] + seed_args
		t = self.spawn('mmgen-txbump', args)
		if seed_args:
			t.do_decrypt_ka_data(pw=self.cfgs['14']['kapasswd'])
		t.expect('deduct the fee from (Hit ENTER for the change output): ', '1\n')
		# Fee must be > tx_fee + network relay fee (currently 0.00001)
		t.expect('OK? (Y/n): ', '\n')
		t.expect('Enter transaction fee: ', self.txbump_fee+'\n')
		t.expect('OK? (Y/n): ', '\n')
		if seed_args: # sign and send
			t.do_comment(False, has_label=True)
			for cnum, wcls in (('1', IncogWallet), ('3', MMGenWallet), ('4', MMGenWallet)):
				t.passphrase(wcls.desc, self.cfgs[cnum]['wpasswd'])
			self._do_confirm_send(t, quiet=not cfg.debug, confirm_send=True)
			if cfg.debug:
				t.written_to_file('Transaction')
		else:
			t.do_comment(False)
			t.expect('Save fee-bumped transaction? (y/N): ', 'y')
			t.written_to_file('Fee-bumped transaction')
		os.unlink(txfile) # our tx file replaces the original
		cmd = 'touch ' + joinpath(self.tmpdir, 'txbump')
		os.system(cmd)
		return t

	def txsend(self, sigfile, extra_opts=[]):
		t = self.spawn('mmgen-txsend', extra_opts + ['-d', self.tmpdir, sigfile])
		self.txsend_ui_common(t, view='t', add_comment='')
		return t

	def txdo(self, addrfile, wallet):
		t = self.txcreate_common(sources=['1'], txdo_args=[wallet])
		self.txsign_ui_common(t, view='n', do_passwd=True)
		self.txsend_ui_common(t)
		return t

	def _walletconv_export(self, wf, uargs=[], out_fmt='w', pf=None):
		opts = ['-d', self.tmpdir, '-o', out_fmt] + uargs + \
			([], [wf])[bool(wf)] + ([], ['-P', pf])[bool(pf)]
		t = self.spawn('mmgen-walletconv', self.testnet_opt + opts, no_passthru_opts=True)
		t.license()

		if not pf:
			icls = get_wallet_cls(ext=get_extension(wf))
			t.passphrase(icls.desc, self.wpasswd)

		ocls = get_wallet_cls(fmt_code=out_fmt)

		if ocls.enc and ocls.type != 'brain':
			t.passphrase_new('new '+ocls.desc, self.wpasswd)
			t.usr_rand(self.usr_rand_chars)

		if ocls.type.startswith('incog'):
			m = 'Encrypting random data from your operating system with ephemeral key'
			t.expect(m)
			t.expect(m)
			incog_id = t.expect_getend('New Incog Wallet ID: ')
			t.expect(m)

		if ocls.type == 'incog_hidden':
			self.write_to_tmpfile(incog_id_fn, incog_id)
			t.hincog_create(hincog_bytes)
		elif ocls.type == 'mmgen':
			t.label()

		return t.written_to_file(capfirst(ocls.desc)), t

	def export_seed(self, wf, out_fmt='seed', pf=None):
		f, t = self._walletconv_export(wf, out_fmt=out_fmt, pf=pf)
		silence()
		wcls = get_wallet_cls(fmt_code=out_fmt)
		msg('==> {}: {}'.format(
			wcls.desc,
			cyan(get_data_from_file(cfg, f, wcls.desc))
		))
		end_silence()
		return t

	def export_hex(self, wf, out_fmt='mmhex', pf=None):
		return self.export_seed(wf, out_fmt=out_fmt, pf=pf)

	def export_mnemonic(self, wf):
		return self.export_seed(wf, out_fmt='words')

	def export_bip39(self, wf):
		return self.export_seed(wf, out_fmt='bip39')

	def export_incog(self, wf, out_fmt='i', add_args=[]):
		uargs = ['-p1', self.usr_rand_arg] + add_args
		_, t = self._walletconv_export(wf, out_fmt=out_fmt, uargs=uargs)
		return t

	def export_incog_hex(self, wf):
		return self.export_incog(wf, out_fmt='xi')

	# TODO: make outdir and hidden incog compatible (ignore --outdir and warn user?)
	def export_incog_hidden(self, wf):
		rf = joinpath(self.tmpdir, hincog_fn)
		add_args = ['-J', f'{rf},{hincog_offset}']
		return self.export_incog(wf, out_fmt='hi', add_args=add_args)

	def addrgen_seed(self, wf, _, in_fmt='seed'):
		wcls = get_wallet_cls(fmt_code=in_fmt)
		stdout = wcls.type == 'seed' # capture output to screen once
		t = self.spawn(
			'mmgen-addrgen',
			(['-S'] if stdout else [])
			+ self.segwit_arg
			+ ['-i' + in_fmt, '-d', self.tmpdir, wf, self.addr_idx_list],
			exit_val = None if stdout else 1)
		t.license()
		t.expect_getend(f'Valid {wcls.desc} for Seed ID ')
		vmsg('Comparing generated checksum with checksum from previous address file')
		verify_checksum_or_exit(
			self._get_addrfile_checksum(),
			t.expect_getend(r'Checksum for address data .*?: ', regex=True))
		if not stdout:
			t.no_overwrite()
		return t

	def addrgen_hex(self, wf, _, in_fmt='mmhex'):
		return self.addrgen_seed(wf, _, in_fmt=in_fmt)

	def addrgen_mnemonic(self, wf, _):
		return self.addrgen_seed(wf, _, in_fmt='words')

	def addrgen_incog(self, wf=[], _='', in_fmt='i', args=[]):
		t = self.spawn(
			'mmgen-addrgen',
			args
			+ self.segwit_arg
			+ ['-i'+in_fmt, '-d', self.tmpdir]
			+ ([wf] if wf else [])
			+ [self.addr_idx_list],
			exit_val = 1)
		t.license()
		t.expect_getend('Incog Wallet ID: ')
		wcls = get_wallet_cls(fmt_code=in_fmt)
		t.hash_preset(wcls.desc, '1')
		t.passphrase(rf'{wcls.desc} \w{{8}}', self.wpasswd)
		vmsg('Comparing generated checksum with checksum from address file')
		chk = t.expect_getend(r'Checksum for address data .*?: ', regex=True)
		verify_checksum_or_exit(self._get_addrfile_checksum(), chk)
		t.no_overwrite()
		return t

	def addrgen_incog_hex(self, wf, _):
		return self.addrgen_incog(wf, '', in_fmt='xi')

	def addrgen_incog_hidden(self, wf, _):
		rf = joinpath(self.tmpdir, hincog_fn)
		return self.addrgen_incog([], '', in_fmt='hi',
			args=['-H', f'{rf},{hincog_offset}', '-l', str(hincog_seedlen)])

	def txsign_keyaddr(self, keyaddr_file, txfile):
		t = self.spawn('mmgen-txsign', ['-d', self.tmpdir, '-p1', '-M', keyaddr_file, txfile])
		t.license()
		t.view_tx('n')
		t.do_decrypt_ka_data(pw=self.kapasswd)
		self.txsign_end(t)
		return t

	def txcreate_ni(self, addrfile):
		return self.txcreate_common(sources=['1'], cmdline_inputs=True, add_args=['--yes'])

	def walletgen2(self, del_dw_run='dummy'):
		return self.walletgen(seed_len=128)

	def addrgen2(self, wf):
		return self.addrgen(wf)

	def txcreate2(self, addrfile):
		return self.txcreate_common(sources=['2'])

	def txsign2(self, wf1, txf1, wf2, txf2):
		t = self.spawn('mmgen-txsign', ['-d', self.tmpdir, txf1, wf1, txf2, wf2])
		t.license()
		for cnum, wf in (('1', wf1), ('2', wf2)):
			wcls = get_wallet_cls(ext=get_extension(wf))
			t.view_tx('n')
			t.passphrase(wcls.desc, self.cfgs[cnum]['wpasswd'])
			self.txsign_end(t, cnum)
		return t

	def export_mnemonic2(self, wf):
		return self.export_mnemonic(wf)

	def walletgen3(self, del_dw_run='dummy'):
		return self.walletgen()

	def addrgen3(self, wf):
		return self.addrgen(wf)

	def txcreate3(self, addrfile1, addrfile2):
		return self.txcreate_common(sources=['1', '3'])

	def txsign3(self, wf1, wf2, txf2):
		t = self.spawn('mmgen-txsign', ['-d', self.tmpdir, wf1, wf2, txf2])
		t.license()
		t.view_tx('n')
		for cnum, wf in (('1', wf1), ('3', wf2)):
			wcls = get_wallet_cls(ext=get_extension(wf))
			t.passphrase(wcls.desc, self.cfgs[cnum]['wpasswd'])
		self.txsign_end(t)
		return t

	walletgen14 = walletgen
	addrgen14 = CmdTestShared.addrgen
	keyaddrgen14 = CmdTestShared.keyaddrgen

	def walletgen4(self, del_dw_run='dummy'):
		bwf = joinpath(self.tmpdir, self.bw_filename)
		make_brainwallet_file(bwf)
		seed_len = str(self.seed_len)
		args = ['-d', self.tmpdir, '-p1', self.usr_rand_arg, '-l'+seed_len, '-ibw']
		t = self.spawn('mmgen-walletconv', self.testnet_opt + args + [bwf], no_passthru_opts=True)
		t.license()
		wcls = MMGenWallet
		t.passphrase_new('new ' +wcls.desc, self.wpasswd)
		t.usr_rand(self.usr_rand_chars)
		t.label()
		t.written_to_file(capfirst(wcls.desc))
		return t

	def addrgen4(self, wf):
		return self.addrgen(wf)

	def txcreate4(self, f1, f2, f3, f4, f5, f6):
		return self.txcreate_common(
			sources         = ['1', '2', '3', '4', '14'],
			non_mmgen_input = '4',
			do_label        = True,
			view            = 'y',
			tweaks          = ['confirm_non_mmgen'])

	def txsign4(self, f1, f2, f3, f4, f5, f6):
		non_mm_file = joinpath(self.tmpdir, non_mmgen_fn)
		add_args = [
			'-d', self.tmpdir,
			'-i', 'brain',
			'-b' + self.bw_params,
			'-p1',
			'--keys-from-file=' + non_mm_file,
			'--mmgen-keys-from-file=' + f6,
			f1, f2, f3, f4, f5]
		t = self.spawn('mmgen-txsign', add_args)
		t.license()
		t.view_tx('t')
		t.do_decrypt_ka_data(pw=self.cfgs['14']['kapasswd'])

		for cnum, wcls in (('1', IncogWallet), ('3', MMGenWallet)):
			t.passphrase(wcls.desc, self.cfgs[cnum]['wpasswd'])

		self.txsign_end(t, has_label=True)
		return t

	def txdo4(self, f1, f2, f3, f4, f5, f6, f7, f8, f9, f10, f11, f12):
		non_mm_file = joinpath(self.tmpdir, non_mmgen_fn)
		add_args = [
			'-d', self.tmpdir,
			'-i', 'brain',
			'-b'+self.bw_params,
			'-p1',
			'--keys-from-file=' + non_mm_file,
			'--mmgen-keys-from-file=' + f12]
		self.get_file_with_ext('sigtx', delete_all=True) # delete tx signed by txsign4
		t = self.txcreate_common(
			sources         = ['1', '2', '3', '4', '14'],
			non_mmgen_input = '4',
			do_label        = True,
			txdo_args       = [f7, f8, f9, f10],
			add_args        = add_args)

		for cnum, wcls in (('1', IncogWallet), ('3', MMGenWallet)):
			t.passphrase(wcls.desc, self.cfgs[cnum]['wpasswd'])

		self.txsign_ui_common(t)
		self.txsend_ui_common(t)

		cmd = 'touch ' + joinpath(self.tmpdir, 'txdo')
		os.system(cmd)
		return t

	def txbump4(self, f1, f2, f3, f4, f5, f6, f7, f8, f9): # f7:txfile, f9:'txdo'
		non_mm_file = joinpath(self.tmpdir, non_mmgen_fn)
		return self.txbump(
			f7,
			prepend_args = ['-p1', '-k', non_mm_file, '-M', f1],
			seed_args    = [f2, f3, f4, f5, f6, f8])

	def walletgen5(self, del_dw_run='dummy'):
		return self.walletgen()

	def addrgen5(self, wf):
		return self.addrgen(wf)

	def txcreate5(self, addrfile):
		return self.txcreate_common(
			sources                    = ['20'],
			non_mmgen_input            = '20',
			non_mmgen_input_compressed = False,
			tweaks                     = ['confirm_non_mmgen'])

	def txsign5(self, wf, txf, bad_vsize=True, add_args=[]):
		non_mm_file = joinpath(self.tmpdir, non_mmgen_fn)
		t = self.spawn(
			'mmgen-txsign',
			add_args + ['-d', self.tmpdir, '-k', non_mm_file, txf, wf],
			exit_val = 2 if bad_vsize else None)
		t.license()
		t.view_tx('n')
		wcls = get_wallet_cls(ext=get_extension(wf))
		t.passphrase(wcls.desc, self.cfgs['20']['wpasswd'])
		if bad_vsize:
			t.expect('Estimated transaction vsize')
			t.expect('1 transaction could not be signed')
		else:
			t.do_comment(False)
			t.expect('Save signed transaction? (Y/n): ', 'y')
		return t

	def walletgen6(self, del_dw_run='dummy'):
		return self.walletgen()

	def addrgen6(self, wf):
		return self.addrgen(wf)

	def txcreate6(self, addrfile):
		return self.txcreate_common(
			sources                    = ['21'],
			non_mmgen_input            = '21',
			non_mmgen_input_compressed = False,
			add_args                   = ['--vsize-adj=1.08'],
			tweaks                     = ['confirm_non_mmgen'])

	def txsign6(self, wf, txf):
		return self.txsign5(wf, txf, bad_vsize=False, add_args=['--vsize-adj=1.08'])

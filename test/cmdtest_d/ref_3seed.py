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
test.cmdtest_d.ref_3seed: Saved and generated reference file tests for 128,
                          192 and 256-bit seeds for the cmdtest.py test suite
"""

import os

from mmgen.util import msg, capfirst
from mmgen.wallet import get_wallet_cls

from ..include.common import cmp_or_die, joinpath
from .include.common import (
	pwfile,
	ref_wallet_hash_preset,
	ref_wallet_brainpass,
	ref_wallet_incog_offset,
	ref_dir,
	ok_msg
)
from .base import CmdTestBase
from .shared import CmdTestShared
from .wallet import CmdTestWalletConv

class CmdTestRef3Seed(CmdTestBase, CmdTestShared):
	'saved wallet files for 128-, 192- and 256-bit seeds + generated filename checks'
	networks = ('btc',)
	mmtypes = (None,)
	tmpdir_nums = [6, 7, 8]
	addr_idx_list_in = '1010,500-501,31-33,1,33,500,1011'
	pass_idx_list_in = '1,4,9-11,1100'
	chk_data = {
		'lens': (128, 192, 256),
		'sids': ('FE3C6545', '1378FC64', '98831F3A'),
	}
	shared_deps = ['mmdat', pwfile]
	skip_cmds = (
		'ref_xmrseed_25_passwdgen_1',
		'ref_xmrseed_25_passwdgen_2',
	)
	cmd_group = (
		# reading saved reference wallets
		('ref_wallet_chk',   'saved reference wallet'),
		('ref_seed_chk',     'saved seed file'),
		('ref_hex_chk',      'saved mmhex file'),
		('ref_plainhex_chk', 'saved hex file'),
		('ref_dieroll_chk',  'saved dieroll (b6d) file'),
		('ref_mn_chk',       'saved native MMGen mnemonic file'),
		('ref_bip39_chk',    'saved BIP39 mnemonic file'),
		('ref_hincog_chk',   'saved hidden incog reference wallet'),
		('ref_brain_chk',    'saved brainwallet'),                    # in shared

		# generating new reference ('abc' brainwallet) wallets for filename checks:
		('ref_walletgen_brain',         'generating new reference wallet + filename check (brain)'),
		('ref_walletconv_words',        'wallet filename (native mnemonic)'),
		('ref_walletconv_bip39',        'wallet filename (bip39)'),
		('ref_walletconv_seed',         'wallet filename (seed)'),
		('ref_walletconv_hexseed',      'wallet filename (hex seed)'),
		('ref_walletconv_plainhexseed', 'wallet filename (plain hex seed)'),
		('ref_walletconv_dieroll',      'wallet filename (dieroll (b6d) seed)'),
		('ref_walletconv_incog',        'wallet filename (incog)'),
		('ref_walletconv_hexincog',     'wallet filename (hex incog)'),
	)

	def __init__(self, cfg, trunner, cfgs, spawn):
		for k, _ in self.cmd_group:
			for n in (1, 2, 3): # 128, 192, 256 bits
				setattr(self, f'{k}_{n}', getattr(self, k))
		if cfgs:
			for n in self.tmpdir_nums:
				cfgs[str(n)]['addr_idx_list'] = self.addr_idx_list_in
				cfgs[str(n)]['pass_idx_list'] = self.pass_idx_list_in
		CmdTestBase.__init__(self, cfg, trunner, cfgs, spawn)

	def ref_wallet_chk(self):
		wf = joinpath(ref_dir, CmdTestWalletConv.sources[str(self.seed_len)]['ref_wallet'])
		return self.walletchk(wf, sid=self.seed_id)

	def ref_ss_chk(self, ss_type):
		ss = get_wallet_cls(ss_type)
		return self.walletchk(
			wf   = joinpath(ref_dir, f'{self.seed_id}.{ss.ext}'),
			wcls = ss,
			sid  = self.seed_id)

	def ref_seed_chk(self):
		return self.ref_ss_chk('seed')

	def ref_hex_chk(self):
		return self.ref_ss_chk('mmhex')

	def ref_plainhex_chk(self):
		return self.ref_ss_chk('plainhex')

	def ref_dieroll_chk(self):
		return self.ref_ss_chk('dieroll')

	def ref_mn_chk(self):
		return self.ref_ss_chk('words')

	def ref_bip39_chk(self):
		return self.ref_ss_chk('bip39')

	def ref_hincog_chk(self, desc='hidden incognito data'):
		source = CmdTestWalletConv.sources[str(self.seed_len)]
		for wtype, edesc, of_arg in (
				('hic_wallet',     '',             []),
				('hic_wallet_old', '(old format)', ['-O'])):
			ic_arg = ['-H{},{}'.format(
				joinpath(ref_dir, source[wtype]),
				ref_wallet_incog_offset)
			]
			slarg = [f'-l{self.seed_len} ']
			hparg = ['-p1']
			if wtype == 'hic_wallet_old' and self.cfg.profile:
				msg('')
			t = self.spawn('mmgen-walletchk',
				slarg + hparg + of_arg + ic_arg,
				extra_desc=edesc)
			t.passphrase(desc, self.wpasswd+'\n')
			if wtype == 'hic_wallet_old':
				t.expect('Is the Seed ID correct? (Y/n): ', '\n')
			chk = t.expect_getend('Seed ID: ')
			cmp_or_die(self.seed_id, chk)
			ok_msg()
		t.skip_ok = True
		return t

	def ref_walletgen_brain(self):
		sl_arg = f'-l{self.seed_len}'
		hp_arg = f'-p{ref_wallet_hash_preset}'
		label = f'ref. wallet (pw {ref_wallet_brainpass!r}, seed len {self.seed_len}) α'
		bf = 'ref.mmbrain'
		args = ['-d', self.tmpdir, hp_arg, sl_arg, '-ibw', '-L', label]
		self.write_to_tmpfile(bf, ref_wallet_brainpass)
		self.write_to_tmpfile(pwfile, self.wpasswd)
		t = self.spawn('mmgen-walletconv', self.testnet_opt + args + [self.usr_rand_arg], no_passthru_opts=True)
		t.license()
		t.expect('Enter brainwallet: ', ref_wallet_brainpass+'\n')
		ocls = get_wallet_cls('mmgen')
		t.passphrase_new('new '+ocls.desc, self.wpasswd)
		t.usr_rand(self.usr_rand_chars)
		fn = os.path.split(t.written_to_file(capfirst(ocls.desc)))[-1]
		import re
		idx = int(self.test_name[-1]) - 1
		pat = r'{}-[0-9A-F]{{8}}\[{},1\]{}.mmdat'.format(
			self.chk_data['sids'][idx],
			self.chk_data['lens'][idx],
			'-α' if self.cfg.debug_utf8 else '')
		assert re.match(pat, fn), f'{pat} != {fn}'
		sid = os.path.basename(fn.split('-')[0])
		cmp_or_die(sid, self.seed_id, desc='Seed ID')
		return t

	def ref_walletconv(self, ofmt, extra_args=[], re_pat=None):
		wf = self.get_file_with_ext('mmdat')
		pf = joinpath(self.tmpdir, pwfile)
		t = self.spawn('mmgen-walletconv', extra_args+['-d', 'test/trash', '-o', ofmt, '-P'+pf, wf])
		wcls = get_wallet_cls(fmt_code=ofmt)
		fn = os.path.split(t.written_to_file(capfirst(wcls.desc)))[-1]
		idx = int(self.test_name[-1]) - 1
		sid = self.chk_data['sids'][idx]
		slen = self.chk_data['lens'][idx]
		if re_pat:
			import re
			pat = re_pat.format(sid, slen)
			assert re.match(pat, fn), f'{pat} != {fn}'
		else:
			cmp_or_die('{}[{}]{}.{}'.format(
				sid,
				slen,
				'-α' if self.cfg.debug_utf8 else '',
				wcls.ext),
				fn)
		return t

	def ref_walletconv_words(self):
		return self.ref_walletconv(ofmt='mn')
	def ref_walletconv_bip39(self):
		return self.ref_walletconv(ofmt='bip39')
	def ref_walletconv_seed(self):
		return self.ref_walletconv(ofmt='mmseed')
	def ref_walletconv_hexseed(self):
		return self.ref_walletconv(ofmt='mmhex')
	def ref_walletconv_plainhexseed(self):
		return self.ref_walletconv(ofmt='hex')
	def ref_walletconv_dieroll(self):
		return self.ref_walletconv(ofmt='dieroll')

	def ref_walletconv_incog(self, ofmt='incog', ext='mmincog'):
		args = ['-r0', '-p1']
		pat = r'{}-[0-9A-F]{{8}}-[0-9A-F]{{8}}\[{},1\]' + ('-α' if self.cfg.debug_utf8 else '') + '.' + ext
		return self.ref_walletconv(ofmt=ofmt, extra_args=args, re_pat=pat)

	def ref_walletconv_hexincog(self):
		return self.ref_walletconv_incog(ofmt='incog_hex', ext='mmincox')

class CmdTestRef3Addr(CmdTestRef3Seed):
	'generated reference address and key-address files for 128-, 192- and 256-bit seeds'
	networks = ('btc', 'btc_tn', 'ltc', 'ltc_tn', 'bch', 'bch_tn')
	passthru_opts = ('coin', 'testnet', 'cashaddr')
	tmpdir_nums = [26, 27, 28]
	shared_deps = ['mmdat', pwfile]

	chk_data = {
		'lens': (128, 192, 256),
		'sids': ('FE3C6545', '1378FC64', '98831F3A'),
		'refaddrgen_legacy_1': {
			'btc': ('B230 7526 638F 38CB', 'A9DC 5A13 12CB 1317'),
			'bch': ('026D AFE0 8C60 6CFF', 'B406 4937 D884 6E48'),
			'ltc': ('2B23 5E97 848A B961', 'AEC3 E774 0B21 0202'),
		},
		'refaddrgen_segwit_1': {
			'btc': ('9914 6D10 2307 F348', '83C8 A6B6 ADA8 25B2'),
			'ltc': ('CC09 A190 B7DF B7CD', '0425 7893 C6F1 ECA3'),
		},
		'refaddrgen_bech32_1': {
			'btc': ('C529 D686 31AA ACD4', '21D0 26AD 3A22 5465'),
			'ltc': ('3DFB CFCC E180 DC9D', '8C72 D5C2 07E0 5F7B'),
		},
		'refaddrgen_compressed_1': {
			'btc': ('95EB 8CC0 7B3B 7856', '16E6 6170 154D 2202'),
			'bch': ('C560 A343 CEAB 118E', '3F56 8DC5 0383 CD78'),
			'ltc': ('35D5 8ECA 9A42 46C3', '15B3 5492 D3D3 6854'),
		},
		'refkeyaddrgen_legacy_1': {
			'btc': ('CF83 32FB 8A8B 08E2', '1F67 B73A FF8C 5D15'),
			'bch': ('6909 4C64 119A 7681', '7E48 5071 5E41 D1AE'),
			'ltc': ('1896 A26C 7F14 2D01', 'FA0E CD4E ADAF DBF4'),
		},
		'refkeyaddrgen_compressed_1': {
			'btc': ('E43A FA46 5751 720A', 'FDEE 8E45 1C0A 02AD'),
			'bch': ('7068 9B37 8ABF 3E31', 'C688 29A5 BA4C 21B2'),
			'ltc': ('7603 2FE3 2145 FFAD', '3FE0 5A8E 5FBE FF3E'),
		},
		'refkeyaddrgen_segwit_1': {
			'btc': ('C13B F717 D4E8 CF59', 'BB71 175C 5416 19D8'),
			'ltc': ('054B 9794 55B4 5D82', 'DE85 3CF3 9636 FE2E'),
		},
		'refkeyaddrgen_bech32_1': {
			'btc': ('934F 1C33 6C06 B18C', 'A283 5BAB 7AF3 3EA4'),
			'ltc': ('A6AD DF53 5968 7B6A', '9572 43E0 A4DC 0B2E'),
		},
		'refaddrgen_legacy_2': {
			'btc': ('8C17 A5FA 0470 6E89', '764C 66F9 7502 AAEA'),
			'bch': ('8117 24B6 3FDA 6B40', 'E58C A8A4 C371 66AE'),
			'ltc': ('2B77 A009 D5D0 22AD', '51D1 979D 0A35 F24B'),
		},
		'refaddrgen_compressed_2': {
			'btc': ('2615 8401 2E98 7ECA', 'A386 EE07 A356 906D'),
			'bch': ('3364 0F9D 8355 2A53', '3451 F741 0A8A FA56'),
			'ltc': ('197C C48C 3C37 AB0F', '8DDC 5FE3 BFF9 1226'),
		},
		'refaddrgen_segwit_2': {
			'btc': ('91C4 0414 89E4 2089', 'BF9F C67F ED22 A47B'),
			'ltc': ('8F12 FA7B 9F12 594C', '2609 8494 A23C F836'),
		},
		'refaddrgen_bech32_2': {
			'btc': ('2AA3 78DF B965 82EB', '027B 1C1F 7FB2 D859'),
			'ltc': ('951C 8FB2 FCA5 87D1', '4A5D 67E0 8210 FEF2'),
		},
		'refkeyaddrgen_legacy_2': {
			'btc': ('9648 5132 B98E 3AD9', '1BD3 5A36 D51C 256D'),
			'bch': ('C4D8 7C36 DC77 F8C2', '953D 245C 8CFF AC72'),
			'ltc': ('DBD4 FAB6 7E46 CD07', '8822 3FDF FEC0 6A8C'),
		},
		'refkeyaddrgen_compressed_2': {
			'btc': ('6D6D 3D35 04FD B9C3', '94BF 4BCF 10B2 394B'),
			'bch': ('3E7F C369 2AB9 BD58', '0C99 14CD 5ADE 6782'),
			'ltc': ('F5DA 9D60 6798 C4E9', '7918 88DE 9096 DD7A'),
		},
		'refkeyaddrgen_segwit_2': {
			'btc': ('C98B DF08 A3D5 204B', '7E7F DF50 FE04 6F68'),
			'ltc': ('1829 7FE7 2567 CB91', 'BE92 D19C 7589 EF30'),
		},
		'refkeyaddrgen_bech32_2': {
			'btc': ('4A6B 3762 DF30 9368', '12DD 1888 36BA 85F7'),
			'ltc': ('5C12 FDD4 17AB F179', 'E195 B28C 59C4 C5EC'),
		},
		'refaddrgen_legacy_3': {
			'btc': ('6FEF 6FB9 7B13 5D91', '424E 4326 CFFE 5F51'),
			'bch': ('E580 43BB 0F96 AA93', '630E 174A 8DDE 1BCE'),
			'ltc': ('AD52 C3FE 8924 AAF0', '4EBE 2E85 E969 1B30'),
		},
		'refaddrgen_compressed_3': {
			'btc': ('A33C 4FDE F515 F5BC', '6C48 AA57 2056 C8C8'),
			'bch': ('E37B AF41 7997 A28C', '0D5D 9A58 D6E9 92EE'),
			'ltc': ('3FC0 8F03 C2D6 BD19', '4C0A 49B6 2DD1 1BE0'),
		},
		'refaddrgen_segwit_3': {
			'btc': ('06C1 9C87 F25C 4EE6', '072C 8B07 2730 CB7A'),
			'ltc': ('63DF E42A 0827 21C3', '5DD1 D186 DBE1 59F2'),
		},
		'refaddrgen_bech32_3': {
			'btc': ('9D2A D4B6 5117 F02E', '0527 9C39 6C1B E39A'),
			'ltc': ('FF1C 7939 5967 AB82', 'ED3D 8AA4 BED4 0B40'),
		},
		'refkeyaddrgen_legacy_3': {
			'btc': ('9F2D D781 1812 8BAD', '88CC 5120 9A91 22C2'),
			'bch': ('A0EE B039 48F4 24AE', 'B014 E0AB 5F87 EC64'),
			'ltc': ('B804 978A 8796 3ED4', '98B5 AC35 F334 0398'),
		},
		'refkeyaddrgen_compressed_3': {
			'btc': ('420A 8EB5 A9E2 7814', 'F43A CB4A 81F3 F735'),
			'bch': ('33E7 5C06 88CF 2792', '6E09 FF73 B7C8 00D4'),
			'ltc': ('8D1C 781F EB7F 44BC', '05F3 5C68 FD31 FCEF'),
		},
		'refkeyaddrgen_segwit_3': {
			'btc': ('A447 12C2 DD14 5A9B', 'C770 7391 C415 21F9'),
			'ltc': ('E8A3 9F6E E164 A521', 'D3D5 BFDD F5D5 20BD'),
		},
		'refkeyaddrgen_bech32_3': {
			'btc': ('D0DD BDE3 87BE 15AE', '7552 D70C AAB8 DEAA'),
			'ltc': ('74A0 7DD5 963B 6326', '2CDA A007 4B9F E9A5'),
		},
	}

	cmd_group = (
		('ref_walletgen_brain',       'generating new reference wallet + filename check (brain)'),
		('refaddrgen_legacy',         'new refwallet addr chksum (uncompressed)'),
		('refaddrgen_compressed',     'new refwallet addr chksum (compressed)'),
		('refaddrgen_segwit',         'new refwallet addr chksum (segwit)'),
		('refaddrgen_bech32',         'new refwallet addr chksum (bech32)'),
		('refkeyaddrgen_legacy',      'new refwallet key-addr chksum (uncompressed)'),
		('refkeyaddrgen_compressed',  'new refwallet key-addr chksum (compressed)'),
		('refkeyaddrgen_segwit',      'new refwallet key-addr chksum (segwit)'),
		('refkeyaddrgen_bech32',      'new refwallet key-addr chksum (bech32)'),
	)

	def call_addrgen(self, mmtype, name='addrgen'):
		wf = self.get_file_with_ext('mmdat')
		return getattr(self, name)(wf, check_ref=True, mmtype=mmtype)

	def refaddrgen_legacy(self):
		return self.call_addrgen('legacy')

	def refaddrgen_compressed(self):
		return self.call_addrgen('compressed')

	def refaddrgen_segwit(self):
		if self.proto.cap('segwit'):
			return self.call_addrgen('segwit')
		return 'skip'

	def refaddrgen_bech32(self):
		if self.proto.cap('segwit'):
			return self.call_addrgen('bech32')
		return 'skip'

	def refkeyaddrgen_legacy(self):
		return self.call_addrgen('legacy', 'keyaddrgen')

	def refkeyaddrgen_compressed(self):
		return self.call_addrgen('compressed', 'keyaddrgen')

	def refkeyaddrgen_segwit(self):
		if self.proto.cap('segwit'):
			return self.call_addrgen('segwit', 'keyaddrgen')
		return 'skip'

	def refkeyaddrgen_bech32(self):
		if self.proto.cap('segwit'):
			return self.call_addrgen('bech32', 'keyaddrgen')
		return 'skip'

class CmdTestRef3Passwd(CmdTestRef3Seed):
	'generated reference password files for 128-, 192- and 256-bit seeds'
	tmpdir_nums = [26, 27, 28]
	shared_deps = ['mmdat', pwfile]

	chk_data = {
		'lens': (128, 192, 256),
		'sids': ('FE3C6545', '1378FC64', '98831F3A'),
		'refpasswdgen_1':               'EB29 DC4F 924B 289F',
		'refpasswdgen_half_1':          'D310 2593 B5D9 2E88',
		'ref_b32passwdgen_1':           '37B6 C218 2ABC 7508',
		'ref_hexpasswdgen_1':           '8E99 E696 84CE E7D5',
		'ref_hexpasswdgen_half_1':      '8E99 E696 84CE E7D5',
		'ref_bip39_12_passwdgen_1':     '834F CF45 0B33 8AF0',
		'ref_bip39_18_passwdgen_1':     '834F CF45 0B33 8AF0',
		'ref_bip39_24_passwdgen_1':     '834F CF45 0B33 8AF0',
		'ref_hex2bip39_24_passwdgen_1': '91AF E735 A31D 72A0',
		'refpasswdgen_2':               'ADEA 0083 094D 489A',
		'refpasswdgen_half_2':          '12B3 4929 9506 76E0',
		'ref_b32passwdgen_2':           '2A28 C5C7 36EC 217A',
		'ref_hexpasswdgen_2':           '88F9 0D48 3A7E 7CC2',
		'ref_hexpasswdgen_half_2':      '59F3 8F48 861E 1186',
		'ref_bip39_12_passwdgen_2':     'D32D B8D7 A840 250B',
		'ref_bip39_18_passwdgen_2':     '0FAA 78DD A6BA 31AD',
		'ref_bip39_24_passwdgen_2':     '0FAA 78DD A6BA 31AD',
		'ref_hex2bip39_24_passwdgen_2': '0E8E 23C9 923F 7C2D',
		'refpasswdgen_3':               '2D6D 8FBA 422E 1315',
		'refpasswdgen_half_3':          '272C B770 0176 D7EA',
		'ref_b32passwdgen_3':           'F6C1 CDFB 97D9 FCAE',
		'ref_hexpasswdgen_3':           'BD4F A0AC 8628 4BE4',
		'ref_hexpasswdgen_half_3':      'FBDD F733 FFB9 21C1',
		'ref_bip39_12_passwdgen_3':     'A86E EA14 974A 1B0E',
		'ref_bip39_18_passwdgen_3':     'EF87 9904 88E2 5884',
		'ref_bip39_24_passwdgen_3':     'EBE8 2A8F 8F8C 7DBD',
		'ref_hex2bip39_24_passwdgen_3': '93FA 5EFD 33F3 760E',
		'ref_xmrseed_25_passwdgen_3':   '91AE E76A 2827 C8CC',
	}

	cmd_group = (
		('ref_walletgen_brain',        'generating new reference wallet + filename check (brain)'),
		('refpasswdgen',               'new refwallet passwd file chksum'),
		('refpasswdgen_half',          'new refwallet passwd file chksum (half-length)'),
		('ref_b32passwdgen',           'new refwallet passwd file chksum (base32)'),
		('ref_hexpasswdgen',           'new refwallet passwd file chksum (hex)'),
		('ref_hexpasswdgen_half',      'new refwallet passwd file chksum (hex, half-length)'),
		('ref_bip39_12_passwdgen',     'new refwallet passwd file chksum (BIP39, 12 words)'),
		('ref_bip39_18_passwdgen',     'new refwallet passwd file chksum (BIP39, up to 18 words)'),
		('ref_bip39_24_passwdgen',     'new refwallet passwd file chksum (BIP39, up to 24 words)'),
		('ref_xmrseed_25_passwdgen',   'new refwallet passwd file chksum (Monero 25-word mnemonic)'),
		('ref_hex2bip39_24_passwdgen', 'new refwallet passwd file chksum (hex-to-BIP39, up to 24 words)'),
	)

	def pwgen(self, ftype, id_str, pwfmt=None, pwlen=None, extra_opts=[], stdout=False):
		wf = self.get_file_with_ext('mmdat')
		pwfmt = ([f'--passwd-fmt={pwfmt}'] if pwfmt else [])
		pwlen = ([f'--passwd-len={pwlen}'] if pwlen else [])
		return self.addrgen(
			wf,
			check_ref  = True,
			ftype      = ftype,
			id_str     = id_str,
			extra_opts = pwfmt + pwlen + extra_opts,
			stdout     = stdout,
			no_passthru_opts = True)

	def refpasswdgen(self):
		return self.pwgen('pass', 'alice@crypto.org')

	def refpasswdgen_half(self):
		return self.pwgen('pass', 'alice@crypto.org', pwlen='h')

	def ref_b32passwdgen(self):
		return self.pwgen('pass32', 'фубар@crypto.org', 'b32', 17)

	def ref_hexpasswdgen(self):
		pwlen = {'1':32, '2':48, '3':64}[self.test_name[-1]]
		return self.pwgen('passhex', 'фубар@crypto.org', 'hex', pwlen)

	def ref_hexpasswdgen_half(self):
		return self.pwgen('passhex', 'фубар@crypto.org', 'hex', 'h', ['--accept-defaults'], stdout=True)

	def mn_pwgen(self, pwlen, pwfmt, ftype='passbip39'):
		if pwlen > {'1':12, '2':18, '3':24}[self.test_name[-1]]:
			return 'skip'
		if pwfmt == 'xmrseed':
			if self.cfg.no_altcoin:
				return 'skip'
			pwlen += 1
		return self.pwgen(ftype, 'фубар@crypto.org', pwfmt, pwlen, ['--accept-defaults'])

	def ref_bip39_12_passwdgen(self):
		return self.mn_pwgen(12, 'bip39')

	def ref_bip39_18_passwdgen(self):
		return self.mn_pwgen(18, 'bip39')

	def ref_bip39_24_passwdgen(self):
		return self.mn_pwgen(24, 'bip39')

	def ref_hex2bip39_24_passwdgen(self):
		return self.mn_pwgen(24, 'hex2bip39')

	def ref_xmrseed_25_passwdgen(self):
		return self.mn_pwgen(24, 'xmrseed', ftype='passxmrseed')

#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2019 The MMGen Project <mmgen@tuta.io>
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
ts_ref_3seed.py: Saved and generated reference file tests for 128, 192 and
                 256-bit seeds for the test.py test suite
"""

from mmgen.globalvars import g
from mmgen.opts import opt
from test.common import *
from test.test_py_d.common import *
from test.test_py_d.ts_base import *
from test.test_py_d.ts_shared import *
from test.test_py_d.ts_wallet import TestSuiteWalletConv

class TestSuiteRef3Seed(TestSuiteBase,TestSuiteShared):
	'saved and generated reference data for 128-, 192- and 256-bit seeds'
	networks = ('btc','btc_tn','ltc','ltc_tn')
	passthru_opts = ('coin','testnet')
	mmtypes = (None,)
	tmpdir_nums = [6,7,8]
	addr_idx_list_in = '1010,500-501,31-33,1,33,500,1011'
	pass_idx_list_in = '1,4,9-11,1100'
	chk_data = {
		'lens': (128, 192, 256),
		'sids': ('FE3C6545', '1378FC64', '98831F3A'),
		'refaddrgen_legacy_1': {
			'btc': ('B230 7526 638F 38CB','A9DC 5A13 12CB 1317'),
			'ltc': ('2B23 5E97 848A B961','AEC3 E774 0B21 0202'),
		},
		'refaddrgen_segwit_1': {
			'btc': ('9914 6D10 2307 F348','83C8 A6B6 ADA8 25B2'),
			'ltc': ('CC09 A190 B7DF B7CD','0425 7893 C6F1 ECA3'),
		},
		'refaddrgen_bech32_1': {
			'btc': ('C529 D686 31AA ACD4','21D0 26AD 3A22 5465'),
			'ltc': ('3DFB CFCC E180 DC9D','8C72 D5C2 07E0 5F7B'),
		},
		'refaddrgen_compressed_1': {
			'btc': ('95EB 8CC0 7B3B 7856','16E6 6170 154D 2202'),
			'ltc': ('35D5 8ECA 9A42 46C3','15B3 5492 D3D3 6854'),
		},
		'refkeyaddrgen_legacy_1': {
			'btc': ('CF83 32FB 8A8B 08E2','1F67 B73A FF8C 5D15'),
			'ltc': ('1896 A26C 7F14 2D01','FA0E CD4E ADAF DBF4'),
		},
		'refkeyaddrgen_compressed_1': {
			'btc': ('E43A FA46 5751 720A','FDEE 8E45 1C0A 02AD'),
			'ltc': ('7603 2FE3 2145 FFAD','3FE0 5A8E 5FBE FF3E'),
		},
		'refkeyaddrgen_segwit_1': {
			'btc': ('C13B F717 D4E8 CF59','BB71 175C 5416 19D8'),
			'ltc': ('054B 9794 55B4 5D82','DE85 3CF3 9636 FE2E'),
		},
		'refkeyaddrgen_bech32_1': {
			'btc': ('934F 1C33 6C06 B18C','A283 5BAB 7AF3 3EA4'),
			'ltc': ('A6AD DF53 5968 7B6A','9572 43E0 A4DC 0B2E'),
		},
		'refpasswdgen_1':     'EB29 DC4F 924B 289F',
		'refpasswdgen_half_1':'D310 2593 B5D9 2E88',
		'ref_b32passwdgen_1': '37B6 C218 2ABC 7508',
		'ref_hexpasswdgen_1': '8E99 E696 84CE E7D5',
		'ref_hexpasswdgen_half_1': '8E99 E696 84CE E7D5',
		'ref_bip39_12_passwdgen_1': '834F CF45 0B33 8AF0',
		'ref_bip39_18_passwdgen_1': '834F CF45 0B33 8AF0',
		'ref_bip39_24_passwdgen_1': '834F CF45 0B33 8AF0',
		'ref_hex2bip39_24_passwdgen_1': '91AF E735 A31D 72A0',
		'refaddrgen_legacy_2': {
			'btc': ('8C17 A5FA 0470 6E89','764C 66F9 7502 AAEA'),
			'ltc': ('2B77 A009 D5D0 22AD','51D1 979D 0A35 F24B'),
		},
		'refaddrgen_compressed_2': {
			'btc': ('2615 8401 2E98 7ECA','A386 EE07 A356 906D'),
			'ltc': ('197C C48C 3C37 AB0F','8DDC 5FE3 BFF9 1226'),
		},
		'refaddrgen_segwit_2': {
			'btc': ('91C4 0414 89E4 2089','BF9F C67F ED22 A47B'),
			'ltc': ('8F12 FA7B 9F12 594C','2609 8494 A23C F836'),
		},
		'refaddrgen_bech32_2': {
			'btc': ('2AA3 78DF B965 82EB','027B 1C1F 7FB2 D859'),
			'ltc': ('951C 8FB2 FCA5 87D1','4A5D 67E0 8210 FEF2'),
		},
		'refkeyaddrgen_legacy_2': {
			'btc': ('9648 5132 B98E 3AD9','1BD3 5A36 D51C 256D'),
			'ltc': ('DBD4 FAB6 7E46 CD07','8822 3FDF FEC0 6A8C'),
		},
		'refkeyaddrgen_compressed_2': {
			'btc': ('6D6D 3D35 04FD B9C3','94BF 4BCF 10B2 394B'),
			'ltc': ('F5DA 9D60 6798 C4E9','7918 88DE 9096 DD7A'),
		},
		'refkeyaddrgen_segwit_2': {
			'btc': ('C98B DF08 A3D5 204B','7E7F DF50 FE04 6F68'),
			'ltc': ('1829 7FE7 2567 CB91','BE92 D19C 7589 EF30'),
		},
		'refkeyaddrgen_bech32_2': {
			'btc': ('4A6B 3762 DF30 9368','12DD 1888 36BA 85F7'),
			'ltc': ('5C12 FDD4 17AB F179','E195 B28C 59C4 C5EC'),
		},
		'refpasswdgen_2':     'ADEA 0083 094D 489A',
		'refpasswdgen_half_2':'12B3 4929 9506 76E0',
		'ref_b32passwdgen_2': '2A28 C5C7 36EC 217A',
		'ref_hexpasswdgen_2': '88F9 0D48 3A7E 7CC2',
		'ref_hexpasswdgen_half_2': '59F3 8F48 861E 1186',
		'ref_bip39_12_passwdgen_2': 'D32D B8D7 A840 250B',
		'ref_bip39_18_passwdgen_2': '0FAA 78DD A6BA 31AD',
		'ref_bip39_24_passwdgen_2': '0FAA 78DD A6BA 31AD',
		'ref_hex2bip39_24_passwdgen_2': '0E8E 23C9 923F 7C2D',
		'refaddrgen_legacy_3': {
			'btc': ('6FEF 6FB9 7B13 5D91','424E 4326 CFFE 5F51'),
			'ltc': ('AD52 C3FE 8924 AAF0','4EBE 2E85 E969 1B30'),
		},
		'refaddrgen_compressed_3': {
			'btc': ('A33C 4FDE F515 F5BC','6C48 AA57 2056 C8C8'),
			'ltc': ('3FC0 8F03 C2D6 BD19','4C0A 49B6 2DD1 1BE0'),
		},
		'refaddrgen_segwit_3': {
			'btc': ('06C1 9C87 F25C 4EE6','072C 8B07 2730 CB7A'),
			'ltc': ('63DF E42A 0827 21C3','5DD1 D186 DBE1 59F2'),
		},
		'refaddrgen_bech32_3': {
			'btc': ('9D2A D4B6 5117 F02E','0527 9C39 6C1B E39A'),
			'ltc': ('FF1C 7939 5967 AB82','ED3D 8AA4 BED4 0B40'),
		},
		'refkeyaddrgen_legacy_3': {
			'btc': ('9F2D D781 1812 8BAD','88CC 5120 9A91 22C2'),
			'ltc': ('B804 978A 8796 3ED4','98B5 AC35 F334 0398'),
		},
		'refkeyaddrgen_compressed_3': {
			'btc': ('420A 8EB5 A9E2 7814','F43A CB4A 81F3 F735'),
			'ltc': ('8D1C 781F EB7F 44BC','05F3 5C68 FD31 FCEF'),
		},
		'refkeyaddrgen_segwit_3': {
			'btc': ('A447 12C2 DD14 5A9B','C770 7391 C415 21F9'),
			'ltc': ('E8A3 9F6E E164 A521','D3D5 BFDD F5D5 20BD'),
		},
		'refkeyaddrgen_bech32_3': {
			'btc': ('D0DD BDE3 87BE 15AE','7552 D70C AAB8 DEAA'),
			'ltc': ('74A0 7DD5 963B 6326','2CDA A007 4B9F E9A5'),
		},
		'refpasswdgen_3':     '2D6D 8FBA 422E 1315',
		'refpasswdgen_half_3':'272C B770 0176 D7EA',
		'ref_b32passwdgen_3': 'F6C1 CDFB 97D9 FCAE',
		'ref_hexpasswdgen_3': 'BD4F A0AC 8628 4BE4',
		'ref_hexpasswdgen_half_3': 'FBDD F733 FFB9 21C1',
		'ref_bip39_12_passwdgen_3': 'A86E EA14 974A 1B0E',
		'ref_bip39_18_passwdgen_3': 'EF87 9904 88E2 5884',
		'ref_bip39_24_passwdgen_3': 'EBE8 2A8F 8F8C 7DBD',
		'ref_hex2bip39_24_passwdgen_3': '93FA 5EFD 33F3 760E',
	}
	cmd_group = (
		# reading
		('ref_wallet_chk', ([],'saved reference wallet')),
		('ref_seed_chk',   ([],'saved seed file')),
		('ref_hex_chk',    ([],'saved mmhex file')),
		('ref_mn_chk',     ([],'saved native MMGen mnemonic file')),
		('ref_bip39_chk',  ([],'saved BIP39 mnemonic file')),
		('ref_hincog_chk', ([],'saved hidden incog reference wallet')),
		('ref_brain_chk',  ([],'saved brainwallet')), # in ts_shared
		# generating new reference ('abc' brainwallet) files:
		('ref_walletgen_brain',   ([],'generating new reference wallet + filename check (brain)')),
		('ref_walletconv_words',  (['mmdat',pwfile],'wallet filename (native mnemonic)')),
		('ref_walletconv_bip39',  (['mmdat',pwfile],'wallet filename (bip39)')),
		('ref_walletconv_seed',   (['mmdat',pwfile],'wallet filename (seed)')),
		('ref_walletconv_hexseed',(['mmdat',pwfile],'wallet filename (hex seed)')),
		('ref_walletconv_incog',  (['mmdat',pwfile],'wallet filename (incog)')),
		('ref_walletconv_xincog', (['mmdat',pwfile],'wallet filename (hex incog)')),
		('refaddrgen_legacy',     (['mmdat',pwfile],'new refwallet addr chksum (uncompressed)')),
		('refaddrgen_compressed',     (['mmdat',pwfile],'new refwallet addr chksum (compressed)')),
		('refaddrgen_segwit',     (['mmdat',pwfile],'new refwallet addr chksum (segwit)')),
		('refaddrgen_bech32',     (['mmdat',pwfile],'new refwallet addr chksum (bech32)')),
		('refkeyaddrgen_legacy',  (['mmdat',pwfile],'new refwallet key-addr chksum (uncompressed)')),
		('refkeyaddrgen_compressed', (['mmdat',pwfile],'new refwallet key-addr chksum (compressed)')),
		('refkeyaddrgen_segwit', (['mmdat',pwfile],'new refwallet key-addr chksum (segwit)')),
		('refkeyaddrgen_bech32', (['mmdat',pwfile],'new refwallet key-addr chksum (bech32)')),
		('refpasswdgen',         (['mmdat',pwfile],'new refwallet passwd file chksum')),
		('refpasswdgen_half',    (['mmdat',pwfile],'new refwallet passwd file chksum (half-length)')),
		('ref_b32passwdgen',     (['mmdat',pwfile],'new refwallet passwd file chksum (base32)')),
		('ref_hexpasswdgen',     (['mmdat',pwfile],'new refwallet passwd file chksum (hex)')),
		('ref_hexpasswdgen_half',(['mmdat',pwfile],'new refwallet passwd file chksum (hex, half-length)')),
		('ref_bip39_12_passwdgen',(['mmdat',pwfile],'new refwallet passwd file chksum (BIP39, 12 words)')),
		('ref_bip39_18_passwdgen',(['mmdat',pwfile],'new refwallet passwd file chksum (BIP39, up to 18 words)')),
		('ref_bip39_24_passwdgen',(['mmdat',pwfile],'new refwallet passwd file chksum (BIP39, up to 24 words)')),
		('ref_hex2bip39_24_passwdgen',(['mmdat',pwfile],'new refwallet passwd file chksum (hex-to-BIP39, up to 24 words)')),
	)

	def __init__(self,trunner,cfgs,spawn):
		for k,j in self.cmd_group:
			for n in (1,2,3): # 128,192,256 bits
				setattr(self,'{}_{}'.format(k,n),getattr(self,k))
		if cfgs:
			for n in self.tmpdir_nums:
				cfgs[str(n)]['addr_idx_list'] = self.addr_idx_list_in
				cfgs[str(n)]['pass_idx_list'] = self.pass_idx_list_in
		return TestSuiteBase.__init__(self,trunner,cfgs,spawn)

	def ref_wallet_chk(self):
		wf = joinpath(ref_dir,TestSuiteWalletConv.sources[str(self.seed_len)]['ref_wallet'])
		return self.walletchk(wf,pf=None,pw=True,sid=self.seed_id)

	def ref_ss_chk(self,ss=None):
		wf = joinpath(ref_dir,'{}.{}'.format(self.seed_id,ss.ext))
		return self.walletchk(wf,pf=None,desc=ss.desc,sid=self.seed_id)

	def ref_seed_chk(self):
		from mmgen.seed import SeedFile
		return self.ref_ss_chk(ss=SeedFile)

	def ref_hex_chk(self):
		from mmgen.seed import HexSeedFile
		return self.ref_ss_chk(ss=HexSeedFile)

	def ref_mn_chk(self):
		from mmgen.seed import MMGenMnemonic
		return self.ref_ss_chk(ss=MMGenMnemonic)

	def ref_bip39_chk(self):
		from mmgen.seed import BIP39Mnemonic
		return self.ref_ss_chk(ss=BIP39Mnemonic)

	def ref_hincog_chk(self,desc='hidden incognito data'):
		source = TestSuiteWalletConv.sources[str(self.seed_len)]
		for wtype,edesc,of_arg in ('hic_wallet','',[]), \
								('hic_wallet_old','(old format)',['-O']):
			ic_arg = ['-H{},{}'.format(joinpath(ref_dir,source[wtype]),ref_wallet_incog_offset)]
			slarg = ['-l{} '.format(self.seed_len)]
			hparg = ['-p1']
			if wtype == 'hic_wallet_old' and opt.profile: msg('')
			t = self.spawn('mmgen-walletchk',
				slarg + hparg + of_arg + ic_arg,
				extra_desc=edesc)
			t.passphrase(desc,self.wpasswd)
			if wtype == 'hic_wallet_old':
				t.expect('Is the Seed ID correct? (Y/n): ','\n')
			chk = t.expect_getend('Seed ID: ')
			t.close()
			cmp_or_die(self.seed_id,chk)
			ok_msg()
		t.skip_ok = True
		return t

	def ref_walletgen_brain(self):
		sl_arg = '-l{}'.format(self.seed_len)
		hp_arg = '-p{}'.format(ref_wallet_hash_preset)
		label = "test.py ref. wallet (pw '{}', seed len {}) α".format(ref_wallet_brainpass,self.seed_len)
		bf = 'ref.mmbrain'
		args = ['-d',self.tmpdir,hp_arg,sl_arg,'-ib','-L',label]
		self.write_to_tmpfile(bf,ref_wallet_brainpass)
		self.write_to_tmpfile(pwfile,self.wpasswd)
		t = self.spawn('mmgen-walletconv', args + [self.usr_rand_arg])
		t.license()
		t.expect('Enter brainwallet: ', ref_wallet_brainpass+'\n')
		t.passphrase_new('new MMGen wallet',self.wpasswd)
		t.usr_rand(self.usr_rand_chars)
		fn = os.path.split(t.written_to_file('MMGen wallet'))[-1]
		import re
		idx = int(self.test_name[-1]) - 1
		pat = r'{}-[0-9A-F]{{8}}\[{},1\].mmdat'.format(
			self.chk_data['sids'][idx],
			self.chk_data['lens'][idx] )
		assert re.match(pat,fn)
		sid = os.path.basename(fn.split('-')[0])
		cmp_or_die(sid,self.seed_id,desc='Seed ID')
		return t

	def ref_walletconv(self,fn,pf,ofmt,desc,ext,extra_args=[],re_pat=None):
		t = self.spawn('mmgen-walletconv',extra_args+['-d','test/trash','-o',ofmt,'-P'+pf,fn])
		fn = os.path.split(t.written_to_file(desc))[-1]
		idx = int(self.test_name[-1]) - 1
		sid = self.chk_data['sids'][idx]
		slen = self.chk_data['lens'][idx]
		if re_pat:
			import re
			assert re.match(re_pat.format(sid,slen),fn)
		else:
			cmp_or_die('{}[{}].{}'.format(sid,slen,ext),fn)
		return t

	def ref_walletconv_words(self,fn,pf):
		return self.ref_walletconv(fn,pf,ofmt='mn',desc='MMGen native mnemonic data',ext='mmwords')

	def ref_walletconv_bip39(self,fn,pf):
		return self.ref_walletconv(fn,pf,ofmt='bip39',desc='BIP39 mnemonic data',ext='bip39')

	def ref_walletconv_seed(self,fn,pf):
		return self.ref_walletconv(fn,pf,ofmt='mmseed',desc='Seed data',ext='mmseed')

	def ref_walletconv_hexseed(self,fn,pf):
		return self.ref_walletconv(fn,pf,ofmt='mmhex',desc='Hexadecimal seed data',ext='mmhex')

	def ref_walletconv_incog(self,fn,pf,desc='Incognito data',ofmt='incog',ext='mmincog'):
		args = ['-r0','-p1']
		pat = r'{}-[0-9A-F]{{8}}-[0-9A-F]{{8}}\[{},1\].' + ext
		return self.ref_walletconv(fn,pf,ofmt=ofmt,desc=desc,ext=ext,extra_args=args,re_pat=pat)

	def ref_walletconv_xincog(self,fn,pf):
		return self.ref_walletconv_incog(fn,pf,desc='Hex incognito data',ofmt='incog_hex',ext='mmincox')

	def refaddrgen_legacy(self,wf,pf):
		return self.addrgen(wf,pf=pf,check_ref=True,mmtype='legacy')

	def refaddrgen_compressed(self,wf,pf):
		return self.addrgen(wf,pf=pf,check_ref=True,mmtype='compressed')

	def refaddrgen_segwit(self,wf,pf):
		return self.addrgen(wf,pf=pf,check_ref=True,mmtype='segwit')

	def refaddrgen_bech32(self,wf,pf):
		return self.addrgen(wf,pf=pf,check_ref=True,mmtype='bech32')

	def refkeyaddrgen_legacy(self,wf,pf,mmtype='legacy'):
		return self.keyaddrgen(wf,pf,check_ref=True)

	def refkeyaddrgen_compressed(self,wf,pf):
		return self.keyaddrgen(wf,pf=pf,check_ref=True,mmtype='compressed')

	def refkeyaddrgen_segwit(self,wf,pf):
		return self.keyaddrgen(wf,pf=pf,check_ref=True,mmtype='segwit')

	def refkeyaddrgen_bech32(self,wf,pf):
		return self.keyaddrgen(wf,pf=pf,check_ref=True,mmtype='bech32')

	def refpasswdgen(self,wf,pf):
		return self.addrgen(wf,pf,check_ref=True,ftype='pass',id_str='alice@crypto.org')

	def refpasswdgen_half(self,wf,pf):
		ea = ['--passwd-len=h']
		return self.addrgen(wf,pf,check_ref=True,ftype='pass',id_str='alice@crypto.org',extra_args=ea)

	def ref_b32passwdgen(self,wf,pf):
		ea = ['--passwd-fmt=b32','--passwd-len=17']
		return self.addrgen(wf,pf,check_ref=True,ftype='pass32',id_str='фубар@crypto.org',extra_args=ea)

	def ref_hexpasswdgen(self,wf,pf):
		pw_len = {'1':32,'2':48,'3':64}[self.test_name[-1]]
		ea = ['--passwd-fmt=hex','--passwd-len={}'.format(pw_len)]
		return self.addrgen(wf,pf,check_ref=True,ftype='passhex',id_str='фубар@crypto.org',extra_args=ea)

	def ref_hexpasswdgen_half(self,wf,pf):
		ea = ['--passwd-fmt=hex','--passwd-len=h','--accept-defaults']
		return self.addrgen(wf,pf,check_ref=True,ftype='passhex',id_str='фубар@crypto.org',extra_args=ea,stdout=1)

	def ref_bip39_passwdgen(self,wf,pf,req_pw_len,pw_fmt='bip39',stdout=False):
		pw_len = min(req_pw_len,{'1':12,'2':18,'3':24}[self.test_name[-1]])
		ea = ['--passwd-fmt='+pw_fmt,'--passwd-len={}'.format(pw_len),'--accept-defaults']
		return self.addrgen(
			wf,pf,check_ref=True,ftype='passbip39',id_str='фубар@crypto.org',extra_args=ea,stdout=stdout)

	def ref_bip39_12_passwdgen(self,wf,pf): return self.ref_bip39_passwdgen(wf,pf,12,stdout=True)
	def ref_bip39_18_passwdgen(self,wf,pf): return self.ref_bip39_passwdgen(wf,pf,18,stdout=True)
	def ref_bip39_24_passwdgen(self,wf,pf): return self.ref_bip39_passwdgen(wf,pf,24)

	def ref_hex2bip39_24_passwdgen(self,wf,pf): return self.ref_bip39_passwdgen(wf,pf,24,'hex2bip39')

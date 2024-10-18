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
test.cmdtest_d.ct_wallet: Wallet conversion tests for the cmdtest.py test suite
"""

import sys, os

from mmgen.util import msg, capfirst, get_extension
from mmgen.wallet import get_wallet_cls

from ..include.common import cfg, joinpath, VirtBlockDevice
from .common import ref_dir, ref_wallet_brainpass, ref_wallet_incog_offset, hincog_fn, hincog_bytes
from .ct_base import CmdTestBase
from .ct_shared import CmdTestShared

class CmdTestWalletConv(CmdTestBase, CmdTestShared):
	'wallet conversion to and from reference data'
	networks = ('btc',)
	tmpdir_nums = [11, 12, 13]
	sources = {
		'128': {
			'ref_wallet':     'FE3C6545-D782B529[128,1].mmdat',
			'ic_wallet':      'FE3C6545-E29303EA-5E229E30[128,1].mmincog',
			'ic_wallet_hex':  'FE3C6545-BC4BE3F2-32586837[128,1].mmincox',

			'hic_wallet':      'FE3C6545-161E495F-BEB7548E[128,1].incog-offset123',
			'hic_wallet_old':  'FE3C6545-161E495F-9860A85B[128,1].incog-old.offset123',
		},
		'192': {
			'ref_wallet':     '1378FC64-6F0F9BB4[192,1].mmdat',
			'ic_wallet':      '1378FC64-2907DE97-F980D21F[192,1].mmincog',
			'ic_wallet_hex':  '1378FC64-4DCB5174-872806A7[192,1].mmincox',

			'hic_wallet':     '1378FC64-B55E9958-77256FC1[192,1].incog.offset123',
			'hic_wallet_old': '1378FC64-B55E9958-D85FF20C[192,1].incog-old.offset123',
		},
		'256': {
			'ref_wallet':     '98831F3A-27F2BF93[256,1].mmdat',
			'ic_wallet':      '98831F3A-5482381C-18460FB1[256,1].mmincog',
			'ic_wallet_hex':  '98831F3A-1630A9F2-870376A9[256,1].mmincox',

			'hic_wallet':      '98831F3A-F59B07A0-559CEF19[256,1].incog.offset123',
			'hic_wallet_old':  '98831F3A-F59B07A0-848535F3[256,1].incog-old.offset123',

		},
	}
	cmd_group = (
		# reading
		('ref_wallet_conv',            'conversion of saved reference wallet'),
		('ref_mn_conv',                'conversion of saved MMGen native mnemonic'),
		('ref_bip39_conv',             'conversion of saved BIP39 mnemonic'),
		('ref_seed_conv',              'conversion of saved seed file'),
		('ref_hex_conv',               'conversion of saved MMGen hexadecimal seed file'),
		('ref_plainhex_conv',          'conversion of saved plain hexadecimal seed file'),
		('ref_dieroll_conv',           'conversion of saved dieroll (b6d) seed file'),
		('ref_brain_conv',             'conversion of ref brainwallet'),
		('ref_incog_conv',             'conversion of saved incog wallet'),
		('ref_incox_conv',             'conversion of saved hex incog wallet'),
		('ref_hincog_conv',            'conversion of saved hidden incog wallet'),
		('ref_hincog_conv_old',        'conversion of saved hidden incog wallet (old format)'),
		# writing
		('ref_wallet_conv_out',        'ref seed conversion to wallet'),
		('ref_mn_conv_out',            'ref seed conversion to MMGen native mnemonic'),
		('ref_bip39_conv_out',         'ref seed conversion to BIP39 mnemonic'),
		('ref_hex_conv_out',           'ref seed conversion to MMGen hex seed'),
		('ref_plainhex_conv_out',      'ref seed conversion to plain hex seed'),
		('ref_dieroll_conv_out',       'ref seed conversion to dieroll (b6d) seed'),
		('ref_seed_conv_out',          'ref seed conversion to seed'),
		('ref_incog_conv_out',         'ref seed conversion to incog data'),
		('ref_incox_conv_out',         'ref seed conversion to hex incog data'),
		('ref_hincog_conv_out',        'ref seed conversion to hidden incog data'),
		('ref_hincog_blkdev_conv_out', 'ref seed conversion to hidden incog data on block device')
	)

	def __init__(self, trunner, cfgs, spawn):
		for k, _ in self.cmd_group:
			for n in (1, 2, 3):
				setattr(self, f'{k}_{n}', getattr(self, k))
		CmdTestBase.__init__(self, trunner, cfgs, spawn)

	def ref_wallet_conv(self):
		wf = joinpath(ref_dir, self.sources[str(self.seed_len)]['ref_wallet'])
		return self.walletconv_in(wf)

	def ref_mn_conv(self, ext='mmwords'):
		wf = joinpath(ref_dir, self.seed_id+'.'+ext)
		return self.walletconv_in(wf)

	def ref_bip39_conv(self):
		return self.ref_mn_conv(ext='bip39')
	def ref_seed_conv(self):
		return self.ref_mn_conv(ext='mmseed')
	def ref_hex_conv(self):
		return self.ref_mn_conv(ext='mmhex')
	def ref_plainhex_conv(self):
		return self.ref_mn_conv(ext='hex')
	def ref_dieroll_conv(self):
		return self.ref_mn_conv(ext='b6d')

	def ref_brain_conv(self):
		uopts = ['-i', 'bw', '-p', '1', '-l', str(self.seed_len)]
		return self.walletconv_in(None, uopts, icls=get_wallet_cls('brain'))

	def ref_incog_conv(self, wfk='ic_wallet', in_fmt='i'):
		uopts = ['-i', in_fmt, '-p', '1', '-l', str(self.seed_len)]
		wf = joinpath(ref_dir, self.sources[str(self.seed_len)][wfk])
		return self.walletconv_in(wf, uopts)

	def ref_incox_conv(self):
		return self.ref_incog_conv(in_fmt='xi', wfk='ic_wallet_hex')

	def ref_hincog_conv(self, wfk='hic_wallet', add_uopts=[]):
		ic_f = joinpath(ref_dir, self.sources[str(self.seed_len)][wfk])
		uopts = ['-i', 'hi', '-p', '1', '-l', str(self.seed_len)] + add_uopts
		hi_opt = ['-H', f'{ic_f},{ref_wallet_incog_offset}']
		return self.walletconv_in(
			None,
			uopts + hi_opt,
			icls = get_wallet_cls('incog_hidden'))

	def ref_hincog_conv_old(self):
		return self.ref_hincog_conv(wfk='hic_wallet_old', add_uopts=['-O'])

	def ref_wallet_conv_out(self):
		return self.walletconv_out('w')
	def ref_mn_conv_out(self):
		return self.walletconv_out('mn')
	def ref_bip39_conv_out(self):
		return self.walletconv_out('bip39')
	def ref_seed_conv_out(self):
		return self.walletconv_out('seed')
	def ref_hex_conv_out(self):
		return self.walletconv_out('hexseed')
	def ref_plainhex_conv_out(self):
		return self.walletconv_out('hex')
	def ref_dieroll_conv_out(self):
		return self.walletconv_out('dieroll')
	def ref_incog_conv_out(self):
		return self.walletconv_out('i')
	def ref_incox_conv_out(self):
		return self.walletconv_out('xi')

	def ref_hincog_conv_out(self, ic_f=None):
		if not ic_f:
			ic_f = joinpath(self.tmpdir, hincog_fn)
		hi_parms = f'{ic_f},{ref_wallet_incog_offset}'
		sl_parm = '-l' + str(self.seed_len)
		return self.walletconv_out(
			'hi',
			uopts     = ['-J', hi_parms, sl_parm],
			uopts_chk = ['-H', hi_parms, sl_parm])

	def ref_hincog_blkdev_conv_out(self):

		if self.skip_for_win('no loop device'):
			return 'skip'

		b = VirtBlockDevice(os.path.join(self.tmpdir, 'hincog_blkdev_img'), '1K')
		b.create()
		b.attach(dev_mode='0666' if sys.platform == 'linux' else None)
		self.ref_hincog_conv_out(ic_f=b.dev)
		b.detach()

		return 'ok'

	# wallet conversion tests
	def walletconv_in(self, infile, uopts=[], icls=None):
		ocls = get_wallet_cls('words')
		opts = ['-d', self.tmpdir, '-o', ocls.fmt_codes[0], self.usr_rand_arg]
		if_arg = [infile] if infile else []
		d = '(convert)'
		t = self.spawn('mmgen-walletconv', opts+uopts+if_arg, extra_desc=d)
		t.license()
		icls = icls or get_wallet_cls(ext=get_extension(infile))
		if icls.type == 'brain':
			t.expect('Enter brainwallet: ', ref_wallet_brainpass+'\n')
		if icls.enc and icls.type != 'brain':
			t.passphrase(icls.desc, self.wpasswd)
			if self.test_name[:19] == 'ref_hincog_conv_old':
				t.expect('Is the Seed ID correct? (Y/n): ', '\n')
			else:
				t.expect(['Passphrase is OK', ' are correct'])
		wf = t.written_to_file(capfirst(ocls.desc))
		t.p.wait()
		# back check of result
		msg('' if cfg.profile else ' OK')
		return self.walletchk(
			wf,
			extra_desc = '(check)',
			sid        = self.seed_id)

	def walletconv_out(self, out_fmt='w', uopts=[], uopts_chk=[]):
		wcls = get_wallet_cls(fmt_code=out_fmt)
		opts = ['-d', self.tmpdir, '-p1', '-o', out_fmt] + uopts
		infile = joinpath(ref_dir, self.seed_id+'.mmwords')
		t = self.spawn('mmgen-walletconv', [self.usr_rand_arg]+opts+[infile], extra_desc='(convert)')

		add_args = [f'-l{self.seed_len}']
		t.license()
		if wcls.enc and wcls.type != 'brain':
			t.passphrase_new('new '+wcls.desc, self.wpasswd)
			t.usr_rand(self.usr_rand_chars)
		if wcls.type.startswith('incog'):
			for _ in range(3):
				t.expect('Encrypting random data from your operating system with ephemeral key')
		if wcls.type == 'incog_hidden':
			t.hincog_create(hincog_bytes)
		if out_fmt == 'w':
			t.label()
		wf = t.written_to_file(capfirst(wcls.desc))

		if wcls.type == 'incog_hidden':
			add_args += uopts_chk
			wf = None
		msg('' if cfg.profile else ' OK')
		return self.walletchk(
			wf,
			wcls       = wcls,
			extra_desc = '(check)',
			sid        = self.seed_id,
			add_args   = add_args)

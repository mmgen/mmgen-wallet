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
ts_wallet.py: Wallet conversion tests for the test.py test suite
"""

import os
from mmgen.opts import opt
from test.test_py_d.common import *
from test.test_py_d.ts_base import *
from test.test_py_d.ts_shared import *

class TestSuiteWalletConv(TestSuiteBase,TestSuiteShared):
	'wallet conversion to and from reference data'
	networks = ('btc',)
	tmpdir_nums = [11,12,13]
	sources = { '128': {
					'ref_wallet':      'FE3C6545-D782B529[128,1].mmdat',
					'ic_wallet':       'FE3C6545-E29303EA-5E229E30[128,1].mmincog',
					'ic_wallet_hex':   'FE3C6545-BC4BE3F2-32586837[128,1].mmincox',

					'hic_wallet':       'FE3C6545-161E495F-BEB7548E[128,1].incog-offset123',
					'hic_wallet_old':   'FE3C6545-161E495F-9860A85B[128,1].incog-old.offset123',
				},
				'192': {
					'ref_wallet':      '1378FC64-6F0F9BB4[192,1].mmdat',
					'ic_wallet':       '1378FC64-2907DE97-F980D21F[192,1].mmincog',
					'ic_wallet_hex':   '1378FC64-4DCB5174-872806A7[192,1].mmincox',

					'hic_wallet':      '1378FC64-B55E9958-77256FC1[192,1].incog.offset123',
					'hic_wallet_old':  '1378FC64-B55E9958-D85FF20C[192,1].incog-old.offset123',
				},
				'256': {
					'ref_wallet':      '98831F3A-{}[256,1].mmdat'.format(('27F2BF93','E2687906')[g.testnet]),
					'ic_wallet':       '98831F3A-5482381C-18460FB1[256,1].mmincog',
					'ic_wallet_hex':   '98831F3A-1630A9F2-870376A9[256,1].mmincox',

					'hic_wallet':       '98831F3A-F59B07A0-559CEF19[256,1].incog.offset123',
					'hic_wallet_old':   '98831F3A-F59B07A0-848535F3[256,1].incog-old.offset123',

				},
			}
	cmd_group = (
		# reading
		('ref_wallet_conv',    'conversion of saved reference wallet'),
		('ref_mn_conv',        'conversion of saved MMGen native mnemonic'),
		('ref_bip39_conv',     'conversion of saved BIP39 mnemonic'),
		('ref_seed_conv',      'conversion of saved seed file'),
		('ref_hex_conv',       'conversion of saved hexadecimal seed file'),
		('ref_brain_conv',     'conversion of ref brainwallet'),
		('ref_incog_conv',     'conversion of saved incog wallet'),
		('ref_incox_conv',     'conversion of saved hex incog wallet'),
		('ref_hincog_conv',    'conversion of saved hidden incog wallet'),
		('ref_hincog_conv_old','conversion of saved hidden incog wallet (old format)'),
		# writing
		('ref_wallet_conv_out', 'ref seed conversion to wallet'),
		('ref_mn_conv_out',     'ref seed conversion to MMGen native mnemonic'),
		('ref_bip39_conv_out',  'ref seed conversion to BIP39 mnemonic'),
		('ref_hex_conv_out',    'ref seed conversion to hex seed'),
		('ref_seed_conv_out',   'ref seed conversion to seed'),
		('ref_incog_conv_out',  'ref seed conversion to incog data'),
		('ref_incox_conv_out',  'ref seed conversion to hex incog data'),
		('ref_hincog_conv_out', 'ref seed conversion to hidden incog data'),
		('ref_hincog_blkdev_conv_out', 'ref seed conversion to hidden incog data on block device')
	)

	def __init__(self,trunner,cfgs,spawn):
		for k,j in self.cmd_group:
			for n in (1,2,3):
				setattr(self,'{}_{}'.format(k,n),getattr(self,k))
		return TestSuiteBase.__init__(self,trunner,cfgs,spawn)

	def ref_wallet_conv(self):
		wf = joinpath(ref_dir,self.sources[str(self.seed_len)]['ref_wallet'])
		return self.walletconv_in(wf,'MMGen wallet',pw=True,oo=True)

	def ref_mn_conv(self,ext='mmwords',desc='MMGen native mnemonic data'):
		wf = joinpath(ref_dir,self.seed_id+'.'+ext)
		return self.walletconv_in(wf,desc,oo=True)

	def ref_bip39_conv(self):
		return self.ref_mn_conv(ext='bip39',desc='BIP39 mnemonic data')

	def ref_seed_conv(self):
		return self.ref_mn_conv(ext='mmseed',desc='Seed data')

	def ref_hex_conv(self):
		return self.ref_mn_conv(ext='mmhex',desc='Hexadecimal seed data')

	def ref_brain_conv(self):
		uopts = ['-i','b','-p','1','-l',str(self.seed_len)]
		return self.walletconv_in(None,'brainwallet',uopts,oo=True)

	def ref_incog_conv(self,wfk='ic_wallet',in_fmt='i',desc='incognito data'):
		uopts = ['-i',in_fmt,'-p','1','-l',str(self.seed_len)]
		wf = joinpath(ref_dir,self.sources[str(self.seed_len)][wfk])
		return self.walletconv_in(wf,desc,uopts,oo=True,pw=True)

	def ref_incox_conv(self):
		return self.ref_incog_conv(in_fmt='xi',wfk='ic_wallet_hex',desc='hex incognito data')

	def ref_hincog_conv(self,wfk='hic_wallet',add_uopts=[]):
		ic_f = joinpath(ref_dir,self.sources[str(self.seed_len)][wfk])
		uopts = ['-i','hi','-p','1','-l',str(self.seed_len)] + add_uopts
		hi_opt = ['-H','{},{}'.format(ic_f,ref_wallet_incog_offset)]
		return self.walletconv_in(None,'hidden incognito data',uopts+hi_opt,oo=True,pw=True)

	def ref_hincog_conv_old(self):
		return self.ref_hincog_conv(wfk='hic_wallet_old',add_uopts=['-O'])

	def ref_wallet_conv_out(self):
		return self.walletconv_out('MMGen wallet','w',pw=True)

	def ref_mn_conv_out(self):
		return self.walletconv_out('MMGen native mnemonic data','mn')

	def ref_bip39_conv_out(self):
		return self.walletconv_out('BIP39 mnemonic data','bip39')

	def ref_seed_conv_out(self):
		return self.walletconv_out('seed data','seed')

	def ref_hex_conv_out(self):
		return self.walletconv_out('hexadecimal seed data','hexseed')

	def ref_incog_conv_out(self):
		return self.walletconv_out('incognito data',out_fmt='i',pw=True)

	def ref_incox_conv_out(self):
		return self.walletconv_out('hex incognito data',out_fmt='xi',pw=True)

	def ref_hincog_conv_out(self,ic_f=None):
		if not ic_f: ic_f = joinpath(self.tmpdir,hincog_fn)
		hi_parms = '{},{}'.format(ic_f,ref_wallet_incog_offset)
		sl_parm = '-l' + str(self.seed_len)
		return self.walletconv_out( 'hidden incognito data','hi',
									uopts     = ['-J',hi_parms,sl_parm],
									uopts_chk = ['-H',hi_parms,sl_parm],
									pw        = True )

	def ref_hincog_blkdev_conv_out(self):
		if self.skip_for_win(): return 'skip'
		imsg('Creating block device image file')
		ic_img = joinpath(self.tmpdir,'hincog_blkdev_img')
		subprocess.check_output(['dd','if=/dev/zero','of='+ic_img,'bs=1K','count=1'],stderr=subprocess.PIPE)
		ic_dev = subprocess.check_output(['/sbin/losetup','-f']).strip().decode()
		ic_dev_mode_orig = '{:o}'.format(os.stat(ic_dev).st_mode & 0xfff)
		ic_dev_mode = '0666'
		imsg("Changing permissions on loop device to '{}'".format(ic_dev_mode))
		subprocess.check_output(['sudo','chmod',ic_dev_mode,ic_dev],stderr=subprocess.PIPE)
		imsg("Attaching loop device '{}'".format(ic_dev))
		subprocess.check_output(['/sbin/losetup',ic_dev,ic_img])
		self.ref_hincog_conv_out(ic_f=ic_dev)
		imsg("Detaching loop device '{}'".format(ic_dev))
		subprocess.check_output(['/sbin/losetup','-d',ic_dev])
		imsg("Resetting permissions on loop device to '{}'".format(ic_dev_mode_orig))
		subprocess.check_output(['sudo','chmod',ic_dev_mode_orig,ic_dev],stderr=subprocess.PIPE)
		return 'ok'

	# wallet conversion tests
	def walletconv_in(self,infile,desc,uopts=[],pw=False,oo=False):
		opts = ['-d',self.tmpdir,'-o','words',self.usr_rand_arg]
		if_arg = [infile] if infile else []
		d = '(convert)'
		t = self.spawn('mmgen-walletconv',opts+uopts+if_arg,extra_desc=d)
		t.license()
		if desc == 'brainwallet':
			t.expect('Enter brainwallet: ',ref_wallet_brainpass+'\n')
		if pw:
			t.passphrase(desc,self.wpasswd)
			if self.test_name[:19] == 'ref_hincog_conv_old':
				t.expect('Is the Seed ID correct? (Y/n): ','\n')
			else:
				t.expect(['Passphrase is OK',' are correct'])
		# Output
		wf = t.written_to_file('MMGen native mnemonic data',oo=oo)
		t.p.wait()
		# back check of result
		msg('' if opt.profile else ' OK')
		return self.walletchk(  wf,
								pf         = None,
								extra_desc = '(check)',
								desc       = 'MMGen native mnemonic data',
								sid        = self.seed_id )

	def walletconv_out(self,desc,out_fmt='w',uopts=[],uopts_chk=[],pw=False):
		opts = ['-d',self.tmpdir,'-p1','-o',out_fmt] + uopts
		infile = joinpath(ref_dir,self.seed_id+'.mmwords')
		t = self.spawn('mmgen-walletconv',[self.usr_rand_arg]+opts+[infile],extra_desc='(convert)')

		add_args = ['-l{}'.format(self.seed_len)]
		t.license()
		if pw:
			t.passphrase_new('new '+desc,self.wpasswd)
			t.usr_rand(self.usr_rand_chars)
		if ' '.join(desc.split()[-2:]) == 'incognito data':
			for i in (1,2,3):
				t.expect('Generating encryption key from OS random data ')
		if desc == 'hidden incognito data':
			ret = t.expect(['Create? (Y/n): ',"'YES' to confirm: "])
			if ret == 0:
				t.send('\n')
				t.expect('Enter file size: ',str(hincog_bytes)+'\n')
			else:
				t.send('YES\n')
		if out_fmt == 'w': t.label()
		wf = t.written_to_file(capfirst(desc),oo=True)
		pf = None

		if desc == 'hidden incognito data':
			add_args += uopts_chk
			wf = None
		msg('' if opt.profile else ' OK')
		return self.walletchk(  wf,
								pf         = pf,
								pw         = pw,
								desc       = desc,
								extra_desc = '(check)',
								sid        = self.seed_id,
								add_args   = add_args )

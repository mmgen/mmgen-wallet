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
ts_shared.py: Shared methods for the test.py test suite
"""

import os
from mmgen.globalvars import g
from mmgen.opts import opt
from mmgen.util import ymsg
from test.test_py_d.common import *
from test.common import *

class TestSuiteShared(object):
	'shared methods for the test.py test suite'

	def txcreate_ui_common(self,t,caller,
							menu=[],inputs='1',
							file_desc='Transaction',
							input_sels_prompt='to spend',
							bad_input_sels=False,non_mmgen_inputs=0,
							interactive_fee='',
							fee_desc='transaction fee',fee_res=None,eth_fee_res=None,
							add_comment='',view='t',save=True):
		for choice in menu + ['q']:
			t.expect(r'\[q\]uit view, .*?:.',choice,regex=True)
		if bad_input_sels:
			for r in ('x','3-1','9999'):
				t.expect(input_sels_prompt+': ',r+'\n')
		t.expect(input_sels_prompt+': ',inputs+'\n')

		if not caller[:4] == 'txdo':
			for i in range(non_mmgen_inputs):
				t.expect('Accept? (y/N): ','y')

		have_est_fee = t.expect([fee_desc+': ','OK? (Y/n): ']) == 1
		if have_est_fee and not interactive_fee:
			t.send('y')
		else:
			if have_est_fee: t.send('n')
			if eth_fee_res:
				t.expect('or gas price: ',interactive_fee+'\n')
			else:
				t.send(interactive_fee+'\n')
			if fee_res: t.expect(fee_res)
			t.expect('OK? (Y/n): ','y')

		t.expect('(Y/n): ','\n')     # chg amt OK?
		t.do_comment(add_comment)
		t.view_tx(view)
		if not caller[:4] == 'txdo':
			t.expect('(y/N): ',('n','y')[save])
			t.written_to_file(file_desc)

		return t

	def txsign_ui_common(   self,t,caller,
							view        = 't',
							add_comment = '',
							file_desc   = 'Signed transaction',
							ni          = False,
							save        = True,
							do_passwd   = False,
							has_label   = False ):
		txdo = caller[:4] == 'txdo'

		if do_passwd:
			t.passphrase('MMGen wallet',self.wpasswd)

		if not ni and not txdo:
			t.view_tx(view)
			t.do_comment(add_comment,has_label=has_label)
			t.expect('(Y/n): ',('n','y')[save])

		t.written_to_file(file_desc)

		return t

	def txsend_ui_common(   self,t,caller,
							view         = 'n',
							add_comment  = '',
							file_desc    = 'Sent transaction',
							confirm_send = True,
							bogus_send   = True,
							quiet        = False,
							has_label    = False ):

		txdo = caller[:4] == 'txdo'
		if not txdo:
			t.license() # MMGEN_NO_LICENSE is set, so does nothing
			t.view_tx(view)
			t.do_comment(add_comment,has_label=has_label)

		self._do_confirm_send(t,quiet=quiet,confirm_send=confirm_send)

		if bogus_send:
			txid = ''
			t.expect('BOGUS transaction NOT sent')
		else:
			txid = t.expect_getend('Transaction sent: ')
			assert len(txid) == 64,"'{}': Incorrect txid length!".format(txid)

		t.written_to_file(file_desc)

		return txid

	def txsign_end(self,t,tnum=None,has_label=False):
		t.expect('Signing transaction')
		t.do_comment(False,has_label=has_label)
		t.expect('Save signed transaction.*?\? \(Y/n\): ','y',regex=True)
		t.written_to_file('Signed transaction' + (' #' + tnum if tnum else ''), oo=True)
		return t

	def txsign( self, txfile, wf,
				pf         = '',
				bumpf      = '',
				save       = True,
				has_label  = False,
				do_passwd  = True,
				extra_opts = [],
				extra_desc = '' ):
		opts = extra_opts + ['-d',self.tmpdir,txfile] + ([wf] if wf else [])
		t = self.spawn('mmgen-txsign', opts, extra_desc)
		t.license()
		t.view_tx('n')
		if do_passwd: t.passphrase('MMGen wallet',self.wpasswd)
		if save:
			self.txsign_end(t,has_label=has_label)
		else:
			t.do_comment(False,has_label=has_label)
			t.expect('Save signed transaction? (Y/n): ','n')
			t.req_exit_val = 1
		return t

	def ref_brain_chk(self,bw_file=ref_bw_file):
		wf = joinpath(ref_dir,bw_file)
		add_args = ['-l{}'.format(self.seed_len), '-p'+ref_bw_hash_preset]
		return self.walletchk(wf,pf=None,add_args=add_args,
			desc='brainwallet',sid=self.ref_bw_seed_id)

	def walletchk(self,wf,pf,desc='MMGen wallet',add_args=[],sid=None,pw=False,extra_desc=''):
		args = []
		hp = self.hash_preset if hasattr(self,'hash_preset') else '1'
		wf_arg = [wf] if wf else []
		t = self.spawn('mmgen-walletchk',
				add_args+args+['-p',hp]+wf_arg,
				extra_desc=extra_desc)
		if desc != 'hidden incognito data':
			t.expect("Getting {} from file '".format(desc))
		if pw:
			t.passphrase(desc,self.wpasswd)
			t.expect(['Passphrase is OK', 'Passphrase.* are correct'],regex=True)
		chk = t.expect_getend('Valid {} for Seed ID '.format(desc))[:8]
		if sid: cmp_or_die(chk,sid)
		return t

	def addrgen(self,wf,pf=None,check_ref=False,ftype='addr',id_str=None,extra_args=[],mmtype=None):
		if not mmtype and ftype[:4] != 'pass':
			mmtype = self.segwit_mmtype
		cmd_pfx = (ftype,'pass')[ftype[:4]=='pass']
		t = self.spawn('mmgen-{}gen'.format(cmd_pfx),
				['-d',self.tmpdir] + extra_args +
				([],['--type='+str(mmtype)])[bool(mmtype)] +
				([],[wf])[bool(wf)] +
				([],[id_str])[bool(id_str)] +
				[getattr(self,'{}_idx_list'.format(cmd_pfx))],
				extra_desc='({})'.format(mmtype) if mmtype in ('segwit','bech32') else '')
		t.license()
		t.passphrase('MMGen wallet',self.wpasswd)
		t.expect('Passphrase is OK')
		desc = ('address','password')[ftype[:4]=='pass']
		chk = t.expect_getend(r'Checksum for {} data .*?: '.format(desc),regex=True)
		if ftype[:4] == 'pass':
			t.expect('Encrypt password list? (y/N): ','\n')
			t.written_to_file('Password list',oo=True)
		else:
			t.written_to_file('Addresses',oo=True)
		if check_ref:
			chk_ref = (self.chk_data[self.test_name] if ftype[:4] == 'pass' else
						self.chk_data[self.test_name][self.fork][g.testnet])
			cmp_or_die(chk,chk_ref,desc='{}list data checksum'.format(ftype))
		return t

	def keyaddrgen(self,wf,pf=None,check_ref=False,mmtype=None):
		if not mmtype:
			mmtype = self.segwit_mmtype
		args = ['-d',self.tmpdir,self.usr_rand_arg,wf,self.addr_idx_list]
		t = self.spawn('mmgen-keygen',
				([],['--type='+str(mmtype)])[bool(mmtype)] + args,
				extra_desc='({})'.format(mmtype) if mmtype in ('segwit','bech32') else '')
		t.license()
		t.passphrase('MMGen wallet',self.wpasswd)
		chk = t.expect_getend(r'Checksum for key-address data .*?: ',regex=True)
		if check_ref:
			chk_ref = self.chk_data[self.test_name][self.fork][g.testnet]
			cmp_or_die(chk,chk_ref,desc='key-address list data checksum')
		t.expect('Encrypt key list? (y/N): ','y')
		t.usr_rand(self.usr_rand_chars)
		t.hash_preset('new key list','1')
		t.passphrase_new('new key list',self.kapasswd)
		t.written_to_file('Encrypted secret keys',oo=True)
		return t

	def _do_confirm_send(self,t,quiet=False,confirm_send=True):
		t.expect('Are you sure you want to broadcast this')
		m = ('YES, I REALLY WANT TO DO THIS','YES')[quiet]
		t.expect("'{}' to confirm: ".format(m),('',m)[confirm_send]+'\n')

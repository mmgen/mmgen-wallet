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
test.cmdtest_d.shared: Shared methods for the cmdtest.py test suite
"""

from mmgen.util import get_extension
from mmgen.wallet import get_wallet_cls
from mmgen.addrlist import AddrList
from mmgen.passwdlist import PasswordList

from ..include.common import cfg, cmp_or_die, strip_ansi_escapes, joinpath, silence, end_silence
from .include.common import ref_bw_file, ref_bw_hash_preset, ref_dir

class CmdTestShared:
	'shared methods for the cmdtest.py test suite'

	@property
	def segwit_mmtype(self):
		return ('segwit', 'bech32')[bool(cfg.bech32)] if self.segwit else None

	@property
	def segwit_arg(self):
		return ['--type=' + self.segwit_mmtype] if self.segwit_mmtype else []

	def txcreate_ui_common(
			self,
			t,
			caller             = None,
			menu               = [],
			inputs             = '1',
			file_desc          = 'Unsigned transaction',
			input_sels_prompt  = 'to spend',
			bad_input_sels     = False,
			interactive_fee    = '',
			fee_desc           = 'transaction fee',
			fee_info_pat       = None,
			add_comment        = '',
			view               = 't',
			save               = True,
			return_early       = False,
			tweaks             = [],
			used_chg_addr_resp = None,
			auto_chg_addr      = None):

		txdo = (caller or self.test_name)[:4] == 'txdo'

		expect_pat = r'\[q\]uit menu, .*?:.'
		delete_pat = r'Enter account number .*:.'
		confirm_pat = r'OK\?.*:.'

		if used_chg_addr_resp is not None:
			t.expect('reuse harms your privacy.*:.*', used_chg_addr_resp, regex=True)

		if auto_chg_addr is not None:
			e1 = 'Choose a change address:.*Enter a number> '
			e2 = fr'Using .*{auto_chg_addr}.* as.*address'
			res = t.expect([e1, e2], regex=True)
			if res == 0:
				choice = [s.split(')')[0].lstrip() for s in t.p.match[0].split('\n') if auto_chg_addr in s][0]
				t.send(f'{choice}\n')
				t.expect(e2, regex=True)
			t.send('y')

		pat = expect_pat
		for choice in menu + ['q']:
			t.expect(pat, choice, regex=True)
			if self.proto.base_proto == 'Ethereum':
				pat = confirm_pat if pat == delete_pat else delete_pat if choice == 'D' else expect_pat

		if bad_input_sels:
			for r in ('x', '3-1', '9999'):
				t.expect(input_sels_prompt+': ', r+'\n')

		t.expect(input_sels_prompt+': ', inputs+'\n')

		have_est_fee = t.expect([f'{fee_desc}: ', 'OK? (Y/n): ']) == 1

		if have_est_fee and not interactive_fee:
			t.send('y')
		else:
			if have_est_fee:
				t.send('n')
				t.expect(f'{fee_desc}: ', interactive_fee+'\n')
			else:
				t.send(interactive_fee+'\n')
			if fee_info_pat:
				t.expect(fee_info_pat, regex=True)
			t.expect('OK? (Y/n): ', 'y')

		t.expect('(Y/n): ', '\n') # chg amt OK prompt

		if 'confirm_non_mmgen' in tweaks:
			t.expect('Continue? (Y/n)', '\n')

		if 'confirm_chg_non_mmgen' in tweaks:
			t.expect('to confirm: ', 'YES\n')

		t.do_comment(add_comment)

		if return_early:
			return t

		t.view_tx(view)

		if not txdo:
			t.expect('(y/N): ', ('n', 'y')[save])
			t.written_to_file(file_desc)

		return t

	def txsign_ui_common(
			self,
			t,
			caller      = None,
			view        = 't',
			add_comment = '',
			file_desc   = 'Signed transaction',
			ni          = False,
			save        = True,
			do_passwd   = False,
			passwd      = None,
			has_label   = False):

		txdo = (caller or self.test_name)[:4] == 'txdo'

		if do_passwd and txdo:
			t.passphrase('MMGen wallet', passwd or self.wpasswd)

		if not (ni or txdo):
			t.view_tx(view)
			if do_passwd:
				t.passphrase('MMGen wallet', passwd or self.wpasswd)
			t.do_comment(add_comment, has_label=has_label)
			t.expect('(Y/n): ', ('n', 'y')[save])

		t.written_to_file(file_desc)

		return t

	def txsend_ui_common(
			self,
			t,
			caller       = None,
			view         = 'n',
			add_comment  = '',
			file_desc    = 'Sent transaction',
			confirm_send = True,
			bogus_send   = True,
			test         = False,
			quiet        = False,
			contract_addr = None,
			has_label    = False,
			wait         = False):

		txdo = (caller or self.test_name)[:4] == 'txdo'

		if not txdo:
			t.license() # MMGEN_NO_LICENSE is set, so does nothing
			t.view_tx(view)
			t.do_comment(add_comment, has_label=has_label)

		if not test:
			self._do_confirm_send(t, quiet=quiet, confirm_send=confirm_send)

		if bogus_send:
			txid = ''
			t.expect('BOGUS transaction NOT sent')
		elif test == 'tx_proxy':
			t.expect('can be sent')
			return True
		else:
			m = 'TxID: ' if test else 'Transaction sent: '
			txid = strip_ansi_escapes(t.expect_getend(m))
			assert len(txid) == 64, f'{txid!r}: Incorrect txid length!'

		if not test:
			if wait:
				t.expect('Waiting for first confirmation..')
				while True:
					if t.expect(['.', 'OK']):
						break

			if contract_addr:
				_ = strip_ansi_escapes(t.expect_getend('Contract address: '))
				assert _ == contract_addr, f'Contract address mismatch: {_} != {contract_addr}'
			t.written_to_file(file_desc)

		return txid

	def txbump_ui_common(self, t, *, fee, fee_desc='transaction fee', bad_fee=None):
		t.expect('(Y/n): ', 'n') # network-estimated fee OK?
		if bad_fee:
			t.expect(f'{fee_desc}: ', f'{bad_fee}\n')
		t.expect(f'{fee_desc}: ', f'{fee}\n')
		t.expect('(Y/n): ', 'y') # fee OK?
		t.expect('(Y/n): ', 'y') # signoff
		t.expect('(y/N): ', 'n') # edit comment
		t.expect('(y/N): ', 'y') # save TX?
		t.written_to_file('Fee-bumped transaction')
		return t

	def txsign_end(self, t, tnum=None, has_label=False):
		t.expect('Signing transaction')
		t.do_comment(False, has_label=has_label)
		t.expect(r'Save signed transaction.*?\? \(Y/n\): ', 'y', regex=True)
		t.written_to_file('Signed transaction' + (' #' + tnum if tnum else ''))
		return t

	def txsign(
			self,
			wf,
			txfile,
			save       = True,
			has_label  = False,
			extra_opts = [],
			extra_desc = '',
			view       = 'n',
			dfl_wallet = False):
		opts = extra_opts + ['-d', self.tmpdir, txfile] + ([wf] if wf else [])
		wcls = get_wallet_cls(ext = 'mmdat' if dfl_wallet else get_extension(wf))
		t = self.spawn(
			'mmgen-txsign',
			opts,
			extra_desc,
			no_passthru_opts = ['coin'],
			exit_val = None if save or (wcls.enc and wcls.type != 'brain') else 1)
		t.license()
		t.view_tx(view)
		if wcls.enc and wcls.type != 'brain':
			t.passphrase(wcls.desc, self.wpasswd)
		if save:
			self.txsign_end(t, has_label=has_label)
		else:
			t.do_comment(False, has_label=has_label)
			t.expect('Save signed transaction? (Y/n): ', 'n')
			t.expect('not saved')
		return t

	def ref_brain_chk(self, bw_file=ref_bw_file):
		wf = joinpath(ref_dir, bw_file)
		add_args = [f'-l{self.seed_len}', f'-p{ref_bw_hash_preset}']
		return self.walletchk(wf, add_args=add_args, sid=self.ref_bw_seed_id)

	def walletchk(
			self,
			wf,
			wcls       = None,
			add_args   = [],
			sid        = None,
			extra_desc = '',
			dfl_wallet = False):
		hp = self.hash_preset if hasattr(self, 'hash_preset') else '1'
		wcls = wcls or get_wallet_cls(ext=get_extension(wf))
		t = self.spawn(
				'mmgen-walletchk',
				([] if dfl_wallet else ['-i', wcls.fmt_codes[0]])
				+ self.testnet_opt
				+ add_args + ['-p', hp]
				+ ([wf] if wf else []),
				extra_desc       = extra_desc,
				no_passthru_opts = True)
		if wcls.type != 'incog_hidden':
			t.expect(f"Getting {wcls.desc} from file ‘")
		if wcls.enc and wcls.type != 'brain':
			t.passphrase(wcls.desc, self.wpasswd)
			t.expect(['Passphrase is OK', 'Passphrase.* are correct'], regex=True)
		chksum = t.expect_getend(f'Valid {wcls.desc} for Seed ID ')[:8]
		if sid:
			cmp_or_die(chksum, sid)
		return t

	def addrgen(
			self,
			wf,
			check_ref  = False,
			ftype      = 'addr',
			id_str     = None,
			extra_opts = [],
			mmtype     = None,
			stdout     = False,
			dfl_wallet = False,
			no_passthru_opts = False):
		list_type = ftype[:4]
		passgen = list_type == 'pass'
		if not mmtype and not passgen:
			mmtype = self.segwit_mmtype
		t = self.spawn(
				f'mmgen-{list_type}gen',
				['-d', self.tmpdir] + extra_opts +
				([], ['--type='+str(mmtype)])[bool(mmtype)] +
				([], ['--stdout'])[stdout] +
				([], [wf])[bool(wf)] +
				([], [id_str])[bool(id_str)] +
				[getattr(self, f'{list_type}_idx_list')],
				extra_desc       = f'({mmtype})' if mmtype in ('segwit', 'bech32') else '',
				no_passthru_opts = no_passthru_opts)
		t.license()
		wcls = get_wallet_cls(ext = 'mmdat' if dfl_wallet else get_extension(wf))
		t.passphrase(wcls.desc, self.wpasswd)
		t.expect('Passphrase is OK')
		desc = ('address', 'password')[passgen]
		chksum = strip_ansi_escapes(t.expect_getend(rf'Checksum for {desc} data .*?: ', regex=True))
		if check_ref:
			chksum_chk = (
				self.chk_data[self.test_name] if passgen else
				self.chk_data[self.test_name][self.fork][self.proto.testnet])
			cmp_or_die(chksum, chksum_chk, desc=f'{ftype}list data checksum')
		if passgen:
			t.expect('Encrypt password list? (y/N): ', 'N')
		if stdout:
			t.read()
		else:
			fn = t.written_to_file('Password list' if passgen else 'Addresses')
			cls = PasswordList if passgen else AddrList
			silence()
			al = cls(cfg, self.proto, infile=fn, skip_chksum_msg=True) # read back the file we’ve written
			end_silence()
			cmp_or_die(al.chksum, chksum, desc=f'{ftype}list data checksum from file')
		return t

	def keyaddrgen(self, wf, check_ref=False, extra_opts=[], mmtype=None):
		if not mmtype:
			mmtype = self.segwit_mmtype
		args = ['-d', self.tmpdir, self.usr_rand_arg, wf, self.addr_idx_list]
		t = self.spawn('mmgen-keygen',
				([f'--type={mmtype}'] if mmtype else []) + extra_opts + args,
				extra_desc = f'({mmtype})' if mmtype in ('segwit', 'bech32') else '')
		t.license()
		wcls = get_wallet_cls(ext=get_extension(wf))
		t.passphrase(wcls.desc, self.wpasswd)
		chksum = t.expect_getend(r'Checksum for key-address data .*?: ', regex=True)
		if check_ref:
			chksum_chk = self.chk_data[self.test_name][self.fork][self.proto.testnet]
			cmp_or_die(chksum, chksum_chk, desc='key-address list data checksum')
		t.expect('Encrypt key list? (y/N): ', 'y')
		t.usr_rand(self.usr_rand_chars)
		t.hash_preset('new key-address list', '1')
		t.passphrase_new('new key-address list', self.kapasswd)
		t.written_to_file('Encrypted secret keys')
		return t

	def _do_confirm_send(self, t, quiet=False, confirm_send=True, sure=True):
		if sure:
			t.expect('Are you sure you want to broadcast this')
		m = ('YES, I REALLY WANT TO DO THIS', 'YES')[quiet]
		t.expect(f'{m!r} to confirm: ', ('', m)[confirm_send]+'\n')

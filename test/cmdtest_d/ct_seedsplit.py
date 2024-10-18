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
test.cmdtest_d.ct_seedsplit: Seed split/join tests for the cmdtest.py test suite
"""

import os

from mmgen.wallet import get_wallet_cls
from mmgen.util import capfirst

from ..include.common import strip_ansi_escapes, cmp_or_die
from .common import get_file_with_ext
from .ct_base import CmdTestBase

ref_wf = 'test/ref/98831F3A.bip39'
ref_sid = '98831F3A'
wpasswd = 'abc'
sh1_passwd = 'xyz'
dfl_wcls = get_wallet_cls('mmgen')

class CmdTestSeedSplit(CmdTestBase):
	'splitting and joining seeds'
	networks = ('btc',)
	tmpdir_nums = [23]
	color = True
	cmd_group = (
		('ss_walletgen',             'wallet generation'),
		('ss_2way_A_dfl1',           '2-way seed split (share A)'),
		('ss_2way_B_dfl1',           '2-way seed split (share B)'),
		('ss_2way_join_dfl1',        '2-way seed join'),
		('ss_2way_A_dfl2',           '2-way seed split ‘default’ (share A)'),
		('ss_2way_B_dfl2',           '2-way seed split ‘default’ (share B)'),
		('ss_2way_join_dfl2',        '2-way seed join ‘default’'),
		('ss_2way_A_alice',          '2-way seed split ‘alice’ (share A)'),
		('ss_2way_B_alice',          '2-way seed split ‘alice’ (share B)'),
		('ss_2way_join_alice',       '2-way seed join ‘alice’'),
		('ss_2way_join_alice_mix',   '2-way seed join ‘alice’ (out of order)'),
		('ss_2way_A_dfl_master3',    '2-way seed split with master share #3 (share A)'),
		('ss_2way_B_dfl_master3',    '2-way seed split with master share #3 (share B)'),
		('ss_2way_join_dfl_master3', '2-way seed join with master share #3'),
		('ss_2way_A_dfl_usw',        '2-way seed split of user-specified wallet (share A)'),
		('ss_2way_B_dfl_usw',        '2-way seed split of user-specified wallet (share B)'),
		('ss_2way_join_dfl_usw',     '2-way seed join of user-specified wallet'),
		('ss_3way_A_dfl',            '3-way seed split (share A)'),
		('ss_3way_B_dfl',            '3-way seed split (share B)'),
		('ss_3way_C_dfl',            '3-way seed split (share C)'),
		('ss_3way_join_dfl',         '3-way seed join'),
		('ss_3way_join_dfl_mix',     '3-way seed join (out of order)'),
		('ss_3way_A_foobar_master7', '3-way seed split ‘φυβαρ’ with master share #7 (share A)'),
		('ss_3way_B_foobar_master7', '3-way seed split ‘φυβαρ’ with master share #7 (share B)'),
		('ss_3way_C_foobar_master7', '3-way seed split ‘φυβαρ’ with master share #7 (share C)'),
		('ss_3way_join_foobar_master7', '3-way seed join ‘φυβαρ’ with master share #7'),
		('ss_3way_join_foobar_master7_mix', '3-way seed join ‘φυβαρ’ with master share #7 (out of order)'),

		('ss_3way_join_dfl_bad_invocation', 'bad invocation of ‘mmgen-seedjoin’ - --id-str with non-master join'),
		('ss_bad_invocation1',       'bad invocation of ‘mmgen-seedsplit’ - no arguments'),
		('ss_bad_invocation2',       'bad invocation of ‘mmgen-seedsplit’ - master share with split specifier'),
		('ss_bad_invocation3',       'bad invocation of ‘mmgen-seedsplit’ - nonexistent file'),
		('ss_bad_invocation4',       'bad invocation of ‘mmgen-seedsplit’ - invalid file extension'),
		('ss_bad_invocation5',       'bad invocation of ‘mmgen-seedjoin’ - no arguments'),
		('ss_bad_invocation6',       'bad invocation of ‘mmgen-seedjoin’ - one file argument'),
		('ss_bad_invocation7',       'bad invocation of ‘mmgen-seedjoin’ - invalid file extension'),
		('ss_bad_invocation8',       'bad invocation of ‘mmgen-seedjoin’ - nonexistent file'),
		('ss_bad_invocation9',       'bad invocation of ‘mmgen-seedsplit’ - bad specifier'),
		('ss_bad_invocation10',      'bad invocation of ‘mmgen-seedsplit’ - nonexistent file'),
		('ss_bad_invocation11',      'bad invocation of ‘mmgen-seedsplit’ - invalid file extension'),
	)

	def get_tmp_subdir(self, subdir):
		return os.path.join(self.tmpdir, subdir)

	def ss_walletgen(self):
		t = self.spawn('mmgen-walletgen', ['-r0', '-p1'])
		t.passphrase_new('new '+dfl_wcls.desc, wpasswd)
		t.label()
		self.write_to_tmpfile('dfl.sid', strip_ansi_escapes(t.expect_getend('Seed ID: ')))
		t.expect('move it to the data directory? (Y/n): ', 'y')
		t.written_to_file(capfirst(dfl_wcls.desc))
		return t

	def ss_splt(self, tdir, ofmt, spec, add_args=[], wf=None, master=None):
		try:
			os.mkdir(self.get_tmp_subdir(tdir))
		except:
			pass
		t = self.spawn('mmgen-seedsplit',
				['-q', '-d', self.get_tmp_subdir(tdir), '-r0', '-o', ofmt]
				+ (['-L', (spec or 'label')] if ofmt == 'w' else [])
				+ add_args
				+ ([f'--master-share={master}'] if master else [])
				+ ([wf] if wf else [])
				+ ([spec] if spec else []))
		if not wf:
			t.passphrase(dfl_wcls.desc, wpasswd)
		if spec:
			from mmgen.seedsplit import SeedSplitSpecifier
			sss = SeedSplitSpecifier(spec)
			pat = rf'Processing .*\b{sss.idx}\b of \b{sss.count}\b of .* id .*‘{sss.id}’'
		else:
			pat = f'master share #{master}'
		t.expect(pat, regex=True)
		ocls = get_wallet_cls(fmt_code=ofmt)
		if ocls.enc:
			t.hash_preset('new '+ocls.desc, '1')
			t.passphrase_new('new '+ocls.desc, sh1_passwd)
			if ocls.type == 'incog_hidden':
				t.hincog_create(1234)
		t.written_to_file(capfirst(ocls.desc))
		return t

	def ss_join(
			self,
			tdir,
			ofmt,
			in_exts,
			add_args = [],
			sid      = None,
			exit_val = None,
			master   = None,
			id_str   = None):
		td = self.get_tmp_subdir(tdir)
		shares = [get_file_with_ext(td, f) for f in in_exts]
		if not sid:
			sid = self.read_from_tmpfile('dfl.sid')
		t = self.spawn('mmgen-seedjoin',
				add_args
				+ ([f'--master-share={master}'] if master else [])
				+ ([f'--id-str={id_str}'] if id_str else [])
				+ ['-d', td, '-o', ofmt]
				+ (['--label', 'Joined Wallet Label', '-r0'] if ofmt == 'w' else [])
				+ shares,
				exit_val = exit_val)
		if exit_val:
			return t
		icls = (dfl_wcls if 'mmdat' in in_exts
			else get_wallet_cls('incog') if 'mmincog' in in_exts
			else get_wallet_cls('incog_hex') if 'mmincox' in in_exts
			else get_wallet_cls('incog_hidden') if '-H' in add_args
			else None)
		if icls.type.startswith('incog'):
			t.hash_preset(icls.desc, '1')
		if icls:
			t.passphrase(icls.desc, sh1_passwd)
		if master:
			fs = "master share #{}, split id.*‘{}’.*, share count {}"
			pat = fs.format(
				master,
				id_str or 'default',
				len(shares) + (icls.type=='incog_hidden'))
			t.expect(pat, regex=True)
		sid_cmp = strip_ansi_escapes(t.expect_getend('Joined Seed ID: '))
		cmp_or_die(sid, sid_cmp)
		ocls = get_wallet_cls(fmt_code=ofmt)
		if ocls.type == 'mmgen':
			t.hash_preset('new '+ocls.desc, '1')
			t.passphrase_new('new '+ocls.desc, wpasswd)
		t.written_to_file(capfirst(ocls.desc))
		return t

	def get_hincog_arg(self, tdir, suf='-default-2of2'):
		sid = self.read_from_tmpfile('dfl.sid')
		return os.path.join(self.tmpdir, tdir, sid+suf+'.hincog') + ',123'

	def ss_2way_A_dfl1(self):
		return self.ss_splt('2way_dfl1', 'w', '1:2')
	def ss_2way_B_dfl1(self):
		return self.ss_splt('2way_dfl1', 'bip39', '2:2')
	def ss_2way_join_dfl1(self):
		return self.ss_join('2way_dfl1', 'w', ['mmdat', 'bip39'])

	def ss_2way_A_dfl2(self):
		return self.ss_splt('2way_dfl2', 'seed', 'default:1:2')
	def ss_2way_B_dfl2(self):
		return self.ss_splt('2way_dfl2', 'hincog', 'default:2:2', ['-J', self.get_hincog_arg('2way_dfl2')])
	def ss_2way_join_dfl2(self):
		return self.ss_join('2way_dfl2', 'mmhex', ['mmseed'], ['-H', self.get_hincog_arg('2way_dfl2')])

	def ss_2way_A_alice(self):
		return self.ss_splt('2way_alice', 'w', 'alice:1:2')
	def ss_2way_B_alice(self):
		return self.ss_splt('2way_alice', 'mmhex', 'alice:2:2')
	def ss_2way_join_alice(self):
		return self.ss_join('2way_alice', 'seed', ['mmdat', 'mmhex'])
	def ss_2way_join_alice_mix(self):
		return self.ss_join('2way_alice', 'seed', ['mmhex', 'mmdat'])

	def ss_2way_A_dfl_usw(self):
		return self.ss_splt('2way_dfl_usw', 'words', '1:2', [], wf=ref_wf)
	def ss_2way_B_dfl_usw(self):
		return self.ss_splt('2way_dfl_usw', 'incog', '2:2', [], wf=ref_wf)
	def ss_2way_join_dfl_usw(self):
		return self.ss_join('2way_dfl_usw', 'mmhex', ['mmwords', 'mmincog'], sid=ref_sid)

	def ss_3way_A_dfl(self):
		return self.ss_splt('3way_dfl', 'words', '1:3')
	def ss_3way_B_dfl(self):
		return self.ss_splt('3way_dfl', 'incog_hex', '2:3')
	def ss_3way_C_dfl(self):
		return self.ss_splt('3way_dfl', 'bip39', '3:3')
	def ss_3way_join_dfl(self):
		return self.ss_join('3way_dfl', 'mmhex', ['mmwords', 'mmincox', 'bip39'])
	def ss_3way_join_dfl_mix(self):
		return self.ss_join('3way_dfl', 'mmhex', ['bip39', 'mmwords', 'mmincox'])

	def ss_2way_A_dfl_master3(self):
		return self.ss_splt('2way_dfl_master3', 'w', '', master=3)
	def ss_2way_B_dfl_master3(self):
		return self.ss_splt('2way_dfl_master3', 'bip39', '2:2', master=3)
	def ss_2way_join_dfl_master3(self):
		return self.ss_join('2way_dfl_master3', 'mmhex', ['mmdat', 'bip39'], master=3)

	tdir2 = '3way_foobar_master7'
	def ss_3way_C_foobar_master7(self):
		return self.ss_splt(self.tdir2, 'hincog', '',
					['-J', self.get_hincog_arg(self.tdir2, '-master7')], master=7)
	def ss_3way_B_foobar_master7(self):
		return self.ss_splt(self.tdir2, 'bip39', 'φυβαρ:2:3', master=7)
	def ss_3way_A_foobar_master7(self):
		return self.ss_splt(self.tdir2, 'mmhex', 'φυβαρ:3:3', master=7)
	def ss_3way_join_foobar_master7(self):
		return self.ss_join(self.tdir2, 'seed', ['bip39', 'mmhex'],
							['-H', self.get_hincog_arg(self.tdir2, '-master7')], master=7, id_str='φυβαρ')
	def ss_3way_join_foobar_master7_mix(self):
		return self.ss_join(self.tdir2, 'seed', ['mmhex', 'bip39'],
							['-H', self.get_hincog_arg(self.tdir2, '-master7')], master=7, id_str='φυβαρ')

	def ss_bad_invocation(self, cmd, args, exit_val, errmsg):
		t = self.spawn(cmd, args, exit_val=exit_val)
		t.expect(errmsg, regex=True)
		return t

	def ss_3way_join_dfl_bad_invocation(self):
		t = self.ss_join('3way_dfl', 'mmhex',
			['mmwords', 'mmincox', 'bip39'],
			id_str   = 'foo',
			exit_val = 1)
		t.expect('option meaningless')
		return t

	def ss_bad_invocation1(self):
		return self.ss_bad_invocation(
			'mmgen-seedsplit', [], 1, 'USAGE:')

	def ss_bad_invocation2(self):
		return self.ss_bad_invocation(
			'mmgen-seedsplit', ['-M1', '1:9'], 1, 'meaningless in master share context')

	def ss_bad_invocation3(self):
		return self.ss_bad_invocation(
			'mmgen-seedsplit', [self.tmpdir+'/no.mmdat', '1:9'], 1, 'input file .* not found')

	def ss_bad_invocation4(self):
		return self.ss_bad_invocation(
			'mmgen-seedsplit', [self.tmpdir+'/dfl.sid', '1:9'], 1, 'unrecognized .* extension')

	def ss_bad_invocation5(self):
		return self.ss_bad_invocation(
			'mmgen-seedjoin', [], 1, 'USAGE:')

	def ss_bad_invocation6(self):
		return self.ss_bad_invocation(
			'mmgen-seedjoin', [self.tmpdir+'/a'], 1, 'USAGE:')

	def ss_bad_invocation7(self):
		return self.ss_bad_invocation(
			'mmgen-seedjoin', [self.tmpdir+'/a', self.tmpdir+'/b'], 1, 'unrecognized .* extension')

	def ss_bad_invocation8(self):
		return self.ss_bad_invocation(
			'mmgen-seedjoin', [self.tmpdir+'/a.mmdat', self.tmpdir+'/b.mmdat'], 1, 'input file .* not found')

	def ss_bad_invocation9(self):
		return self.ss_bad_invocation(
			'mmgen-seedsplit', ['x'], 1, 'USAGE:')

	def ss_bad_invocation10(self):
		return self.ss_bad_invocation(
			'mmgen-seedsplit', [self.tmpdir+'/a.mmdat', '1:2'], 1, 'input file .* not found')

	def ss_bad_invocation11(self):
		return self.ss_bad_invocation(
			'mmgen-seedsplit', [self.tmpdir+'/dfl.sid', '1:2'], 1, 'unrecognized .* extension')

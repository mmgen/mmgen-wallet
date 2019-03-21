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
ts_misc.py: Miscellaneous test groups for the test.py test suite
"""

from mmgen.globalvars import g
from test.common import *
from test.test_py_d.common import *
from test.test_py_d.ts_base import *
from test.test_py_d.ts_main import TestSuiteMain

class TestSuiteHelp(TestSuiteBase):
	'help and usage screens'
	tmpdir_nums = []
	passthru_opts = ('coin','testnet')
	cmd_group = (
		('helpscreens',     (1,'help screens',             [])),
		('longhelpscreens', (1,'help screens (--longhelp)',[])),
		('tool_help',       (1,"'mmgen-tool' usage screen",[])),
		('test_help',       (1,"'test.py' help screens",[])),
	)
	def helpscreens(self,arg='--help'):
		scripts = (
			'walletgen','walletconv','walletchk','txcreate','txsign','txsend','txdo','txbump',
			'addrgen','addrimport','keygen','passchg','tool','passgen','regtest','autosign')
		for s in scripts:
			t = self._run_cmd('mmgen-'+s,[arg],extra_desc='(mmgen-{})'.format(s),no_output=True)
		return t

	def longhelpscreens(self):
		return self.helpscreens(arg='--longhelp')

	def _run_cmd(   self, cmd_name,
					cmd_args = [],
					no_msg = False,
					extra_desc = '',
					cmd_dir = 'cmds',
					no_output = False):
		t = self.spawn( cmd_name,
						args       = cmd_args,
						no_msg     = no_msg,
						extra_desc = extra_desc,
						cmd_dir    = cmd_dir,
						no_output  = no_output)
		t.read()
		ret = t.p.wait()
		if ret == 0:
			msg('OK')
		else:
			rdie(1,"\n'{}' returned {}".format(self.test_name,ret))
		t.skip_ok = True
		return t

	def tool_help(self):
		self._run_cmd('mmgen-tool',['help'],extra_desc="('mmgen-tool help')")
		return self._run_cmd('mmgen-tool',['usage'],extra_desc="('mmgen-tool usage')")

	def test_help(self):
		self._run_cmd('test.py',['-h'],cmd_dir='test')
		self._run_cmd('test.py',['-L'],cmd_dir='test',extra_desc='(cmd group list)')
		return self._run_cmd('test.py',['-l'],cmd_dir='test',extra_desc='(cmd list)')

class TestSuiteTool(TestSuiteMain,TestSuiteBase):
	"tests for interactive 'mmgen-tool' commands"
	networks = ('btc',)
	segwit_opts_ok = False
	tmpdir_nums = [9]
	enc_infn = 'tool_encrypt.in'
	cmd_group = (
		('tool_find_incog_data', (9,"'mmgen-tool find_incog_data'", [[[hincog_fn],1],[[incog_id_fn],1]])),
		('tool_rand2file',       (9,"'mmgen-tool rand2file'", [])),
		('tool_encrypt',         (9,"'mmgen-tool encrypt' (random data)",     [])),
		('tool_decrypt',         (9,"'mmgen-tool decrypt' (random data)", [[[enc_infn+'.mmenc'],9]])),
		# ('tool_encrypt_ref', (9,"'mmgen-tool encrypt' (reference text)",  [])),
	)

	def tool_rand2file(self):
		outfile = os.path.join(self.tmpdir,'rand2file.out')
		from mmgen.tool import MMGenToolCmd
		tu = MMGenToolCmd()
		for nbytes in ('1','1023','1K','1048575','1M','1048577','123M'):
			t = self.spawn( 'mmgen-tool',
							['-d',self.tmpdir,'-r0','rand2file','rand2file.out',nbytes],
							extra_desc='({} byte{})'.format(nbytes,suf(tu.bytespec(nbytes)))
							)
			t.expect('random data written to file')
			t.read()
			t.p.wait()
			t.ok()
		t.skip_ok = True
		return t

	def tool_encrypt(self):
		infile = joinpath(self.tmpdir,self.enc_infn)
		write_to_file(infile,os.urandom(1033),binary=True)
		t = self.spawn('mmgen-tool',['-d',self.tmpdir,self.usr_rand_arg,'encrypt',infile])
		t.usr_rand(self.usr_rand_chars)
		t.hash_preset('user data','1')
		t.passphrase_new('user data',tool_enc_passwd)
		t.written_to_file('Encrypted data')
		return t

	def tool_decrypt(self,f1):
		out_fn = 'tool_encrypt.out'
		t = self.spawn('mmgen-tool',['-d',self.tmpdir,'decrypt',f1,'outfile='+out_fn,'hash_preset=1'])
		t.passphrase('user data',tool_enc_passwd)
		t.written_to_file('Decrypted data')
		d1 = self.read_from_tmpfile(self.enc_infn,binary=True)
		d2 = self.read_from_tmpfile(out_fn,binary=True)
		cmp_or_die(d1,d2)
		return t

	def tool_find_incog_data(self,f1,f2):
		i_id = read_from_file(f2).rstrip()
		vmsg('Incog ID: {}'.format(cyan(i_id)))
		t = self.spawn('mmgen-tool',['-d',self.tmpdir,'find_incog_data',f1,i_id])
		o = t.expect_getend('Incog data for ID {} found at offset '.format(i_id))
		os.unlink(f1)
		cmp_or_die(hincog_offset,int(o))
		return t

class TestSuiteRefTX(TestSuiteMain,TestSuiteBase):
	'create a reference transaction file (administrative command)'
	segwit_opts_ok = False
	passthru_opts = ('coin','testnet')
	tmpdir_nums = [31,32,33,34]
	cmd_group = (
		('ref_tx_addrgen1', (31,'address generation (legacy)', [[[],1]])),
		('ref_tx_addrgen2', (32,'address generation (compressed)', [[[],1]])),
		('ref_tx_addrgen3', (33,'address generation (segwit)', [[[],1]])),
		('ref_tx_addrgen4', (34,'address generation (bech32)', [[[],1]])),
		('ref_tx_txcreate', (31,'transaction creation',
								([['addrs'],31],[['addrs'],32],[['addrs'],33],[['addrs'],34]))),
	)

	def __init__(self,trunner,cfgs,spawn):
		for n in self.tmpdir_nums:
			cfgs[str(n)].update({   'addr_idx_list': '1-2',
									'segwit': n in (33,34),
									'dep_generators': { 'addrs':'ref_tx_addrgen'+str(n)[-1] }})
		return TestSuiteMain.__init__(self,trunner,cfgs,spawn)

	def ref_tx_addrgen(self,atype):
		if atype not in g.proto.mmtypes: return
		t = self.spawn('mmgen-addrgen',['--outdir='+self.tmpdir,'--type='+atype,dfl_words_file,'1-2'])
		t.read()
		return t

	def ref_tx_addrgen1(self): return self.ref_tx_addrgen(atype='L')
	def ref_tx_addrgen2(self): return self.ref_tx_addrgen(atype='C')
	def ref_tx_addrgen3(self): return self.ref_tx_addrgen(atype='S')
	def ref_tx_addrgen4(self): return self.ref_tx_addrgen(atype='B')

	def ref_tx_txcreate(self,f1,f2,f3,f4):
		sources = ['31','32']
		if 'S' in g.proto.mmtypes: sources += ['33']
		if 'B' in g.proto.mmtypes: sources += ['34']
		return self.txcreate_common(
									addrs_per_wallet = 2,
									sources          = sources,
									add_args         = ['--locktime=1320969600'],
									do_label         = True )

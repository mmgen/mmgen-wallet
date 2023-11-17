#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
#
# Project source code repository: https://github.com/mmgen/mmgen-wallet
# Licensed according to the terms of GPL Version 3.  See LICENSE for details.

"""
test.cmdtest_py_d.ct_tool: tool tests for the MMGen cmdtest.py test suite
"""

import sys,os

from mmgen.util import suf
from mmgen.color import cyan

from ..include.common import (
	cfg,
	vmsg,
	read_from_file,
	write_to_file,
	cmp_or_die,
	joinpath,
	getrand
)
from .common import hincog_fn,incog_id_fn,hincog_offset,tool_enc_passwd,ref_dir
from .ct_base import CmdTestBase
from .ct_main import CmdTestMain

class CmdTestTool(CmdTestMain,CmdTestBase):
	"interactive 'mmgen-tool' commands"
	networks = ('btc',)
	segwit_opts_ok = False
	tmpdir_nums = [9]
	enc_infn = 'tool_encrypt.in'
	cmd_group = (
		('tool_find_incog_data', (9,"'mmgen-tool find_incog_data'", [[[hincog_fn],1],[[incog_id_fn],1]])),
		('tool_rand2file',       (9,"'mmgen-tool rand2file'", [])),
		('tool_encrypt',         (9,"'mmgen-tool encrypt' (random data)",     [])),
		('tool_decrypt',         (9,"'mmgen-tool decrypt' (random data)", [[[enc_infn+'.mmenc'],9]])),
		('tool_twview_bad_comment',(9,"'mmgen-tool twview' (with bad comment)", [])),
		('tool_extract_key_from_geth_wallet',(9,"'mmgen-tool extract_key_from_geth_wallet'", [])),
		('tool_api',             (9,'tool API (initialization, config methods, wif2addr)',[])),
		# ('tool_encrypt_ref', (9,"'mmgen-tool encrypt' (reference text)",  [])),
	)

	def tool_rand2file(self):
		from mmgen.util2 import parse_bytespec
		for nbytes in ('1','1023','1K','1048575','1M','1048577','123M'):
			t = self.spawn(
				'mmgen-tool',
				['-d',self.tmpdir,'-r0','rand2file','rand2file.out',nbytes],
				extra_desc='({} byte{})'.format( nbytes, suf(parse_bytespec(nbytes)) )
			)
			t.expect('random data written to file')
			t.read()
			t.p.wait()
			t.ok()
		t.skip_ok = True
		return t

	def tool_encrypt(self):
		infile = joinpath(self.tmpdir,self.enc_infn)
		write_to_file(infile,getrand(1033),binary=True)
		t = self.spawn('mmgen-tool',['-d',self.tmpdir,self.usr_rand_arg,'encrypt',infile])
		t.usr_rand(self.usr_rand_chars)
		t.hash_preset('data','1')
		t.passphrase_new('data',tool_enc_passwd)
		t.written_to_file('Encrypted data')
		return t

	def tool_decrypt(self,f1):
		out_fn = 'tool_encrypt.out'
		t = self.spawn('mmgen-tool',['-d',self.tmpdir,'decrypt',f1,'outfile='+out_fn,'hash_preset=1'])
		t.passphrase('data',tool_enc_passwd)
		t.written_to_file('Decrypted data')
		d1 = self.read_from_tmpfile(self.enc_infn,binary=True)
		d2 = self.read_from_tmpfile(out_fn,binary=True)
		cmp_or_die(d1,d2)
		return t

	def tool_find_incog_data(self,f1,f2):
		i_id = read_from_file(f2).rstrip()
		vmsg(f'Incog ID: {cyan(i_id)}')
		t = self.spawn('mmgen-tool',['-d',self.tmpdir,'find_incog_data',f1,i_id])
		o = t.expect_getend(f'Incog data for ID {i_id} found at offset ')
		if not sys.platform == 'win32':
			os.unlink(f1) # causes problems with MSYS2
		cmp_or_die(hincog_offset,int(o))
		return t

	def tool_twview_bad_comment(self): # test correct operation of get_tw_label()
		t = self.spawn(
			'mmgen-tool',
			['twview'],
			env = { 'MMGEN_BOGUS_UNSPENT_DATA': joinpath(ref_dir,'bad-comment-unspent.json') })
		t.expect('cannot be converted to TwComment')
		t.req_exit_val = 2
		return t

	def tool_extract_key_from_geth_wallet(self):
		if cfg.no_altcoin:
			return 'skip'
		fn = 'test/ref/ethereum/geth-wallet.json'
		key = '9627ddb68354f5e0ff45fb2da49d7a20a013b7257a83ef4adbbbd87aeaccc75e'
		t = self.spawn('mmgen-tool',['-d',self.tmpdir,'extract_key_from_geth_wallet',fn])
		t.expect('Enter passphrase: ','\n')
		t.expect(key)
		return t

	def tool_api(self):
		t = self.spawn(
				'tool_api_test.py',
				(['no_altcoin'] if cfg.no_altcoin else []),
				cmd_dir = 'test/misc' )
		t.expect('legacy.*compressed.*segwit.*bech32',regex=True)
		return t

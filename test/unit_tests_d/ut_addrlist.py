#!/usr/bin/env python3

"""
test.unit_tests_d.ut_addrlist: address list unit tests for the MMGen suite
"""

from mmgen.common import *
from mmgen.seed import Seed
from mmgen.addr import MMGenAddrType
from mmgen.addrlist import AddrIdxList,AddrList,KeyList,KeyAddrList
from mmgen.passwdlist import PasswordList
from mmgen.protocol import init_proto

def do_test(list_type,chksum,idx_spec=None,pw_id_str=None,add_kwargs=None):
	qmsg(blue(f'Testing {list_type.__name__}'))
	proto = init_proto('btc')
	seed = Seed(seed_bin=bytes.fromhex('feedbead'*8))
	mmtype = MMGenAddrType(proto,'C')
	idxs = AddrIdxList(idx_spec or '1-3')

	if opt.verbose:
		debug_addrlist_save = g.debug_addrlist
		g.debug_addrlist = True

	kwargs = {
		'seed': seed,
		'pw_idxs': idxs,
		'pw_id_str': pw_id_str,
		'pw_fmt': 'b58',
	} if pw_id_str else {
		'seed': seed,
		'addr_idxs': idxs,
		'mmtype': mmtype,
	}

	if add_kwargs:
		kwargs.update(add_kwargs)

	al = list_type( proto, **kwargs )

	af = al.get_file()
	af.format()

	qmsg(f'Filename: {af.filename}\n')
#	af.write('-')
	vmsg(f'------------\n{af.fmt_data}\n------------')

	if chksum:
		assert al.chksum == chksum, f'{al.chksum} != {chksum}'

	if opt.verbose:
		g.debug_addrlist = debug_addrlist_save

	return True

class unit_tests:

	def addr(self,name,ut):
		return (
			do_test(AddrList,'BCE8 082C 0973 A525','1-3') and
			do_test(AddrList,'88FA B04B A380 C1CB','199999,99-101,77-78,7,3,2-9')
		)

	def key(self,name,ut):
		return do_test(KeyList,None)

	def keyaddr(self,name,ut):
		return do_test(KeyAddrList,'4A36 AA65 8C2B 7C35')

	def passwd(self,name,ut):
		return do_test(PasswordList,'FF4A B716 4513 8F8F',pw_id_str='foo')

	def passwd_bip39(self,name,ut):
		return do_test(PasswordList,'C3A8 B2B2 1AA1 FB40',pw_id_str='foo',add_kwargs={'pw_fmt':'bip39'})

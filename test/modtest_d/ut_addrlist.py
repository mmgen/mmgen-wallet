#!/usr/bin/env python3

"""
test.modtest_d.ut_addrlist: address list unit tests for the MMGen suite
"""

from mmgen.color import blue
from mmgen.util import msg

from mmgen.seed import Seed
from mmgen.addr import MMGenAddrType
from mmgen.addrlist import AddrIdxList, AddrList, KeyList, KeyAddrList, ViewKeyAddrList
from mmgen.passwdlist import PasswordList
from mmgen.protocol import init_proto
from ..include.common import cfg, qmsg, vmsg

def do_test(
		list_type,
		chksum,
		idx_spec   = None,
		pw_id_str  = None,
		add_kwargs = None,
		coin       = None,
		addrtype   = None):

	qmsg(blue(f'Testing {list_type.__name__}'))
	proto = init_proto(cfg, coin or 'btc')
	seed = Seed(cfg, seed_bin=bytes.fromhex('feedbead'*8))
	mmtype = MMGenAddrType(proto, addrtype or 'C')
	idxs = AddrIdxList(idx_spec or '1-3')

	if cfg.verbose:
		debug_addrlist_save = cfg.debug_addrlist
		cfg.debug_addrlist = True

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

	al = list_type(cfg, proto, **kwargs)

	al.file.format()

	qmsg(f'Filename: {al.file.filename}\n')

	vmsg(f'------------\n{al.file.fmt_data}\n------------')

	if chksum:
		assert al.chksum == chksum, f'{al.chksum} != {chksum}'

	if cfg.verbose:
		cfg.debug_addrlist = debug_addrlist_save

	return True

class unit_tests:

	altcoin_deps = ('keyaddr_xmr', 'viewkeyaddr')

	def idxlist(self, name, ut):
		for i, o in (
				('99,88-102,1-3,4,9,818,444-445,816',        '1-4,9,88-102,444-445,816,818'),
				('99,88-99,100,102,4-7,9,818,444-445,816,1', '1,4-7,9,88-100,102,444-445,816,818'),
				('8',             '8'),
				('2-4',           '2-4'),
				('1,2-4',         '1-4'),
				('2-4,1-9,9,1,8', '1-9'),
				('2-4,1',         '1-4'),
				('2-2',           '2'),
				('2,2',           '2'),
				('2-3',           '2-3'),
				('2,3',           '2-3'),
				('3,2',           '2-3'),
				('2,4',           '2,4'),
				('',              ''),
			):
			l = AddrIdxList(i)
			if cfg.verbose:
				msg(f'list: {list(l)}\nin:   {i}\nout:  {o}\n')
			assert l.id_str == o, f'{l.id_str} != {o}'

		return True

	def addr(self, name, ut):
		return (
			do_test(AddrList, 'BCE8 082C 0973 A525', '1-3') and
			do_test(AddrList, '88FA B04B A380 C1CB', '199999,99-101,77-78,7,3,2-9')
		)

	def key(self, name, ut):
		return do_test(KeyList, None)

	def keyaddr(self, name, ut):
		return do_test(KeyAddrList, '4A36 AA65 8C2B 7C35')

	def keyaddr_xmr(self, name, ut):
		return do_test(KeyAddrList, 'AAA2 BA69 17FC 9A88', coin='XMR', addrtype='M')

	def viewkeyaddr(self, name, ut):
		return do_test(ViewKeyAddrList, 'C122 2E58 DC28 D6AE', coin='XMR', addrtype='M')

	def passwd(self, name, ut):
		return do_test(PasswordList, 'FF4A B716 4513 8F8F', pw_id_str='foo')

	def passwd_bip39(self, name, ut):
		return do_test(PasswordList, 'C3A8 B2B2 1AA1 FB40', pw_id_str='foo', add_kwargs={'pw_fmt': 'bip39'})

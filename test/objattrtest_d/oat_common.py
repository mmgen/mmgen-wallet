#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>

"""
test.objattrtest_d.oat_common: shared data for MMGen data objects tests
"""

from decimal import Decimal
from collections import namedtuple

from mmgen.obj import TwComment, CoinTxID, HexStr
from mmgen.seed import Seed, SeedID
from mmgen.subseed import SubSeedIdx, SubSeedList
from mmgen.seedsplit import SeedShareList, SeedShareCount, SeedSplitIDString, SeedShareIdx, MasterShareIdx
from mmgen.addr import AddrIdx

from ..include.common import cfg, getrand

atd = namedtuple('attrtest_entry', ['attrs', 'args', 'kwargs'])

seed_bin = getrand(32)

# use the constructors here! otherwise reassignment test might fail when
# reassignment would otherwise succeed
sample_objs = {
	'int':       int(1),
	'Decimal':   Decimal('0.01'),
	'NoneType':  None,
	'bool':      bool(True),
	'str':       str('foo'),
	'dict':      dict({'a': 1}),
	'list':      list([1]),
	'tuple':     tuple((1, 2)),
	'bytes':     bytes(1),

	'HexStr':    HexStr('ff'),
	'AddrIdx':   AddrIdx(1),
	'TwComment': TwComment('αω'),
	'CoinTxID':  CoinTxID('aa'*32),

	'SeedID':    SeedID(sid='F00F00BB'),
	'Seed':      Seed(cfg, seed_bin=seed_bin),

	'SubSeedList': SubSeedList(Seed(cfg, seed_bin=seed_bin)),
	'SubSeedIdx':  SubSeedIdx('1S'),

	'SeedSplitIDString': SeedSplitIDString('alice'),
	'SeedShareList':     SeedShareList(Seed(cfg, seed_bin=seed_bin), SeedShareCount(2)),
	'SeedShareIdx':      SeedShareIdx(1),
	'SeedShareCount':    SeedShareCount(2),
	'MasterShareIdx':    MasterShareIdx(7),
}

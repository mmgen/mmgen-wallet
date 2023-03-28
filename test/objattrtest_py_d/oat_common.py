#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>

"""
test.objattrtest_py_d.oat_common: shared data for MMGen data objects tests
"""

import os
from decimal import Decimal

from mmgen.obj import *
from mmgen.seedsplit import *
from mmgen.protocol import *
from mmgen.addr import *
from mmgen.tx import *
from mmgen.tw.unspent import *
from mmgen.key import *
from ..include.common import cfg,getrand

from collections import namedtuple
atd = namedtuple('attrtest_entry',['attrs','args','kwargs'])

seed_bin = getrand(32)

# use the constructors here! otherwise reassignment test might fail when
# reassignment would otherwise succeed
sample_objs = {
	'int':       int(1),
	'Decimal':   Decimal('0.01'),
	'NoneType':  None,
	'bool':      bool(True),
	'str':       str('foo'),
	'dict':      dict({'a':1}),
	'list':      list([1]),
	'tuple':     tuple((1,2)),
	'bytes':     bytes(1),

	'HexStr':    HexStr('ff'),
	'AddrIdx':   AddrIdx(1),
	'TwComment': TwComment('αω'),
	'CoinTxID':  CoinTxID('aa'*32),

	'SeedID':    SeedID(sid='F00F00BB'),
	'Seed':      Seed(cfg,seed_bin=seed_bin),

	'SubSeedList': SubSeedList(Seed(cfg,seed_bin=seed_bin)),
	'SubSeedIdx':  SubSeedIdx('1S'),

	'SeedSplitIDString': SeedSplitIDString('alice'),
	'SeedShareList':     SeedShareList(Seed(cfg,seed_bin=seed_bin),SeedShareCount(2)),
	'SeedShareIdx':      SeedShareIdx(1),
	'SeedShareCount':    SeedShareCount(2),
	'MasterShareIdx':    MasterShareIdx(7),
}

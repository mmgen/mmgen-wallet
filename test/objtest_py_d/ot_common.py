#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>

"""
test.objtest_py_d.ot_common: shared data for MMGen data objects tests
"""

import os
from mmgen.globalvars import g
from ..common import *

r32,r24,r16,r17,r18 = os.urandom(32),os.urandom(24),os.urandom(16),os.urandom(17),os.urandom(18)
tw_pfx = g.proto.base_coin.lower()+':'

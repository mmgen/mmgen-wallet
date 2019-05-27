#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2019 The MMGen Project <mmgen@tuta.io>

"""
test.objtest_py_d.ot_common: shared data for MMGen data objects tests
"""

import os
from mmgen.globalvars import g

r32,r24,r16,r17,r18 = os.urandom(32),os.urandom(24),os.urandom(16),os.urandom(17),os.urandom(18)
tw_pfx = g.proto.base_coin.lower()+':'
utf8_text           = '[α-$ample UTF-8 text-ω]' * 10   # 230 chars, unicode types L,N,P,S,Z
utf8_text_combining = '[α-$ámple UTF-8 téxt-ω]' * 10   # L,N,P,S,Z,M
utf8_text_control   = '[α-$ample\nUTF-8\ntext-ω]' * 10 # L,N,P,S,Z,C

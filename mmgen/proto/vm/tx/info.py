#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.vm.tx.info: transaction info methods for VM chains
"""

from ....util import fmt
from ....addr import MMGenID

def mmid_disp(io, nonmm_str):
	return ' ' + (io.mmid.hl() if io.mmid else MMGenID.hlc(nonmm_str))

class VmTxInfo:

	txinfo_hdr_fs = '{hdr}\n  ID={i} ({a} {c}) Sig={s}\n'
	txinfo_hdr_fs_short = 'TX {i} ({a} {c}) Sig={s}\n'
	txinfo_ftr_fs = fmt("""
		Total in account:  {i} {d}
		Total to spend:    {o} {d}
		Remaining balance: {C} {d}
		TX fee:            {a} {c}{r}
	""")

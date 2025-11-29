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
xmrwallet.ops.restore: Monero wallet ops for the MMGen Suite
"""

from ...util import msg, gmsg, bmsg, ymsg, rmsg, die

from ..file.outputs import MoneroWalletDumpFile
from ..rpc import MoneroWalletRPC

from .create import OpCreate

class OpRestore(OpCreate):
	wallet_offline = True

	def check_uopts(self):
		if self.cfg.restore_height is not None:
			die(1, '--restore-height must be unset when running the ‘restore’ command')

	async def process_wallet(self, d, fn, last):

		def get_dump_data():

			def gen():
				for fn in [self.get_wallet_fn(d, watch_only=wo) for wo in (True, False)]:
					ret = fn.parent / (fn.name + '.dump')
					if ret.exists():
						yield ret

			match tuple(gen()):
				case [dump_fn, *rest]:
					if rest:
						ymsg(f'Warning: more than one dump file found for ‘{fn}’ - using the first!')
				case _:
					die(1, f'No suitable dump file found for ‘{fn}’')

			return MoneroWalletDumpFile.Completed(
				parent = self,
				fn     = dump_fn).data._asdict()['wallet_metadata']

		def restore_accounts():
			bmsg('  Restoring accounts:')
			for acct_idx, acct_data in enumerate(data[1:], 1):
				msg(fs.format(acct_idx, 0, acct_data['address']))
				self.c.call('create_account')

		def restore_subaddresses():
			bmsg('  Restoring subaddresses:')
			for acct_idx, acct_data in enumerate(data):
				for addr_idx, addr_data in enumerate(acct_data['addresses'][1:], 1):
					msg(fs.format(acct_idx, addr_idx, addr_data['address']))
					self.c.call('create_address', account_index=acct_idx)

		def restore_labels():
			bmsg('  Restoring labels:')
			for acct_idx, acct_data in enumerate(data):
				for addr_idx, addr_data in enumerate(acct_data['addresses']):
					addr_data['used'] = False # do this so that restored data matches
					msg(fs.format(acct_idx, addr_idx, addr_data['label']))
					self.c.call(
						'label_address',
						index = {'major': acct_idx, 'minor': addr_idx},
						label = addr_data['label'])

		def make_format_str():
			return '    acct {:O>%s}, addr {:O>%s} [{}]' % (
				len(str(len(data) - 1)),
				len(str(max(len(acct_data['addresses']) for acct_data in data) - 1)))

		def check_restored_data():
			restored_data = h.get_wallet_data(print=False).addrs_data
			if restored_data != data:
				rmsg('Restored data does not match original dump!  Dumping bad data.')
				MoneroWalletDumpFile.New(
					parent    = self,
					wallet_fn = fn,
					data      = {'wallet_metadata': restored_data}
				).write(add_suf='.bad')
				die(3, 'Fatal error')

		await super().process_wallet(d, fn, last)

		h = MoneroWalletRPC(self, d)
		h.open_wallet('newly created')

		msg('')
		data = get_dump_data()
		fs = make_format_str()

		gmsg('\nRestoring accounts, subaddresses and labels from dump file:\n')

		restore_accounts()
		restore_subaddresses()
		restore_labels()

		check_restored_data()

		return True

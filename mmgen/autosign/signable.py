#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
autosign.signable: Signable class for MMGen Wallet autosigning
"""

import sys

from ..util import msg, msg_r, gmsg, bmsg, die, suf, fmt_list
from ..color import yellow, red, orange

class Signable:

	class base:

		clean_all = False
		multiple_ok = True
		action_desc = 'signed'
		fail_msg = 'failed to sign'

		def __init__(self, parent):
			self.parent = parent
			self.cfg = parent.cfg
			self.dir = getattr(parent, self.dir_name)
			self.name = type(self).__name__

		@property
		def unsigned(self):
			return self._unprocessed('_unsigned', self.rawext, self.sigext)

		def _unprocessed(self, attrname, rawext, sigext):
			if not hasattr(self, attrname):
				dirlist = sorted(self.dir.iterdir())
				names = {f.name for f in dirlist}
				setattr(
					self,
					attrname,
					tuple(f for f in dirlist
						if f.name.endswith('.' + rawext)
							and f.name[:-len(rawext)] + sigext not in names))
			return getattr(self, attrname)

		def print_bad_list(self, bad_files):
			msg('\n{a}\n{b}'.format(
				a = red(f'Failed {self.desc}s:'),
				b = '  {}\n'.format('\n  '.join(
					self.gen_bad_list(sorted(bad_files, key=lambda f: f.name))))))

		def gen_bad_list(self, bad_files):
			for f in bad_files:
				yield red(f.name)

	class transaction(base):
		desc = 'non-automount transaction'
		dir_name = 'tx_dir'
		rawext = 'rawtx'
		sigext = 'sigtx'
		automount = False

		async def sign(self, f):
			from ..tx import UnsignedTX
			tx1 = UnsignedTX(
				cfg       = self.cfg,
				filename  = f,
				automount = self.automount)
			if tx1.proto.coin == 'XMR':
				ctx = Signable.xmr_compat_transaction(self.parent)
				for k in ('desc', 'print_summary', 'print_bad_list'):
					setattr(self, k, getattr(ctx, k))
				return await ctx.sign(f, compat_call=True)
			if tx1.proto.sign_mode == 'daemon':
				from ..rpc import rpc_init
				tx1.rpc = await rpc_init(self.cfg, tx1.proto, ignore_wallet=True)
			from ..tx.keys import TxKeys
			tx2 = await tx1.sign(
				TxKeys(
					self.cfg,
					tx1,
					seedfiles = self.parent.wallet_files[:],
					keylist = self.parent.keylist,
					passwdfile = str(self.parent.keyfile),
					autosign = True).keys)
			if tx2:
				tx2.file.write(ask_write=False, outdir=self.dir)
				return tx2
			else:
				return False

		def print_summary(self, signables):

			if self.cfg.full_summary:
				bmsg('\nAutosign summary:\n')
				msg_r('\n'.join(tx.info.format(terse=True) for tx in signables))
				return

			def gen():
				for tx in signables:
					non_mmgen = [o for o in tx.outputs if not o.mmid]
					if non_mmgen:
						yield (tx, non_mmgen)

			body = list(gen())

			if body:
				bmsg('\nAutosign summary:')
				fs = '{}  {} {}'
				t_wid, a_wid = 6, 44

				def gen():
					yield fs.format('TX ID ', 'Non-MMGen outputs'+' '*(a_wid-17), 'Amount')
					yield fs.format('-'*t_wid, '-'*a_wid, '-'*7)
					for tx, non_mmgen in body:
						for nm in non_mmgen:
							yield fs.format(
								tx.txid.fmt(t_wid, color=True) if nm is non_mmgen[0] else ' '*t_wid,
								nm.addr.fmt(nm.addr.view_pref, a_wid, color=True),
								nm.amt.hl() + ' ' + yellow(tx.coin))

				msg('\n' + '\n'.join(gen()))
			else:
				msg('\nNo non-MMGen outputs')

	class automount_transaction(transaction):
		desc = 'automount transaction'
		dir_name = 'txauto_dir'
		rawext = 'arawtx'
		sigext = 'asigtx'
		subext = 'asubtx'
		multiple_ok = False
		automount = True

		@property
		def unsubmitted(self):
			return self._unprocessed('_unsubmitted', self.sigext, self.subext)

		@property
		def unsubmitted_raw(self):
			return self._unprocessed('_unsubmitted_raw', self.rawext, self.subext)

		unsent = unsubmitted
		unsent_raw = unsubmitted_raw

		@property
		def submitted(self):
			return self._processed('_submitted', self.subext)

		def _processed(self, attrname, ext):
			if not hasattr(self, attrname):
				setattr(self, attrname, tuple(f for f in sorted(self.dir.iterdir())
					if f.name.endswith('.' + ext)))
			return getattr(self, attrname)

		def die_wrong_num_txs(self, tx_type, *, msg=None, desc=None, show_dir=False):
			match len(getattr(self, tx_type)): # num_txs
				case 0: subj, suf, pred = ('No', 's', 'present')
				case 1: subj, suf, pred = ('One', '', 'already present')
				case _: subj, suf, pred = ('More than one', '', 'already present')
			die('AutosignTXError', '{m}{a} {b} transaction{c} {d} {e}!'.format(
				m = msg + '\n' if msg else '',
				a = subj,
				b = desc or tx_type,
				c = suf,
				d = pred,
				e = f'in ‘{getattr(self.parent, self.dir_name)}’'
					if show_dir else 'on removable device'))

		def check_create_ok(self):
			if len(self.unsigned):
				self.die_wrong_num_txs('unsigned', msg='Cannot create transaction')
			if len(self.unsent):
				die('AutosignTXError', 'Cannot create transaction: you have an unsent transaction')

		def get_unsubmitted(self, tx_type='unsubmitted'):
			if len(self.unsubmitted) == 1:
				return self.unsubmitted[0]
			else:
				self.die_wrong_num_txs(tx_type)

		def get_unsent(self):
			return self.get_unsubmitted('unsent')

		def get_submitted(self):
			if len(self.submitted) == 0:
				self.die_wrong_num_txs('submitted')
			else:
				return self.submitted

		def get_abortable(self):
			if len(self.unsent_raw) != 1:
				self.die_wrong_num_txs('unsent_raw', desc='unsent')
			if len(self.unsent) > 1:
				self.die_wrong_num_txs('unsent')
			if self.unsent:
				if self.unsent[0].stem != self.unsent_raw[0].stem:
					die(1, f'{self.unsent[0]}, {self.unsent_raw[0]}: file mismatch')
			return self.unsent_raw + self.unsent

		def shred_abortable(self):
			from ..ui import keypress_confirm
			from ..fileutil import shred_file
			files = self.get_abortable() # raises AutosignTXError if no unsent TXs available
			keypress_confirm(
				self.cfg,
				'The following file{} will be securely deleted:\n{}\nOK?'.format(
					suf(files),
					fmt_list(map(str, files), fmt='col', indent='  ')),
					do_exit = True)
			for fn in files:
				msg(f'Shredding file ‘{fn}’')
				shred_file(self.cfg, fn, iterations=15)
			sys.exit(0)

		async def get_last_sent(self, *, tx_range):
			return await self.get_last_created(
				# compat fallback - ‘sent_timestamp’ attr is missing in some old TX files:
				sort_key = lambda x: x.sent_timestamp or x.timestamp,
				tx_range = tx_range)

		async def get_last_created(self, *, tx_range, sort_key=lambda x: x.timestamp):
			from ..tx import CompletedTX
			fns = [f for f in self.dir.iterdir() if f.name.endswith(self.subext)]
			files = sorted(
				[await CompletedTX(cfg=self.cfg, filename=str(txfile), quiet_open=True)
					for txfile in fns],
				key = sort_key)
			if files:
				return files[len(files) - 1 - tx_range.last:len(files) - tx_range.first]
			else:
				die(1, 'No sent automount transactions!')

	class xmr_signable: # mixin class
		automount = True
		summary_footer = ''

		def need_daemon_restart(self, m, new_idx):
			old_idx = self.parent.xmr_cur_wallet_idx
			self.parent.xmr_cur_wallet_idx = new_idx
			return old_idx != new_idx or m.wd.state != 'ready'

		def print_summary(self, signables):
			bmsg('\nAutosign summary:')
			msg('\n'.join(s.get_info(indent='  ') for s in signables) + self.summary_footer)

	class xmr_transaction(xmr_signable, automount_transaction):
		desc = 'Monero non-compat transaction'
		dir_name = 'xmr_tx_dir'
		rawext = 'rawtx'
		sigext = 'sigtx'
		subext = 'subtx'

		async def sign(self, f, compat_call=False):
			from .. import xmrwallet
			from ..xmrwallet.file.tx import MoneroMMGenTX
			tx1 = MoneroMMGenTX.Completed(self.parent.xmrwallet_cfg, f)
			m = xmrwallet.op(
				'sign',
				self.parent.xmrwallet_cfg,
				infile  = str(self.parent.wallet_files[0]), # MMGen wallet file
				wallets = str(tx1.src_wallet_idx),
				compat_call = compat_call)
			tx2 = await m.main(f, restart_daemon=self.need_daemon_restart(m, tx1.src_wallet_idx))
			tx2.write(ask_write=False)
			return tx2

	class xmr_compat_transaction(xmr_transaction):
		desc = 'Monero compat transaction'
		dir_name = 'txauto_dir'
		rawext = 'arawtx'
		sigext = 'asigtx'
		subext = 'asubtx'

	class xmr_wallet_outputs_file(xmr_signable, base):
		desc = 'Monero wallet outputs file'
		dir_name = 'xmr_outputs_dir'
		rawext = 'raw'
		sigext = 'sig'
		clean_all = True
		summary_footer = '\n'

		@property
		def unsigned(self):
			import json
			return tuple(
				f for f in super().unsigned
					if not json.loads(f.read_text())['MoneroMMGenWalletOutputsFile']['data']['imported'])

		async def sign(self, f):
			from .. import xmrwallet
			wallet_idx = xmrwallet.op_cls('wallet').get_idx_from_fn(f)
			m = xmrwallet.op(
				'import_outputs',
				self.parent.xmrwallet_cfg,
				infile  = str(self.parent.wallet_files[0]), # MMGen wallet file
				wallets = str(wallet_idx))
			obj = await m.main(f, wallet_idx, restart_daemon=self.need_daemon_restart(m, wallet_idx))
			obj.write(quiet=not obj.data.sign)
			self.action_desc = 'imported and signed' if obj.data.sign else 'imported'
			return obj

	class message(base):
		desc = 'message file'
		dir_name = 'msg_dir'
		rawext = 'rawmsg.json'
		sigext = 'sigmsg.json'
		fail_msg = 'failed to sign or signed incompletely'

		async def sign(self, f):
			from ..msg import UnsignedMsg, SignedMsg
			m = UnsignedMsg(self.cfg, infile=f)
			await m.sign(wallet_files=self.parent.wallet_files[:], passwd_file=str(self.parent.keyfile))
			m = SignedMsg(self.cfg, data=m.__dict__)
			m.write_to_file(
				outdir = self.dir.resolve(),
				ask_overwrite = False)
			if m.data.get('failed_sids'):
				die(
					'MsgFileFailedSID',
					f'Failed Seed IDs: {fmt_list(m.data["failed_sids"], fmt="bare")}')
			return m

		def print_summary(self, signables):
			gmsg('\nSigned message files:')
			for message in signables:
				gmsg('  ' + message.signed_filename)

		def gen_bad_list(self, bad_files):
			for f in bad_files:
				sigfile = f.parent / (f.name[:-len(self.rawext)] + self.sigext)
				yield orange(sigfile.name) if sigfile.exists() else red(f.name)

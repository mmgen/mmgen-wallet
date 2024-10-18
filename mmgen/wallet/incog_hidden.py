#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
wallet.incog_hidden: hidden incognito wallet class
"""

import sys, os

from ..seed import Seed
from ..util import msg, die, capfirst
from ..util2 import parse_bytespec
from .incog_base import wallet

class wallet(wallet):

	desc = 'hidden incognito data'
	file_mode = 'binary'
	no_tty = True

	_msg = {
		'choose_file_size': """
  You must choose a size for your new hidden incog data.  The minimum size
  is {} bytes, which puts the incog data right at the end of the file.
  Since you probably want to hide your data somewhere in the middle of the
  file where it's harder to find, you're advised to choose a much larger file
  size than this.
	""",
		'check_incog_id': """
  Check generated Incog ID above against your records.  If it doesn't match,
  then your incognito data is incorrect or corrupted, or you may have speci-
  fied an incorrect offset.
	""",
		'record_incog_id': """
  Make a record of the Incog ID but keep it secret.  You will used it to
  identify the incog wallet data in the future and to locate the offset
  where the data is hidden in the event you forget it.
	""",
		'decrypt_params': ', hash preset, offset {} seed length'
	}

	def _get_hincog_params(self, wtype):
		a = getattr(self.cfg, 'hidden_incog_'+ wtype +'_params').split(',')
		return ','.join(a[:-1]), int(a[-1]) # permit comma in filename

	def _check_valid_offset(self, fn, action):
		d = self.ssdata
		m = ('Input', 'Destination')[action=='write']
		if fn.size < d.hincog_offset + d.target_data_len:
			die(1, '{a} file {b!r} has length {c}, too short to {d} {e} bytes of data at offset {f}'.format(
				a = m,
				b = fn.name,
				c = fn.size,
				d = action,
				e = d.target_data_len,
				f = d.hincog_offset))

	def _get_data(self):
		d = self.ssdata
		d.hincog_offset = self._get_hincog_params('input')[1]

		self.cfg._util.qmsg(f'Getting hidden incog data from file {self.infile.name!r}')

		# Already sanity-checked:
		d.target_data_len = self._get_incog_data_len(self.cfg.seed_len or Seed.dfl_len)
		self._check_valid_offset(self.infile, 'read')

		flgs = os.O_RDONLY|os.O_BINARY if sys.platform == 'win32' else os.O_RDONLY
		fh = os.open(self.infile.name, flgs)
		os.lseek(fh, int(d.hincog_offset), os.SEEK_SET)
		self.fmt_data = os.read(fh, d.target_data_len)
		os.close(fh)
		self.cfg._util.qmsg(f'Data read from file {self.infile.name!r} at offset {d.hincog_offset}')

	# overrides method in Wallet
	def write_to_file(self, **kwargs):
		d = self.ssdata
		self._format()
		self.cfg._util.compare_or_die(
			val1  = d.target_data_len,
			desc1 = 'target data length',
			val2  = len(self.fmt_data),
			desc2 = 'length of formatted ' + self.desc)

		k = ('output', 'input')[self.op=='pwchg_new']
		fn, d.hincog_offset = self._get_hincog_params(k)

		if self.cfg.outdir and not os.path.dirname(fn):
			fn = os.path.join(self.cfg.outdir, fn)

		check_offset = True
		try:
			os.stat(fn)
		except:
			from ..ui import keypress_confirm, line_input
			if keypress_confirm(
					self.cfg,
					f'Requested file {fn!r} does not exist.  Create?',
					default_yes = True):
				min_fsize = d.target_data_len + d.hincog_offset
				msg('\n  ' + self.msg['choose_file_size'].strip().format(min_fsize)+'\n')
				while True:
					fsize = parse_bytespec(line_input(self.cfg, 'Enter file size: '))
					if fsize >= min_fsize:
						break
					msg(f'File size must be an integer no less than {min_fsize}')

				from ..tool.fileutil import tool_cmd
				tool_cmd(self.cfg).rand2file(fn, str(fsize))
				check_offset = False
			else:
				die(1, 'Exiting at user request')

		from ..filename import MMGenFile
		f = MMGenFile(fn, subclass=type(self), write=True)

		self.cfg._util.dmsg('{} data len {}, offset {}'.format(
			capfirst(self.desc),
			d.target_data_len,
			d.hincog_offset))

		if check_offset:
			self._check_valid_offset(f, 'write')
			if not self.cfg.quiet:
				from ..ui import confirm_or_raise
				confirm_or_raise(
					self.cfg,
					message = '',
					action  = f'alter file {f.name!r}')

		flgs = os.O_RDWR|os.O_BINARY if sys.platform == 'win32' else os.O_RDWR
		fh = os.open(f.name, flgs)
		os.lseek(fh, int(d.hincog_offset), os.SEEK_SET)
		os.write(fh, self.fmt_data)
		os.close(fh)
		msg('{} written to file {!r} at offset {}'.format(
			capfirst(self.desc),
			f.name,
			d.hincog_offset))

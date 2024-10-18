#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
tool.file: Address and transaction file routines for the 'mmgen-tool' utility
"""

from .common import tool_cmd_base, options_annot_str

class tool_cmd(tool_cmd_base):
	"utilities for viewing/checking MMGen address and transaction files"

	need_proto = True

	def __init__(self, cfg, cmdname=None, proto=None, mmtype=None):
		if cmdname == 'txview':
			self.need_amt = True
		super().__init__(cfg=cfg, cmdname=cmdname, proto=proto, mmtype=mmtype)

	def _file_chksum(self, mmgen_addrfile, obj):
		kwargs = {'skip_chksum_msg':True}
		if not obj.__name__ == 'PasswordList':
			kwargs.update({'key_address_validity_check':False})
		ret = obj(self.cfg, self.proto, mmgen_addrfile, **kwargs)
		if self.cfg.verbose:
			from ..util import msg, capfirst
			if ret.al_id.mmtype.name == 'password':
				msg('Passwd fmt:  {}\nPasswd len:  {}\nID string:   {}'.format(
					capfirst(ret.pw_info[ret.pw_fmt].desc),
					ret.pw_len,
					ret.pw_id_str))
			else:
				msg(f'Base coin:   {ret.base_coin} {capfirst(ret.network)}')
				msg(f'MMType:      {capfirst(ret.al_id.mmtype.name)}')
			msg(f'List length: {len(ret.data)}')
		return ret.chksum

	def addrfile_chksum(self, mmgen_addrfile: str):
		"compute checksum for MMGen address file"
		from ..addrlist import AddrList
		return self._file_chksum(mmgen_addrfile, AddrList)

	def keyaddrfile_chksum(self, mmgen_keyaddrfile: str):
		"compute checksum for MMGen key-address file"
		from ..addrlist import KeyAddrList
		return self._file_chksum(mmgen_keyaddrfile, KeyAddrList)

	def viewkeyaddrfile_chksum(self, mmgen_viewkeyaddrfile: str):
		"compute checksum for MMGen key-address file"
		from ..addrlist import ViewKeyAddrList
		return self._file_chksum(mmgen_viewkeyaddrfile, ViewKeyAddrList)

	def passwdfile_chksum(self, mmgen_passwdfile: str):
		"compute checksum for MMGen password file"
		from ..passwdlist import PasswordList
		return self._file_chksum(mmgen_passwdfile, PasswordList)

	async def txview(
			self,
			varargs_call_sig = { # hack to allow for multiple filenames - must be second argument!
				'args': (
					'mmgen_tx_file(s)',
					'pager',
					'terse',
					'sort',
					'filesort'),
				'dfls': (False, False, 'addr', 'mtime'),
				'annots': {
					'mmgen_tx_file(s)': str,
					'pager': 'send output to pager',
					'terse': 'produce compact tabular output',
					'sort':  'sort order for transaction inputs and outputs ' + options_annot_str(['addr', 'raw']),
					'filesort': 'file sort order ' + options_annot_str(['mtime', 'ctime', 'atime']),
				}
			},
			*infiles,
			**kwargs):
		"display specified raw or signed MMGen transaction files in human-readable form"

		terse = bool(kwargs.get('terse'))
		tx_sort = kwargs.get('sort') or 'addr'
		file_sort = kwargs.get('filesort') or 'mtime'

		from ..filename import MMGenFileList
		from ..tx import completed, CompletedTX
		flist = MMGenFileList(infiles, base_class=completed.Completed, proto=self.proto)
		flist.sort_by_age(key=file_sort) # in-place sort

		async def process_file(f):
			return (await CompletedTX(
				cfg        = self.cfg,
				filename   = f.name,
				quiet_open = True)).info.format(terse=terse, sort=tx_sort)

		return ('—'*77+'\n').join([await process_file(f) for f in flist]).rstrip()

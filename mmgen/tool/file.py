#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
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
tool/file.py: Address and transaction file routines for the 'mmgen-tool' utility
"""

from .common import tool_cmd_base,options_annot_str

class tool_cmd(tool_cmd_base):
	"utilities for viewing/checking MMGen address and transaction files"

	def __init__(self,proto=None,mmtype=None):
		if proto:
			self.proto = proto
		else:
			from ..protocol import init_proto_from_opts
			self.proto = init_proto_from_opts()

	def _file_chksum(self,mmgen_addrfile,objname):
		from ..opts import opt
		from ..addrlist import AddrList,KeyAddrList
		from ..passwdlist import PasswordList
		verbose,yes,quiet = [bool(i) for i in (opt.verbose,opt.yes,opt.quiet)]
		opt.verbose,opt.yes,opt.quiet = (False,True,True)
		ret = locals()[objname](self.proto,mmgen_addrfile)
		opt.verbose,opt.yes,opt.quiet = (verbose,yes,quiet)
		if verbose:
			from ..util import msg,capfirst
			if ret.al_id.mmtype.name == 'password':
				msg('Passwd fmt:  {}\nPasswd len:  {}\nID string:   {}'.format(
					capfirst(ret.pw_info[ret.pw_fmt].desc),
					ret.pw_len,
					ret.pw_id_str ))
			else:
				msg(f'Base coin:   {ret.base_coin} {capfirst(ret.network)}')
				msg(f'MMType:      {capfirst(ret.al_id.mmtype.name)}')
			msg(    f'List length: {len(ret.data)}')
		return ret.chksum

	def addrfile_chksum(self,mmgen_addrfile:str):
		"compute checksum for MMGen address file"
		return self._file_chksum(mmgen_addrfile,'AddrList')

	def keyaddrfile_chksum(self,mmgen_keyaddrfile:str):
		"compute checksum for MMGen key-address file"
		return self._file_chksum(mmgen_keyaddrfile,'KeyAddrList')

	def passwdfile_chksum(self,mmgen_passwdfile:str):
		"compute checksum for MMGen password file"
		return self._file_chksum(mmgen_passwdfile,'PasswordList')

	async def txview(
			varargs_call_sig = { # hack to allow for multiple filenames
				'args': (
					'mmgen_tx_file(s)',
					'pager',
					'terse',
					'sort',
					'filesort' ),
				'dfls': ( False, False, 'addr', 'mtime' ),
				'annots': {
					'mmgen_tx_file(s)': str,
					'sort': options_annot_str(['addr','raw']),
					'filesort': options_annot_str(['mtime','ctime','atime']),
				}
			},
			*infiles,
			**kwargs ):
		"show raw/signed MMGen transaction in human-readable form"

		terse = bool(kwargs.get('terse'))
		tx_sort = kwargs.get('sort') or 'addr'
		file_sort = kwargs.get('filesort') or 'mtime'

		from ..filename import MMGenFileList
		from ..tx import MMGenTX
		flist = MMGenFileList( infiles, ftype=MMGenTX )
		flist.sort_by_age( key=file_sort ) # in-place sort

		async def process_file(fn):
			if fn.endswith(MMGenTX.Signed.ext):
				tx = MMGenTX.Signed(
					filename   = fn,
					quiet_open = True,
					tw         = await MMGenTX.Signed.get_tracking_wallet(fn) )
			else:
				tx = MMGenTX.Unsigned(
					filename   = fn,
					quiet_open = True )
			return tx.format_view( terse=terse, sort=tx_sort )

		return ('—'*77+'\n').join([await process_file(fn) for fn in flist.names()]).rstrip()

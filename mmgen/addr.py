#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2015 Philemon <mmgen-py@yandex.com>
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
addr.py:  Address generation/display routines for the MMGen suite
"""

import sys
from hashlib import sha256, sha512
from hashlib import new as hashlib_new
from binascii import hexlify, unhexlify

from mmgen.bitcoin import numtowif
# from mmgen.util import msg,qmsg,qmsg_r,make_chksum_N,get_lines_from_file,get_data_from_file,get_extension
from mmgen.util import *
from mmgen.tx import *
from mmgen.obj import *
import mmgen.globalvars as g
import mmgen.opt as opt

pnm = g.proj_name

addrmsgs = {
	'addrfile_header': """
# {pnm} address file
#
# This file is editable.
# Everything following a hash symbol '#' is a comment and ignored by {pnm}.
# A text label of {n} characters or less may be added to the right of each
# address, and it will be appended to the bitcoind wallet label upon import.
# The label may contain any printable ASCII symbol.
""".strip().format(n=g.max_addr_label_len,pnm=pnm),
	'no_keyconv_msg': """
Executable '{kconv}' unavailable. Falling back on (slow) internal ECDSA library.
Please install '{kconv}' from the {vgen} package on your system for much
faster address generation.
""".format(kconv=g.keyconv_exec, vgen="vanitygen")
}

def test_for_keyconv(silent=False):

	from subprocess import check_output,STDOUT
	try:
		check_output([g.keyconv_exec, '-G'],stderr=STDOUT)
	except:
		if not silent: msg(addrmsgs['no_keyconv_msg'])
		return False

	return True


def generate_addrs(seed, addrnums, source="addrgen"):

	from util import make_chksum_8
	seed_id = make_chksum_8(seed) # Must do this before seed gets clobbered

	if 'a' in opt.gen_what:
		if opt.no_keyconv or test_for_keyconv() == False:
			msg("Using (slow) internal ECDSA library for address generation")
			from mmgen.bitcoin import privnum2addr
			keyconv = False
		else:
			from subprocess import check_output
			keyconv = "keyconv"

	addrnums = sorted(set(addrnums)) # don't trust the calling function
	t_addrs,num,pos,out = len(addrnums),0,0,[]

	w = {
		'ka': ('key/address pair','s'),
		'k':  ('key','s'),
		'a':  ('address','es')
	}[opt.gen_what]

	from mmgen.addr import AddrInfoEntry,AddrInfo

	while pos != t_addrs:
		seed = sha512(seed).digest()
		num += 1 # round

		if num != addrnums[pos]: continue

		pos += 1

		qmsg_r("\rGenerating %s #%s (%s of %s)" % (w[0],num,pos,t_addrs))

		e = AddrInfoEntry()
		e.idx = num

		# Secret key is double sha256 of seed hash round /num/
		sec = sha256(sha256(seed).digest()).hexdigest()
		wif = numtowif(int(sec,16))

		if 'a' in opt.gen_what:
			if keyconv:
				e.addr = check_output([keyconv, wif]).split()[1]
			else:
				e.addr = privnum2addr(int(sec,16))

		if 'k' in opt.gen_what: e.wif = wif
		if opt.b16: e.sec = sec

		out.append(e)

	m = w[0] if t_addrs == 1 else w[0]+w[1]
	qmsg("\r%s: %s %s generated%s" % (seed_id,t_addrs,m," "*15))
	a = AddrInfo(has_keys='k' in opt.gen_what, source=source)
	a.initialize(seed_id,out)
	return a

def _parse_addrfile_body(lines,has_keys=False,check=False):

	if has_keys and len(lines) % 2:
		return "Key-address file has odd number of lines"

	ret = []
	while lines:
		a = AddrInfoEntry()
		l = lines.pop(0)
		d = l.split(None,2)

		if not is_mmgen_idx(d[0]):
			return "'%s': invalid address num. in line: '%s'" % (d[0],l)
		if not is_btc_addr(d[1]):
			return "'%s': invalid Bitcoin address" % d[1]

		if len(d) == 3: check_addr_label(d[2])
		else:           d.append("")

		a.idx,a.addr,a.comment = int(d[0]),unicode(d[1]),unicode(d[2])

		if has_keys:
			l = lines.pop(0)
			d = l.split(None,2)

			if d[0] != "wif:":
				return "Invalid key line in file: '%s'" % l
			if not is_wif(d[1]):
				return "'%s': invalid Bitcoin key" % d[1]

			a.wif = unicode(d[1])

		ret.append(a)

	if has_keys and keypress_confirm("Check key-to-address validity?"):
		wif2addr_f = get_wif2addr_f()
		llen = len(ret)
		for n,e in enumerate(ret):
			msg_r("\rVerifying keys %s/%s" % (n+1,llen))
			if e.addr != wif2addr_f(e.wif):
				return "Key doesn't match address!\n  %s\n  %s" % (e.wif,e.addr)
		msg(" - done")

	return ret


def _parse_addrfile(fn,buf=[],has_keys=False,exit_on_error=True):

	if buf: lines = remove_comments(buf.split("\n"))
	else:   lines = get_lines_from_file(fn,"address data",trim_comments=True)

	try:
		sid,obrace = lines[0].split()
	except:
		errmsg = "Invalid first line: '%s'" % lines[0]
	else:
		cbrace = lines[-1]
		if obrace != '{':
			errmsg = "'%s': invalid first line" % lines[0]
		elif cbrace != '}':
			errmsg = "'%s': invalid last line" % cbrace
		elif not is_mmgen_seed_id(sid):
			errmsg = "'%s': invalid seed ID" % sid
		else:
			ret = _parse_addrfile_body(lines[1:-1],has_keys)
			if type(ret) == list: return sid,ret
			else: errmsg = ret

	if exit_on_error:
		msg(errmsg)
		sys.exit(3)
	else:
		return False


def _parse_keyaddr_file(infile):
	d = get_data_from_file(infile,"{pnm} key-address file data".format(pnm=pnm))
	enc_ext = get_extension(infile) == g.mmenc_ext
	if enc_ext or not is_utf8(d):
		m = "Decrypting" if enc_ext else "Attempting to decrypt"
		msg("%s key-address file %s" % (m,infile))
		from crypto import mmgen_decrypt_retry
		d = mmgen_decrypt_retry(d,"key-address file")
	return _parse_addrfile("",buf=d,has_keys=True,exit_on_error=False)


class AddrInfoList(MMGenObject):

	def __init__(self,addrinfo=None,bitcoind_connection=None):
		self.data = {}
		if bitcoind_connection:
			self.add_wallet_data(bitcoind_connection)

	def seed_ids(self):
		return self.data.keys()

	def addrinfo(self,sid):
		# TODO: Validate sid
		if sid in self.data:
			return self.data[sid]

	def add_wallet_data(self,c):
		vmsg_r("Getting account data from wallet...")
		data,accts,i = {},c.listaccounts(minconf=0,includeWatchonly=True),0
		for acct in accts:
			ma,comment = parse_mmgen_label(acct)
			if ma:
				i += 1
				addrlist = c.getaddressesbyaccount(acct)
				if len(addrlist) != 1:
					msg(wmsg['too_many_acct_addresses'] % acct)
					sys.exit(2)
				seed_id,idx = ma.split(":")
				if seed_id not in data:
					data[seed_id] = []
				a = AddrInfoEntry()
				a.idx,a.addr,a.comment = \
					int(idx),unicode(addrlist[0]),unicode(comment)
				data[seed_id].append(a)
		vmsg("{n} {pnm} addresses found, {m} accounts total".format(
				n=i,pnm=pnm,m=len(accts)))
		for sid in data:
			self.add(AddrInfo(sid=sid,adata=data[sid]))

	def add(self,addrinfo):
		if type(addrinfo) == AddrInfo:
			self.data[addrinfo.seed_id] = addrinfo
			return True
		else:
			msg("Error: object %s is not of type AddrInfo" % repr(addrinfo))
			sys.exit(1)

	def make_reverse_dict(self,btcaddrs):
		d = {}
		for k in self.data.keys():
			d.update(self.data[k].make_reverse_dict(btcaddrs))
		return d

class AddrInfoEntry(MMGenObject):

	def __init__(self): pass

class AddrInfo(MMGenObject):

	def __init__(self,addrfile="",has_keys=False,sid="",adata=[], source=""):
		self.has_keys = has_keys
		do_chksum = True
		if addrfile:
			f = _parse_keyaddr_file if has_keys else _parse_addrfile
			sid,adata = f(addrfile)
			self.source = "addrfile"
		elif sid and adata: # data from wallet
			self.source = "wallet"
		elif sid or adata:
			die(3,"Must specify address file, or seed_id + adata")
		else:
			self.source = source if source else "unknown"
			return

		self.initialize(sid,adata)

	def initialize(self,seed_id,addrdata):
		if seed_id in self.__dict__:
			msg("Seed ID already set for object %s" % self)
			return False
		self.seed_id = seed_id
		self.addrdata = addrdata
		self.num_addrs = len(addrdata)
		if self.source in ("wallet","txsign") or \
				(self.source == "addrgen" and opt.gen_what == "k"):
			self.checksum = None
			self.idxs_fmt = None
		else: # self.source in addrfile, addrgen
			self.make_addrdata_chksum()
			self.fmt_addr_idxs()
			w = "key-address" if self.has_keys else "address"
			qmsg("Checksum for %s data %s[%s]: %s" %
					(w,self.seed_id,self.idxs_fmt,self.checksum))
			if self.source == "addrgen":
				qmsg(
		"This checksum will be used to verify the address file in the future")
			elif self.source == "addrfile":
				qmsg("Check this value against your records")

	def idxs(self):
		return [e.idx for e in self.addrdata]

	def addrs(self):
		return ["%s:%s"%(self.seed_id,e.idx) for e in self.addrdata]

	def addrpairs(self):
		return [(e.idx,e.addr) for e in self.addrdata]

	def btcaddrs(self):
		return [e.addr for e in self.addrdata]

	def comments(self):
		return [e.comment for e in self.addrdata]

	def entry(self,idx):
		for e in self.addrdata:
			if idx == e.idx: return e

	def btcaddr(self,idx):
		for e in self.addrdata:
			if idx == e.idx: return e.addr

	def comment(self,idx):
		for e in self.addrdata:
			if idx == e.idx: return e.comment

	def set_comment(self,idx,comment):
		for e in self.addrdata:
			if idx == e.idx:
				if is_valid_tx_comment(comment):
					e.comment = comment
				else:
					sys.exit(2)

	def make_reverse_dict(self,btcaddrs):
		d,b = {},btcaddrs
		for e in self.addrdata:
			try:
				d[b[b.index(e.addr)]] = ("%s:%s"%(self.seed_id,e.idx),e.comment)
			except: pass
		return d


	def make_addrdata_chksum(self):
		nchars = 24
		lines=[" ".join([str(e.idx),e.addr]+([e.wif] if self.has_keys else []))
						for e in self.addrdata]
		self.checksum = make_chksum_N(" ".join(lines), nchars, sep=True)


	def fmt_data(self,enable_comments=False):

		# Check data integrity - either all or none must exist for each attr
		attrs  = ['addr','wif','sec']
		status = [0,0,0]
		for i in range(self.num_addrs):
			for j,attr in enumerate(attrs):
				try:
					getattr(self.addrdata[i],attr)
					status[j] += 1
				except: pass

		for i,s in enumerate(status):
			if s != 0 and s != self.num_addrs:
				msg("%s missing %s in addr data"% (self.num_addrs-s,attrs[i]))
				sys.exit(3)

		if status[0] == None and status[1] == None:
			msg("Addr data contains neither addresses nor keys")
			sys.exit(3)

		# Header
		out = []
		from mmgen.addr import addrmsgs
		out.append(addrmsgs['addrfile_header'] + "\n")
		w = "Key-address" if status[1] else "Address"
		out.append("# {} data checksum for {}[{}]: {}".format(
					w, self.seed_id, self.idxs_fmt, self.checksum))
		out.append("# Record this value to a secure location\n")
		out.append("%s {" % self.seed_id)

		# Body
		fs = "  {:<%s}  {:<34}{}" % len(str(self.addrdata[-1].idx))
		for e in self.addrdata:
			c = ""
			if enable_comments:
				try:    c = " "+e.comment
				except: pass
			if status[0]:  # First line with idx
				out.append(fs.format(e.idx, e.addr,c))
			else:
				out.append(fs.format(e.idx, "wif: "+e.wif,c))

			if status[1]:   # Subsequent lines
				if status[2]:
					out.append(fs.format("", "hex: "+e.sec,c))
				if status[0]:
					out.append(fs.format("", "wif: "+e.wif,c))

		out.append("}")

		return "\n".join([l.rstrip() for l in out])


	def fmt_addr_idxs(self):

		try: int(self.addrdata[0].idx)
		except:
			self.idxs_fmt = "(no idxs)"
			return

		addr_idxs = [e.idx for e in self.addrdata]
		prev = addr_idxs[0]
		ret = prev,

		for i in addr_idxs[1:]:
			if i == prev + 1:
				if i == addr_idxs[-1]: ret += "-", i
			else:
				if prev != ret[-1]: ret += "-", prev
				ret += ",", i
			prev = i

		self.idxs_fmt = "".join([str(i) for i in ret])

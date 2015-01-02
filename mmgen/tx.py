#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2014 Philemon <mmgen-py@yandex.com>
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
tx.py:  Bitcoin transaction routines
"""

import sys, os
from binascii import unhexlify
from decimal import Decimal

import mmgen.config as g
from mmgen.util import *
from mmgen.term import do_pager

def trim_exponent(n):
	'''Remove exponent and trailing zeros.
	'''
	d = Decimal(n)
	return d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize()

def is_btc_amt(amt):
	# amt must be a string!

	from decimal import Decimal
	try:
		ret = Decimal(amt)
	except:
		msg("%s: Invalid amount" % amt)
		return False

	if g.debug:
		print "Decimal(amt): %s\nAs tuple: %s" % (amt,repr(ret.as_tuple()))

	if ret.as_tuple()[-1] < -8:
		msg("%s: Too many decimal places in amount" % amt)
		return False

	if ret == 0:
		msg("Requested zero BTC amount")
		return False

	return trim_exponent(ret)

def normalize_btc_amt(amt):
	# amt must be a string!
	ret = is_btc_amt(amt)
	if ret: return ret
	else:   sys.exit(3)

def parse_mmgen_label(s,check_label_len=False):
	l = split2(s)
	if not is_mmgen_addr(l[0]): return "",s
	if check_label_len: check_addr_label(l[1])
	return tuple(l)

def is_mmgen_seed_id(s):
	import re
	return re.match(r"^[0123456789ABCDEF]{8}$",s) is not None

def is_mmgen_idx(s):
	import re
	m = g.mmgen_idx_max_digits
	return re.match(r"^[0123456789]{1,"+str(m)+r"}$",s) is not None

def is_mmgen_addr(s):
	seed_id,idx = split2(s,":")
	return is_mmgen_seed_id(seed_id) and is_mmgen_idx(idx)

def is_btc_addr(s):
	from mmgen.bitcoin import verify_addr
	return verify_addr(s)

def is_b58_str(s):
	from mmgen.bitcoin import b58a
	for ch in s:
		if ch not in b58a: return False
	return True

def is_btc_key(s):
	if s == "": return False
	compressed = not s[0] == '5'
	from mmgen.bitcoin import wiftohex
	return wiftohex(s,compressed) is not False

def wiftoaddr(s):
	if s == "": return False
	compressed = not s[0] == '5'
	from mmgen.bitcoin import wiftohex,privnum2addr
	hex_key = wiftohex(s,compressed)
	if not hex_key: return False
	return privnum2addr(int(hex_key,16),compressed)

def is_valid_tx_comment(s, verbose=True):
	if len(s) > g.max_tx_comment_len:
		if verbose: msg("Invalid transaction comment (longer than %s characters)" %
				g.max_tx_comment_len)
		return False
	try: s.decode("utf8")
	except:
		if verbose: msg("Invalid transaction comment (not UTF-8)")
		return False
	else: return True

def check_addr_label(label):

	if len(label) > g.max_addr_label_len:
		msg("'%s': overlong label (length must be <=%s)" %
				(label,g.max_addr_label_len))
		sys.exit(3)

	for ch in label:
		if ch not in g.addr_label_symbols:
			msg("""
"%s": illegal character in label "%s".
Only ASCII printable characters are permitted.
""".strip() % (ch,label))
			sys.exit(3)


def view_tx_data(c,inputs_data,tx_hex,b2m_map,comment,metadata,pager=False,pause=True):

	td = c.decoderawtransaction(tx_hex)

	out = "TRANSACTION DATA\n\n"
	out += "Header: [Tx ID: {}] [Amount: {} BTC] [Time: {}]\n\n".format(*metadata)
	if comment: out += "Comment: %s\n\n" % comment
	out += "Inputs:\n\n"

	total_in = 0
	for n,i in enumerate(td['vin']):
		for j in inputs_data:
			if j['txid'] == i['txid'] and j['vout'] == i['vout']:
				days = int(j['confirmations'] * g.mins_per_block / (60*24))
				total_in += j['amount']
				mmid,label,mmid_str = "","",""
				if 'account' in j:
					mmid,label = parse_mmgen_label(j['account'])
					if not mmid: mmid = "non-%s address" % g.proj_name
					mmid_str = " ({:>{l}})".format(mmid,l=34-len(j['address']))

				for d in (
	(n+1, "tx,vout:",       "%s,%s" % (i['txid'], i['vout'])),
	("",  "address:",       j['address'] + mmid_str),
	("",  "label:",         label),
	("",  "amount:",        "%s BTC" % trim_exponent(j['amount'])),
	("",  "confirmations:", "%s (around %s days)" % (j['confirmations'], days))
					):
					if d[2]: out += ("%3s %-8s %s\n" % d)
				out += "\n"

				break
	total_out = 0
	out += "Outputs:\n\n"
	for n,i in enumerate(td['vout']):
		addr = i['scriptPubKey']['addresses'][0]
		mmid,label = b2m_map[addr] if addr in b2m_map else ("","")
		if not mmid: mmid = "non-%s address" % g.proj_name
		mmid_str = " ({:>{l}})".format(mmid,l=34-len(j['address']))
		total_out += i['value']
		for d in (
				(n+1, "address:",  addr + mmid_str),
				("",  "label:",    label),
				("",  "amount:",   trim_exponent(i['value']))
			):
			if d[2]: out += ("%3s %-8s %s\n" % d)
		out += "\n"

	out += "Total input:  %s BTC\n" % trim_exponent(total_in)
	out += "Total output: %s BTC\n" % trim_exponent(total_out)
	out += "TX fee:       %s BTC\n" % trim_exponent(total_in-total_out)

	o = out.encode("utf8")
	if pager: do_pager(o)
	else:
		print "\n"+o
		if pause:
			get_char("Press any key to continue: ")
			msg("")


def parse_tx_file(tx_data,infile):

	err_str,err_fmt = "","Invalid %s in transaction file"

	if len(tx_data) == 5:
		metadata,tx_hex,inputs_data,outputs_data,comment = tx_data
	elif len(tx_data) == 4:
		metadata,tx_hex,inputs_data,outputs_data = tx_data
		comment = ""
	else:
		err_str = "number of lines"

	if not err_str:
		if len(metadata.split()) != 3:
			err_str = "metadata"
		else:
			try: unhexlify(tx_hex)
			except: err_str = "hex data"
			else:
				try: inputs_data = eval(inputs_data)
				except: err_str = "inputs data"
				else:
					try: outputs_data = eval(outputs_data)
					except: err_str = "mmgen-to-btc address map data"
					else:
						if comment:
							from mmgen.bitcoin import b58decode
							comment = b58decode(comment)
							if comment == False:
								err_str = "encoded comment (not base58)"
							else:
								if is_valid_tx_comment(comment,True):
									comment = comment.decode("utf8")
								else:
									err_str = "comment"

	if err_str:
		msg(err_fmt % err_str)
		sys.exit(2)
	else:
		return metadata.split(),tx_hex,inputs_data,outputs_data,comment


def get_wif2addr_f():
	if g.no_keyconv: return wiftoaddr
	from mmgen.addr import test_for_keyconv
	return wiftoaddr_keyconv if test_for_keyconv() else wiftoaddr


def make_addr_data_chksum(adata,keys=False):
	nchars = 24
	return make_chksum_N(" ".join([" ".join(
					[str(n),d[0],d[2]] if keys else [str(n),d[0]]
				) for n,d in adata]), nchars, sep=True)


def get_addr_data_hash(e,keys=False):
	def s_addrdata(a): return int(a[0])
	adata = [(k,e[k]) for k in e.keys()]
	return make_addr_data_chksum(sorted(adata,key=s_addrdata),keys)


def _parse_addrfile_body(lines,keys=False,check=False):

	def parse_addr_lines(lines):
		ret = []
		for l in lines:
			d = l.split(None,2)

			if not is_mmgen_idx(d[0]):
				msg("'%s': invalid address num. in line: '%s'" % (d[0],l))
				sys.exit(3)

			if not is_btc_addr(d[1]):
				msg("'%s': invalid Bitcoin address" % d[1])
				sys.exit(3)

			if len(d) == 3:
				comment = d[2]
				check_addr_label(comment)
			else:
				comment = ""

			ret.append([d[0],d[1],comment])

		return ret

	def parse_key_lines(lines):
		ret = []
		for l in lines:
			d = l.split(None,2)

			if d[0] != "wif:":
				msg("Invalid key line in file: '%s'" % l)
				sys.exit(3)

			if not is_btc_key(d[1]):
				msg("'%s': invalid Bitcoin key" % d[1])
				sys.exit(3)

			ret.append(d[1])

		return ret

	z = len(lines) / 2
	if keys:
        # returns list of lists
		adata = parse_addr_lines([lines[i*2] for i in range(z)])
        # returns list of strings
		kdata = parse_key_lines([lines[i*2+1] for i in range(z)])
		if len(adata) != len(kdata):
			msg("Odd number of lines in key file")
			sys.exit(2)
		if check or keypress_confirm("Check key-to-address validity?"):
			wif2addr_f = get_wif2addr_f()
			for i in range(z):
				msg_r("\rVerifying keys %s/%s" % (i+1,z))
				if adata[i][1] != wif2addr_f(kdata[i]):
					msg("Key doesn't match address!\n  %s\n  %s" %
							kdata[i],adata[i][1])
					sys.exit(2)
			msg(" - done")
		return [adata[i] + [kdata[i]] for i in range(z)]
	else:
		return parse_addr_lines(lines)


def parse_addrfile(f,addr_data,keys=False,return_chk_and_sid=False):
	return parse_addrfile_lines(
				get_lines_from_file(f,"address data",trim_comments=True),
					addr_data,keys,return_chk_and_sid=return_chk_and_sid)

def parse_addrfile_lines(lines,addr_data,keys=False,exit_on_error=True,return_chk_and_sid=False):

	try:
		seed_id,obrace = lines[0].split()
	except:
		errmsg = "Invalid first line: '%s'" % lines[0]
	else:
		cbrace = lines[-1]
		if obrace != '{':
			errmsg = "'%s': invalid first line" % lines[0]
		elif cbrace != '}':
			errmsg = "'%s': invalid last line" % cbrace
		elif not is_mmgen_seed_id(seed_id):
			errmsg = "'%s': invalid Seed ID" % seed_id
		else:
			ldata = _parse_addrfile_body(lines[1:-1],keys)
			if seed_id not in addr_data: addr_data[seed_id] = {}
			for l in ldata:
				addr_data[seed_id][l[0]] = l[1:]
			chk = get_addr_data_hash(addr_data[seed_id],keys)
			if return_chk_and_sid: return chk,seed_id
			from mmgen.addr import fmt_addr_idxs
			fl = fmt_addr_idxs([int(i) for i in addr_data[seed_id].keys()])
			w = "key" if keys else "addr"
			qmsg_r("Computed checksum for "+w+" data ",w.capitalize()+" checksum ")
			msg("{}[{}]: {}".format(seed_id,fl,chk))
			qmsg("Check this value against your records")
			return True

	if exit_on_error:
		msg(errmsg)
		sys.exit(3)
	else:
		return False


def parse_keyaddr_file(infile,addr_data):
	d = get_data_from_file(infile,"%s key-address file data" % g.proj_name)
	enc_ext = get_extension(infile) == g.mmenc_ext
	if enc_ext or not is_utf8(d):
		m = "Decrypting" if enc_ext else "Attempting to decrypt"
		msg("%s key-address file %s" % (m,infile))
		from crypto import mmgen_decrypt_retry
		d = mmgen_decrypt_retry(d,"key-address file")
	parse_addrfile_lines(remove_comments(d.split("\n")),addr_data,True,False)


def get_tx_comment_from_file(infile):
	s = get_data_from_file(infile,"transaction comment")
	if is_valid_tx_comment(s, verbose=True):
		return s.decode("utf8").strip()
	else:
		sys.exit(2)

def get_tx_comment_from_user(comment=""):
	try:
		while True:
			s = my_raw_input("Comment: ",insert_txt=comment.encode("utf8"))
			if s == "": return False
			if is_valid_tx_comment(s, verbose=True):
				return s.decode("utf8")
	except KeyboardInterrupt:
		msg("User interrupt")
		return False

def make_tx_data(metadata_fmt, tx_hex, inputs_data, b2m_map, comment):
	from mmgen.bitcoin import b58encode
	s = (b58encode(comment.encode("utf8")),) if comment else ()
	lines = (metadata_fmt, tx_hex, repr(inputs_data), repr(b2m_map)) + s
	return "\n".join(lines)+"\n"

def mmaddr2btcaddr_addrdata(mmaddr,addr_data,source=""):
	seed_id,idx = mmaddr.split(":")
	if seed_id in addr_data:
		if idx in addr_data[seed_id]:
			vmsg("%s -> %s%s" % (mmaddr,addr_data[seed_id][idx][0],
				" (from "+source+")" if source else ""))
			return addr_data[seed_id][idx]

	return "",""

def get_bitcoind_cfg_options(cfg_keys):

	if "HOME" in os.environ:       # Linux
		homedir,datadir = os.environ["HOME"],".bitcoin"
	elif "HOMEPATH" in os.environ: # Windows:
		homedir,data_dir = os.environ["HOMEPATH"],r"Application Data\Bitcoin"
	else:
		msg("Neither $HOME nor %HOMEPATH% are set")
		msg("Don't know where to look for 'bitcoin.conf'")
		sys.exit(3)

	cfg_file = os.path.join(homedir, datadir, "bitcoin.conf")

	cfg = dict([(k,v) for k,v in [split2(line.translate(None,"\t "),"=")
			for line in get_lines_from_file(cfg_file)] if k in cfg_keys])

	for k in set(cfg_keys) - set(cfg.keys()):
		msg("Configuration option '%s' must be set in %s" % (k,cfg_file))
		sys.exit(2)

	return cfg

def connect_to_bitcoind():

	host,port,user,passwd = "localhost",8332,"rpcuser","rpcpassword"
	cfg = get_bitcoind_cfg_options((user,passwd))

	import mmgen.rpc.connection
	f = mmgen.rpc.connection.BitcoinConnection

	try:
		c = f(cfg[user],cfg[passwd],host,port)
	except:
		msg("Unable to establish RPC connection with bitcoind")
		sys.exit(2)

	return c


def wiftoaddr_keyconv(wif):
	if wif[0] == '5':
		from subprocess import check_output
		return check_output(["keyconv", wif]).split()[1]
	else:
		return wiftoaddr(wif)

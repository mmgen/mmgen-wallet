#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C) 2013 by philemon <mmgen-py@yandex.com>
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

from binascii import unhexlify
from mmgen.utils import *
import sys, os
from decimal import Decimal
from mmgen.config import *

txmsg = {
'not_enough_btc': "Not enough BTC in the inputs for this transaction (%s BTC)",
'throwaway_change': """
ERROR: This transaction produces change (%s BTC); however, no change
address was specified.  Total inputs - transaction fee = %s BTC.
To create a valid transaction with no change address, send this sum to the
specified recipient address.
""".strip(),
'mixed_inputs': """
NOTE: This transaction uses a mixture of both mmgen and non-mmgen inputs,
which makes the signing process more complicated.  When signing the
transaction, keys for the non-mmgen inputs must be supplied in a separate
file using the '-k' option of mmgen-txsign.

Alternatively, you may import the mmgen keys into the wallet.dat of your
offline bitcoind, first generating the required keys with mmgen-keygen and
then running mmgen-txsign with the '-f' option to force the use of
wallet.dat as the key source.

Selected mmgen inputs: %s"""
}


def connect_to_bitcoind(http_timeout=30):

	host,port,user,passwd = "localhost",8332,"rpcuser","rpcpassword"
	cfg = get_cfg_options((user,passwd))

	import mmgen.rpc.connection
	f = mmgen.rpc.connection.BitcoinConnection

	try:
		c = f(cfg[user],cfg[passwd],host,port,http_timeout=http_timeout)
	except:
		msg("Unable to establish RPC connection with bitcoind")
		sys.exit(2)

	return c


def trim_exponent(d):
	'''Remove exponent and trailing zeros.
	'''
	return d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize()


def	check_address(rcpt_address):
	from mmgen.bitcoin import verify_addr
	if not verify_addr(rcpt_address):
		sys.exit(3)


def check_btc_amt(send_amt):

	from decimal import Decimal
	try:
		retval = Decimal(send_amt)
	except:
		msg("%s: Invalid amount" % send_amt)
		sys.exit(3)

	if retval.as_tuple()[-1] < -8:
		msg("%s: Too many decimal places in amount" % send_amt)
		sys.exit(3)

	return trim_exponent(retval)


def get_cfg_options(cfg_keys):

	cfg_file = "%s/%s" % (os.environ["HOME"], ".bitcoin/bitcoin.conf")
	try:
		f = open(cfg_file)
	except:
		msg("Unable to open file '%s' for reading" % cfg_file)
		sys.exit(2)

	cfg = {}

	for line in f.readlines():
		s = line.translate(None,"\n\t ").split("=")
		for k in cfg_keys:
			if s[0] == k: cfg[k] = s[1]

	f.close()

	for k in cfg_keys:
		if not k in cfg:
			msg("Configuration option '%s' must be set in %s" % (k,cfg_file))
			sys.exit(2)

	return cfg


def print_tx_to_file(tx,sel_unspent,send_amt,opts):
	sig_data = [{"txid":i.txid,"vout":i.vout,"scriptPubKey":i.scriptPubKey}
					for i in sel_unspent]
	tx_id = make_chksum_6(unhexlify(tx)).upper()
	outfile = "tx_%s[%s].raw" % (tx_id,send_amt)
	if 'outdir' in opts:
		outfile = "%s/%s" % (opts['outdir'], outfile)
	metadata = "%s %s %s" % (tx_id, send_amt, make_timestamp())
	data = "%s\n%s\n%s\n%s\n" % (
			metadata, tx, repr(sig_data),
			repr([i.__dict__ for i in sel_unspent])
		)
	write_to_file(outfile,data,confirm=False)
	msg("Transaction data saved to file '%s'" % outfile)


def print_signed_tx_to_file(tx,sig_tx,metadata,opts):
	tx_id = make_chksum_6(unhexlify(tx)).upper()
	outfile = "tx_{}[{}].sig".format(*metadata[:2])
	if 'outdir' in opts:
		outfile = "%s/%s" % (opts['outdir'], outfile)
	data = "%s\n%s\n" % (" ".join(metadata),sig_tx)
	write_to_file(outfile,data,confirm=False)
	msg("Signed transaction saved to file '%s'" % outfile)


def print_sent_tx_to_file(tx,metadata,opts):
	outfile = "tx_{}[{}].out".format(*metadata[:2])
	if 'outdir' in opts:
		outfile = "%s/%s" % (opts['outdir'], outfile)
	write_to_file(outfile,tx+"\n",confirm=False)
	msg("Transaction ID saved to file '%s'" % outfile)


def sort_and_view(unspent):

	def s_amt(a,b):  return cmp(a.amount,b.amount)
	def s_txid(a,b):
		return cmp("%s %03s" % (a.txid,a.vout), "%s %03s" % (b.txid,b.vout))
	def s_addr(a,b): return cmp(a.address,b.address)
	def s_age(a,b):  return cmp(b.confirmations,a.confirmations)
	def s_mmgen(a,b): return cmp(a.account,b.account)

	fs =     " %-4s %-11s %-2s %-34s %13s %-s"
	fs_hdr = " %-4s %-11s %-4s %-35s %-9s %-s"
	sort,group,mmaddr,reverse = "",False,False,False

	from copy import deepcopy
	msg("")
	while True:
		out = deepcopy(unspent)
		for i in out: i.skip = ""
		for n in range(len(out)):
			if group and n < len(out)-1:
				a,b = out[n],out[n+1]
				if sort == "address" and a.address == b.address:
					out[n+1].skip = "d"
				elif sort == "txid" and a.txid == b.txid:
					out[n+1].skip = "t"

		output = []
		output.append("UNSPENT OUTPUTS (sort order: %s%s%s)" % (
				"reverse " if reverse else "",
				sort if sort else "None",
	" (grouped)" if group and (sort == "address" or sort == "txid") else ""
			))
		output.append(fs_hdr % ("Num","TX id","Vout","Address","Amount",
					"Age (days)"))

		for n,i in enumerate(out):
			amt = str(trim_exponent(i.amount))
			fill = 8 - len(amt.split(".")[-1]) if "." in amt else 9
			if i.skip == "d":
				addr = " |" + "-"*32
			else:
				if mmaddr:
					if i.account and verify_mmgen_label(i.account):
						addr = "%s.. %s" % (i.address[:4],i.account)
					else:
						addr = i.address
				else:
					addr = i.address
			txid = "       |---" if i.skip == "t" else i.txid[:8]+"..."
			days = int(i.confirmations * mins_per_block / (60*24))

			output.append(fs % (str(n+1)+")", txid,i.vout,addr,amt+(" "*fill),days))

		while True:
			reply = get_char("\n".join(output) +
"""\n
Sort options: [t]xid, [a]mount, a[d]dress, [A]ge, [r]everse, [M]mgen addr
View options: [g]roup, show [m]mgen addr
(Type 'q' to quit sorting): """).strip()
			if   reply == 'a': unspent.sort(s_amt);  sort = "amount"; break
			elif reply == 't': unspent.sort(s_txid); sort = "txid"; break
			elif reply == 'd': unspent.sort(s_addr); sort = "address"; break
			elif reply == 'A': unspent.sort(s_age);  sort = "age"; break
			elif reply == 'M': unspent.sort(s_mmgen); mmaddr,sort=True,"mmgen"; break
			elif reply == 'r':
				reverse = False if reverse else True
				unspent.reverse()
				break
			elif reply == 'g': group = False if group else True; break
			elif reply == 'm': mmaddr = False if mmaddr else True; break
			elif reply == 'q': break
			else: msg("Invalid input")

		msg("\n")
		if reply == 'q': break

	return tuple(unspent)


def verify_mmgen_label(s,return_str=False,check_label_len=False):

	fail    = "" if return_str else False
	success = s  if return_str else True

	if not s: return fail

	mminfo,comment = s.split(None,1)
	if mminfo[8] != ':': return fail
	for i in mminfo[:8]:
		if not i in "01234567890ABCDEF": return fail
	for i in mminfo[9:]:
		if not i in "0123456789": return fail

	if check_label_len:
		check_wallet_addr_comment(comment)

	return success


def view_tx_data(c,inputs_data,tx_hex,metadata=[]):

	td = c.decoderawtransaction(tx_hex)

	msg("TRANSACTION DATA:\n")

	if metadata: msg(
		"Header: [ID: {}] [Amount: {} BTC] [Time: {}]\n".format(*metadata))

	msg("Inputs:")
	total_in = 0
	for n,i in enumerate(td['vin']):
		for j in inputs_data:
			if j['txid'] == i['txid'] and j['vout'] == i['vout']:
				days = int(j['confirmations'] * mins_per_block / (60*24))
				total_in += j['amount']
				msg(" " + """
%-2s tx,vout: %s,%s
    address:        %s
    label:          %s
    amount:         %s BTC
    confirmations:  %s (around %s days)
""".strip() %
	(n+1,i['txid'],i['vout'],j['address'],verify_mmgen_label(j['account'],True),
		trim_exponent(j['amount']),j['confirmations'],days)+"\n")
				break

	msg("Total input: %s BTC\n" % trim_exponent(total_in))

	total_out = 0
	msg("Outputs:")
	for n,i in enumerate(td['vout']):
		total_out += i['value']
		msg(" " + """
%-2s address: %s
    amount:  %s BTC
""".strip() % (
		n,
		i['scriptPubKey']['addresses'][0],
		trim_exponent(i['value']))
	+ "\n")
	msg("Total output: %s BTC" % trim_exponent(total_out))
	msg("TX fee:       %s BTC\n" % trim_exponent(total_in-total_out))


def parse_tx_data(tx_data,infile):

	if len(tx_data) != 4:
		msg("'%s': not a transaction file" % infile)
		sys.exit(2)

	err_fmt = "Transaction %s is invalid"

	if len(tx_data[0].split()) != 3:
		msg(err_fmt % "metadata")
		sys.exit(2)

	try: unhexlify(tx_data[1])
	except:
		msg(err_fmt % "hex data")
		sys.exit(2)

	try:
		sig_data = eval(tx_data[2])
	except:
		msg(err_fmt % "signature data")
		sys.exit(2)

	try:
		inputs_data = eval(tx_data[3])
	except:
		msg(err_fmt % "inputs data")
		sys.exit(2)

	return tx_data[0].split(),tx_data[1],sig_data,inputs_data


def select_outputs(unspent,prompt):

	while True:
		reply = my_raw_input(prompt).strip()

		if not reply: continue

		from mmgen.utils import parse_address_list
		selected = parse_address_list(reply,sep=None)

		if not selected: continue

		if selected[-1] > len(unspent):
			msg("Inputs must be less than %s" % len(unspent))
			continue

		return selected



def make_tx_out(rcpt_arg):

	import decimal
	try:
		tx_out = dict([(i.split(":")[0],i.split(":")[1])
							for i in rcpt_arg.split(",")])
	except:
		msg("Invalid format: %s" % rcpt_arg)
		sys.exit(3)

	try:
		for i in tx_out.keys():
			tx_out[i] = trim_exponent(Decimal(tx_out[i]))
	except decimal.InvalidOperation:
		msg("Decimal conversion error in suboption '%s:%s'" % (i,tx_out[i]))
		sys.exit(3)

	return tx_out

def check_wallet_addr_comment(label):

	if len(label) > max_wallet_addr_label_len:
		msg("'%s': overlong label (length must be <=%s)" %
				(label,max_wallet_addr_label_len))
		sys.exit(3)

	from string import ascii_letters, digits
	chrs = tuple(ascii_letters + digits) + wallet_addr_label_symbols
	for ch in list(label):
		if ch not in chrs:
			msg("'%s': illegal character in label '%s'" % (ch,label))
			msg("Permitted characters: A-Za-z0-9, plus '%s'" %
					"', '".join(wallet_addr_label_symbols))
			sys.exit(3)


def parse_addrs_file(f):
	lines = get_lines_from_file(f,"address data")
	lines = remove_blanks_comments(lines)

	seed_id,obrace = lines[0].split()
	cbrace = lines[-1]

	if   obrace != '{':
		msg("'%s': invalid first line" % lines[0])
	elif cbrace != '}':
		msg("'%s': invalid last line" % cbrace)
	elif len(seed_id) != 8:
		msg("'%s': invalid Seed ID" % seed_id)
	else:
		try:
			unhexlify(seed_id)
		except:
			msg("'%s': invalid Seed ID" % seed_id)
			sys.exit(3)

		ret = []
		for i in lines[1:-1]:
			d = i.split(None,2)

			try: d[0] = int(d[0])
			except:
				msg("'%s': invalid address num. in line: %s" % (d[0],d))
				sys.exit(3)

			from mmgen.bitcoin import verify_addr
			if not verify_addr(d[1]):
				msg("'%s': invalid address" % d[1])
				sys.exit(3)

			if len(d) == 3: check_wallet_addr_comment(d[2])

			ret.append(d)

		return seed_id,ret

	sys.exit(3)

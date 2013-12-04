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
from mmgen.utils import msg,msg_r,write_to_file,my_raw_input,get_char,make_chksum_8,make_timestamp
import sys, os
from bitcoinrpc.connection import *
from decimal import Decimal
from mmgen.config import *

txmsg = {
'not_enough_btc': "Not enough BTC in the inputs for this transaction (%s BTC)",
'throwaway_change': """
ERROR: This transaction produces change (%s BTC); however, no change
address was specified.  Total inputs - transaction fee = %s BTC.
To create a valid transaction with no change address, send this sum to the
specified recipient address.
""".strip()
}

def connect_to_bitcoind():

	host,port,user,passwd = "localhost",8332,"rpcuser","rpcpassword"
	cfg = get_cfg_options((user,passwd))

	try:
		c = BitcoinConnection(cfg[user],cfg[passwd],host,port)
	except:
		msg("Unable to establish RPC connection with bitcoind")
		sys.exit(2)

	return c


def remove_exponent(d):
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
	
	return remove_exponent(retval)


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
	tx_id = make_chksum_8(unhexlify(tx))
	outfile = "%s[%s].tx" % (tx_id,send_amt)
	if 'outdir' in opts:
		outfile = "%s/%s" % (opts['outdir'], outfile)
	input_data = sel_unspent
	data = "%s\n%s\n%s\n%s\n" % (
			make_timestamp(), tx, repr(sig_data),
			repr([i.__dict__ for i in sel_unspent])
		)
	write_to_file(outfile,data,confirm=False)
	msg("Transaction data saved to file '%s'" % outfile)


def print_signed_tx_to_file(tx,sig_tx,opts):
	tx_id = make_chksum_8(unhexlify(tx))
	outfile = "%s.txsig" % tx_id
	if 'outdir' in opts:
		outfile = "%s/%s" % (opts['outdir'], outfile)
	write_to_file(outfile,sig_tx+"\n",confirm=False)
	msg("Signed transaction saved to file '%s'" % outfile)


def print_sent_tx_to_file(tx):
	outfile = "tx.out"
	write_to_file(outfile,tx+"\n",confirm=False)
	msg("Transaction ID saved to file '%s'" % outfile)

def sort_and_view(unspent):

	def s_amt(a,b):  return cmp(a.amount,b.amount)
	def s_txid(a,b):
		return cmp("%s %03s" % (a.txid,a.vout), "%s %03s" % (b.txid,b.vout))
	def s_addr(a,b): return cmp(a.address,b.address)
	def s_age(a,b):  return cmp(b.confirmations,a.confirmations)

	fs = "%-4s %-11s %-2s %-34s %13s"
	sort,group,reverse = "",False,False

	from copy import deepcopy
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
		output.append("Sort order: %s%s%s" % (
				"reverse " if reverse else "",
				sort if sort else "None",
	" (grouped)" if group and (sort == "address" or sort == "txid") else ""
			))
		output.append(fs % ("Num","TX id","Vout","Address","Amount       "))

		for n,i in enumerate(out):
			amt = str(remove_exponent(i.amount))
			fill = 8 - len(amt.split(".")[-1]) if "." in amt else 9
			addr = " |" + "-"*32 if i.skip == "d" else i.address
			txid = "       |---" if i.skip == "t" else i.txid[:8]+"..."

			output.append(fs % (str(n+1)+")", txid,i.vout,addr,amt+(" "*fill)))

		while True:
			reply = get_char("\n".join(output) +
"""\n
Sort options: [t]xid, [a]mount, a[d]dress, [A]ge, [r]everse, [g]roup
(Type 'q' to quit sorting): """).strip()
			if   reply == 'a': unspent.sort(s_amt);  sort = "amount"; break
			elif reply == 't': unspent.sort(s_txid); sort = "txid"; break
			elif reply == 'd': unspent.sort(s_addr); sort = "address"; break
			elif reply == 'A': unspent.sort(s_age);  sort = "age"; break
			elif reply == 'r': 
				reverse = False if reverse else True
				unspent.reverse()
				break
			elif reply == 'g': group = False if group else True; break
			elif reply == 'q': break
			else: msg("Invalid input")

		msg("\n")
		if reply == 'q': break

	return unspent


def view_tx_data(c,inputs_data,tx_hex,timestamp=""):

	td = c.decoderawtransaction(tx_hex)

	msg("TRANSACTION DATA:\n")

	if timestamp: msg("Timestamp: %s\n" % timestamp)

	msg("Inputs:")
	total_in = 0
	for n,i in enumerate(td['vin']):
		for j in inputs_data:
			if j['txid'] == i['txid'] and j['vout'] == i['vout']:
				days = j['confirmations'] * mins_per_block / (60*24)
				total_in += j['amount']
				msg("""
%-3s tx,vout: %s,%s
    address:        %s
    amount:         %s BTC
    confirmations:  %s (around %s days)
""".strip() %
	(n+1,i['txid'],i['vout'],j['address'],
	 remove_exponent(j['amount']),j['confirmations'],days)+"\n")
				break

	msg("Total input: %s BTC\n" % remove_exponent(total_in))

	total_out = 0
	msg("Outputs:")
	for n,i in enumerate(td['vout']):
		total_out += i['value']
 		msg("""
%-3s address: %s
    amount:  %s BTC
""".strip() % (
		n,
		i['scriptPubKey']['addresses'][0],
		remove_exponent(i['value']))
	+ "\n")
	msg("Total output: %s BTC" % remove_exponent(total_out))
	msg("TX fee:       %s BTC\n" % remove_exponent(total_in-total_out))


def parse_tx_data(tx_data):

	if len(tx_data) != 4:
		msg("'%s': not a transaction file" % infile)
		sys.exit(2)

	try: unhexlify(tx_data[1])
	except:
		msg("Transaction data is invalid")
		sys.exit(2)

	try:
		sig_data = eval(tx_data[2])
	except:
		msg("Signature data is invalid")
		sys.exit(2)

	try:
		inputs_data = eval(tx_data[3])
	except:
		msg("Inputs data is invalid")
		sys.exit(2)

	return tx_data[0],tx_data[1],sig_data,inputs_data


def select_outputs(unspent,prompt):

	while True:
		reply = my_raw_input(prompt).strip()
		if reply:
			selected = ()
			try:
				selected = [int(i) - 1 for i in reply.split()]
			except: pass
			else:
				for i in selected:
					if i < 0 or i >= len(unspent):
						msg(
		"Input must be a number or numbers between 1 and %s" % len(unspent))
						break
				else: break

		msg("'%s': Invalid input" % reply)

	return [unspent[i] for i in selected]

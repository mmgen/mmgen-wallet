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
import mmgen.config as g

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
file using the '-k' option to mmgen-txsign.

Selected mmgen inputs: %s"""
}

# Deleted text:
# Alternatively, you may import the mmgen keys into the wallet.dat of your
# offline bitcoind, first generating the required keys with mmgen-keygen and
# then running mmgen-txsign with the '-f' option to force the use of
# wallet.dat as the key source.


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


def trim_exponent(n):
	'''Remove exponent and trailing zeros.
	'''
	d = Decimal(n)
	return d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize()


def check_address(rcpt_address):
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

	if g.debug:
		print "Decimal(amt): %s\nAs tuple: %s" % (send_amt,repr(retval.as_tuple()))

	if retval.as_tuple()[-1] < -8:
		msg("%s: Too many decimal places in amount" % send_amt)
		sys.exit(3)

	return trim_exponent(retval)


def get_bitcoind_cfg_options(cfg_keys):

	if "HOME" in os.environ:
		data_dir = ".bitcoin"
		cfg_file = "%s/%s/%s" % (os.environ["HOME"], data_dir, "bitcoin.conf")
	elif "HOMEPATH" in os.environ:
	# Windows:
		data_dir = r"Application Data\Bitcoin"
		cfg_file = "%s\%s\%s" % (os.environ["HOMEPATH"],data_dir,"bitcoin.conf")
	else:
		msg("Neither $HOME nor %HOMEPATH% is set")
		msg("Don't know where to look for 'bitcoin.conf'")
		sys.exit(3)

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
	tx_id = make_chksum_6(unhexlify(tx)).upper()
	outfile = "tx_%s[%s].raw" % (tx_id,send_amt)
	if 'outdir' in opts:
		outfile = "%s/%s" % (opts['outdir'], outfile)
	metadata = "%s %s %s" % (tx_id, send_amt, make_timestamp())
	sig_data = [{"txid":i.txid,"vout":i.vout,"scriptPubKey":i.scriptPubKey}
					for i in sel_unspent]
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

	fs = " %-4s %-11s %-2s %-34s %-13s %-s"
	sort,group,show_mmaddr,reverse = "",False,False,False
	total = trim_exponent(sum([i.amount for i in unspent]))

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

		output = ["UNSPENT OUTPUTS (sort order: %s%s%s)  Total BTC: %s" % (
				"reverse " if reverse else "",
				sort if sort else "None",
	" (grouped)" if group and (sort == "address" or sort == "txid") else "",
				total
			)]
		output.append(fs % ("Num","TX id  Vout","","Address","Amount (BTC)",
					"Age(days)"))

		for i in out:
			amt = str(trim_exponent(i.amount))
			lfill = 3 - len(amt.split(".")[0]) if "." in amt else 3 - len(amt)
			i.amt = " "*lfill + amt
			i.days = int(i.confirmations * g.mins_per_block / (60*24))

		for n,i in enumerate(out):
			if i.skip == "d":
				addr = "|" + "." * 33
			else:
				if show_mmaddr:
					if verify_mmgen_label(i.account):
						addr = "%s.. %s" % (i.address[:4],i.account)
					else:
						addr = i.address
				else:
					addr = i.address
			txid = "       |..." if i.skip == "t" else i.txid[:8]+"..."

			output.append(fs % (str(n+1)+")",txid,i.vout,addr,i.amt,i.days))

		skip_body = False
		while True:
			if skip_body:
				skip_body = False
				immed_chars = "qpP"
			else:
				msg("\n".join(output))
				msg("""
Sort options: [t]xid, [a]mount, a[d]dress, [A]ge, [r]everse, [M]mgen addr
View options: [g]roup, show [m]mgen addr""")
				immed_chars = "qpPtadArMgm"

			reply = get_char(
"(Type 'q' to quit sorting, 'p' to print to file, 'v' to view in pager): ",
				immed_chars=immed_chars)

			if   reply == 'a': unspent.sort(s_amt);  sort = "amount"; break
			elif reply == 't': unspent.sort(s_txid); sort = "txid"; break
			elif reply == 'd': unspent.sort(s_addr); sort = "address"; break
			elif reply == 'A': unspent.sort(s_age);  sort = "age"; break
			elif reply == 'M': unspent.sort(s_mmgen); show_mmaddr,sort=True,"mmgen"; break
			elif reply == 'r':
				reverse = False if reverse else True
				unspent.reverse()
				break
			elif reply == 'g': group = False if group else True; break
			elif reply == 'm': show_mmaddr = False if show_mmaddr else True; break
			elif reply == 'p':
				pfs  = " %-4s %-67s %-34s %-12s %-13s %-10s %s"
				pout = [pfs % ("Num","TX id,Vout","Address","MMgen ID",
					"Amount (BTC)","Age (days)", "Comment")]

				for n,i in enumerate(out):
					if verify_mmgen_label(i.account):
						s = i.account.split(None,1)
						mmid,cmt = s[0],(s[1] if len(s) == 2 else "")
					else:
						mmid,cmt = "",i.account
					os = pfs % (str(n+1)+")", str(i.txid)+","+str(i.vout),
							i.address,mmid,i.amt,i.days,cmt)
					pout.append(os.rstrip())

				sort_info = (
					("reverse," if reverse else "") +
					(sort if sort else "unsorted")
				)
				outdata = \
"Unspent outputs ({} UTC)\nSort order: {}\n\n{}\n\nTotal BTC: {}\n".format(
					make_timestr(), sort_info, "\n".join(pout), total
				)
				outfile = "listunspent[%s].out" % sort_info
				write_to_file(outfile, outdata)
				skip_body = True
				msg("\nData written to '%s'" % outfile)
			elif reply == 'v': do_pager("\n".join(output))
			elif reply == 'q': break
			else: msg("Invalid input")

		msg("\n")
		if reply in 'q': break

	return tuple(unspent)


def verify_mmgen_label(s,return_str=False,check_label_len=False):

	fail    = "" if return_str else False
	success = s  if return_str else True

	if not s: return fail

	try:
		mminfo,comment = s.split(None,1)
	except:
		mminfo,comment = s,None

	if mminfo[8] != ':': return fail
	for i in mminfo[:8]:
		if not i in "01234567890ABCDEF": return fail
	for i in mminfo[9:]:
		if not i in "0123456789": return fail

	if check_label_len and comment:
		check_addr_comment(comment)

	return success


def view_tx_data(c,inputs_data,tx_hex,metadata=[],pager=False):

	td = c.decoderawtransaction(tx_hex)

	out = "TRANSACTION DATA\n\n"

	if metadata:
		out += "Header: [Tx ID: {}] [Amount: {} BTC] [Time: {}]\n\n".format(*metadata)

	out += "Inputs:\n\n"
	total_in = 0
	for n,i in enumerate(td['vin']):
		for j in inputs_data:
			if j['txid'] == i['txid'] and j['vout'] == i['vout']:
				days = int(j['confirmations'] * g.mins_per_block / (60*24))
				total_in += j['amount']
				out += (" " + """
%-2s tx,vout: %s,%s
    address:        %s
    ID/label:       %s
    amount:         %s BTC
    confirmations:  %s (around %s days)
""".strip() %
	(n+1,i['txid'],i['vout'],j['address'],verify_mmgen_label(j['account'],True),
		trim_exponent(j['amount']),j['confirmations'],days)+"\n\n")
				break

	out += "Total input: %s BTC\n\n" % trim_exponent(total_in)

	total_out = 0
	out += "Outputs:\n\n"
	for n,i in enumerate(td['vout']):
		total_out += i['value']
		out += (" " + """
%-2s address: %s
    amount:  %s BTC
""".strip() % (
		n,
		i['scriptPubKey']['addresses'][0],
		trim_exponent(i['value']))
	+ "\n\n")
	out += "Total output: %s BTC\n" % trim_exponent(total_out)
	out += "TX fee:       %s BTC\n" % trim_exponent(total_in-total_out)

	if pager: do_pager(out+"\n")
	else:     msg("\n"+out)



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
		reply = my_raw_input(prompt,allowed_chars="0123456789 -").strip()

		if not reply: continue

		from mmgen.utils import parse_address_list
		selected = parse_address_list(reply,sep=None)

		if not selected: continue

		if selected[-1] > len(unspent):
			msg("Inputs must be less than %s" % len(unspent))
			continue

		return selected


def mmgen_addr_to_btc_addr(m,addr_data):

	ID,num = m.split(":")
	from binascii import unhexlify
	try: unhexlify(ID)
	except: pass
	else:
		try: num = int(num)
		except: pass
		else:
			if not addr_data:
				msg("Address data must be supplied for MMgen address '%s'" % m)
				sys.exit(2)
			for i in addr_data:
				if ID == i[0]:
					for j in i[1]:
						if j[0] == num:
							return j[1]
			msg("MMgen address '%s' not found in supplied address data" % m)
			sys.exit(2)

	msg("Invalid format: %s" % m)
	sys.exit(3)



def make_tx_out(tx_arg,addr_data):

	tx = {}
	for i in tx_arg:
		addr,amt = i.split(",")

		if ":" in addr:
			addr = mmgen_addr_to_btc_addr(addr,addr_data)
		else:
			check_address(addr)

		try: tx[addr] = amt
		except:
			msg("Invalid format: %s: %s" % (addr,amt))
			sys.exit(3)

	if g.debug:
		print "TX (cl):   ", repr(tx_arg)
		print "TX (proc): ", repr(tx)

	import decimal
	try:
		for i in tx.keys():
			tx[i] = trim_exponent(Decimal(tx[i]))
	except decimal.InvalidOperation:
		msg("Decimal conversion error in suboption '%s:%s'" % (i,tx[i]))
		sys.exit(3)

	return tx


def check_addr_comment(label):

	if len(label) > g.max_addr_label_len:
		msg("'%s': overlong label (length must be <=%s)" %
				(label,g.max_addr_label_len))
		sys.exit(3)

	for ch in list(label):
		if ch not in g.addr_label_symbols:
			msg("'%s': illegal character in label '%s'" % (ch,label))
			msg("Permitted characters: A-Za-z0-9, plus '%s'" %
					"', '".join(g.addr_label_punc))
			sys.exit(3)


def parse_addrs_file(f):
	lines = get_lines_from_file(f,"address data",remove_comments=True)

	try:
		seed_id,obrace = lines[0].split()
	except:
		msg("Invalid first line: '%s'" % lines[0])
		sys.exit(3)

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

			if len(d) == 3: check_addr_comment(d[2])

			ret.append(tuple(d))

		return seed_id,ret

	sys.exit(3)


def sign_transaction(c,tx_hex,sig_data,keys=None):

	if keys:
		msg("%s keys total" % len(keys))
		if g.debug: print "Keys:\n  %s" % "\n  ".join(keys)

	from mmgen.rpc import exceptions

	try:
		sig_tx = c.signrawtransaction(tx_hex,sig_data,keys)
	except exceptions.InvalidAddressOrKey:
		msg("Invalid address or key")
		sys.exit(3)
# 	except:
# 		msg("Failed to sign transaction")
# 		sys.exit(3)

	return sig_tx


def get_keys_for_mmgen_addrs(mmgen_addrs,infiles,opts):

	seed_ids = list(set([i['account'][:8] for i in mmgen_addrs]))
	seed_ids_save = seed_ids[0:]
	keys = []

	while seed_ids:
		infile = False
		if infiles:
			infile = infiles.pop()
			seed = get_seed(infile,opts)
		elif "from_brain" in opts or "from_mnemonic" in opts or "from_seed" in opts:
			msg("Need data for seed ID %s" % seed_ids[0])
			seed = get_seed_retry("",opts)
		else:
			b,p,v = ("A seed","","is") if len(seed_ids) == 1 else ("Seed","s","are")
			msg("ERROR: %s source%s %s required for the following seed ID%s: %s" %
					(b,p,v,p," ".join(seed_ids)))
			sys.exit(2)

		seed_id = make_chksum_8(seed)
		if seed_id in seed_ids:
			seed_ids.remove(seed_id)
			seed_id_addrs = [
				int(i['account'].split()[0][9:]) for i in mmgen_addrs
					if i['account'][:8] == seed_id]

			from mmgen.addr import generate_keys
			keys += [i['wif'] for i in generate_keys(seed, seed_id_addrs)]
		else:
			if seed_id in seed_ids_save:
				msg_r("Ignoring duplicate seed source")
				if infile: msg(" '%s'" % infile)
				else:      msg(" for ID %s" % seed_id)
			else:
				msg("Seed source produced an invalid seed ID (%s)" % seed_id)
				if infile:
					msg("Invalid input file: %s" % infile)
					sys.exit(2)

	return keys


def sign_tx_with_bitcoind_wallet(c,tx_hex,sig_data,keys,opts):

	try:
		sig_tx = sign_transaction(c,tx_hex,sig_data,keys)
	except:
		from mmgen.rpc import exceptions
		msg("Using keys in wallet.dat as per user request")
		prompt = "Enter passphrase for bitcoind wallet: "
		while True:
			passwd = get_bitcoind_passphrase(prompt,opts)

			try:
				c.walletpassphrase(passwd, 9999)
			except exceptions.WalletPassphraseIncorrect:
				msg("Passphrase incorrect")
			else:
				msg("Passphrase OK"); break

		sig_tx = sign_transaction(c,tx_hex,sig_data,keys)

		msg("Locking wallet")
		try:
			c.walletlock()
		except:
			msg("Failed to lock wallet")

	return sig_tx


def missing_keys_errormsg(other_addrs):
	msg("""
A key file (option '-f') or wallet.dat (option '-w') must be supplied
for the following non-mmgen address%s: %s""" %
	("" if len(other_addrs) == 1 else "es",
	" ".join([i['address'] for i in other_addrs])
	  ))

def get_addr_data(cmd_args):
	for f in cmd_args:
		data = parse_addrs_file(f)
		print repr(data); sys.exit() # DEBUG

#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C) 2013-2014 by philemon <mmgen-py@yandex.com>
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

txmsg = {
'not_enough_btc': "Not enough BTC in the inputs for this transaction (%s BTC)",
'throwaway_change': """
ERROR: This transaction produces change (%s BTC); however, no change
address was specified.
""".strip(),
'mixed_inputs': """
NOTE: This transaction uses a mixture of both mmgen and non-mmgen inputs,
which makes the signing process more complicated.  When signing the
transaction, keys for the non-mmgen inputs must be supplied in a separate
file using the '-k' option to {}-txsign.

Selected mmgen inputs: %s""".format(g.proj_name.lower()),
'too_many_acct_addresses': """
ERROR: More than one address found for account: "%s".
The tracking "wallet.dat" file appears to have been altered by a non-{g.proj_name}
program.  Please restore "wallet.dat" from a backup or create a new wallet
and re-import your addresses.""".strip().format(g=g),
	'addrfile_no_data_msg': """
No data found for MMgen address '%s'. Please import this address into
your tracking wallet, or supply an address file for it on the command line.
""".strip(),
	'addrfile_warn_msg': """
Warning: no data for address '{mmaddr}' was found in the tracking wallet, so
this information was taken from the user-supplied address file. You're strongly
advised to import this address into your tracking wallet before proceeding with
this transaction.  The address will not be tracked until you do so.
""".strip(),
	'addrfile_fail_msg': """
No data for MMgen address '{mmaddr}' could be found in either the tracking
wallet or the supplied address file.  Please import this address into your
tracking wallet, or supply an address file for it on the command line.
""".strip(),
	'no_spendable_outputs': """
No spendable outputs found!  Import addresses with balances into your
watch-only wallet using '{}-addrimport' and then re-run this program.
""".strip().format(g.proj_name.lower()),
	'mapping_error': """
MMGen -> BTC address mappings differ!
In transaction:      %s
Generated from seed: %s
""".strip(),
	'skip_mapping_checks_warning': """
You've chosen the '--all-keys-from-file' option.  Since all signing keys will
be taken from this file, no {pnm} seed source will be consulted and {pnm}-to-
BTC mapping checks cannot not be performed.  Were an attacker to compromise
your tracking wallet or raw transaction file, he could thus cause you to spend
coin to an unintended address.  For greater security, supply a trusted {pnm}
address file for your output addresses on the command line.
""".strip().format(pnm=g.proj_name),
	'missing_mappings': """
No information was found in the supplied address files for the following {pnm}
addresses: %s
The {pnm}-to-BTC mappings for these addresses cannot be verified!
""".strip().format(pnm=g.proj_name),
}


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
	ret = is_btc_amt(amt)
	if ret: return ret
	else:   sys.exit(3)


def get_bitcoind_cfg_options(cfg_keys):

	if "HOME" in os.environ:       # Linux
		homedir,datadir = os.environ["HOME"],".bitcoin"
	elif "HOMEPATH" in os.environ: # Windows:
		homedir,data_dir = os.environ["HOMEPATH"],r"Application Data\Bitcoin"
	else:
		msg("Neither $HOME nor %HOMEPATH% are set")
		msg("Don't know where to look for 'bitcoin.conf'")
		sys.exit(3)

	cfg_file = os.sep.join((homedir, datadir, "bitcoin.conf"))

	cfg = dict([(k,v) for k,v in [split2(line.translate(None,"\t "),"=")
			for line in get_lines_from_file(cfg_file)] if k in cfg_keys])

	for k in set(cfg_keys) - set(cfg.keys()):
		msg("Configuration option '%s' must be set in %s" % (k,cfg_file))
		sys.exit(2)

	return cfg


def format_unspent_outputs_for_printing(out,sort_info,total):

	pfs  = " %-4s %-67s %-34s %-12s %-13s %-8s %-10s %s"
	pout = [pfs % ("Num","TX id,Vout","Address","MMgen ID",
		"Amount (BTC)","Conf.","Age (days)", "Comment")]

	for n,i in enumerate(out):
		addr = "=" if i.skip == "addr" and "grouped" in sort_info else i.address
		tx = " " * 63 + "=" \
			if i.skip == "txid" and "grouped" in sort_info else str(i.txid)

		s = pfs % (str(n+1)+")", tx+","+str(i.vout),addr,
				i.mmid,i.amt,i.confirmations,i.days,i.label)
		pout.append(s.rstrip())

	return \
"Unspent outputs ({} UTC)\nSort order: {}\n\n{}\n\nTotal BTC: {}\n".format(
		make_timestr(), " ".join(sort_info), "\n".join(pout), total
	)


def sort_and_view(unspent,opts):

	def s_amt(i):   return i.amount
	def s_txid(i):  return "%s %03s" % (i.txid,i.vout)
	def s_addr(i):  return i.address
	def s_age(i):   return i.confirmations
	def s_mmgen(i):
		m = parse_mmgen_label(i.account)[0]
		if m: return "{}:{:>0{w}}".format(w=g.mmgen_idx_max_digits, *m.split(":"))
		else: return "G" + i.account

	sort,group,show_days,show_mmaddr,reverse = "age",False,False,True,True
	unspent.sort(key=s_age,reverse=reverse) # Reverse age sort by default

	total = trim_exponent(sum([i.amount for i in unspent]))
	max_acct_len = max([len(i.account) for i in unspent])

	hdr_fmt   = "UNSPENT OUTPUTS (sort order: %s)  Total BTC: %s"
	options_msg = """
Sort options: [t]xid, [a]mount, a[d]dress, [A]ge, [r]everse, [M]mgen addr
Display options: show [D]ays, [g]roup, show [m]mgen addr, r[e]draw screen
""".strip()
	prompt = \
"('q' = quit sorting, 'p' = print to file, 'v' = pager view, 'w' = wide view): "

	from copy import deepcopy
	from mmgen.term import get_terminal_size

	write_to_file_msg = ""
	msg("")

	while True:
		cols = get_terminal_size()[0]
		if cols < g.min_screen_width:
			msg("%s-txcreate requires a screen at least %s characters wide" %
					(g.proj_name.lower(),g.min_screen_width))
			sys.exit(2)

		addr_w = min(34+((1+max_acct_len) if show_mmaddr else 0),cols-46)
		acct_w   = min(max_acct_len, max(24,int(addr_w-10)))
		btaddr_w = addr_w - acct_w - 1
		tx_w = max(11,min(64, cols-addr_w-32))
		txdots = "..." if tx_w < 64 else ""
		fs = " %-4s %-" + str(tx_w) + "s %-2s %-" + str(addr_w) + "s %-13s %-s"
		table_hdr = fs % ("Num","TX id  Vout","","Address","Amount (BTC)",
							"Age(d)" if show_days else "Conf.")

		unsp = deepcopy(unspent)
		for i in unsp: i.skip = ""
		if group and (sort == "address" or sort == "txid"):
			for a,b in [(unsp[i],unsp[i+1]) for i in range(len(unsp)-1)]:
				if sort == "address" and a.address == b.address: b.skip = "addr"
				elif sort == "txid" and a.txid == b.txid:        b.skip = "txid"

		for i in unsp:
			amt = str(trim_exponent(i.amount))
			lfill = 3 - len(amt.split(".")[0]) if "." in amt else 3 - len(amt)
			i.amt = " "*lfill + amt
			i.days = int(i.confirmations * g.mins_per_block / (60*24))
			i.age = i.days if show_days else i.confirmations
			i.mmid,i.label = parse_mmgen_label(i.account)

			if i.skip == "addr":
				i.addr = "|" + "." * 33
			else:
				if show_mmaddr:
					dots = ".." if btaddr_w < len(i.address) else ""
					i.addr = "%s%s %s" % (
						i.address[:btaddr_w-len(dots)],
						dots,
						i.account[:acct_w])
				else:
					i.addr = i.address

			i.tx = " " * (tx_w-4) + "|..." if i.skip == "txid" \
					else i.txid[:tx_w-len(txdots)]+txdots

		sort_info = ["reverse"] if reverse else []
		sort_info.append(sort if sort else "unsorted")
		if group and (sort == "address" or sort == "txid"):
			sort_info.append("grouped")

		out  = [hdr_fmt % (" ".join(sort_info), total), table_hdr]
		out += [fs % (str(n+1)+")",i.tx,i.vout,i.addr,i.amt,i.age)
					for n,i in enumerate(unsp)]

		msg("\n".join(out) +"\n\n" + write_to_file_msg + options_msg)
		write_to_file_msg = ""

		skip_prompt = False

		while True:
			reply = get_char(prompt, immed_chars="atDdAMrgmeqpvw")

			if   reply == 'a': unspent.sort(key=s_amt);  sort = "amount"
			elif reply == 't': unspent.sort(key=s_txid); sort = "txid"
			elif reply == 'D': show_days = False if show_days else True
			elif reply == 'd': unspent.sort(key=s_addr); sort = "address"
			elif reply == 'A': unspent.sort(key=s_age);  sort = "age"
			elif reply == 'M':
				unspent.sort(key=s_mmgen); sort = "mmgen"
				show_mmaddr = True
			elif reply == 'r':
				unspent.reverse()
				reverse = False if reverse else True
			elif reply == 'g': group = False if group else True
			elif reply == 'm': show_mmaddr = False if show_mmaddr else True
			elif reply == 'e': pass
			elif reply == 'q': pass
			elif reply == 'p':
				d = format_unspent_outputs_for_printing(unsp,sort_info,total)
				of = "listunspent[%s].out" % ",".join(sort_info)
				write_to_file(of, d, opts,"",False,False)
				write_to_file_msg = "Data written to '%s'\n\n" % of
			elif reply == 'v':
				do_pager("\n".join(out))
				continue
			elif reply == 'w':
				data = format_unspent_outputs_for_printing(unsp,sort_info,total)
				do_pager(data)
				continue
			else:
				msg("\nInvalid input")
				continue

			break

		msg("\n")
		if reply == 'q': break

	return tuple(unspent)


def parse_mmgen_label(s,check_label_len=False):
	l = split2(s)
	if not is_mmgen_addr(l[0]): return "",s
	if check_label_len: check_addr_label(l[1])
	return tuple(l)


def view_tx_data(c,inputs_data,tx_hex,b2m_map,metadata=[],pager=False):

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
				addr = j['address']
				mmid,label = parse_mmgen_label(j['account']) \
							 if 'account' in j else ("","")
				mmid_str = ((34-len(addr))*" " + " (%s)" % mmid) if mmid else ""

				for d in (
	(n+1, "tx,vout:",       "%s,%s" % (i['txid'], i['vout'])),
	("",  "address:",       addr + mmid_str),
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
		mmid_str = ((34-len(addr))*" " + " (%s)" % mmid) if mmid else ""
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

	if pager: do_pager(out)
	else:     print "\n"+out


def parse_tx_data(tx_data,infile):

	try:
		metadata,tx_hex,inputs_data,outputs_data = tx_data
	except:
		msg("'%s': not a transaction file" % infile)
		sys.exit(2)

	err_fmt = "Transaction %s is invalid"

	if len(metadata.split()) != 3:
		msg(err_fmt % "metadata")
		sys.exit(2)

	try: unhexlify(tx_hex)
	except:
		msg(err_fmt % "hex data")
		sys.exit(2)
	else:
		if not tx_hex:
			msg("Transaction is empty!")
			sys.exit(2)

	try:
		inputs_data = eval(inputs_data)
	except:
		msg(err_fmt % "inputs data")
		sys.exit(2)

	try:
		outputs_data = eval(outputs_data)
	except:
		msg(err_fmt % "mmgen to btc address map data")
		sys.exit(2)

	return metadata.split(),tx_hex,inputs_data,outputs_data


def select_outputs(unspent,prompt):

	while True:
		reply = my_raw_input(prompt).strip()

		if not reply: continue

		from mmgen.util import parse_address_list
		selected = parse_address_list(reply,sep=None)

		if not selected: continue

		if selected[-1] > len(unspent):
			msg("Inputs must be less than %s" % len(unspent))
			continue

		return selected

def is_mmgen_seed_id(s):
	import re
	return True if re.match(r"^[0123456789ABCDEF]{8}$",s) else False

def is_mmgen_idx(s):
	import re
	m = g.mmgen_idx_max_digits
	return True if re.match(r"^[0123456789]{1,"+str(m)+r"}$",s) else False

def is_mmgen_addr(s):
	seed_id,idx = split2(s,":")
	return is_mmgen_seed_id(seed_id) and is_mmgen_idx(idx)

def is_btc_addr(s):
	from mmgen.bitcoin import verify_addr
	return verify_addr(s)


def mmaddr2btcaddr_bitcoind(c,mmaddr,acct_data):

	# We don't want to create a new object, so we'll use append()
	if not acct_data:
		for i in c.listaccounts():
			acct_data.append(i)

	for acct in acct_data:
		m,comment = parse_mmgen_label(acct)
		if m == mmaddr:
			addrlist = c.getaddressesbyaccount(acct)
			if len(addrlist) == 1:
				return addrlist[0],comment
			else:
				msg(txmsg['too_many_acct_addresses'] % acct); sys.exit(2)

	return "",""


def mmaddr2btcaddr_addrfile(mmaddr,addr_data,silent=False):

	mmid,mmidx = mmaddr.split(":")

	for ad in addr_data:
		if mmid == ad[0]:
			for j in ad[1]:
				if j[0] == mmidx:
					if not silent:
						msg(txmsg['addrfile_warn_msg'].format(mmaddr=mmaddr))
						if not user_confirm("Continue anyway?"):
							sys.exit(1)
					return j[1:] if len(j) == 3 else (j[1],"")

	if silent: return "",""
	else: msg(txmsg['addrfile_fail_msg'].format(mmaddr=mmaddr)); sys.exit(2)


def check_mmgen_to_btc_addr_mappings(mmgen_inputs,b2m_map,infiles,saved_seeds,opts):
	in_maplist  = [(i['account'].split()[0],i['address']) for i in mmgen_inputs]
	out_maplist = [(i[1][0],i[0]) for i in b2m_map.items()]

	for maplist,label in (in_maplist,"inputs"), (out_maplist,"outputs"):
		if not maplist: continue
		qmsg("Checking MMGen -> BTC address mappings for %s" % label)
		pairs = get_keys_for_mmgen_addrs([i[0] for i in maplist],
				infiles,saved_seeds,opts,gen_pairs=True)
		for a,b in zip(sorted(pairs),sorted(maplist)):
			if a != b:
				msg(txmsg['mapping_error'] % (" ".join(a)," ".join(b)))
				sys.exit(3)

	qmsg("Address mappings OK")


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

def make_addr_data_chksum(addr_data):
	nchars = 24
	return make_chksum_N(
		" ".join(["{} {}".format(*d[:2]) for d in addr_data]), nchars, sep=True
	)

def check_addr_data_hash(seed_id,addr_data):
	def s_addrdata(a): return int(a[0])
	addr_data_chksum = make_addr_data_chksum(sorted(addr_data,key=s_addrdata))
	from mmgen.addr import fmt_addr_idxs
	fl = fmt_addr_idxs([int(a[0]) for a in addr_data])
	msg("Computed checksum for addr data {}[{}]: {}".format(
				seed_id,fl,addr_data_chksum))
	qmsg("Check this value against your records")

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
	elif not is_mmgen_seed_id(seed_id):
		msg("'%s': invalid Seed ID" % seed_id)
	else:
		addr_data = []
		for i in lines[1:-1]:
			d = i.split(None,2)

			if not is_mmgen_idx(d[0]):
				msg("'%s': invalid address num. in line: %s" % (d[0],d))
				sys.exit(3)

			if not is_btc_addr(d[1]):
				msg("'%s': invalid Bitcoin address" % d[1])
				sys.exit(3)

			if len(d) == 3:
				check_addr_label(d[2])

			addr_data.append(tuple(d))

		check_addr_data_hash(seed_id,addr_data)

		return seed_id,addr_data

	sys.exit(3)


def sign_transaction(c,tx_hex,sig_data,keys=None):

	if keys:
		qmsg("%s keys total" % len(keys))
		if g.debug: print "Keys:\n  %s" % "\n  ".join(keys)

	msg_r("Signing transaction...")
	from mmgen.rpc import exceptions
	try:
		sig_tx = c.signrawtransaction(tx_hex,sig_data,keys)
	except exceptions.InvalidAddressOrKey:
		msg("failed\nInvalid address or key")
		sys.exit(3)

	return sig_tx

def get_seed_for_seed_id(seed_id,infiles,saved_seeds,opts):

	if seed_id in saved_seeds.keys():
		return saved_seeds[seed_id]

	while True:
		if infiles:
			seed = get_seed_retry(infiles.pop(0),opts)
		elif "from_brain" in opts or "from_mnemonic" in opts \
			or "from_seed" in opts or "from_incog" in opts:
			msg("Need data for seed ID %s" % seed_id)
			seed = get_seed_retry("",opts)
			msg("User input produced seed ID %s" % make_chksum_8(seed))
		else:
			msg("ERROR: No seed source found for seed ID: %s" % seed_id)
			sys.exit(2)

		s_id = make_chksum_8(seed)
		saved_seeds[s_id] = seed

		if s_id == seed_id: return seed


def get_keys_for_mmgen_addrs(mmgen_addrs,infiles,saved_seeds,opts,gen_pairs=False):

	seed_ids = list(set([i[:8] for i in mmgen_addrs]))
	ret = []

	for seed_id in seed_ids:
		# Returns only if seed is found
		seed = get_seed_for_seed_id(seed_id,infiles,saved_seeds,opts)

		addr_ids = [int(i[9:]) for i in mmgen_addrs if i[:8] == seed_id]
		from mmgen.addr import generate_addrs
		if gen_pairs:
			ret += [("{}:{}".format(seed_id,i.num),i.addr)
				for i in generate_addrs(seed, addr_ids, {'gen_what':("addrs")})]
		else:
			ret += [i.wif for i in generate_addrs(
						seed,addr_ids,{'gen_what':("keys")})]

	return ret


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


def preverify_keys(addrs_orig, keys_orig):

	addrs,keys,wrong_keys = set(addrs_orig[0:]),set(keys_orig[0:]),[]

	if len(keys) < len(addrs):
		msg("ERROR: not enough keys (%s) for number of non-%s addresses (%s)" %
				(len(keys),g.proj_name,len(addrs)))
		sys.exit(2)

	import mmgen.bitcoin as b

	qmsg_r('Checking that user-supplied key list contains valid keys...')

	invalid_keys = []

	for n,k in enumerate(keys,1):
		c = False if k[0] == '5' else True
		if b.wiftohex(k,compressed=c) == False:
			invalid_keys.append(k)

	if invalid_keys:
		s = "" if len(invalid_keys) == 1 else "s"
		msg("\n%s/%s invalid key%s in keylist!\n" % (len(invalid_keys),len(keys),s))
		sys.exit(2)
	else: qmsg("OK")

	# Check that keys match addresses:
	msg('Pre-verifying keys in user-supplied key list (Ctrl-C to skip)')

	try:
		for n,k in enumerate(keys,1):
			msg_r("\rkey %s of %s" % (n,len(keys)))
			c = False if k[0] == '5' else True
			hexkey = b.wiftohex(k,compressed=c)
			addr = b.privnum2addr(int(hexkey,16),compressed=c)
			if addr in addrs:
				addrs.remove(addr)
				if not addrs: break
			else:
				wrong_keys.append(k)
	except KeyboardInterrupt:
		msg("\nSkipping")
	else:
		msg("")
		if wrong_keys:
			s = "" if len(wrong_keys) == 1 else "s"
			msg("%s extra key%s found" % (len(wrong_keys),s))

		if addrs:
			s = "" if len(addrs) == 1 else "es"
			msg("No keys found for the following non-%s address%s:" %
					(g.proj_name,s))
			print "  %s" % "\n  ".join(addrs)
			sys.exit(2)


def missing_keys_errormsg(other_addrs):
	msg("""
A key file must be supplied (or use the "-w" option) for the following
non-mmgen address%s:
""".strip() % ("" if len(other_addrs) == 1 else "es"))
	print "  %s" % "\n  ".join([i['address'] for i in other_addrs])


def check_mmgen_to_btc_addr_mappings_addrfile(mmgen_inputs,b2m_map,addrfiles):
	addr_data = [parse_addrs_file(a) for a in addrfiles]
	in_maplist  = [(i['account'].split()[0],i['address']) for i in mmgen_inputs]
	out_maplist = [(i[1][0],i[0]) for i in b2m_map.items()]

	missing,wrong = [],[]
	for maplist,label in (in_maplist,"inputs"), (out_maplist,"outputs"):
		qmsg("Checking MMGen -> BTC address mappings for %s" % label)
		for i in maplist:
			btaddr = mmaddr2btcaddr_addrfile(i[0],addr_data,silent=True)[0]
			if not btaddr: missing.append(i[0])
			elif btaddr != i[1]: wrong.append((i[0],i[1],btaddr))

	if wrong:
		fs = " {:11} {:35} {}"
		msg("ERROR: The following address mappings did not match!")
		msg(fs.format("MMGen addr","In TX file:","In address file:"))
		for w in wrong: msg(fs.format(*w))
		sys.exit(3)

	if missing:
		confirm_or_exit(txmsg['missing_mappings'] % " ".join(missing),"continue")
	else: qmsg("Address mappings OK")

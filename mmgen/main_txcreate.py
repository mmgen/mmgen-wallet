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
mmgen-txcreate: Create a Bitcoin transaction from MMGen- or non-MMGen inputs
                to MMGen- or non-MMGen outputs
"""

import sys
from decimal import Decimal

import mmgen.config as g
from mmgen.Opts import *
from mmgen.license import *
from mmgen.tx import *
from mmgen.util import msg, msg_r, keypress_confirm

help_data = {
	'prog_name': g.prog_name,
	'desc':    "Create a BTC transaction with outputs to specified addresses",
	'usage':   "[opts]  <addr,amt> ... [change addr] [addr file] ...",
	'options': """
-h, --help            Print this help message
-c, --comment-file= f Source the transaction's comment from file 'f'
-d, --outdir=       d Specify an alternate directory 'd' for output
-e, --echo-passphrase Print passphrase to screen when typing it
-f, --tx-fee=       f Transaction fee (default: {g.tx_fee} BTC)
-i, --info            Display unspent outputs and exit
-q, --quiet           Suppress warnings; overwrite files without
                      prompting
""".format(g=g),
	'notes': """

Transaction inputs are chosen from a list of the user's unpent outputs
via an interactive menu.

Ages of transactions are approximate based on an average block creation
interval of {g.mins_per_block} minutes.

Addresses on the command line can be Bitcoin addresses or {pnm} addresses
of the form <seed ID>:<number>.

To send all inputs (minus TX fee) to a single output, specify one address
with no amount on the command line.
""".format(g=g,pnm=g.proj_name)
}

opts,cmd_args = parse_opts(sys.argv,help_data)

if g.debug: show_opts_and_cmd_args(opts,cmd_args)

c = connect_to_bitcoind()

if not 'info' in opts:
	do_license_msg(immed=True)

	tx_out,addr_data,b2m_map,acct_data,change_addr = {},[],{},[],""

	addrfiles = [a for a in cmd_args if get_extension(a) == g.addrfile_ext]
	cmd_args = set(cmd_args) - set(addrfiles)

	for a in addrfiles:
		check_infile(a)
		addr_data.append(parse_addrs_file(a))

	def mmaddr2btcaddr(c,mmaddr,acct_data,addr_data,b2m_map):
		# assume mmaddr has already been checked
		btcaddr,label = mmaddr2btcaddr_bitcoind(c,mmaddr,acct_data)
		if not btcaddr:
			if addr_data:
				btcaddr,label = mmaddr2btcaddr_addrfile(mmaddr,addr_data)
			else:
				msg(txmsg['addrfile_no_data_msg'] % mmaddr)
				sys.exit(2)

		b2m_map[btcaddr] = mmaddr,label
		return btcaddr

	for a in cmd_args:
		if "," in a:
			a1,a2 = a.split(",")
			if is_btc_addr(a1):
				btcaddr = a1
			elif is_mmgen_addr(a1):
				btcaddr = mmaddr2btcaddr(c,a1,acct_data,addr_data,b2m_map)
			else:
				msg("%s: unrecognized subargument in argument '%s'" % (a1,a))
				sys.exit(2)

			if is_btc_amt(a2):
				tx_out[btcaddr] = normalize_btc_amt(a2)
			else:
				msg("%s: invalid amount in argument '%s'" % (a2,a))
				sys.exit(2)
		elif is_mmgen_addr(a) or is_btc_addr(a):
			if change_addr:
				msg("ERROR: More than one change address specified: %s, %s" %
						(change_addr, a))
				sys.exit(2)
			change_addr = a if is_btc_addr(a) else \
				mmaddr2btcaddr(c,a,acct_data,addr_data,b2m_map)
			tx_out[change_addr] = 0
		else:
			msg("%s: unrecognized argument" % a)
			sys.exit(2)

	if not tx_out:
		msg("At least one output must be specified on the command line")
		sys.exit(2)

	tx_fee = opts['tx_fee'] if 'tx_fee' in opts else g.tx_fee
	tx_fee = normalize_btc_amt(tx_fee)
	if tx_fee > g.max_tx_fee:
		msg("Transaction fee too large: %s > %s" % (tx_fee,g.max_tx_fee))
		sys.exit(2)

if g.debug: show_opts_and_cmd_args(opts,cmd_args)

#write_to_file("bogus_unspent.json", repr(us), opts); sys.exit()

#if False:
if g.bogus_wallet_data:
	import mmgen.rpc
	us = eval(get_data_from_file(g.bogus_wallet_data))
else:
	us = c.listunspent()

if not us: msg(txmsg['no_spendable_outputs']); sys.exit(2)

unspent = sort_and_view(us,opts)

total = trim_exponent(sum([i.amount for i in unspent]))

msg("Total unspent: %s BTC (%s outputs)" % (total, len(unspent)))
if 'info' in opts: sys.exit(0)

send_amt = sum([tx_out[i] for i in tx_out.keys()])
msg("Total amount to spend: %s%s" % (
		(send_amt or "Unknown")," BTC" if send_amt else ""))

while True:
	sel_nums = select_outputs(unspent,
			"Enter a range or space-separated list of outputs to spend: ")
	msg("Selected output%s: %s" %
		(("" if len(sel_nums) == 1 else "s"), " ".join(str(i) for i in sel_nums))
	)
	sel_unspent = [unspent[i-1] for i in sel_nums]

	mmaddrs = set([parse_mmgen_label(i.account)[0] for i in sel_unspent])
	mmaddrs.discard("")

	if mmaddrs and len(mmaddrs) < len(sel_unspent):
		msg(txmsg['mixed_inputs'] % ", ".join(sorted(mmaddrs)))
		if not keypress_confirm("Accept?"):
			continue

	total_in = trim_exponent(sum([i.amount for i in sel_unspent]))
	change   = trim_exponent(total_in - (send_amt + tx_fee))

	if change >= 0:
		prompt = "Transaction produces %s BTC in change.  OK?" % change
		if keypress_confirm(prompt,default_yes=True):
			break
	else:
		msg(txmsg['not_enough_btc'] % change)

if change > 0 and not change_addr:
	msg(txmsg['throwaway_change'] % change)
	sys.exit(2)

if change_addr in tx_out and not change:
	msg("Warning: Change address will be unused as transaction produces no change")
	del tx_out[change_addr]

for k,v in tx_out.items(): tx_out[k] = float(v)

if change > 0: tx_out[change_addr] = float(change)

tx_in = [{"txid":i.txid, "vout":i.vout} for i in sel_unspent]

if g.debug:
	print "tx_in:", repr(tx_in)
	print "tx_out:", repr(tx_out)

if 'comment_file' in opts:
	comment = get_tx_comment_from_file(opts['comment_file'])
	if comment == False: sys.exit(2)
	if keypress_confirm("Edit comment?",False):
		comment = get_tx_comment_from_user(comment)
else:
	if keypress_confirm("Add a comment to transaction?",False):
		comment = get_tx_comment_from_user()
	else: comment = False

tx_hex = c.createrawtransaction(tx_in,tx_out)
qmsg("Transaction successfully created")

prompt = "View decoded transaction? (y)es, (N)o, (v)iew in pager"
reply = prompt_and_get_char(prompt,"YyNnVv",enter_ok=True)

amt = send_amt or change
tx_id = make_chksum_6(unhexlify(tx_hex)).upper()
metadata = tx_id, amt, make_timestamp()

if reply and reply in "YyVv":
	view_tx_data(c,[i.__dict__ for i in sel_unspent],tx_hex,b2m_map,
			comment,metadata,True if reply in "Vv" else False)

prompt = "Save transaction?"
if keypress_confirm(prompt,default_yes=True):
	outfile = "tx_%s[%s].%s" % (tx_id,amt,g.rawtx_ext)
	data = make_tx_data("{} {} {}".format(*metadata), tx_hex,
			[i.__dict__ for i in sel_unspent], b2m_map, comment)
	write_to_file(outfile,data,opts,"transaction",False,True)
else:
	msg("Transaction not saved")

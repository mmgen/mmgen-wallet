#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2016 Philemon <mmgen-py@yandex.com>
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
mmgen-txcreate: Create a Bitcoin transaction to and from MMGen- or non-MMGen
                inputs and outputs
"""

from decimal import Decimal

from mmgen.common import *
from mmgen.tx import *
from mmgen.tw import *

pnm = g.proj_name

opts_data = {
	'desc':    'Create a BTC transaction with outputs to specified addresses',
	'usage':   '[opts]  <addr,amt> ... [change addr] [addr file] ...',
	'options': """
-h, --help            Print this help message
-a, --tx-fee-adj=   f Adjust transaction fee by factor 'f' (see below)
-c, --comment-file= f Source the transaction's comment from file 'f'
-C, --tx-confs=     c Desired number of confirmations (default: {g.tx_confs})
-d, --outdir=       d Specify an alternate directory 'd' for output
-e, --echo-passphrase Print passphrase to screen when typing it
-f, --tx-fee=       f Transaction fee (default: {g.tx_fee} BTC (but see below))
-i, --info            Display unspent outputs and exit
-q, --quiet           Suppress warnings; overwrite files without prompting
-v, --verbose         Produce more verbose output
""".format(g=g),
	'notes': """

Transaction inputs are chosen from a list of the user's unpent outputs
via an interactive menu.

If the transaction fee is not specified by the user, it will be calculated
using bitcoind's "estimatefee" function for the default (or user-specified)
number of confirmations.  If "estimatefee" fails, the global default fee of
{g.tx_fee} BTC will be used.

Dynamic fees will be multiplied by the value of '--tx-fee-adj', if specified.

Ages of transactions are approximate based on an average block discovery
interval of {g.mins_per_block} minutes.

All addresses on the command line can be either Bitcoin addresses or {pnm}
addresses of the form <seed ID>:<index>.

To send the value of all inputs (minus TX fee) to a single output, specify
one address with no amount on the command line.
""".format(g=g,pnm=pnm)
}

wmsg = {
	'addr_in_addrfile_only': """
Warning: output address {mmgenaddr} is not in the tracking wallet, which means
its balance will not be tracked.  You're strongly advised to import the address
into your tracking wallet before broadcasting this transaction.
""".strip(),
	'addr_not_found': """
No data for {pnm} address {mmgenaddr} could be found in either the tracking
wallet or the supplied address file.  Please import this address into your
tracking wallet, or supply an address file for it on the command line.
""".strip(),
	'addr_not_found_no_addrfile': """
No data for {pnm} address {mmgenaddr} could be found in the tracking wallet.
Please import this address into your tracking wallet or supply an address file
for it on the command line.
""".strip(),
	'mixed_inputs': """
NOTE: This transaction uses a mixture of both {pnm} and non-{pnm} inputs, which
makes the signing process more complicated.  When signing the transaction, keys
for the non-{pnm} inputs must be supplied to '{pnl}-txsign' in a file with the
'--keys-from-file' option.

Selected mmgen inputs: %s
""".strip().format(pnm=pnm,pnl=pnm.lower()),
	'not_enough_btc': """
Not enough BTC in the inputs for this transaction (%s BTC)
""".strip(),
	'throwaway_change': """
ERROR: This transaction produces change (%s BTC); however, no change address
was specified.
""".strip(),
}

def select_outputs(unspent,prompt):

	while True:
		reply = my_raw_input(prompt).strip()

		if not reply: continue

		selected = parse_addr_idxs(reply,sep=None)

		if not selected: continue

		if selected[-1] > len(unspent):
			msg('Inputs must be less than %s' % len(unspent))
			continue

		return selected


def mmaddr2baddr(c,mmaddr,ail_w,ail_f):

	# assume mmaddr has already been checked
	btc_addr = ail_w.mmaddr2btcaddr(mmaddr)

	if not btc_addr:
		if ail_f:
			btc_addr = ail_f.mmaddr2btcaddr(mmaddr)
			if btc_addr:
				msg(wmsg['addr_in_addrfile_only'].format(mmgenaddr=mmaddr))
				if not keypress_confirm('Continue anyway?'):
					sys.exit(1)
			else:
				die(2,wmsg['addr_not_found'].format(pnm=pnm,mmgenaddr=mmaddr))
		else:
			die(2,wmsg['addr_not_found_no_addrfile'].format(pnm=pnm,mmgenaddr=mmaddr))

	return btc_addr


def get_fee_estimate():
	if 'tx_fee' in opt.set_by_user:
		return None
	else:
		ret = c.estimatefee(opt.tx_confs)
		if ret != -1:
			return ret
		else:
			m = """
Fee estimation failed!
Your possible courses of action (from best to worst):
    1) Re-run script with a different '--tx-confs' parameter (now '{c}')
    2) Re-run script with the '--tx-fee' option (specify fee manually)
    3) Accept the global default fee of {f} BTC
Accept the global default fee of {f} BTC?
""".format(c=opt.tx_confs,f=opt.tx_fee).strip()
			if keypress_confirm(m):
				return None
			else:
				die(1,'Exiting at user request')

# main(): execution begins here

cmd_args = opts.init(opts_data)

tx = MMGenTX()

if opt.comment_file: tx.add_comment(opt.comment_file)

c = bitcoin_connection()

if not opt.info:
	do_license_msg(immed=True)

	addrfiles = [a for a in cmd_args if get_extension(a) == g.addrfile_ext]
	cmd_args = set(cmd_args) - set(addrfiles)

	from mmgen.addr import AddrInfo,AddrInfoList
	ail_f = AddrInfoList()
	for a in addrfiles:
		check_infile(a)
		ail_f.add(AddrInfo(a))

	ail_w = AddrInfoList(bitcoind_connection=c)

	for a in cmd_args:
		if ',' in a:
			a1,a2 = split2(a,',')
			if is_btc_addr(a1):
				btc_addr = a1
			elif is_mmgen_addr(a1):
				btc_addr = mmaddr2baddr(c,a1,ail_w,ail_f)
			else:
				die(2,"%s: unrecognized subargument in argument '%s'" % (a1,a))

			btc_amt = convert_to_btc_amt(a2)
			if btc_amt:
				tx.add_output(btc_addr,btc_amt)
			else:
				die(2,"%s: invalid amount in argument '%s'" % (a2,a))
		elif is_mmgen_addr(a) or is_btc_addr(a):
			if tx.change_addr:
				die(2,'ERROR: More than one change address specified: %s, %s' %
						(change_addr, a))
			tx.change_addr = a if is_btc_addr(a) else mmaddr2baddr(c,a,ail_w,ail_f)
			tx.add_output(tx.change_addr,Decimal('0'))
		else:
			die(2,'%s: unrecognized argument' % a)

	if not tx.outputs:
		die(2,'At least one output must be specified on the command line')

	if opt.tx_fee > g.max_tx_fee:
		die(2,'Transaction fee too large: %s > %s' % (opt.tx_fee,g.max_tx_fee))

	fee_estimate = get_fee_estimate()

tw = MMGenTrackingWallet()
tw.view_and_sort()
tw.display_total()

if opt.info: sys.exit()

tx.send_amt = tx.sum_outputs()

msg('Total amount to spend: %s' % ('Unknown','%s BTC'%tx.send_amt,)[bool(tx.send_amt)])

while True:
	sel_nums = select_outputs(tw.unspent,
			'Enter a range or space-separated list of outputs to spend: ')
	msg('Selected output%s: %s' % (
			('s','')[len(sel_nums)==1],
			' '.join(str(i) for i in sel_nums)
		))
	sel_unspent = [tw.unspent[i-1] for i in sel_nums]

	mmaddrs = set([i['mmid'] for i in sel_unspent])

	if '' in mmaddrs and len(mmaddrs) > 1:
		mmaddrs.discard('')
		msg(wmsg['mixed_inputs'] % ', '.join(sorted(mmaddrs)))
		if not keypress_confirm('Accept?'):
			continue

	tx.copy_inputs(sel_unspent)              # makes tx.inputs

	tx.calculate_size_and_fee(fee_estimate)  # sets tx.size, tx.fee

	change_amt = tx.sum_inputs() - tx.send_amt - tx.fee

	if change_amt >= 0:
		prompt = 'Transaction produces %s BTC in change.  OK?' % change_amt
		if keypress_confirm(prompt,default_yes=True):
			break
	else:
		msg(wmsg['not_enough_btc'] % change_amt)

if change_amt > 0:
	if not tx.change_addr:
		die(2,wmsg['throwaway_change'] % change_amt)
	tx.add_output(tx.change_addr,change_amt)
elif tx.change_addr:
	msg('Warning: Change address will be unused as transaction produces no change')
	tx.del_output(tx.change_addr)

if not tx.send_amt:
	tx.send_amt = change_amt

dmsg('tx: %s' % tx)

tx.add_comment()   # edits an existing comment
tx.create_raw(c)   # creates tx.hex, tx.txid
tx.add_mmaddrs_to_outputs(ail_w,ail_f)
tx.add_timestamp()
tx.add_blockcount(c)

qmsg('Transaction successfully created')

dmsg('TX (final): %s' % tx)

tx.view_with_prompt('View decoded transaction?')

tx.write_to_file(ask_write_default_yes=False)

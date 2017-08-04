#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2017 Philemon <mmgen-py@yandex.com>
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
txcreate: Create a Bitcoin transaction to and from MMGen- or non-MMGen inputs
          and outputs
"""

from mmgen.common import *
from mmgen.tx import *
from mmgen.tw import *

pnm = g.proj_name

txcreate_notes = """
The transaction's outputs are specified on the command line, while its inputs
are chosen from a list of the user's unpent outputs via an interactive menu.

If the transaction fee is not specified on the command line (see FEE
SPECIFICATION below), it will be calculated dynamically using bitcoind's
"estimatefee" function for the default (or user-specified) number of
confirmations.  If "estimatefee" fails, the user will be prompted for a fee.

Dynamic ("estimatefee") fees will be multiplied by the value of '--tx-fee-adj',
if specified.

Ages of transactions are approximate based on an average block discovery
interval of {g.mins_per_block} minutes.

All addresses on the command line can be either Bitcoin addresses or {pnm}
addresses of the form <seed ID>:<index>.

To send the value of all inputs (minus TX fee) to a single output, specify
one address with no amount on the command line.
""".format(g=g,pnm=pnm)

fee_notes = """
FEE SPECIFICATION: Transaction fees, both on the command line and at the
interactive prompt, may be specified as either absolute {} amounts, using
a plain decimal number, or as satoshis per byte, using an integer followed by
the letter 's'.
""".format(g.coin)

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
	'non_mmgen_inputs': """
NOTE: This transaction includes non-{pnm} inputs, which makes the signing
process more complicated.  When signing the transaction, keys for non-{pnm}
inputs must be supplied to '{pnl}-txsign' in a file with the '--keys-from-file'
option.
Selected non-{pnm} inputs: {{}}
""".strip().format(pnm=pnm,pnl=pnm.lower()),
	'not_enough_btc': """
Selected outputs insufficient to fund this transaction ({{}} {} needed)
""".strip().format(g.coin),
	'no_change_output': """
ERROR: No change address specified.  If you wish to create a transaction with
only one output, specify a single output address with no {} amount
""".strip().format(g.coin),
}

def select_unspent(unspent,prompt):
	while True:
		reply = my_raw_input(prompt).strip()
		if reply:
			selected = AddrIdxList(fmt_str=','.join(reply.split()),on_fail='return')
			if selected:
				if selected[-1] <= len(unspent):
					return selected
				msg('Unspent output number must be <= %s' % len(unspent))

def mmaddr2baddr(c,mmaddr,ad_w,ad_f):

	# assume mmaddr has already been checked
	btc_addr = ad_w.mmaddr2btcaddr(mmaddr)

	if not btc_addr:
		if ad_f:
			btc_addr = ad_f.mmaddr2btcaddr(mmaddr)
			if btc_addr:
				msg(wmsg['addr_in_addrfile_only'].format(mmgenaddr=mmaddr))
				if not keypress_confirm('Continue anyway?'):
					sys.exit(1)
			else:
				die(2,wmsg['addr_not_found'].format(pnm=pnm,mmgenaddr=mmaddr))
		else:
			die(2,wmsg['addr_not_found_no_addrfile'].format(pnm=pnm,mmgenaddr=mmaddr))

	return BTCAddr(btc_addr)

def get_fee_from_estimate_or_user(tx,estimate_fail_msg_shown=[]):

	c = bitcoin_connection()

	if opt.tx_fee:
		desc = 'User-selected'
		start_fee = opt.tx_fee
	else:
		desc = 'Network-estimated'
		ret = c.estimatefee(opt.tx_confs)
		if ret == -1:
			if not estimate_fail_msg_shown:
				msg('Network fee estimation for {} confirmations failed'.format(opt.tx_confs))
				estimate_fail_msg_shown.append(True)
			start_fee = None
		else:
			start_fee = BTCAmt(ret) * opt.tx_fee_adj * tx.estimate_size() / 1024
			if opt.verbose:
				msg('{} fee ({} confs): {} {}/kB'.format(desc,opt.tx_confs,ret,g.coin))
				msg('TX size (estimated): {}'.format(tx.estimate_size()))

	return tx.get_usr_fee_interactive(start_fee,desc=desc)

def get_outputs_from_cmdline(cmd_args,tx):
	from mmgen.addr import AddrList,AddrData
	addrfiles = [a for a in cmd_args if get_extension(a) == AddrList.ext]
	cmd_args = set(cmd_args) - set(addrfiles)

	ad_f = AddrData()
	for a in addrfiles:
		check_infile(a)
		ad_f.add(AddrList(a))

	ad_w = AddrData(source='tw')

	for a in cmd_args:
		if ',' in a:
			a1,a2 = a.split(',',1)
			if is_mmgen_id(a1) or is_btc_addr(a1):
				btc_addr = mmaddr2baddr(c,a1,ad_w,ad_f) if is_mmgen_id(a1) else BTCAddr(a1)
				tx.add_output(btc_addr,BTCAmt(a2))
			else:
				die(2,"%s: unrecognized subargument in argument '%s'" % (a1,a))
		elif is_mmgen_id(a) or is_btc_addr(a):
			if tx.get_chg_output_idx() != None:
				die(2,'ERROR: More than one change address listed on command line')
			btc_addr = mmaddr2baddr(c,a,ad_w,ad_f) if is_mmgen_id(a) else BTCAddr(a)
			tx.add_output(btc_addr,BTCAmt('0'),is_chg=True)
		else:
			die(2,'%s: unrecognized argument' % a)

	if not tx.outputs:
		die(2,'At least one output must be specified on the command line')

	if tx.get_chg_output_idx() == None:
		die(2,('ERROR: No change output specified',wmsg['no_change_output'])[len(tx.outputs) == 1])

	tx.add_mmaddrs_to_outputs(ad_w,ad_f)

	if not segwit_is_active() and tx.has_segwit_outputs():
		fs = '{} Segwit address requested on the command line, but Segwit is not active on this chain'
		rdie(2,fs.format(g.proj_name))

def get_inputs_from_user(tw,tx,caller):

	while True:
		m = 'Enter a range or space-separated list of outputs to spend: '
		sel_nums = select_unspent(tw.unspent,m)
		msg('Selected output%s: %s' % (suf(sel_nums,'s'),' '.join(str(i) for i in sel_nums)))

		sel_unspent = tw.MMGenTwOutputList([tw.unspent[i-1] for i in sel_nums])

		t_inputs = sum(s.amt for s in sel_unspent)
		if t_inputs < tx.send_amt:
			msg(wmsg['not_enough_btc'].format(tx.send_amt-t_inputs))
			continue

		non_mmaddrs = [i for i in sel_unspent if i.twmmid.type == 'non-mmgen']
		if non_mmaddrs and caller != 'txdo':
			msg(wmsg['non_mmgen_inputs'].format(', '.join(set(sorted([a.addr.hl() for a in non_mmaddrs])))))
			if not keypress_confirm('Accept?'):
				continue

		tx.copy_inputs_from_tw(sel_unspent)  # makes tx.inputs

		change_amt = tx.sum_inputs() - tx.send_amt - get_fee_from_estimate_or_user(tx)

		if change_amt >= 0:
			p = 'Transaction produces {} {} in change'.format(change_amt.hl(),g.coin)
			if opt.yes or keypress_confirm(p+'.  OK?',default_yes=True):
				if opt.yes: msg(p)
				return change_amt
		else:
			msg(wmsg['not_enough_btc'].format(abs(change_amt)))

def txcreate(cmd_args,do_info=False,caller='txcreate'):

	tx = MMGenTX()

	if opt.comment_file: tx.add_comment(opt.comment_file)

	c = bitcoin_connection()

	if not do_info: get_outputs_from_cmdline(cmd_args,tx)

	tw = MMGenTrackingWallet(minconf=opt.minconf)
	tw.view_and_sort(tx)
	tw.display_total()

	if do_info: sys.exit(0)

	tx.send_amt = tx.sum_outputs()

	msg('Total amount to spend: {}'.format(
		('Unknown','{} {}'.format(tx.send_amt.hl(),g.coin))[bool(tx.send_amt)]
	))

	change_amt = get_inputs_from_user(tw,tx,caller)

	if opt.rbf: tx.signal_for_rbf() # only after we have inputs

	chg_idx = tx.get_chg_output_idx()

	if change_amt == 0:
		msg('Warning: Change address will be deleted as transaction produces no change')
		tx.del_output(chg_idx)
	else:
		tx.update_output_amt(chg_idx,BTCAmt(change_amt))

	if not tx.send_amt:
		tx.send_amt = change_amt

	dmsg('tx: %s' % tx)

	if not opt.yes:
		tx.add_comment()   # edits an existing comment
	tx.create_raw(c)       # creates tx.hex, tx.txid

	tx.add_timestamp()
	tx.add_blockcount(c)
	tx.chain = g.chain

	assert tx.sum_inputs() - tx.sum_outputs() <= g.max_tx_fee

	qmsg('Transaction successfully created')

	dmsg('TX (final): %s' % tx)

	if not opt.yes:
		tx.view_with_prompt('View decoded transaction?')

	return tx

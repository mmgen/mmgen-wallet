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
from mmgen.term import get_char

pnm = g.proj_name

opts_data = {
	'desc':    'Create a BTC transaction with outputs to specified addresses',
	'usage':   '[opts]  <addr,amt> ... [change addr] [addr file] ...',
	'options': """
-h, --help            Print this help message
-c, --comment-file= f Source the transaction's comment from file 'f'
-C, --tx-confs=     c Estimated confirmations (default: {g.tx_confs})
-d, --outdir=       d Specify an alternate directory 'd' for output
-e, --echo-passphrase Print passphrase to screen when typing it
-f, --tx-fee=       f Transaction fee (default: {g.tx_fee} BTC (but see below))
-i, --info            Display unspent outputs and exit
-q, --quiet           Suppress warnings; overwrite files without
                      prompting
-v, --verbose         Produce more verbose output
""".format(g=g),
	'notes': """

Transaction inputs are chosen from a list of the user's unpent outputs
via an interactive menu.

If not specified by the user, transaction fees are calculated using
bitcoind's "estimatefee" function for the default (or user-specified)
number of confirmations.  Only if "estimatefee" fails is the default fee
of {g.tx_fee} BTC used.

Ages of transactions are approximate based on an average block creation
interval of {g.mins_per_block} minutes.

Addresses on the command line can be Bitcoin addresses or {pnm} addresses
of the form <seed ID>:<number>.

To send all inputs (minus TX fee) to a single output, specify one address
with no amount on the command line.
""".format(g=g,pnm=pnm)
}

wmsg = {
	'too_many_acct_addresses': """
ERROR: More than one address found for account: '%s'.
Your 'wallet.dat' file appears to have been altered by a non-{pnm} program.
Please restore your tracking wallet from a backup or create a new one and
re-import your addresses.
""".strip().format(pnm=pnm),
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
	'no_spendable_outputs': """
No spendable outputs found!  Import addresses with balances into your
watch-only wallet using '{pnm}-addrimport' and then re-run this program.
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

def format_unspent_outputs_for_printing(out,sort_info,total):

	pfs  = ' %-4s %-67s %-34s %-14s %-12s %-8s %-6s %s'
	pout = [pfs % ('Num','Tx ID,Vout','Address','{pnm} ID'.format(pnm=pnm),
		'Amount(BTC)','Conf.','Age(d)', 'Comment')]

	for n,i in enumerate(out):
		addr = '=' if i['skip'] == 'addr' and 'grouped' in sort_info else i['address']
		tx = ' ' * 63 + '=' \
			if i['skip'] == 'txid' and 'grouped' in sort_info else str(i['txid'])

		s = pfs % (str(n+1)+')', tx+','+str(i['vout']),addr,
				i['mmid'],i['amt'].strip(),i['confirmations'],i['days'],i['comment'])
		pout.append(s.rstrip())

	return \
'Unspent outputs ({} UTC)\nSort order: {}\n\n{}\n\nTotal BTC: {}\n'.format(
		make_timestr(), ' '.join(sort_info), '\n'.join(pout), total
	)


def sort_and_view(unspent):

	def s_amt(i):   return i['amount']
	def s_txid(i):  return '%s %03s' % (i['txid'],i['vout'])
	def s_addr(i):  return i['address']
	def s_age(i):   return i['confirmations']
	def s_mmgen(i):
		if i['mmid']:
			return '{}:{:>0{w}}'.format(
				*i['mmid'].split(':'), w=g.mmgen_idx_max_digits)
		else: return 'G' + i['comment']

	sort,group,show_days,show_mmaddr,reverse = 'age',False,False,True,True
	unspent.sort(key=s_age,reverse=reverse) # Reverse age sort by default

	total = trim_exponent(sum([i['amount'] for i in unspent]))
	max_acct_len = max([len(i['mmid']+' '+i['comment']) for i in unspent])

	hdr_fmt   = 'UNSPENT OUTPUTS (sort order: %s)  Total BTC: %s'
	options_msg = """
Sort options: [t]xid, [a]mount, a[d]dress, [A]ge, [r]everse, [M]mgen addr
Display options: show [D]ays, [g]roup, show [m]mgen addr, r[e]draw screen
""".strip()
	prompt = \
"('q' = quit sorting, 'p' = print to file, 'v' = pager view, 'w' = wide view): "

	mmid_w = max(len(i['mmid']) for i in unspent)
	from copy import deepcopy
	from mmgen.term import get_terminal_size

	written_to_file_msg = ''
	msg('')

	while True:
		cols = get_terminal_size()[0]
		if cols < g.min_screen_width:
			die(2,
	'{pnl}-txcreate requires a screen at least {w} characters wide'.format(
					pnl=pnm.lower(),w=g.min_screen_width))

		addr_w = min(34+((1+max_acct_len) if show_mmaddr else 0),cols-46)
		acct_w   = min(max_acct_len, max(24,int(addr_w-10)))
		btaddr_w = addr_w - acct_w - 1
		tx_w = max(11,min(64, cols-addr_w-32))
		txdots = ('','...')[tx_w < 64]
		fs = ' %-4s %-' + str(tx_w) + 's %-2s %-' + str(addr_w) + 's %-13s %-s'
		table_hdr = fs % ('Num','TX id  Vout','','Address','Amount (BTC)',
							('Conf.','Age(d)')[show_days])

		unsp = deepcopy(unspent)
		for i in unsp: i['skip'] = ''
		if group and (sort == 'address' or sort == 'txid'):
			for a,b in [(unsp[i],unsp[i+1]) for i in range(len(unsp)-1)]:
				if sort == 'address' and a['address'] == b['address']: b['skip'] = 'addr'
				elif sort == 'txid' and a['txid'] == b['txid']:        b['skip'] = 'txid'

		for i in unsp:
			amt = str(trim_exponent(i['amount']))
			lfill = 3 - len(amt.split('.')[0]) if '.' in amt else 3 - len(amt)
			i['amt'] = ' '*lfill + amt
			i['days'] = int(i['confirmations'] * g.mins_per_block / (60*24))
			i['age'] = i['days'] if show_days else i['confirmations']

			addr_disp = (i['address'],'|' + '.'*33)[i['skip']=='addr']
			mmid_disp = (i['mmid'],'.'*len(i['mmid']))[i['skip']=='addr']

			if show_mmaddr:
				dots = ('','..')[btaddr_w < len(i['address'])]
				i['addr'] = '%s%s %s' % (
					addr_disp[:btaddr_w-len(dots)],
					dots, (
					('{:<{w}} '.format(mmid_disp,w=mmid_w) if i['mmid'] else '')
						+ i['comment'])[:acct_w]
					)
			else:
				i['addr'] = addr_disp

			i['tx'] = ' ' * (tx_w-4) + '|...' if i['skip'] == 'txid' \
					else i['txid'][:tx_w-len(txdots)]+txdots

		sort_info = ([],['reverse'])[reverse]
		sort_info.append(sort if sort else 'unsorted')
		if group and (sort == 'address' or sort == 'txid'):
			sort_info.append('grouped')

		out  = [hdr_fmt % (' '.join(sort_info), total), table_hdr]
		out += [fs % (str(n+1)+')',i['tx'],i['vout'],i['addr'],i['amt'],i['age'])
					for n,i in enumerate(unsp)]

		msg('\n'.join(out) +'\n\n' + written_to_file_msg + options_msg)
		written_to_file_msg = ''

		skip_prompt = False

		while True:
			reply = get_char(prompt, immed_chars='atDdAMrgmeqpvw')

			if   reply == 'a': unspent.sort(key=s_amt);  sort = 'amount'
			elif reply == 't': unspent.sort(key=s_txid); sort = 'txid'
			elif reply == 'D': show_days = not show_days
			elif reply == 'd': unspent.sort(key=s_addr); sort = 'address'
			elif reply == 'A': unspent.sort(key=s_age);  sort = 'age'
			elif reply == 'M':
				unspent.sort(key=s_mmgen); sort = 'mmgen'
				show_mmaddr = True
			elif reply == 'r':
				unspent.reverse()
				reverse = not reverse
			elif reply == 'g': group = not group
			elif reply == 'm': show_mmaddr = not show_mmaddr
			elif reply == 'e': pass
			elif reply == 'q': pass
			elif reply == 'p':
				d = format_unspent_outputs_for_printing(unsp,sort_info,total)
				of = 'listunspent[%s].out' % ','.join(sort_info)
				write_data_to_file(of,d,'unspent outputs listing')
				written_to_file_msg = "Data written to '%s'\n\n" % of
			elif reply == 'v':
				do_pager('\n'.join(out))
				continue
			elif reply == 'w':
				data = format_unspent_outputs_for_printing(unsp,sort_info,total)
				do_pager(data)
				continue
			else:
				msg('\nInvalid input')
				continue

			break

		msg('\n')
		if reply == 'q': break

	return tuple(unspent)


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


def mmaddr2btcaddr_unspent(unspent,mmaddr):
	vmsg_r('Searching for {pnm} address {m} in wallet...'.format(pnm=pnm,m=mmaddr))
	m = [u for u in unspent if u['mmid'] == mmaddr]
	if len(m) == 0:
		vmsg('not found')
		return '',''
	elif len(m) > 1:
		die(2,wmsg['too_many_acct_addresses'] % acct)
	else:
		vmsg('success (%s)' % m[0].address)
		return m[0].address, m[0].comment


def mmaddr2btcaddr(c,mmaddr,ail_w,ail_f):

	# assume mmaddr has already been checked
	btcaddr = ail_w.mmaddr2btcaddr(mmaddr)

	if not btcaddr:
		if ail_f:
			btcaddr = ail_f.mmaddr2btcaddr(mmaddr)
			if btcaddr:
				msg(wmsg['addr_in_addrfile_only'].format(mmgenaddr=mmaddr))
				if not keypress_confirm('Continue anyway?'):
					sys.exit(1)
			else:
				die(2,wmsg['addr_not_found'].format(pnm=pnm,mmgenaddr=mmaddr))
		else:
			die(2,wmsg['addr_not_found_no_addrfile'].format(pnm=pnm,mmgenaddr=mmaddr))

	return btcaddr


def make_b2m_map(inputs_data,tx_out,ail_w,ail_f):
	d = dict([(d['address'], (d['mmid'],d['comment']))
				for d in inputs_data if d['mmid']])
	d.update(ail_w.make_reverse_dict(tx_out.keys()))
	d.update(ail_f.make_reverse_dict(tx_out.keys()))
	return d

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

# see: https://bitcoin.stackexchange.com/questions/1195/how-to-calculate-transaction-size-before-sending
def get_tx_size_and_fee(inputs,outputs):
	tx_size = len(inputs)*180 + len(outputs)*34 + 10
	if fee_estimate:
		ftype,fee = 'Calculated','{:.8f}'.format(fee_estimate * tx_size / 1024)
	else:
		ftype,fee = 'User-selected',opt.tx_fee
	if not keypress_confirm('{} TX fee: {} BTC.  OK?'.format(ftype,fee),default_yes=True):
		while True:
			ufee = my_raw_input('Enter transaction fee: ')
			if normalize_btc_amt(ufee):
				if Decimal(ufee) > g.max_tx_fee:
					msg('{} BTC: fee too large (maximum fee: {} BTC)'.format(ufee,g.max_tx_fee))
				else:
					fee = ufee
					break
	vmsg('Inputs:{}  Outputs:{}  TX size:{}'.format(len(sel_unspent),len(tx_out),tx_size))
	vmsg('Fee estimate: {} (1024 bytes, {} confs)'.format(fee_estimate,opt.tx_confs))
	vmsg('TX fee:       {}'.format(fee))
	return tx_size,normalize_btc_amt(fee)

# main(): execution begins here

cmd_args = opts.init(opts_data)

if opt.comment_file:
	comment = get_tx_comment_from_file(opt.comment_file)

c = bitcoin_connection()

if not opt.info:
	do_license_msg(immed=True)

	tx_out,change_addr = {},''

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
				btcaddr = a1
			elif is_mmgen_addr(a1):
				btcaddr = mmaddr2btcaddr(c,a1,ail_w,ail_f)
			else:
				die(2,"%s: unrecognized subargument in argument '%s'" % (a1,a))

			ret = normalize_btc_amt(a2)
			if ret:
				tx_out[btcaddr] = ret
			else:
				die(2,"%s: invalid amount in argument '%s'" % (a2,a))
		elif is_mmgen_addr(a) or is_btc_addr(a):
			if change_addr:
				die(2,'ERROR: More than one change address specified: %s, %s' %
						(change_addr, a))
			change_addr = a if is_btc_addr(a) else mmaddr2btcaddr(c,a,ail_w,ail_f)
			tx_out[change_addr] = 0
		else:
			die(2,'%s: unrecognized argument' % a)

	if not tx_out:
		die(2,'At least one output must be specified on the command line')

	if opt.tx_fee > g.max_tx_fee:
		die(2,'Transaction fee too large: %s > %s' % (opt.tx_fee,g.max_tx_fee))

	fee_estimate = get_fee_estimate()


if g.bogus_wallet_data:  # for debugging purposes only
	us = eval(get_data_from_file(g.bogus_wallet_data))
else:
	us = c.listunspent()
#	write_data_to_file('bogus_unspent.json', repr(us), 'bogus unspent data')
#	sys.exit()

if not us:
	die(2,wmsg['no_spendable_outputs'])
for o in us:
	o['mmid'],o['comment'] = parse_mmgen_label(o['account'])
	del o['account']
unspent = sort_and_view(us)

total = trim_exponent(sum([i['amount'] for i in unspent]))

msg('Total unspent: %s BTC (%s outputs)' % (total, len(unspent)))
if opt.info: sys.exit()

send_amt = sum([tx_out[i] for i in tx_out.keys()])
msg('Total amount to spend: %s' % ('%s BTC'%send_amt,'Unknown')[bool(send_amt)])

while True:
	sel_nums = select_outputs(unspent,
			'Enter a range or space-separated list of outputs to spend: ')
	msg('Selected output%s: %s' % (
			('s','')[len(sel_nums)==1],
			' '.join(str(i) for i in sel_nums)
		))
	sel_unspent = [unspent[i-1] for i in sel_nums]

	mmaddrs = set([i['mmid'] for i in sel_unspent])

	if '' in mmaddrs and len(mmaddrs) > 1:
		mmaddrs.discard('')
		msg(wmsg['mixed_inputs'] % ', '.join(sorted(mmaddrs)))
		if not keypress_confirm('Accept?'):
			continue

	total_in = trim_exponent(sum([i['amount'] for i in sel_unspent]))
	tx_size,tx_fee = get_tx_size_and_fee(sel_unspent,tx_out)
	change = trim_exponent(total_in - (send_amt + tx_fee))

	if change >= 0:
		prompt = 'Transaction produces %s BTC in change.  OK?' % change
		if keypress_confirm(prompt,default_yes=True):
			break
	else:
		msg(wmsg['not_enough_btc'] % change)

if change > 0 and not change_addr:
	die(2,wmsg['throwaway_change'] % change)

if change_addr in tx_out and not change:
	msg('Warning: Change address will be unused as transaction produces no change')
	del tx_out[change_addr]

for k,v in tx_out.items(): tx_out[k] = float(v)

if change > 0: tx_out[change_addr] = float(change)

tx_in = [{'txid':i['txid'], 'vout':i['vout']} for i in sel_unspent]

dmsg('tx_in:  %s\ntx_out: %s' % (repr(tx_in),repr(tx_out)))

if opt.comment_file:
	if keypress_confirm('Edit comment?',False):
		comment = get_tx_comment_from_user(comment)
else:
	if keypress_confirm('Add a comment to transaction?',False):
		comment = get_tx_comment_from_user()
	else: comment = False

tx_hex = c.createrawtransaction(tx_in,tx_out)
qmsg('Transaction successfully created')

amt = send_amt or change
tx_id = make_chksum_6(unhexlify(tx_hex)).upper()
metadata = tx_id, amt, make_timestamp()

b2m_map = make_b2m_map(sel_unspent,tx_out,ail_w,ail_f)

prompt_and_view_tx_data(c,'View decoded transaction?',
		sel_unspent,tx_hex,b2m_map,comment,metadata)

outfile = 'tx_%s[%s].%s' % (tx_id,amt,g.rawtx_ext)
data = make_tx_data('{} {} {}'.format(*metadata),
			tx_hex,sel_unspent,b2m_map,comment)
write_data_to_file(outfile,data,'transaction',ask_write_default_yes=False)

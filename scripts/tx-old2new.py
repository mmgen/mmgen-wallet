#!/usr/bin/env python

import sys,os
repo_root = os.path.split(os.path.abspath(os.path.dirname(sys.argv[0])))[0]
sys.path = [repo_root] + sys.path

from mmgen.common import *
from mmgen.tx import *

opts_data = lambda: {
	'desc':    "Convert MMGen transaction file from old format to new format",
	'usage':   "<tx file>",
	'options': """
-h, --help    Print this help message
-S, --stdout  Write data to STDOUT instead of file
"""
}

cmd_args = opts.init(opts_data)

if len(cmd_args) != 1: opts.usage()
def parse_tx_file(infile):

	err_fmt = 'Invalid {} in transaction file'
	tx_data = get_lines_from_file(infile)

	try:
		err_str = 'number of lines'
		assert len(tx_data) in (4,5)
		if len(tx_data) == 5:
			metadata,tx_hex,inputs,outputs,comment = tx_data
		elif len(tx_data) == 4:
			metadata,tx_hex,inputs,outputs = tx_data
			comment = ''
		err_str = 'metadata'
		assert len(metadata.split()) == 3
		err_str = 'hex data'
		unhexlify(tx_hex)
		err_str = 'inputs data'
		inputs = eval(inputs)
		err_str = 'btc-to-mmgen address map data'
		outputs = eval(outputs)
		if comment:
			from mmgen.bitcoin import b58decode
			comment = b58decode(comment)
			if comment == False:
				err_str = 'encoded comment (not base58)'
			else:
				err_str = 'comment'
				comment = MMGenTXLabel(comment)
	except:
		die(2,err_fmt.format(err_str))
	else:
		return metadata.split(),tx_hex,inputs,outputs,comment

def find_block_by_time(c,timestamp):
	secs = decode_timestamp(timestamp)
	block_num = c.getblockcount()
#	print 'secs:',secs, 'last block:',last_block
	top,bot = block_num,0
	m = 'Searching for block'
	msg_r(m)
	for i in range(40):
		msg_r('.')
		bhash = c.getblockhash(block_num)
		block = c.getblock(bhash)
#		print 'block_num:',block_num, 'mediantime:',block['mediantime'], 'target:',secs
		cur_secs = block['mediantime']
		if cur_secs > secs:
			top = block_num
		else:
			bot = block_num
		block_num = (top + bot) / 2
		if top - bot < 2:
			msg('\nFound: %s ' % block_num)
			break

	return block_num

tx = MMGenTX()

metadata,tx.hex,inputs,b2m_map,tx.label = parse_tx_file(cmd_args[0])
tx.txid,send_amt,tx.timestamp = metadata
tx.send_amt = Decimal(send_amt)

g.testnet = False
g.rpc_host = 'localhost'
c = bitcoin_connection()

for i in inputs:
	if not 'mmid' in i and 'account' in i:
		from mmgen.tw import parse_tw_acct_label
		a,b = parse_tw_acct_label(i['account'])
		if a:
			i['mmid'] = a.decode('utf8')
			if b: i['comment'] = b.decode('utf8')

tx.inputs = tx.decode_io_oldfmt(inputs)

if tx.marked_signed(c):
	msg('Transaction is signed')

dec_tx = c.decoderawtransaction(tx.hex)
tx.outputs = MMGenList(MMGenTX.MMGenTxOutput(addr=i['scriptPubKey']['addresses'][0],amt=i['value'])
				for i in dec_tx['vout'])
for e in tx.outputs:
	if e.addr in b2m_map:
		f = b2m_map[e.addr]
		e.mmid = f[0]
		if f[1]: e.label = f[1].decode('utf8')
	else:
		for f in tx.inputs:
			if e.addr == f.addr and f.mmid:
				e.mmid = f.mmid
				if f.label: e.label = f.label.decode('utf8')

tx.blockcount = find_block_by_time(c,tx.timestamp)
tx.write_to_file(ask_tty=False)

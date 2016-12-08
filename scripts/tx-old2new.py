#!/usr/bin/env python

import sys,os
repo_root = os.path.split(os.path.abspath(os.path.dirname(sys.argv[0])))[0]
sys.path = [repo_root] + sys.path

from mmgen.common import *

from mmgen.tool import *
from mmgen.tx import *
from mmgen.bitcoin import *
from mmgen.obj import MMGenTXLabel
from mmgen.seed import *
from mmgen.term import do_pager

help_data = {
	'desc':    "Convert MMGen transaction file from old format to new format",
	'usage':   "<tx file>",
	'options': """
-h, --help    Print this help message
-S, --stdout  Write data to STDOUT instead of file
"""
}

import mmgen.opts
cmd_args = opts.init(help_data)

if len(cmd_args) != 1: opts.usage()
def parse_tx_file(infile):

	err_str,err_fmt = '','Invalid %s in transaction file'
	tx_data = get_lines_from_file(infile)

	if len(tx_data) == 5:
		metadata,tx_hex,inputs_data,outputs_data,comment = tx_data
	elif len(tx_data) == 4:
		metadata,tx_hex,inputs_data,outputs_data = tx_data
		comment = ''
	else:
		err_str = 'number of lines'

	if not err_str:
		if len(metadata.split()) != 3:
			err_str = 'metadata'
		else:
			try: unhexlify(tx_hex)
			except: err_str = 'hex data'
			else:
				try: inputs_data = eval(inputs_data)
				except: err_str = 'inputs data'
				else:
					try: outputs_data = eval(outputs_data)
					except: err_str = 'btc-to-mmgen address map data'
					else:
						if comment:
							from mmgen.bitcoin import b58decode
							comment = b58decode(comment)
							if comment == False:
								err_str = 'encoded comment (not base58)'
							else:
								try:
									comment = MMGenTXLabel(comment)
								except:
									err_str = 'comment'

	if err_str:
		msg(err_fmt % err_str)
		sys.exit(2)
	else:
		return metadata.split(),tx_hex,inputs_data,outputs_data,comment

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

[tx.txid,send_amt,tx.timestamp],tx.hex,inputs,b2m_map,tx.label = parse_tx_file(cmd_args[0])
tx.send_amt = Decimal(send_amt)

g.testnet = False
g.rpc_host = 'localhost'
c = bitcoin_connection()

# attrs = 'txid','vout','amt','comment','mmid','addr','wif'
#pp_msg(inputs)
for i in inputs:
	if not 'mmid' in i and 'account' in i:
		from mmgen.tw import parse_tw_acct_label
		a,b = parse_tw_acct_label(i['account'])
		if a:
			i['mmid'] = a.decode('utf8')
			if b: i['comment'] = b.decode('utf8')

#pp_msg(inputs)
tx.inputs = tx.decode_io_oldfmt(inputs)

if tx.check_signed(c):
	msg('Transaction is signed')

dec_tx = c.decoderawtransaction(tx.hex)
tx.outputs = [MMGenTxOutput(addr=i['scriptPubKey']['addresses'][0],amt=i['value'])
				for i in dec_tx['vout']]

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
#for i in tx.inputs: print i
#for i in tx.outputs: print i
#die(1,'')
tx.blockcount = find_block_by_time(c,tx.timestamp)

tx.write_to_file(ask_tty=False)

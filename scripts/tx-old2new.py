#!/usr/bin/env python

import sys,os
repo_root = os.path.split(os.path.abspath(os.path.dirname(sys.argv[0])))[0]
sys.path = [repo_root] + sys.path

from mmgen.common import *

from mmgen.tool import *
from mmgen.tx import *
from mmgen.bitcoin import *
from mmgen.seed import *
from mmgen.term import do_pager

help_data = {
	'desc':    "Convert MMGen transaction file from old format to new format",
	'usage':   "<tx file>",
	'options': """
-h, --help    Print this help message
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
								if is_valid_tx_comment(comment):
									comment = comment.decode('utf8')
								else:
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

[tx.txid,send_amt,tx.timestamp],tx.hex,inputs,b2m_map,tx.comment = parse_tx_file(cmd_args[0])
tx.send_amt = Decimal(send_amt)

c = bitcoin_connection()

tx.copy_inputs(inputs)
if tx.check_signed(c):
	msg('Transaction is signed')

dec_tx = c.decoderawtransaction(tx.hex)
tx.outputs = dict([(i['scriptPubKey']['addresses'][0],(i['value'],)) for i in dec_tx['vout']])

tx.blockcount = find_block_by_time(c,tx.timestamp)

for k in tx.outputs:
	if k in b2m_map:
		tx.outputs[k] += b2m_map[k]

tx.write_to_file(ask_write=False)

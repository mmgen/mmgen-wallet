#!/usr/bin/env python
# Convert MMGen 'v1' transaction file (extension '.raw' or '.sig')
# to MMGen 'v3' ('.rawtx' or '.sigtx' + amounts as strings)

import sys,os
repo_root = os.path.split(os.path.abspath(os.path.dirname(sys.argv[0])))[0]
sys.path = [repo_root] + sys.path

from mmgen.common import *

opts_data = lambda: {
	'desc':    "Convert MMGen transaction file from v1 format to v3 format",
	'usage':   "<tx file>",
	'options': """
-h, --help     Print this help message
-d, --outdir=d Output files to directory 'd' instead of working dir
-q, --quiet    Write (and overwrite) files without prompting
-S, --stdout   Write data to STDOUT instead of file
"""
}

cmd_args = opts.init(opts_data)

from mmgen.tx import *

if len(cmd_args) != 1: opts.usage()
def parse_tx_file(infile):
	from ast import literal_eval

	def eval_io_data(raw_data,desc):
		import re
		d = literal_eval(re.sub(r"[A-Za-z]+?\(('.+?')\)",r'\1',raw_data))
		assert type(d) == list,'{} data not a list!'.format(desc)
		assert len(d),'no {}!'.format(desc)
		for e in d: e['amount'] = g.proto.coin_amt(e['amount'])
		return d

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
		inputs = eval_io_data(inputs,'inputs')
		err_str = 'btc-to-mmgen address map data'
		outputs = literal_eval(outputs)
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

def find_block_by_time(timestamp):
	secs = decode_timestamp(timestamp)
	block_num = g.rpch.getblockcount()
#	print 'secs:',secs, 'last block:',last_block
	top,bot = block_num,0
	m = 'Searching for block'
	msg_r(m)
	for i in range(40):
		msg_r('.')
		bhash = g.rpch.getblockhash(block_num)
		block = g.rpch.getblock(bhash)
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

metadata,tx.hex,inputs,outputs,tx.label = parse_tx_file(cmd_args[0])
tx.txid,send_amt,tx.timestamp = metadata
tx.send_amt = Decimal(send_amt)

g.testnet = False
g.rpc_host = 'localhost'
rpc_init()

for i in inputs:
	if not 'mmid' in i and 'account' in i:
		lbl = TwLabel(i['account'])
		i['mmid'] = lbl.mmid
		i['comment'] = lbl.comment

tx.inputs = tx.MMGenTxInputList(tx.decode_io_oldfmt(inputs))

if tx.marked_signed():
	msg('Transaction is signed')

dec_tx = g.rpch.decoderawtransaction(tx.hex)
tx.outputs = tx.MMGenTxOutputList(
				MMGenTX.MMGenTxOutput(addr=i['scriptPubKey']['addresses'][0],
						amt=g.proto.coin_amt(i['value']))
			for i in dec_tx['vout'])
for e in tx.outputs:
	if e.addr in outputs:
		f = outputs[e.addr]
		e.mmid = f[0]
		if f[1]: e.label = f[1].decode('utf8')
	else:
		for f in tx.inputs:
			if e.addr == f.addr and f.mmid:
				e.mmid = f.mmid
				if f.label: e.label = f.label.decode('utf8')

tx.blockcount = find_block_by_time(tx.timestamp)
tx.write_to_file(ask_tty=False,ask_overwrite=not opt.quiet,ask_write=not opt.quiet)

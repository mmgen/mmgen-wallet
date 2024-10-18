#!/usr/bin/env python3

"""
test.modtest_d.ut_devtools: devtools unit tests for the MMGen suite
"""

import os, json
from mmgen.util import msg
from mmgen.devtools import print_diff, get_ndiff, print_stack_trace, pmsg_r, pmsg, Pmsg
from . import unit_tests_base

textA = """
def main():
	a = 1
	b = 2
	c = 3
""".lstrip()

textB = """
def main():
	a = 1
	b = 0
	c = 3
""".lstrip()

with open('test/ref/ethereum/tracking-wallet-v1.json') as fh:
	jsonA = fh.read()
dataB = json.loads(jsonA)
dataB['coin'] = 'ETC'
jsonB = json.dumps(dataB)

text_data = (
	(textA, textB, 'a/main.py',   'b/main.py',   False, 'text: one line difference'),
	('',    textB, 'a/main.py',   'b/main.py',   False, 'text: first file empty'),
	(textA, textA, 'a/main.py',   'b/main.py',   False, 'text: identical files'),
	('',    '',    'a/empty.txt', 'b/empty.txt', False, 'text: empty files'),
)

json_data = (
	(jsonA, jsonB, 'a/data.json', 'b/data.json', True,  'json: one difference'),
	('{}',  jsonB, 'a/data.json', 'b/data.json', True,  'json: first file empty'),
	(jsonA, jsonA, 'a/data.json', 'b/data.json', True,  'json: identical files'),
	('{}',  '{}',  'a/data.json', 'b/data.json', True,  'json: empty files'),
)

def print_hdr(hdr):
	print('{a} {b} {c}'.format(
		a = '-' * ((78 - len(hdr))//2),
		b = hdr,
		c = '-' * ((78 - len(hdr))//2 + (len(hdr) % 2))))

# TODO: add data checks
class unit_tests(unit_tests_base):

	silence_output = True

	def _post_subtest(self, name, subname, ut):
		print('-' * 80 + '\n')

	def diff(self, name, ut):
		for data in text_data + json_data:
			print_hdr(data[-1])
			print_diff(*data[:-1])
		return True

	def ndiff(self, name, ut):
		for data in text_data:
			print_hdr(data[-1])
			print('\n'.join(get_ndiff(*data[:2])))
		return True

	def stack_trace(self, name, ut):
		print_hdr('stack trace')
		print_stack_trace('Test', fh_list=[open(os.devnull, 'w')], trim=0)
		return True

	def obj_pmsg(self, name, ut):
		from mmgen.protocol import init_proto
		from mmgen.seed import Seed
		from mmgen.addrlist import AddrList
		from ..include.common import cfg
		print_hdr('MMGenObject.pmsg()')
		AddrList(
			cfg         = cfg,
			proto       = init_proto(cfg, 'btc'),
			seed        = Seed(cfg, seed_bin=bytes.fromhex('bead'*16)),
			addr_idxs   = '1',
			mmtype      = 'B',
			skip_chksum = True).pmsg(color='green')
		return True

	def pmsg(self, name, ut):
		colors = (None, 'red', 'green', 'yellow', 'blue', 'purple')

		msg('\npmsg_r():')
		for color in colors:
			pmsg_r({'color':color}, color=color)

		msg('\n\npmsg():')
		for color in colors:
			pmsg({'color':color}, color=color)

		msg('\nPmsg():')
		for color in colors:
			Pmsg({'color':color}, color=color)

		return True

#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
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
test/gentest.py: Cryptocoin key/address generation tests for the MMGen suite
"""

import sys, os, time

try:
	from include import test_init
except ImportError:
	from test.include import test_init

# Import these _after_ local path's been added to sys.path
from mmgen.cfg import gc, Config
from mmgen.color import green, red, purple
from mmgen.util import msg, ymsg, capfirst, is_int, die

results_file = 'gentest.out.json'

rounds = 100
opts_data = {
	'text': {
		'desc': 'Test key/address generation of the MMGen suite in various ways',
		'usage':'[options] <spec> <rounds | dump file>',
		'options': """
-h, --help         Print this help message
--, --longhelp     Print help message for long (global) options
-a, --all-coins    Test all coins supported by specified external tool
-k, --use-internal-keccak-module Force use of the internal keccak module
-q, --quiet        Produce quieter output
-s, --save-results Save output of external tool in Compare test to
                   {rf!r}
-t, --type=t       Specify address type (e.g. 'compressed', 'segwit',
                   'zcash_z', 'bech32')
-v, --verbose      Produce more verbose output
""",
	'notes': """
TEST TYPES:

  Compare: {prog} A:B <rounds>  (compare address generators A and B)
  Speed:   {prog} A <rounds>    (test speed of generator A)
  Dump:    {prog} A <dump file> (compare generator A to wallet dump)

  where:

      A and B are keygen backend numbers ('1' being the default); or
      B is the name of an external tool (see below) or 'ext'.

      If B is 'ext', the external tool will be chosen automatically.

  For the Compare test, A may be 'all' to test all backends for the current
  coin/address type combination.

EXAMPLES:

  Compare addresses generated by 'libsecp256k1' and 'python-ecdsa' backends,
  with 100 random rounds plus private-key edge cases:
  $ {prog} 1:2 100

  Compare Segwit addresses from default 'libsecp256k1' backend to 'pycoin'
  library for all supported coins, 100 rounds + edge cases:
  $ {prog} --all-coins --type=segwit 1:pycoin 100

  Compare addresses from 'python-ecdsa' backend to output of 'keyconv' tool
  for all supported coins, 100 rounds + edge cases:
  $ {prog} --all-coins --type=compressed 2:keyconv 100

  Compare bech32 addrs from 'libsecp256k1' backend to Bitcoin Core wallet
  dump:
  $ {prog} --type=bech32 1 bech32wallet.dump

  Compare addresses from Monero 'ed25519ll' backend to output of default
  external tool, 10 rounds + edge cases:
  $ {prog} --coin=xmr 3:ext 10

  Test the speed of default Monero 'nacl' backend, 10,000 rounds:
  $ test/gentest.py --coin=xmr 1 10000

  Same for Zcash:
  $ test/gentest.py --coin=zec --type=zcash_z 1 10000

  Test all configured Monero backends against the 'monero-python' library, 3 rounds
  + edge cases:
  $ test/gentest.py --coin=xmr all:monero-python 3

  Test 'nacl' and 'ed25519ll_djbec' backends against each other, 10,000 rounds
  + edge cases:
  $ test/gentest.py --coin=xmr 1:2 10000

SUPPORTED EXTERNAL TOOLS:

  + eth-keys (for ETH, ETC)
	https://github.com/ethereum/eth-keys

  + zcash-mini (for Zcash-Z addresses and view keys)
    https://github.com/FiloSottile/zcash-mini

  + monero-python (for Monero addresses and view keys)
    https://github.com/monero-ecosystem/monero-python

  + pycoin (for supported coins)
    https://github.com/richardkiss/pycoin

  + keyconv (for supported coins)
    https://github.com/exploitagency/vanitygen-plus
    ('keyconv' does not generate Segwit addresses)
"""
	},
	'code': {
		'options': lambda s: s.format(
			rf   = results_file,
		),
		'notes': lambda s: s.format(
			prog = 'test/gentest.py',
			pnm  = gc.proj_name,
			snum = rounds)
	}
}

def get_cmd_output(cmd, input=None):
	return run(cmd, input=input, stdout=PIPE, stderr=DEVNULL).stdout.decode().splitlines()

saved_results = {}

class GenTool:

	def __init__(self, proto, addr_type):
		self.proto = proto
		self.addr_type = addr_type
		self.data = {}

	def __del__(self):
		if cfg.save_results:
			key = f'{self.proto.coin}-{self.proto.network}-{self.addr_type.name}-{self.desc}'.lower()
			saved_results[key] = {k.hex():v._asdict() for k, v in self.data.items()}

	def run_tool(self, sec, cache_data):
		vcoin = 'BTC' if self.proto.coin == 'BCH' else self.proto.coin
		key = sec.orig_bytes
		if key in self.data:
			return self.data[key]
		else:
			ret = self.run(sec, vcoin)
			if cache_data:
				self.data[key] = sd(**{'reduced':sec.hex()}, **ret._asdict())
			return ret

class GenToolEth_keys(GenTool):
	desc = 'eth-keys'

	def __init__(self, *args, **kwargs):
		from eth_keys import keys
		self.keys = keys
		super().__init__(*args, **kwargs)

	def run(self, sec, vcoin):
		sk = self.keys.PrivateKey(sec)
		return gtr(str(sk)[2:], sk.public_key.to_address()[2:], None)

class GenToolKeyconv(GenTool):
	desc = 'keyconv'
	def run(self, sec, vcoin):
		o = get_cmd_output(['keyconv', '-C', vcoin, sec.wif])
		return gtr(
			o[1].split()[1],
			o[0].split()[1],
			None)

class GenToolZcash_mini(GenTool):
	desc = 'zcash-mini'
	def run(self, sec, vcoin):
		o = get_cmd_output(['zcash-mini', '-key', '-simple'], input=(sec.wif+'\n').encode())
		return gtr(o[1], o[0], o[-1])

class GenToolPycoin(GenTool):
	"""
	pycoin/networks/all.py pycoin/networks/legacy_networks.py
	"""
	desc = 'pycoin'
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		try:
			from pycoin.networks.registry import network_for_netcode
		except ImportError as e:
			raise ImportError(
				f'{e}\nUnable to import pycoin.networks.registry. Is pycoin installed on your system?') from e
		self.nfnc = network_for_netcode

	def run(self, sec, vcoin):
		if self.proto.testnet:
			vcoin = cinfo.external_tests['testnet']['pycoin'][vcoin]
		network = self.nfnc(vcoin)
		key = network.keys.private(
			secret_exponent = int(sec.hex(), 16),
			is_compressed = self.addr_type.name != 'legacy')
		if key is None:
			die(1, f'can’t parse {sec.hex()}')
		if self.addr_type.name in ('segwit', 'bech32'):
			hash160_c = key.hash160(is_compressed=True)
			if self.addr_type.name == 'segwit':
				p2sh_script = network.contract.for_p2pkh_wit(hash160_c)
				addr = network.address.for_p2s(p2sh_script)
			else:
				addr = network.address.for_p2pkh_wit(hash160_c)
		else:
			addr = key.address()
		return gtr(key.wif(), addr, None)

class GenToolMonero_python(GenTool):
	desc = 'monero-python'

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		try:
			from monero.seed import Seed
		except ImportError as e:
			raise ImportError(
				f'{e}\nUnable to import monero-python. Is monero-python installed on your system?') from e
		self.Seed = Seed

	def run(self, sec, vcoin):
		seed = self.Seed(sec.orig_bytes.hex())
		sk = seed.secret_spend_key()
		vk = seed.secret_view_key()
		addr = seed.public_address()
		return gtr(sk, addr, vk)

def find_or_check_tool(proto, addr_type, toolname):

	ext_progs = list(cinfo.external_tests[proto.network])

	if toolname not in ext_progs + ['ext']:
		die(1, f'{toolname!r}: unsupported tool for network {proto.network}')

	if cfg.all_coins and toolname == 'ext':
		die(1, "'--all-coins' must be combined with a specific external testing tool")
	else:
		tool = cinfo.get_test_support(
			proto.coin,
			addr_type.name,
			proto.network,
			verbose = not cfg.quiet,
			toolname = toolname if toolname != 'ext' else None)
		if tool and toolname in ext_progs and toolname != tool:
			sys.exit(3)
		if tool is None:
			return None
		return tool

def test_equal(desc, a_val, b_val, in_bytes, sec, wif, a_desc, b_desc):
	if a_val != b_val:
		fs = """
  {i:{w}}: {}
  {s:{w}}: {}
  {W:{w}}: {}
  {a:{w}}: {}
  {b:{w}}: {}
			"""
		die(3,
			red('\nERROR: {} do not match!').format(desc)
			+ fs.format(
				in_bytes.hex(), sec, wif, a_val, b_val,
				i='input', s='sec key', W='WIF key', a=a_desc, b=b_desc,
				w=max(len(e) for e in (a_desc, b_desc)) + 1
		).rstrip())

def do_ab_test(proto, scfg, addr_type, gen1, kg2, ag, tool, cache_data):

	def do_ab_inner(n, trounds, in_bytes):
		global last_t
		if cfg.verbose or time.time() - last_t >= 0.1:
			qmsg_r(f'\rRound {i+1}/{trounds} ')
			last_t = time.time()
		sec = PrivKey(proto, in_bytes, compressed=addr_type.compressed, pubkey_type=addr_type.pubkey_type)
		data = kg1.gen_data(sec)
		addr1 = ag.to_addr(data)
		view_pref = 1 if proto.coin == 'BCH' else 0
		tinfo = (in_bytes, sec, sec.wif, type(kg1).__name__, type(kg2).__name__ if kg2 else tool.desc)

		def do_msg():
			if cfg.verbose:
				msg(fs.format(b=in_bytes.hex(), r=sec.hex(), k=sec.wif, v=vk2, a=addr1))

		if tool:
			def run_tool():
				o = tool.run_tool(sec, cache_data)
				test_equal('WIF keys', sec.wif, o.wif, *tinfo)
				test_equal('addresses', addr1.views[view_pref], o.addr, *tinfo)
				if o.viewkey:
					test_equal('view keys', ag.to_viewkey(data), o.viewkey, *tinfo)
				return o.viewkey
			vk2 = run_tool()
			do_msg()
		else:
			test_equal('addresses', addr1.views[view_pref], ag.to_addr(kg2.gen_data(sec)), *tinfo)
			vk2 = None
			do_msg()

		qmsg_r(f'\rRound {n+1}/{trounds} ')

	def get_randbytes():
		if tool and len(tool.data) > len(edgecase_sks):
			yield from tuple(tool.data)[len(edgecase_sks):]
		else:
			for _ in range(scfg.rounds):
				yield getrand(32)

	kg1 = KeyGenerator(cfg, proto, addr_type.pubkey_type, backend=gen1)
	if type(kg1) == type(kg2):
		die(4, 'Key generators are the same!')

	e = cinfo.get_entry(proto.coin, proto.network)
	qmsg(green("Comparing address generators '{A}' and '{B}' for {N} {c} ({n}), addrtype {a!r}".format(
		A = type(kg1).__name__.replace('_', '-'),
		B = type(kg2).__name__.replace('_', '-') if kg2 else tool.desc,
		N = proto.network,
		c = proto.coin,
		n = e.name if e else '---',
		a = addr_type.name)))

	global last_t
	last_t = time.time()

	fs  = (
		'\ninput:    {b}' +
		'\nreduced:  {r}' +
		'\n{:9} {{k}}'.format(addr_type.wif_label+':') +
		('\nviewkey:  {v}' if 'viewkey' in addr_type.extra_attrs else '') +
		'\naddr:     {a}\n')

	group_order = CoinProtocol.Secp256k1.secp256k1_group_order

	# test some important private key edge cases:
	edgecase_sks = (
		bytes([0x00]*31 + [0x01]), # min
		bytes([0xff]*32),          # max
		bytes([0x0f] + [0xff]*31), # produces same key as above for zcash-z
		int.to_bytes(group_order + 1, 32, 'big'), # bitcoin will reduce
		int.to_bytes(group_order - 1, 32, 'big'), # bitcoin will not reduce
		bytes([0x00]*31 + [0xff]), # monero will reduce
		bytes([0xff]*31 + [0x0f]), # monero will not reduce
		bytes.fromhex('deadbeef'*8),
	)

	qmsg(purple('edge cases:'))
	for i, privbytes in enumerate(edgecase_sks):
		do_ab_inner(i, len(edgecase_sks), privbytes)
	qmsg(green('\rOK            ' if cfg.verbose else 'OK'))

	qmsg(purple('random input:'))
	for i, privbytes in enumerate(get_randbytes()):
		do_ab_inner(i, scfg.rounds, privbytes)
	qmsg(green('\rOK            ' if cfg.verbose else 'OK'))

def init_tool(proto, addr_type, toolname):
	return globals()['GenTool'+capfirst(toolname.replace('-', '_'))](proto, addr_type)

def ab_test(proto, scfg):

	addr_type = MMGenAddrType(proto=proto, id_str=cfg.type or proto.dfl_mmtype)

	if scfg.gen2:
		assert scfg.gen1 != 'all', "'all' must be used only with external tool"
		kg2 = KeyGenerator(cfg, proto, addr_type.pubkey_type, backend=scfg.gen2)
		tool = None
	else:
		toolname = find_or_check_tool(proto, addr_type, scfg.tool)
		if toolname is None:
			ymsg(f'Warning: skipping tool {scfg.tool!r} for {proto.coin} {addr_type.name}')
			return
		tool = init_tool(proto, addr_type, toolname)
		kg2 = None

	ag = AddrGenerator(cfg, proto, addr_type)

	if scfg.all_backends: # check all backends against external tool
		for n in range(len(get_backends(addr_type.pubkey_type))):
			do_ab_test(
					proto,
					scfg,
					addr_type,
					gen1       = n+1,
					kg2        = kg2,
					ag         = ag,
					tool       = tool,
					cache_data = scfg.rounds < 1000 and not n)
	else:                # check specific backend against external tool or another backend
		do_ab_test(
				proto,
				scfg,
				addr_type,
				gen1       = scfg.gen1,
				kg2        = kg2,
				ag         = ag,
				tool       = tool,
				cache_data = False)

def speed_test(proto, kg, ag, rounds):
	qmsg(green('Testing speed of address generator {!r} for coin {}'.format(
		type(kg).__name__,
		proto.coin)))
	from struct import pack
	seed = getrand(28)
	qmsg('Incrementing key with each round')
	qmsg('Starting key: {}'.format((seed + pack('I', 0)).hex()))
	start = last_t = time.time()

	for i in range(rounds):
		if time.time() - last_t >= 0.1:
			qmsg_r(f'\rRound {i+1}/{rounds} ')
			last_t = time.time()
		sec = PrivKey(proto, seed+pack('I', i), compressed=ag.compressed, pubkey_type=ag.pubkey_type)
		addr = ag.to_addr(kg.gen_data(sec))
		vmsg(f'\nkey:  {sec.wif}\naddr: {addr}\n')
	qmsg(
		f'\rRound {i+1}/{rounds} ' +
		f'\n{rounds} addresses generated' +
		('' if cfg.test_suite_deterministic else f' in {time.time()-start:.2f} seconds')
	)

def dump_test(proto, kg, ag, filename):

	with open(filename) as fp:
		dump = [[*(e.split()[0] for e in line.split('addr='))] for line in fp.readlines() if 'addr=' in line]
		if not dump:
			die(1, f'File {filename!r} appears not to be a wallet dump')

	qmsg(green(
		"A: generator pair '{}:{}'\nB: wallet dump {!r}".format(
			type(kg).__name__,
			type(ag).__name__,
			filename)))

	for count, (b_wif, b_addr) in enumerate(dump, 1):
		qmsg_r(f'\rKey {count}/{len(dump)} ')
		try:
			b_sec = PrivKey(proto, wif=b_wif)
		except:
			die(2, f'\nInvalid {proto.network} WIF address in dump file: {b_wif}')
		a_addr = ag.to_addr(kg.gen_data(b_sec))
		vmsg(f'\nwif: {b_wif}\naddr: {b_addr}\n')
		tinfo = (b_sec, b_sec.hex(), b_wif, type(kg).__name__, filename)
		test_equal('addresses', a_addr, b_addr, *tinfo)

	qmsg(green(('\n', '')[bool(cfg.verbose)] + 'OK'))

def get_protos(proto, addr_type, toolname):

	init_genonly_altcoins(testnet=proto.testnet)

	for coin in cinfo.external_tests[proto.network][toolname]:
		if coin.lower() not in CoinProtocol.coins:
			continue
		ret = init_proto(cfg, coin, testnet=proto.testnet)
		if addr_type not in ret.mmtypes:
			continue
		yield ret

def parse_args():

	if len(cfg._args) != 2:
		cfg._usage()

	arg1, arg2 = cfg._args
	gen1, gen2, rounds = (0, 0, 0)
	tool, all_backends, dumpfile = (None, None, None)

	if is_int(arg1) and is_int(arg2):
		test = 'speed'
		gen1 = arg1
		rounds = arg2
	elif is_int(arg1) and os.access(arg2, os.R_OK):
		test = 'dump'
		gen1 = arg1
		dumpfile = arg2
	else:
		test = 'ab'
		rounds = arg2

		if not is_int(arg2):
			die(1, 'Second argument must be dump filename or integer rounds specification')

		try:
			a, b = arg1.split(':')
		except:
			die(1, 'First argument must be a generator backend number or two colon-separated arguments')

		if is_int(a):
			gen1 = a
		else:
			if a == 'all':
				all_backends = True
			else:
				die(1, "First part of first argument must be a generator backend number or 'all'")

		if is_int(b):
			if cfg.all_coins:
				die(1, '--all-coins must be used with external tool only')
			gen2 = b
		else:
			tool = b
			ext_progs = list(cinfo.external_tests[cfg._proto.network]) + ['ext']
			if b not in ext_progs:
				die(1, f'Second part of first argument must be a generator backend number or one of {ext_progs}')

	return namedtuple('parsed_args',
			['test', 'gen1', 'gen2', 'rounds', 'tool', 'all_backends', 'dumpfile'])(
		test,
		int(gen1) or None,
		int(gen2) or None,
		int(rounds) or None,
		tool,
		all_backends,
		dumpfile)

def main():

	scfg = parse_args()

	addr_type = MMGenAddrType(proto=proto, id_str=cfg.type or proto.dfl_mmtype)

	if scfg.test == 'ab':
		protos = get_protos(proto, addr_type, scfg.tool) if cfg.all_coins else [proto]
		for p in protos:
			ab_test(p, scfg)
	else:
		kg = KeyGenerator(cfg, proto, addr_type.pubkey_type, backend=scfg.gen1)
		ag = AddrGenerator(cfg, proto, addr_type)
		if scfg.test == 'speed':
			speed_test(proto, kg, ag, scfg.rounds)
		elif scfg.test == 'dump':
			dump_test(proto, kg, ag, scfg.dumpfile)

	if saved_results:
		import json
		with open(results_file, 'w') as fp:
			fp.write(json.dumps(saved_results, indent=4))

from subprocess import run, PIPE, DEVNULL
from collections import namedtuple
from mmgen.protocol import init_proto, CoinProtocol
from mmgen.altcoin.params import init_genonly_altcoins
from test.altcointest import TestCoinInfo as cinfo
from mmgen.key import PrivKey
from mmgen.addr import MMGenAddrType
from mmgen.addrgen import KeyGenerator, AddrGenerator
from mmgen.keygen import get_backends
from test.include.common import getrand, set_globals

gtr = namedtuple('gen_tool_result', ['wif', 'addr', 'viewkey'])
sd = namedtuple('saved_data_item', ['reduced', 'wif', 'addr', 'viewkey'])

sys.argv = [sys.argv[0]] + ['--skip-cfg-file'] + sys.argv[1:]

cfg = Config(opts_data=opts_data)
set_globals(cfg)

qmsg = cfg._util.qmsg
qmsg_r = cfg._util.qmsg_r
vmsg = cfg._util.vmsg

proto = cfg._proto

if proto.coin in ('XMR', 'ETH', 'ETC'):
	from mmgen.util2 import load_cryptodome
	load_cryptodome()

if __name__ == '__main__':
	from mmgen.main import launch
	launch(func=main)

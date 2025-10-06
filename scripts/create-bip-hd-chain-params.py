#!/usr/bin/env python3

import json

from bip_utils.slip.slip44 import Slip44
from bip_utils.bip.conf.bip44.bip44_conf import Bip44Conf
from bip_utils.bip.conf.bip49.bip49_conf import Bip49Conf
from bip_utils.bip.conf.bip84.bip84_conf import Bip84Conf
from bip_utils.bip.conf.bip86.bip86_conf import Bip86Conf

import script_init
from mmgen.cfg import Config
from mmgen.main import launch

opts_data = {
	'text': {
		'desc': 'Aggregate bip_lib and SLIP-44 data into a bip_hd chainparams table',
		'usage':'[opts] infile',
		'options': """
-h, --help               Print this help message.
""",
	'notes': """
source: https://github.com/MetaMask/slip44/blob/main/slip44.json
"""
	}
}

cfg = Config(opts_data=opts_data)

def curve_clsname_abbr(s):
	return {
		'Bip32Slip10Secp256k1':      'x',
		'Bip32Slip10Ed25519':        'edw',
		'Bip32Slip10Ed25519Blake2b': 'blk',
		'Bip32Slip10Nist256p1':      'nist',
		'Bip32KholawEd25519':        'khol',
	}.get(s, s)

fs2 = '{:5} {:2} {:16} {:8} {:8} {:6} {:8} {:8}'
hdr2 = fs2.format('CURVE', 'NW', 'ADDR_CLS', 'VB_PRV', 'VB_PUB', 'VB_WIF', 'VB_ADDR', 'DFL_PATH')

dfl_vb_prv = '0488ade4'
dfl_vb_pub = '0488b21e'
dfl_curve = 'secp'
dfl_dfl_path = "0'/0/0"

def get_bip_utils_data(bipnum, n):
	name, v = bip_utils_data[bipnum][n]
	vb_prv = v.m_key_net_ver.m_priv_net_ver.hex()
	vb_pub = v.m_key_net_ver.m_pub_net_ver.hex()
	ap = v.m_addr_params
	return fs2.format(
		curve_clsname_abbr(v.m_bip32_cls.__name__),
		'T' if v.m_is_testnet else 'm',
		v.m_addr_cls.__name__.removesuffix('AddrEncoder'),
		'x' if vb_prv == dfl_vb_prv else vb_prv,
		'x' if vb_pub == dfl_vb_pub else vb_pub,
		v.m_wif_net_ver.hex() if isinstance(v.m_wif_net_ver, bytes) else '-',
		ap['net_ver'].hex() if 'net_ver' in ap else 'h:'+ap['hrp'] if 'hrp' in ap else 'spec' if ap else '-',
		'x' if v.m_def_path == dfl_dfl_path else v.m_def_path,
	)

def gen():

	def format_data(bipnum, n, sym, name):
		return fs.format(
			n,
			sym if sym else '---',
			get_bip_utils_data(bipnum, n) if bipnum else '-',
			name if name else '---')

	fs = '{:<6} {:6} {:1} {}'

	yield f'[defaults]'
	yield fs.format('IDX', 'CHAIN', hdr2, 'NAME')
	yield fs.format('0', '-', fs2.format(dfl_curve, '-', '-', dfl_vb_prv, dfl_vb_pub, '-', '-', dfl_dfl_path), '-')

	yield f'\n[bip-44]'
	yield fs.format('IDX', 'CHAIN', hdr2, 'NAME')
	for k, v in slip44_data.items():
		if int(k) in bip_utils_data[44]:
			yield format_data(44, int(k), v['symbol'], v['name'])

	for bipnum in (49, 84, 86):
		yield f'\n[bip-{bipnum}]'
		yield fs.format('IDX', 'CHAIN', hdr2, 'NAME')
		for n, v in sorted(bip_utils_data[bipnum].items()):
			nd = v[1].m_coin_names
			yield format_data(bipnum, n, nd.m_abbr, nd.m_name)

	yield f'\n[bip-44-unsupported]'
	yield fs.format('IDX', 'CHAIN', '', 'NAME')
	for k, v in slip44_data.items():
		if not int(k) in bip_utils_data[44]:
			yield format_data(None, int(k), v['symbol'], v['name'])

def main():

	global slip44_data, bip_utils_data

	if len(cfg._args) != 1:
		cfg._usage()

	with open(cfg._args[0]) as fh:
		slip44_data = json.loads(fh.read())

	bip_utils_data = {
		n: {v.m_coin_idx: (k, v)
			for k, v in globals()[f'Bip{n}Conf'].__dict__.items() if not k.startswith('_')}
				for n in (44, 49, 84, 86)}

	print('\n'.join(gen()))

launch(func=main)

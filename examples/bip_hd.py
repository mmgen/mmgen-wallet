#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
examples/bip_hd.py: Usage examples for the MMGen BIP-32/-44 hierarchical/deterministic library
"""

from mmgen.cfg import Config
from mmgen.util import fmt
from mmgen.bip39 import bip39
from mmgen.bip_hd import MasterNode, BipHDNode

cfg = Config()

bip39_mnemonic = 'cat swing flag economy stadium alone churn speed unique patch report train'

seed = bip39().generate_seed(bip39_mnemonic.split())

m = MasterNode(cfg, seed)

# Derive sample path:

# to_chain() derives default chain for coin/addr_type pair:
dfl_pub_chain = m.to_chain(idx=0, coin='ltc', addr_type='bech32')
dfl_chg_chain = m.to_chain(idx=1, coin='ltc', addr_type='bech32')

print('Default path (LTC, bech32):\n')
print(f'  public chain xpub:\n    {dfl_pub_chain.xpub}\n')
print(f'  internal chain xpub:\n    {dfl_chg_chain.xpub}\n')
print(f'  public chain addr 0:\n    {dfl_pub_chain.derive_public(0).address}\n')
print(f'  public chain addr 1:\n    {dfl_pub_chain.derive_public(1).address}\n')

# Derive sample path using path string:

dfl_pub_chain_from_path = BipHDNode.from_path(
	base_cfg  = cfg,
	seed      = seed,
	# purpose=84 (bech32 [BIP-84]), coin_type=2 (LTC mainnet [SLIP-44]), account=0, chain=0 (public)
	# as per BIP-44, ‘purpose’, ‘coin_type’ and ‘account’ are hardened, while ‘chain’ is not
	path_str  = "m/84'/2'/0'/0",
	coin      = 'ltc',
	addr_type = 'bech32')

assert dfl_pub_chain_from_path.xpub == dfl_pub_chain.xpub

# Derive sample path step-by-step:

# Configure master node with coin/addr_type pair:
master = m.init_cfg(coin='ltc', addr_type='bech32')

# ‘idx’ and ‘hardened’ args may be omitted at depths where defaults exist:
purpose = master.derive_private()     # ‘idx’ is auto-computed from addr_type (BIP-44/49/84)
coin_type = purpose.derive_private()  # ‘idx’ is auto-computed from coin/network (SLIP-44)
account = coin_type.derive_private(idx=0)
pub_chain = account.derive_public(idx=0)

assert pub_chain.xpub == dfl_pub_chain.xpub

# Initialize node from xpub:
pub_chain_from_xpub = BipHDNode.from_extended_key(cfg, 'ltc', pub_chain.xpub)

assert pub_chain_from_xpub.xpub == pub_chain.xpub

# To derive arbitrary BIP-32 paths, ignoring BIP-44, specify ‘no_path_checks’
nonstd_path = BipHDNode.from_path(
	base_cfg  = cfg,
	seed      = seed,
	path_str  = "m/111'/222/333/444",
	coin      = 'eth',
	addr_type = 'E',
	no_path_checks = True)

print('Non-standard path (ETH):\n')
print(f'  xpub:\n    {nonstd_path.xpub}\n')
print(f'  WIF key:\n    {nonstd_path.privkey.wif}\n')
print(f'  address:\n    {nonstd_path.address}\n')

# Display parsed xpub:
parsed_xpub = nonstd_path.key_extended(public=True)
print('Default path parsed xpub:\n')
print(fmt(str(parsed_xpub), indent='  '))

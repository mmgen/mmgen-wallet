#!/usr/bin/env python3

"""
test.modtest_d.nostr: Nostr unit test for the MMGen suite
"""

from collections import namedtuple

from mmgen.bip_hd import BipHDNode, MasterNode
from mmgen.bip39 import bip39

from ..include.common import cfg, vmsg

# Source: https://nostr-nips.com/nip-06
nv = namedtuple('nostr_test_vector', 'mnemonic privhex nsec pubhex npub')
vecs = [
	nv( 'leader monkey parrot ring guide accident before fence cannon height naive bean',
		'7f7ff03d123792d6ac594bfa67bf6d0c0ab55b6b1fdb6249303fe861f1ccba9a',
		'nsec10allq0gjx7fddtzef0ax00mdps9t2kmtrldkyjfs8l5xruwvh2dq0lhhkp',
		'17162c921dc4d2518f9a101db33695df1afb56ab82f5ff3e5da6eec3ca5cd917',
		'npub1zutzeysacnf9rru6zqwmxd54mud0k44tst6l70ja5mhv8jjumytsd2x7nu'),
	nv( 'what bleak badge arrange retreat wolf trade produce cricket blur garlic valid '
		'proud rude strong choose busy staff weather area salt hollow arm fade',
		'c15d739894c81a2fcfd3a2df85a0d2c0dbc47a280d092799f144d73d7ae78add',
		'nsec1c9wh8xy5eqdzln7n5t0ctgxjcrdug73gp5yj0x03gntn67h83twssdfhel',
		'd41b22899549e1f3d335a31002cfd382174006e166d3e658e3a5eecdb6463573',
		'npub16sdj9zv4f8sl85e45vgq9n7nsgt5qphpvmf7vk8r5hhvmdjxx4es8rq74h')]

path = "m/44'/1237'/0'/0/0"

class unit_tests:

	def path(self, name, ut):
		for v in vecs:
			vmsg(f'mnemonic: {v.mnemonic}')
			seed = bip39().generate_seed(v.mnemonic.split())
			res = BipHDNode.from_path(cfg, seed, path, coin='nostr')
			xprv = res.key_extended(public=False)
			xpub = res.key_extended(public=True)
			vmsg(f'prv:  {xprv.key.hex()}')
			vmsg(f'pub:  {xpub.key.hex()}')
			vmsg(f'addr: {res.address}')
			vmsg(f'wif:  {res.privkey.wif}')
			assert res.privkey.hex() == v.privhex
			assert res.address.bytes.hex() == v.pubhex
			assert xprv.key.hex() == v.privhex
			assert xpub.key.hex()[2:] == v.pubhex
			assert res.address == v.npub
			assert res.privkey.wif == v.nsec
			vmsg('')
		return True

	def derive(self, name, ut):
		for v in vecs:
			vmsg(f'mnemonic: {v.mnemonic}')
			seed = bip39().generate_seed(v.mnemonic.split())
			res = MasterNode(cfg, seed).to_chain(idx=0, coin='nostr').derive_private(0)
			vmsg(f'addr: {res.address}')
			vmsg(f'wif:  {res.privkey.wif}')
			assert res.address == v.npub
			assert res.privkey.wif == v.nsec
			vmsg('')
		return True

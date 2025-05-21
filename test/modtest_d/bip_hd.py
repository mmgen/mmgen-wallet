#!/usr/bin/env python3

"""
test.modtest_d.bip_hd: bip_hd unit test for the MMGen suite
"""

from mmgen.color import gray, pink, blue
from mmgen.util import fmt
from mmgen.bip_hd import Bip32ExtendedKey, BipHDConfig, BipHDNode, MasterNode, get_chain_params

from ..include.common import cfg, vmsg

# Source: BIP-32
vectors_bip32 = [
{
	'seed': '000102030405060708090a0b0c0d0e0f',
	"m": {
		'xpub': 'xpub661MyMwAqRbcFtXgS5sYJABqqG9YLmC4Q1Rdap9gSE8NqtwybGhePY2gZ29ESFjqJoCu1Rupje8YtGqsefD265TMg7usUDFdp6W1EGMcet8',
		'xprv': 'xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHi',
	},
	"m/0'": {
		'xpub': 'xpub68Gmy5EdvgibQVfPdqkBBCHxA5htiqg55crXYuXoQRKfDBFA1WEjWgP6LHhwBZeNK1VTsfTFUHCdrfp1bgwQ9xv5ski8PX9rL2dZXvgGDnw',
		'xprv': 'xprv9uHRZZhk6KAJC1avXpDAp4MDc3sQKNxDiPvvkX8Br5ngLNv1TxvUxt4cV1rGL5hj6KCesnDYUhd7oWgT11eZG7XnxHrnYeSvkzY7d2bhkJ7',
	},
	"m/0'/1": {
		'xpub': 'xpub6ASuArnXKPbfEwhqN6e3mwBcDTgzisQN1wXN9BJcM47sSikHjJf3UFHKkNAWbWMiGj7Wf5uMash7SyYq527Hqck2AxYysAA7xmALppuCkwQ',
		'xprv': 'xprv9wTYmMFdV23N2TdNG573QoEsfRrWKQgWeibmLntzniatZvR9BmLnvSxqu53Kw1UmYPxLgboyZQaXwTCg8MSY3H2EU4pWcQDnRnrVA1xe8fs',
	},
	"m/0'/1/2'": {
		'xpub': 'xpub6D4BDPcP2GT577Vvch3R8wDkScZWzQzMMUm3PWbmWvVJrZwQY4VUNgqFJPMM3No2dFDFGTsxxpG5uJh7n7epu4trkrX7x7DogT5Uv6fcLW5',
		'xprv': 'xprv9z4pot5VBttmtdRTWfWQmoH1taj2axGVzFqSb8C9xaxKymcFzXBDptWmT7FwuEzG3ryjH4ktypQSAewRiNMjANTtpgP4mLTj34bhnZX7UiM',
	},
	"m/0'/1/2'/2": {
		'xpub': 'xpub6FHa3pjLCk84BayeJxFW2SP4XRrFd1JYnxeLeU8EqN3vDfZmbqBqaGJAyiLjTAwm6ZLRQUMv1ZACTj37sR62cfN7fe5JnJ7dh8zL4fiyLHV',
		'xprv': 'xprvA2JDeKCSNNZky6uBCviVfJSKyQ1mDYahRjijr5idH2WwLsEd4Hsb2Tyh8RfQMuPh7f7RtyzTtdrbdqqsunu5Mm3wDvUAKRHSC34sJ7in334',
	},
	"m/0'/1/2'/2/1000000000": {
		'xpub': 'xpub6H1LXWLaKsWFhvm6RVpEL9P4KfRZSW7abD2ttkWP3SSQvnyA8FSVqNTEcYFgJS2UaFcxupHiYkro49S8yGasTvXEYBVPamhGW6cFJodrTHy',
		'xprv': 'xprvA41z7zogVVwxVSgdKUHDy1SKmdb533PjDz7J6N6mV6uS3ze1ai8FHa8kmHScGpWmj4WggLyQjgPie1rFSruoUihUZREPSL39UNdE3BBDu76',
	},
}, {
	'seed': 'fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a29f9c999693908d8a8784817e7b7875726f6c696663605d5a5754514e4b484542',
	'm': {
		'xpub': 'xpub661MyMwAqRbcFW31YEwpkMuc5THy2PSt5bDMsktWQcFF8syAmRUapSCGu8ED9W6oDMSgv6Zz8idoc4a6mr8BDzTJY47LJhkJ8UB7WEGuduB',
		'xprv': 'xprv9s21ZrQH143K31xYSDQpPDxsXRTUcvj2iNHm5NUtrGiGG5e2DtALGdso3pGz6ssrdK4PFmM8NSpSBHNqPqm55Qn3LqFtT2emdEXVYsCzC2U',
	},
	"m/0": {
		'xpub': 'xpub69H7F5d8KSRgmmdJg2KhpAK8SR3DjMwAdkxj3ZuxV27CprR9LgpeyGmXUbC6wb7ERfvrnKZjXoUmmDznezpbZb7ap6r1D3tgFxHmwMkQTPH',
		'xprv': 'xprv9vHkqa6EV4sPZHYqZznhT2NPtPCjKuDKGY38FBWLvgaDx45zo9WQRUT3dKYnjwih2yJD9mkrocEZXo1ex8G81dwSM1fwqWpWkeS3v86pgKt',
	},
	"m/0/2147483647'": {
		'xpub': 'xpub6ASAVgeehLbnwdqV6UKMHVzgqAG8Gr6riv3Fxxpj8ksbH9ebxaEyBLZ85ySDhKiLDBrQSARLq1uNRts8RuJiHjaDMBU4Zn9h8LZNnBC5y4a',
		'xprv': 'xprv9wSp6B7kry3Vj9m1zSnLvN3xH8RdsPP1Mh7fAaR7aRLcQMKTR2vidYEeEg2mUCTAwCd6vnxVrcjfy2kRgVsFawNzmjuHc2YmYRmagcEPdU9',
	},
	"m/0/2147483647'/1": {
		'xpub': 'xpub6DF8uhdarytz3FWdA8TvFSvvAh8dP3283MY7p2V4SeE2wyWmG5mg5EwVvmdMVCQcoNJxGoWaU9DCWh89LojfZ537wTfunKau47EL2dhHKon',
		'xprv': 'xprv9zFnWC6h2cLgpmSA46vutJzBcfJ8yaJGg8cX1e5StJh45BBciYTRXSd25UEPVuesF9yog62tGAQtHjXajPPdbRCHuWS6T8XA2ECKADdw4Ef',
	},
	"m/0/2147483647'/1/2147483646'": {
		'xpub': 'xpub6ERApfZwUNrhLCkDtcHTcxd75RbzS1ed54G1LkBUHQVHQKqhMkhgbmJbZRkrgZw4koxb5JaHWkY4ALHY2grBGRjaDMzQLcgJvLJuZZvRcEL',
		'xprv': 'xprvA1RpRA33e1JQ7ifknakTFpgNXPmW2YvmhqLQYMmrj4xJXXWYpDPS3xz7iAxn8L39njGVyuoseXzU6rcxFLJ8HFsTjSyQbLYnMpCqE2VbFWc',
	},
	"m/0/2147483647'/1/2147483646'/2": {
		'xpub': 'xpub6FnCn6nSzZAw5Tw7cgR9bi15UV96gLZhjDstkXXxvCLsUXBGXPdSnLFbdpq8p9HmGsApME5hQTZ3emM2rnY5agb9rXpVGyy3bdW6EEgAtqt',
		'xprv': 'xprvA2nrNbFZABcdryreWet9Ea4LvTJcGsqrMzxHx98MMrotbir7yrKCEXw7nadnHM8Dq38EGfSh6dqA9QWTyefMLEcBYJUuekgW4BYPJcr9E7j',
	},
}, {
	'comment': 'These vectors test for the retention of leading zeros. See bitpay/bitcore-lib#47 and iancoleman/bip39#58 for more information.',
	'seed': '4b381541583be4423346c643850da4b320e46a87ae3d2a4e6da11eba819cd4acba45d239319ac14f863b8d5ab5a0d0c64d2e8a1e7d1457df2e5a3c51c73235be',
	'm': {
		'xpub': 'xpub661MyMwAqRbcEZVB4dScxMAdx6d4nFc9nvyvH3v4gJL378CSRZiYmhRoP7mBy6gSPSCYk6SzXPTf3ND1cZAceL7SfJ1Z3GC8vBgp2epUt13',
		'xprv': 'xprv9s21ZrQH143K25QhxbucbDDuQ4naNntJRi4KUfWT7xo4EKsHt2QJDu7KXp1A3u7Bi1j8ph3EGsZ9Xvz9dGuVrtHHs7pXeTzjuxBrCmmhgC6',
	},
	"m/0'": {
		'xpub': 'xpub68NZiKmJWnxxS6aaHmn81bvJeTESw724CRDs6HbuccFQN9Ku14VQrADWgqbhhTHBaohPX4CjNLf9fq9MYo6oDaPPLPxSb7gwQN3ih19Zm4Y',
		'xprv': 'xprv9uPDJpEQgRQfDcW7BkF7eTya6RPxXeJCqCJGHuCJ4GiRVLzkTXBAJMu2qaMWPrS7AANYqdq6vcBcBUdJCVVFceUvJFjaPdGZ2y9WACViL4L',
	},
}, {
	'comment': 'These vectors test for the retention of leading zeros. See btcsuite/btcutil#172 for more information.',
	'seed': '3ddd5602285899a946114506157c7997e5444528f3003f6134712147db19b678',
	"m": {
		'xpub': 'xpub661MyMwAqRbcGczjuMoRm6dXaLDEhW1u34gKenbeYqAix21mdUKJyuyu5F1rzYGVxyL6tmgBUAEPrEz92mBXjByMRiJdba9wpnN37RLLAXa',
		'xprv': 'xprv9s21ZrQH143K48vGoLGRPxgo2JNkJ3J3fqkirQC2zVdk5Dgd5w14S7fRDyHH4dWNHUgkvsvNDCkvAwcSHNAQwhwgNMgZhLtQC63zxwhQmRv',
	},
	"m/0'": {
		'xpub': 'xpub69AUMk3qDBi3uW1sXgjCmVjJ2G6WQoYSnNHyzkmdCHEhSZ4tBok37xfFEqHd2AddP56Tqp4o56AePAgCjYdvpW2PU2jbUPFKsav5ut6Ch1m',
		'xprv': 'xprv9vB7xEWwNp9kh1wQRfCCQMnZUEG21LpbR9NPCNN1dwhiZkjjeGRnaALmPXCX7SgjFTiCTT6bXes17boXtjq3xLpcDjzEuGLQBM5ohqkao9G',
	},
	"m/0'/1'": {
		'xpub': 'xpub6BJA1jSqiukeaesWfxe6sNK9CCGaujFFSJLomWHprUL9DePQ4JDkM5d88n49sMGJxrhpjazuXYWdMf17C9T5XnxkopaeS7jGk1GyyVziaMt',
		'xprv': 'xprv9xJocDuwtYCMNAo3Zw76WENQeAS6WGXQ55RCy7tDJ8oALr4FWkuVoHJeHVAcAqiZLE7Je3vZJHxspZdFHfnBEjHqU5hG1Jaj32dVoS6XLT1',
	},
}]

# Source: BIP-32
# These vectors test that invalid extended keys are recognized as invalid.
vectors_bip32_invalid = [
	('xpub661MyMwAqRbcEYS8w7XLSVeEsBXy79zSzH1J8vCdxAZningWLdN3zgtU6LBpB85b3D2yc8sfvZU521AAwdZafEz7mnzBBsz4wKY5fTtTQBm', 'pubkey version / prvkey mismatch'),
	('xprv9s21ZrQH143K24Mfq5zL5MhWK9hUhhGbd45hLXo2Pq2oqzMMo63oStZzFGTQQD3dC4H2D5GBj7vWvSQaaBv5cxi9gafk7NF3pnBju6dwKvH', 'prvkey version / pubkey mismatch'),
	('xpub661MyMwAqRbcEYS8w7XLSVeEsBXy79zSzH1J8vCdxAZningWLdN3zgtU6Txnt3siSujt9RCVYsx4qHZGc62TG4McvMGcAUjeuwZdduYEvFn', 'invalid pubkey prefix 04'),
	('xprv9s21ZrQH143K24Mfq5zL5MhWK9hUhhGbd45hLXo2Pq2oqzMMo63oStZzFGpWnsj83BHtEy5Zt8CcDr1UiRXuWCmTQLxEK9vbz5gPstX92JQ', 'invalid prvkey prefix 04'),
	('xpub661MyMwAqRbcEYS8w7XLSVeEsBXy79zSzH1J8vCdxAZningWLdN3zgtU6N8ZMMXctdiCjxTNq964yKkwrkBJJwpzZS4HS2fxvyYUA4q2Xe4', 'invalid pubkey prefix 01'),
	('xprv9s21ZrQH143K24Mfq5zL5MhWK9hUhhGbd45hLXo2Pq2oqzMMo63oStZzFAzHGBP2UuGCqWLTAPLcMtD9y5gkZ6Eq3Rjuahrv17fEQ3Qen6J', 'invalid prvkey prefix 01'),
	('xprv9s2SPatNQ9Vc6GTbVMFPFo7jsaZySyzk7L8n2uqKXJen3KUmvQNTuLh3fhZMBoG3G4ZW1N2kZuHEPY53qmbZzCHshoQnNf4GvELZfqTUrcv', 'zero depth with non-zero parent fingerprint'),
	('xpub661no6RGEX3uJkY4bNnPcw4URcQTrSibUZ4NqJEw5eBkv7ovTwgiT91XX27VbEXGENhYRCf7hyEbWrR3FewATdCEebj6znwMfQkhRYHRLpJ', 'zero depth with non-zero parent fingerprint'),
	('xprv9s21ZrQH4r4TsiLvyLXqM9P7k1K3EYhA1kkD6xuquB5i39AU8KF42acDyL3qsDbU9NmZn6MsGSUYZEsuoePmjzsB3eFKSUEh3Gu1N3cqVUN', 'zero depth with non-zero index'),
	('xpub661MyMwAuDcm6CRQ5N4qiHKrJ39Xe1R1NyfouMKTTWcguwVcfrZJaNvhpebzGerh7gucBvzEQWRugZDuDXjNDRmXzSZe4c7mnTK97pTvGS8', 'zero depth with non-zero index'),
	('DMwo58pR1QLEFihHiXPVykYB6fJmsTeHvyTp7hRThAtCX8CvYzgPcn8XnmdfHGMQzT7ayAmfo4z3gY5KfbrZWZ6St24UVf2Qgo6oujFktLHdHY4', 'unknown extended key version'),
	('DMwo58pR1QLEFihHiXPVykYB6fJmsTeHvyTp7hRThAtCX8CvYzgPcn8XnmdfHPmHJiEDXkTiJTVV9rHEBUem2mwVbbNfvT2MTcAqj3nesx8uBf9', 'unknown extended key version'),
	('xprv9s21ZrQH143K24Mfq5zL5MhWK9hUhhGbd45hLXo2Pq2oqzMMo63oStZzF93Y5wvzdUayhgkkFoicQZcP3y52uPPxFnfoLZB21Teqt1VvEHx', 'private key 0 not in 1..n-1'),
	('xprv9s21ZrQH143K24Mfq5zL5MhWK9hUhhGbd45hLXo2Pq2oqzMMo63oStZzFAzHGBP2UuGCqWLTAPLcMtD5SDKr24z3aiUvKr9bJpdrcLg1y3G', 'private key n not in 1..n-1'),
	('xpub661MyMwAqRbcEYS8w7XLSVeEsBXy79zSzH1J8vCdxAZningWLdN3zgtU6Q5JXayek4PRsn35jii4veMimro1xefsM58PgBMrvdYre8QyULY', 'invalid pubkey 02000000...07'),
	('xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHL', 'invalid checksum'),
]

# Source: bip_utils
vectors_derive = {
	'bech32': {
		0: 'bc1qwg77fxw0tkmc3h58tcnnpegxk7mp3h6ly44d3n',
		1: 'bc1q6g79y6kwpkufevv2njacvnqnsdxmen68jyvjde',
		2: 'bc1qknujpwlxc9e9e6avz50q5k90p552xy8g3qjd8u',
	}
}

# Source: bip_utils
vectors_addrfmt = {
	'pub': {
		'compressed': 'xpub6GJknXsmpFcEubJsddGacncHhyY5Bk9zMQKC8pC97vBVAphrchYxuoJsAqfZW2uEMfPr6umSPRrhuaA7zeuExkwuAWiUcKcXjSf437VMLwR',
		'segwit': 'ypub6aNved9dRKbMRjLfMbGPoXKgNN1tr86qi8WoBxSVr4mHX9fdzUxJFtEH63QZZxArk4f2fwFZQUQ7FRkNiBarTLu2Y69SRxzn68WysngXPrp',
		'bech32': 'zpub6urFg31yVogtpf3Y7aV3CLuxQUsEpZ2asqBx3fzYMuFRTFrMNKxn5B2QXAGMSuwVfEA9KSJr2CUs8vqbmhUCkzVvxysB4p6vybLS2CgQnze',
	},
	'prv': {
		'compressed': 'xprvA3KQP2Lsyt3wh7EQXbjaFefZ9whanHS8zBPbLRnXZaeWJ2Ni5AEiMzzPKbKHsG7Dn6hkhSkG8V4H4XUsjszxU4nd2sMnc5ag9sHLLYBqrr4',
		'segwit': 'yprvAMPaF7cjax34DFGCFZjPSPNwpLBQSfNzLubCPa2tHjEJeMLVSwe3i5uoEnUg4etxP3XEqr5ZJinjGkUJrte3xFNZ1jVKbjVaFJVHi4Msekw',
		'bech32': 'zprvAgruGXV5fS8bcAy51Yx2qCyDrT2kR6JjWcGMFHavoZiSaTXCpneXXNhvfsMLeyBmjzACqkpxB2KGCMAe85wUrW1dnenu6kVHCk4kXh7XFE6',
	}
}

# Source: Asgardex Wallet
vectors_multicoin = {
	'btc_bech32':   'bc1qwg77fxw0tkmc3h58tcnnpegxk7mp3h6ly44d3n',
	'eth':          '373731f4d885Fc7Da05498F9f0804a87A14F891b',
	'doge':         'DFX88RXpi4S4W24YVvuMgbdUcCAYNeEYGd',
	'avax-c':       '0x373731f4d885Fc7Da05498F9f0804a87A14F891b',
	'ltc_bech32':   'ltc1q3uh5ga5cp9kkdfx6a52uymxj9keq4tpzep7er0',
	'bch_compressed': 'bitcoincash:qpqpcllprftg4s0chdgkpxhxv23wfymq3gj7n0a9vw',
	'bsc_smart':    '0x373731f4d885Fc7Da05498F9f0804a87A14F891b',
	'bnb_beacon':   'bnb179c3ymltqm4utlp089zxqeta5dvn48a305rhe5',
	'rune':         'thor1nr6fye3nznyn20m5w6fey6w8a8l4q599cdqmpc',
}

def wif2addr(cfg, wif):
	from mmgen.tool.coin import tool_cmd
	return tool_cmd(
		cfg     = cfg.base_cfg,
		cmdname = 'wif2addr',
		proto   = cfg.base_cfg._proto,
		mmtype  = cfg.addr_type).wif2addr(wif)

class unit_tests:

	altcoin_deps = ('multicoin',)

	@property
	def _seed(self):
		if not hasattr(self, '__seed'):
			with open('test/ref/98831F3A.bip39') as fh:
				mnemonic = fh.read().strip()
			from mmgen.bip39 import bip39
			self.__seed = bip39().generate_seed(mnemonic.split())
		return self.__seed

	def chainparams(self, name, ut):
		for bipnum, idx, chain, addr_cls in (
				(44, 0,  'btc',  'P2PKH'),
				(49, 0,  'btc',  'P2SH'),
				(84, 0,  'btc',  'P2WPKH'),
				(44, 60, 'eth',  'Eth'),
				(44, 61, 'etc',  'Eth'),
				(44, 2,  'ltc',  'P2PKH'),
				(44, 3,  'doge', 'P2PKH'),
			):
			res = get_chain_params(bipnum, chain)
			assert res.idx == idx, res.idx
			assert res.chain == chain.upper()
			assert res.addr_cls == addr_cls
			vmsg(f'  {res}')
		vmsg('')
		return True

	def derive(self, name, ut):
		vmsg('seed: 98831F3A (default derivation)')

		m = MasterNode(cfg, self._seed)

		purpose = m.init_cfg(coin='btc', addr_type='bech32').derive_private()
		vmsg(f'  {purpose.address=}')

		coin_type1 = purpose.derive_private()

		coin_type2 = m.to_coin_type(coin='btc', addr_type='bech32')
		assert coin_type1.address == coin_type2.address
		vmsg(f'  {coin_type1.address=}')

		acct = coin_type2.derive_private(idx=0)
		chain1 = acct.derive_private(idx=0, hardened=False)

		chain2 = m.to_chain(idx=0, coin='btc', addr_type='bech32', public=False)
		assert chain2.address == chain1.address

		chain3 = m.to_coin_type(coin='btc', addr_type='bech32').to_chain(0, public=True)
		assert chain3.address == chain1.address
		vmsg(f'  {chain1.address=}')

		a = BipHDNode.from_extended_key(cfg, 'btc', chain2.xpub)
		b = BipHDNode.from_extended_key(cfg, 'btc', chain2.xprv)
		vmsg(
			'\n  xpub:\n' +
			fmt(str(Bip32ExtendedKey(b.xpub)), indent='    ')
		)
		assert a.xpub == b.xpub

		vmsg('  Addresses:')
		for i in range(3):
			res = chain1.derive_public(i)
			vmsg(f'    {i} {res.address}')
			assert res.address == vectors_derive['bech32'][i]
			res = chain1.derive_private(i)
			assert res.address == vectors_derive['bech32'][i]

		vmsg('')
		return True

	def derive_addrfmt(self, name, ut):
		vmsg('seed: 98831F3A (default derivation)')

		m = MasterNode(cfg, self._seed)

		for addr_type in ('compressed', 'segwit', 'bech32'):
			chk_xpub = vectors_addrfmt['pub'][addr_type]
			chk_xprv = vectors_addrfmt['prv'][addr_type]

			res1 = m.to_chain(idx=0, coin='btc', addr_type=addr_type).derive_public(0)
			vmsg(f'  {addr_type}: {res1.xpub}')
			assert res1.xpub == chk_xpub

			res2 = m.to_chain(idx=0, coin='btc', addr_type=addr_type).derive_private(0, False)
			vmsg(f'  {addr_type}: {res2.xprv}')
			assert res2.xprv == chk_xprv
			assert res2.xpub == chk_xpub

			assert res2.address == wif2addr(res2.cfg, res2.privkey.wif)

		vmsg('')
		return True

	def path(self, name, ut):

		for vec in vectors_bip32:
			seed = bytes.fromhex(vec['seed'])
			vmsg(f'Seed: {vec["seed"]}')

			for n, path_str in enumerate(vec):
				if path_str in ('seed', 'comment'):
					continue

				path_arg = path_str.replace("'", 'H') if n % 2 else path_str
				node = BipHDNode.from_path(cfg, seed, path_arg, no_path_checks=True)
				vmsg('  Path {} {}'.format(pink(path_str), blue('('+node.desc+')')))

				for xkey_type in ('xpub', 'xprv'):
					vmsg(f'    {getattr(node, xkey_type)}')
					assert getattr(node, xkey_type) == vec[path_str][xkey_type]

			vmsg('')

		return True

	def parse_extended(self, name, ut):
		vmsg('Parsing and validating extended keys:\n')

		for vec in vectors_bip32:
			vmsg(f'  Seed: {vec["seed"]}')

			for path_str in vec:
				if path_str in ('seed', 'comment'):
					continue

				vmsg('    Path {}'.format(pink(path_str)))
				for xkey_type in ('xpub', 'xprv'):
					xkey = vec[path_str][xkey_type]
					vmsg(f'      {xkey}')
					node = BipHDNode.from_extended_key(cfg, 'btc', xkey)
					assert getattr(node, xkey_type) == xkey

			vmsg('')

		return True

	def multicoin(self, name, ut):
		m = MasterNode(cfg, self._seed)

		fs = '  {:6} {:10} {}'
		vmsg(fs.format('COIN', 'ADDR_TYPE', 'ADDR'))
		for id_str, addr_chk in vectors_multicoin.items():
			ss = id_str.split('_')
			coin = ss[0]
			addr_type = ss[1] if len(ss) == 2 else None
			if coin not in BipHDConfig.supported_coins:
				vmsg(gray(fs.format(coin.upper(), (addr_type or ''), '[not supported yet]')))
				continue
			vmsg(fs.format(coin.upper(), (addr_type or 'auto'), addr_chk))
			node = m.to_chain(idx=0, coin=coin, addr_type=addr_type).derive_private(0)
			xpub_parsed = node.key_extended(public=True)
			xprv_parsed = node.key_extended(public=False)
			addr = node.address
			at_arg = 'compressed' if coin == 'doge' else None
			from_xpub = BipHDNode.from_extended_key(node.cfg.base_cfg, coin, xpub_parsed.base58, addr_type=at_arg)
			from_xprv = BipHDNode.from_extended_key(node.cfg.base_cfg, coin, xprv_parsed.base58, addr_type=at_arg)
			assert from_xpub.xpub == node.xpub, f'{from_xpub.xpub=} != {node.xpub}'
			assert from_xprv.xpub == node.xpub, f'{from_xprv.xpub=} != {node.xpub}'
			assert from_xpub.address == addr, f'{from_xpub.address} != {addr}'
			assert from_xprv.address == addr, f'{from_xprv.address} != {addr}'
			addr_from_wif = wif2addr(node.cfg, node.privkey.wif)
			proto = node.cfg.base_cfg._proto
			if proto.base_proto == 'Ethereum':
				addr = proto.checksummed_addr(node.address)
				addr_from_wif = proto.checksummed_addr(addr_from_wif)
			assert addr == addr_chk, f'{addr} != {addr_chk}'
			assert addr == addr_from_wif, f'{addr} != {addr_from_wif}'

		vmsg('')
		return True

	def errors(self, name, ut):
		vmsg('Checking error handling:')

		m = MasterNode(cfg, self._seed)
		m_btc = m.init_cfg(coin='btc', addr_type='bech32')

		purpose = m_btc.derive_private()
		coin_type = purpose.derive_private()
		acct = coin_type.derive_private(idx=0)
		chain = acct.derive_private(idx=0, hardened=False)

		def bad01():
			m.to_chain(idx=0, coin='erq', addr_type='C')
		def bad02():
			m_btc.derive_private(idx=0)
		def bad03():
			m_btc.derive_private(hardened=False)
		def bad04():
			purpose.derive_private(idx=8)
		def bad05():
			purpose.derive_private(hardened=False)
		def bad06():
			coin_type.derive_private() # no acct idx
		def bad08():
			m_btc.derive_public() # must be private
		def bad09():
			coin_type.derive_private(idx=8, hardened=False)
		def bad10():
			acct.derive_private()
		def bad11():
			chain.derive_private()
		def bad12():
			chain.derive_private(hardened=True, idx=3)

		bad_data = (
			('unsupported coin',                       'ValueError', 'not supported',        bad01),
			('depth 1 (purpose):   idx not None',      'ValueError', 'index for path comp',  bad02),
			('depth 1 (purpose):   hardened False',    'ValueError', 'value for ‘hardened’', bad03),
			('depth 2 (coin type): idx mismatch',      'ValueError', 'index 8 at depth',     bad04),
			('depth 2 (coin type): hardened False',    'ValueError', 'value for ‘hardened’', bad05),
			('depth 3 (account):   idx not set',       'ValueError', 'must be set',          bad06),
			('depth 1 (purpose):   node not hardened', 'ValueError', 'must be hardened',     bad08),
			('depth 3 (account):   node not hardened', 'ValueError', 'value for ‘hardened’', bad09),
			('depth 4 (chain):     idx not set',       'ValueError', 'must be either 0',     bad10),
			('depth 5 (leaf node): idx not set',       'ValueError', 'must be set',          bad11),
			('depth 5 (leaf node): hardened True',     'ValueError', 'must be None',         bad12),
		)

		ut.process_bad_data(bad_data, pfx='')
		vmsg('')
		return True

	def parse_extended_errors(self, name, ut):
		vmsg('Parsing and validating invalid extended keys:')
		vec = vectors_bip32_invalid
		func = [lambda m=n: BipHDNode.from_extended_key(cfg, 'btc', vec[m][0]) for n in range(len(vec))]
		exc = (
			'first byte for public',
			'first byte for private',
			'first byte for public',
			'first byte for private',
			'first byte for public',
			'first byte for private',
			'non-zero parent fingerprint',
			'non-zero parent fingerprint',
			'non-zero index',
			'non-zero index',
			'unrecognized extended key v',
			'unrecognized extended key v',
			'private key is zero!',
			'private key >= group order!',
			'Public key could not be parsed', # extmod
			'incorrect checksum',
		)
		ut.process_bad_data([(vec[n][1], 'ValueError', exc[n], func[n]) for n in range(len(vec))], pfx='')
		vmsg('')
		return True

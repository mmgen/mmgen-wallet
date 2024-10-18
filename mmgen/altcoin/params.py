#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
altcoin.py - Constants for Bitcoin-derived altcoins
"""

# Sources:
#   lb: https://github.com/libbitcoin/libbitcoin/wiki/Altcoin-Version-Mappings
#   pc: https://github.com/richardkiss/pycoin/blob/master/pycoin/networks/legacy_networks.py
#   vg: https://github.com/exploitagency/vanitygen-plus/blob/master/keyconv.c
#   wn: https://walletgenerator.net
#   cc: https://www.cryptocompare.com/api/data/coinlist/ (names, symbols only)

# BIP44
# https://github.com/bitcoin/bips/blob/master/bip-0044.mediawiki
# BIP44 registered coin types: https://github.com/satoshilabs/slips/blob/master/slip-0044.md

# WIP:
#   NSR:  149/191 c/u,  63/('S'),  64/('S'|'T')
#   NBT:  150/191 c/u,  25/('B'),  26/('B')

from collections import namedtuple

from ..cfg import gc
from ..protocol import CoinProtocol
from ..proto.btc.params import mainnet

ce = namedtuple('CoinInfoEntry',
	['name', 'symbol', 'wif_ver_num', 'p2pkh_info', 'p2sh_info', 'has_segwit', 'trust_level'])

class CoinInfo:
	coin_constants = {}
	coin_constants['mainnet'] = (
#   Trust levels: -1=disabled 0=untested 1=low 2=med 3=high 4=very high (no warn) 5=unconditional
#   Trust levels apply to key/address generation only.
#   Non core-coin fork coins (i.e. BCG) must be disabled here to prevent generation from
#   incorrect scrambled seed.
	ce('Bitcoin',               'BTC',     0x80,   (0x00,'1'),       (0x05,'3'),       True,  5),
	ce('BitcoinCashNode',       'BCH',     0x80,   (0x00,'1'),       (0x05,'3'),       False, 5),
	ce('BitcoinGold',           'BCG',     0x80,   (0x00,'1'),       (0x05,'3'),       True, -1),
	ce('2GiveCoin',             '2GIVE',   0xa7,   (0x27,('G','H')), None,             False, 0),
	ce('42Coin',                '42',      0x88,   (0x08,'4'),       None,             False, 1),
	ce('ACoin',                 'ACOIN',   0xe6,   (0x17,'A'),       None,             False, 0),
	ce('Alphacoin',             'ALF',     0xd2,   (0x52,('Z','a')), None,             False, 0),
	ce('Anoncoin',              'ANC',     0x97,   (0x17,'A'),       None,             False, 1),
	ce('Apexcoin',              'APEX',    0x97,   (0x17,'A'),       None,             False, 0),
	ce('Aquariuscoin',          'ARCO',    0x97,   (0x17,'A'),       None,             False, 0),
	ce('Argentum',              'ARG',     0x97,   (0x17,'A'),       (0x05,'3'),       False, 1),
	ce('AsiaCoin',              'AC',      0x97,   (0x17,'A'),       (0x08,'4'),       False, 1),
	ce('Auroracoin',            'AUR',     0x97,   (0x17,'A'),       None,             False, 1),
	ce('BBQcoin',               'BQC',     0xd5,   (0x55,'b'),       None,             False, 1),
	ce('BitcoinDark',           'BTCD',    0xbc,   (0x3c,'R'),       (0x55,'b'),       False, 1),
	ce('BitcoinFast',           'BCF',     0xe0,   (0x60,('f','g')), None,             False, 0),
	ce('BitQuark',              'BTQ',     0xba,   (0x3a,'Q'),       None,             False, 0),
	ce('Blackcoin',             'BLK',     0x99,   (0x19,'B'),       (0x55,'b'),       False, 1),
	ce('BlackmoonCrypto',       'BMC',     0x83,   (0x03,'2'),       None,             False, 0),
	ce('BlockCat',              'CAT',     0x95,   (0x15,'9'),       None,             False, 0),
	ce('CanadaECoin',           'CDN',     0x9c,   (0x1c,'C'),       (0x05,'3'),       False, 1),
	ce('CannabisCoin',          'CANN',    0x9c,   (0x1c,'C'),       None,             False, 0),
	ce('CannaCoin',             'CCN',     0x9c,   (0x1c,'C'),       (0x05,'3'),       False, 1),
	ce('Capricoin',             'CPC',     0x9c,   (0x1c,'C'),       None,             False, 0),
	ce('CashCoin',              'CASH',    0xa2,   (0x22,('E','F')), None,             False, 0),
	ce('CashOut',               'CSH',     0xa2,   (0x22,('E','F')), None,             False, 0),
	ce('ChainCoin',             'CHC',     0x9c,   (0x1c,'C'),       None,             False, 0),
	ce('Clams',                 'CLAM',    0x85,   (0x89,'x'),       (0x0d,'6'),       False, 1),
	ce('CoinMagi',              'XMG',     0x94,   (0x14,'9'),       None,             False, 0),
	ce('Condensate',            'RAIN',    0xbc,   (0x3c,'R'),       None,             False, 0),
	ce('CryptoBullion',         'CBX',     0x8b,   (0x0b,'5'),       None,             False, 0),
	ce('Cryptonite',            'XCN',     0x80,   (0x1c,'C'),       None,             False, 0),
	ce('CryptoPennies',         'CRPS',    0xc2,   (0x42,'T'),       None,             False, 0),
	ce('Dash',                  'DASH',    0xcc,   (0x4c,'X'),       (0x10,'7'),       False, 2),
	ce('Decred',                'DCR',     0x22de, (0x073f,'D'),     (0x071a,'D'),     False, 1),
	ce('DeepOnion',             'ONION',   0x9f,   (0x1f,'D'),       None,             False, 1),
	ce('Defcoin',               'DFC',     0x9e,   (0x1e,'D'),       (0x05,'3'),       False, 1),
	ce('Devcoin',               'DVC',     0x80,   (0x00,'1'),       None,             False, 1),
	ce('DigiByte',              'DGB',     0x80,   (0x1e,'D'),       (0x05,'3'),       False, 1),
	ce('DigiCoin',              'DGC',     0x9e,   (0x1e,'D'),       (0x05,'3'),       False, 1),
	ce('DogecoinDark',          'DOGED',   0x9e,   (0x1e,'D'),       (0x21,'E'),       False, 1),
	ce('Dogecoin',              'DOGE',    0x9e,   (0x1e,'D'),       (0x16,('9','A')), False, 2),
	ce('DopeCoin',              'DOPE',    0x88,   (0x08,'4'),       (0x05,'3'),       False, 1),
	ce('EGulden',               'EFL',     0xb0,   (0x30,'L'),       (0x05,'3'),       False, 1),
	ce('Emerald',               'EMD',     0xa2,   (0x22,('E','F')), None,             False, 0),
	ce('Emercoin',              'EMC',     0x80,   (0x21,'E'),       (0x5c,'e'),       False, 2),
	ce('EnergyCoin',            'ENRG',    0xdc,   (0x5c,'e'),       None,             False, 0),
	ce('Espers',                'ESP',     0xa1,   (0x21,'E'),       None,             False, 0),
	ce('Faircoin',              'FAI',     0xdf,   (0x5f,'f'),       (0x24,'F'),       False, 1),
	ce('Fastcoin',              'FST',     0xe0,   (0x60,('f','g')), None,             False, 0),
	ce('Feathercoin',           'FTC',     0x8e,   (0x0e,('6','7')), (0x05,'3'),       False, 2),
	ce('Fibre',                 'FIBRE',   0xa3,   (0x23,'F'),       None,             False, 0),
	ce('FlorinCoin',            'FLO',     0xb0,   (0x23,'F'),       None,             False, 0),
	ce('Fluttercoin',           'FLT',     0xa3,   (0x23,'F'),       None,             False, 0),
	ce('Fuel2Coin',             'FC2',     0x80,   (0x24,'F'),       None,             False, 0),
	ce('Fujicoin',              'FJC',     0xa4,   (0x24,'F'),       None,             False, 0),
	ce('Fujinto',               'NTO',     0xa4,   (0x24,'F'),       None,             False, 0),
	ce('GlobalBoost',           'BSTY',    0xa6,   (0x26,'G'),       None,             False, 0),
	ce('GlobalCurrencyReserve', 'GCR',     0x9a,   (0x26,'G'),       (0x61,'g'),       False, 1),
	ce('GoldenBird',            'XGB',     0xaf,   (0x2f,('K','L')), None,             False, 0),
	ce('Goodcoin',              'GOOD',    0xa6,   (0x26,'G'),       None,             False, 0),
	ce('GridcoinResearch',      'GRC',     0xbe,   (0x3e,('R','S')), None,             False, 1),
	ce('Gulden',                'NLG',     0xa6,   (0x26,'G'),       None,             False, 1),
	ce('Guncoin',               'GUN',     0xa7,   (0x27,('G','H')), None,             False, 1),
	ce('HamRadioCoin',          'HAM',     0x80,   (0x00,'1'),       None,             False, 1),
	ce('HTML5Coin',             'HTML5',   0xa8,   (0x28,'H'),       None,             False, 0),
	ce('HyperStake',            'HYP',     0xf5,   (0x75,'p'),       None,             False, 0),
	ce('iCash',                 'ICASH',   0xcc,   (0x66,'i'),       None,             False, 0),
	ce('ImperiumCoin',          'IPC',     0xb0,   (0x30,'L'),       None,             False, 0),
	ce('IncaKoin',              'NKA',     0xb5,   (0x35,'N'),       None,             False, 0),
	ce('Influxcoin',            'INFX',    0xe6,   (0x66,'i'),       None,             False, 0),
	ce('InPay',                 'INPAY',   0xb7,   (0x37,'P'),       None,             False, 0),
#	ce('iXcoin',                'IXC',     0x80,   (0x8a,'x'),       None,             False, 1),
	ce('Judgecoin',             'JUDGE',   0xab,   (0x2b,'J'),       None,             False, 0),
	ce('Jumbucks',              'JBS',     0xab,   (0x2b,'J'),       (0x69,'j'),       False, 2),
	ce('Lanacoin',              'LANA',    0xb0,   (0x30,'L'),       None,             False, 0),
	ce('Latium',                'LAT',     0x80,   (0x17,'A'),       None,             False, 0),
	ce('Litecoin',              'LTC',     0xb0,   (0x30,'L'),       (0x32,'M'),       True,  5), # old p2sh: 0x05
	ce('LiteDoge',              'LDOGE',   0xab,   (0x5a,'d'),       None,             False, 0),
	ce('LomoCoin',              'LMC',     0xb0,   (0x30,'L'),       None,             False, 0),
	ce('Marscoin',              'MARS',    0xb2,   (0x32,'M'),       None,             False, 0),
	ce('MarsCoin',              'MRS',     0xb2,   (0x32,'M'),       None,             False, 0),
	ce('MartexCoin',            'MXT',     0xb2,   (0x32,'M'),       None,             False, 0),
	ce('MasterCar',             'MCAR',    0xe6,   (0x17,'A'),       None,             False, 0),
	ce('MazaCoin',              'MZC',     0xe0,   (0x32,'M'),       (0x09,('4','5')), False, 2),
	ce('MegaCoin',              'MEC',     0xb2,   (0x32,'M'),       None,             False, 1),
	ce('MintCoin',              'MINT',    0xb3,   (0x33,'M'),       None,             False, 0),
	ce('Mobius',                'MOBI',    0x80,   (0x00,'1'),       None,             False, 0),
	ce('MonaCoin',              'MONA',    0xb0,   (0x32,'M'),       (0x05,'3'),       False, 1),
	ce('MonetaryUnit',          'MUE',     0x8f,   (0x0f,'7'),       (0x09,('4','5')), False, 1),
	ce('MoonCoin',              'MOON',    0x83,   (0x03,'2'),       None,             False, 0),
	ce('MyriadCoin',            'MYR',     0xb2,   (0x32,'M'),       (0x09,('4','5')), False, 1),
	ce('Myriadcoin',            'MYRIAD',  0xb2,   (0x32,'M'),       None,             False, 1),
	ce('Namecoin',              'NMC',     0xb4,   (0x34,('M','N')), (0x0d,'6'),       False, 1),
	ce('Neoscoin',              'NEOS',    0xef,   (0x3f,'S'),       (0xbc,'2'),       False, 1),
	ce('NevaCoin',              'NEVA',    0xb1,   (0x35,'N'),       None,             False, 0),
	ce('Novacoin',              'NVC',     0x88,   (0x08,'4'),       (0x14,'9'),       False, 1),
	ce('OKCash',                'OK',      0xb7,   (0x37,'P'),       (0x1c,'C'),       False, 1),
	ce('Omnicoin',              'OMC',     0xf3,   (0x73,'o'),       None,             False, 1),
	ce('Omni',                  'OMNI',    0xf3,   (0x73,'o'),       None,             False, 0),
	ce('Onix',                  'ONX',     0x80,   (0x8a,'x'),       None,             False, 0),
	ce('PandaCoin',             'PND',     0xb7,   (0x37,'P'),       (0x16,('9','A')), False, 1),
	ce('ParkByte',              'PKB',     0xb7,   (0x37,'P'),       (0x1c,'C'),       False, 1),
	ce('Particl',               'PART',    0x6c,   (0x38,'P'),       None,             False, 0),
	ce('Paycoin',               'CON',     0xb7,   (0x37,'P'),       None,             False, 1),
	ce('Peercoin',              'PPC',     0xb7,   (0x37,'P'),       (0x75,'p'),       False, 1),
	ce('PesetaCoin',            'PTC',     0xaf,   (0x2f,('K','L')), None,             False, 1),
	ce('PhoenixCoin',           'PXC',     0xb8,   (0x38,'P'),       None,             False, 0),
	ce('PinkCoin',              'PINK',    0x83,   (0x03,'2'),       None,             False, 1),
	ce('PIVX',                  'PIVX',    0xd4,   (0x1e,'D'),       None,             False, 0),
	ce('PokeChain',             'XPOKE',   0x9c,   (0x1c,'C'),       None,             False, 0),
	ce('Potcoin',               'POT',     0xb7,   (0x37,'P'),       (0x05,'3'),       False, 1),
	ce('Primecoin',             'XPM',     0x97,   (0x17,'A'),       (0x53,'a'),       False, 1),
	ce('Quark',                 'QRK',     0xba,   (0x3a,'Q'),       None,             False, 0),
	ce('ReddCoin',              'RDD',     0xbd,   (0x3d,'R'),       None,             False, 1),
	ce('Riecoin',               'RIC',     0x80,   (0x3c,'R'),       (0x05,'3'),       False, 2),
	ce('Rimbit',                'RBT',     0xbc,   (0x3c,'R'),       None,             False, 0),
	ce('Rubycoin',              'RBY',     0xbd,   (0x3d,'R'),       (0x55,'b'),       False, 1),
	ce('ShadowCash',            'SDC',     0xbf,   (0x3f,'S'),       (0x7d,'s'),       False, 1),
	ce('Sibcoin',               'SIB',     0x80,   (0x3f,'S'),       None,             False, 0),
	ce('SixEleven',             '611',     0x80,   (0x34,('M','N')), None,             False, 0),
	ce('SmileyCoin',            'SMLY',    0x99,   (0x19,'B'),       None,             False, 0),
	ce('Songcoin',              'SONG',    0xbf,   (0x3f,'S'),       None,             False, 0),
	ce('Spreadcoin',            'SPR',     0xbf,   (0x3f,'S'),       None,             False, 1),
	ce('Startcoin',             'START',   0xfd,   (0x7d,'s'),       (0x05,'3'),       False, 1),
	ce('StealthCoin',           'XST',     0xbe,   (0x3e,('R','S')), None,             False, 0),
	ce('SwagBucks',             'BUCKS',   0x99,   (0x3f,'S'),       None,             False, 0),
	ce('SysCoin',               'SYS',     0x80,   (0x00,'1'),       None,             False, 0),
	ce('TajCoin',               'TAJ',     0x6f,   (0x41,'T'),       None,             False, 0),
	ce('Templecoin',            'TPC',     0xc1,   (0x41,'T'),       (0x05,'3'),       False, 1),
	ce('Terracoin',             'TRC',     0x80,   (0x00,'1'),       None,             False, 0),
	ce('Titcoin',               'TIT',     0x80,   (0x00,'1'),       None,             False, 0),
	ce('TittieCoin',            'TTC',     0xc1,   (0x41,'T'),       None,             False, 0),
	ce('Transfer',              'TX',      0x99,   (0x42,'T'),       None,             False, 0),
	ce('Unobtanium',            'UNO',     0xe0,   (0x82,'u'),       (0x1e,'D'),       False, 2),
	ce('Vcash',                 'XVC',     0xc7,   (0x47,'V'),       None,             False, 0),
	ce('Vertcoin',              'VTC',     0xc7,   (0x47,'V'),       (0x05,'3'),       False, 1),
	ce('Viacoin',               'VIA',     0xc7,   (0x47,'V'),       (0x21,'E'),       False, 2),
	ce('VpnCoin',               'VPN',     0xc7,   (0x47,'V'),       (0x05,'3'),       False, 1),
	ce('WankCoin',              'WKC',     0x80,   (0x00,'1'),       None,             False, 1),
	ce('WashingtonCoin',        'WASH',    0xc9,   (0x49,'W'),       None,             False, 0),
	ce('WeAreSatoshi',          'WSX',     0x97,   (0x87,'w'),       None,             False, 0),
	ce('WisdomCoin',            'WISC',    0x87,   (0x49,'W'),       None,             False, 0),
	ce('WorldCoin',             'WDC',     0xc9,   (0x49,'W'),       None,             False, 1),
	ce('XRealEstateDevcoin',    'XRED',    0x80,   (0x00,'1'),       None,             False, 0),
	ce('ZetaCoin',              'ZET',     0xe0,   (0x50,'Z'),       None,             False, 0),
	ce('ZiftrCoin',             'ZRC',     0xd0,   (0x50,'Z'),       (0x05,'3'),       False, 1),
	ce('ZLiteQubit',            'ZLQ',     0xe0,   (0x26,'G'),       None,             False, 0),
	ce('Zoomcoin',              'ZOOM',    0xe7,   (0x67,'i'),       (0x5c,'e'),       False, 1),
	)

	coin_constants['testnet'] = (
	ce('Bitcoin',     'BTC',   0xef,   (0x6f,('m','n')), (0xc4,'2'),       True,  5),
	ce('BitcoinCashNode','BCH',0xef,   (0x6f,('m','n')), (0xc4,'2'),       True,  5),
	ce('BitcoinGold', 'BCG',   0xef,   (0x6f,('m','n')), (0xc4,'2'),       True, -1),
	ce('Dash',        'DASH',  0xef,   (0x8c,'y'),       (0x13,('8','9')), False, 1),
	ce('Decred',      'DCR',   0x230e, (0x0f21,'T'),     (0x0e6c,'S'),     False, 1),
	ce('Dogecoin',    'DOGE',  0xf1,   (0x71,'n'),       (0xc4,'2'),       False, 2),
	ce('Feathercoin', 'FTC',   0xc1,   (0x41,'T'),       (0xc4,'2'),       False, 2),
	ce('Viacoin',     'VIA',   0xff,   (0x7f,'t'),       (0xc4,'2'),       False, 2),
	ce('Emercoin',    'EMC',   0xef,   (0x6f,('m','n')), (0xc4,'2'),       False, 2),
	ce('Litecoin',    'LTC',   0xef,   (0x6f,('m','n')), (0x3a,'Q'),       True,  5), # old p2sh: 0xc4
	)

	coin_sources = (
	('BTC',    'https://github.com/bitcoin/bitcoin/blob/master/src/chainparams.cpp'),
	('EMC',    'https://github.com/emercoin/emercoin/blob/master/src/chainparams.cpp'), # checked mn,tn
	('LTC',    'https://github.com/litecoin-project/litecoin/blob/master-0.10/src/chainparams.cpp'),
	('DOGE',   'https://github.com/dogecoin/dogecoin/blob/master/src/chainparams.cpp'),
	('RDD',    'https://github.com/reddcoin-project/reddcoin/blob/master/src/base58.h'),
	('DASH',   'https://github.com/dashpay/dash/blob/master/src/chainparams.cpp'),
	('PPC',    'https://github.com/belovachap/peercoin/blob/master/src/base58.h'),
	('NMC',    'https://github.com/domob1812/namecore/blob/master/src/chainparams.cpp'),
	('FTC',    'https://github.com/FeatherCoin/Feathercoin/blob/master-0.8/src/base58.h'),
	('BLK',    'https://github.com/rat4/blackcoin/blob/master/src/chainparams.cpp'),
	('NSR',    'https://nubits.com/nushares/introduction'),
	('NBT',    'https://bitbucket.org/JordanLeePeershares/nubit/NuBit / src /base58.h'),
	('MZC',    'https://github.com/MazaCoin/MazaCoin/blob/master/src/chainparams.cpp'),
	('VIA',    'https://github.com/viacoin/viacoin/blob/master/src/chainparams.cpp'),
	('RBY',    'https://github.com/rubycoinorg/rubycoin/blob/master/src/base58.h'),
	('GRS',    'https://github.com/GroestlCoin/groestlcoin/blob/master/src/groestlcoin.cpp'),
	('DGC',    'https://github.com/DGCDev/digitalcoin/blob/master/src/chainparams.cpp'),
	('CCN',    'https://github.com/Cannacoin-Project/Cannacoin/blob/Proof-of-Stake/src/base58.h'),
	('DGB',    'https://github.com/digibyte/digibyte/blob/master/src/chainparams.cpp'),
	('MONA',   'https://github.com/monacoinproject/monacoin/blob/master-0.10/src/chainparams.cpp'),
	('CLAM',   'https://github.com/nochowderforyou/clams/blob/master/src/chainparams.cpp'),
	('XPM',    'https://github.com/primecoin/primecoin/blob/master/src/base58.h'),
	('NEOS',   'https://github.com/bellacoin/neoscoin/blob/master/src/chainparams.cpp'),
	('JBS',    'https://github.com/jyap808/jumbucks/blob/master/src/base58.h'),
	('ZRC',    'https://github.com/ZiftrCOIN/ziftrcoin/blob/master/src/chainparams.cpp'),
	('VTC',    'https://github.com/vertcoin/vertcoin/blob/master/src/base58.h'),
	('NXT',    'https://bitbucket.org/JeanLucPicard/nxt/src and unofficial at https://github.com/Blackcomb/nxt'),
	('MUE',    'https://github.com/MonetaryUnit/MUE-Src/blob/master/src/chainparams.cpp'),
	('ZOOM',   'https://github.com/zoom-c/zoom/blob/master/src/base58.h'),
	('VPN',    'https://github.com/Bit-Net/VpnCoin/blob/master/src/base58.h'),
	('CDN',    'https://github.com/ThisIsOurCoin/canadaecoin/blob/master/src/base58.h'),
	('SDC',    'https://github.com/ShadowProject/shadow/blob/master/src/chainparams.cpp'),
	('PKB',    'https://github.com/parkbyte/ParkByte/blob/master/src/base58.h'),
	('PND',    'https://github.com/coinkeeper/2015-04-19_21-22_pandacoin/blob/master/src/base58.h'),
	('START',  'https://github.com/startcoin-project/startcoin/blob/master/src/base58.h'),
	('GCR',    'https://github.com/globalcurrencyreserve/gcr/blob/master/src/chainparams.cpp'),
	('NVC',    'https://github.com/novacoin-project/novacoin/blob/master/src/base58.h'),
	('AC',     'https://github.com/AsiaCoin/AsiaCoinFix/blob/master/src/base58.h'),
	('BTCD',   'https://github.com/jl777/btcd/blob/master/src/base58.h'),
	('DOPE',   'https://github.com/dopecoin-dev/DopeCoinV3/blob/master/src/base58.h'),
	('TPC',    'https://github.com/9cat/templecoin/blob/templecoin/src/base58.h'),
	('OK',     'https://github.com/okcashpro/okcash/blob/master/src/chainparams.cpp'),
	('DOGED',  'https://github.com/doged/dogedsource/blob/master/src/base58.h'),
	('EFL',    'https://github.com/Electronic-Gulden-Foundation/egulden/blob/master/src/base58.h'),
	('POT',    'https://github.com/potcoin/Potcoin/blob/master/src/base58.h'),
	)

	@classmethod
	def get_supported_coins(cls, network):
		return [e for e in cls.coin_constants[network] if e.trust_level != -1]

	@classmethod
	def get_entry(cls, coin, network):
		try:
			idx = [e.symbol for e in cls.coin_constants[network]].index(coin.upper())
		except:
			return None
		return cls.coin_constants[network][idx]

def make_proto(e, testnet=False):

	proto = ('X_' if e.name[0] in '0123456789' else '') + e.name + ('Testnet' if testnet else '')

	if hasattr(CoinProtocol, proto):
		return

	def num2hexstr(n):
		return '{:0{}x}'.format(n, (4, 2)[n < 256])

	setattr(
		CoinProtocol,
		proto,
		type(
			proto,
			(mainnet,),
			{
				'base_coin': e.symbol,
				'addr_ver_info': dict(
					[(num2hexstr(e.p2pkh_info[0]), 'p2pkh')] +
					([(num2hexstr(e.p2sh_info[0]), 'p2sh')] if e.p2sh_info else [])
				),
				'wif_ver_num': {'std': num2hexstr(e.wif_ver_num)},
				'mmtypes':    ('L', 'C', 'S') if e.has_segwit else ('L', 'C'),
				'dfl_mmtype': 'L',
				'mmcaps':     (),
			},
		)
	)

def init_genonly_altcoins(usr_coin=None, testnet=False):
	"""
	Initialize altcoin protocol class or classes for current network.
	If usr_coin is a core coin, initialization is skipped.
	If usr_coin has a trust level of -1, an exception is raised.
	If usr_coin is None, initializes all coins for current network with trust level >-1.
	Returns trust_level of usr_coin, or 0 (untrusted) if usr_coin is None.
	"""

	data = {'mainnet': (), 'testnet': ()}
	networks = ['mainnet'] + (['testnet'] if testnet else [])
	network = 'testnet' if testnet else 'mainnet'

	if usr_coin is None:
		for network in networks:
			data[network] = CoinInfo.get_supported_coins(network)
	else:
		if usr_coin.lower() in gc.core_coins: # core coin, so return immediately
			return CoinProtocol.coins[usr_coin.lower()].trust_level
		for network in networks:
			data[network] = (CoinInfo.get_entry(usr_coin, network),)

		cinfo = data[network][0]
		if not cinfo:
			raise ValueError(f'{usr_coin.upper()!r}: unrecognized coin for network {network.upper()}')
		if cinfo.trust_level == -1:
			raise ValueError(f'{usr_coin.upper()!r}: unsupported (disabled) coin for network {network.upper()}')

	for e in data['mainnet']:
		make_proto(e)

	for e in data['testnet']:
		make_proto(e, testnet=True)

	for e in data['mainnet']:
		if e.symbol.lower() in CoinProtocol.coins:
			continue
		CoinProtocol.coins[e.symbol.lower()] = CoinProtocol.proto_info(
			name        = 'X_'+e.name if e.name[0] in '0123456789' else e.name,
			trust_level = e.trust_level)

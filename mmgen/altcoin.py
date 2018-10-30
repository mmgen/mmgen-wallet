#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2018 The MMGen Project <mmgen@tuta.io>
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
altcoin.py - Coin constants for Bitcoin-derived altcoins
"""

# Sources:
#   lb: https://github.com/libbitcoin/libbitcoin/wiki/Altcoin-Version-Mappings
#   pc: https://github.com/richardkiss/pycoin/blob/master/pycoin/networks/legacy_networks.py
#   vg: https://github.com/exploitagency/vanitygen-plus/blob/master/keyconv.c
#   wn: https://walletgenerator.net
#   cc: https://www.cryptocompare.com/api/data/coinlist/ (names,symbols only)

# WIP:
#   NSR:  149/191 c/u,  63/('S'),  64/('S'|'T')
#   NBT:  150/191 c/u,  25/('B'),  26/('B')

import sys
def msg(s): sys.stderr.write(s+'\n')

class CoinInfo(object):
	coin_constants = {}
	coin_constants['mainnet'] = (
#    NAME                     SYM        WIF     P2PKH             P2SH              SEGWIT TRUST
#                                        trust levels: 0=untested 1=low 2=med 3=high -1=disable
#   Fork coins must be disabled here to prevent generation from incorrect sub-seed
	('Bitcoin',               'BTC',     0x80,   (0x00,'1'),       (0x05,'3'),       True, -1),
	('BitcoinSegwit2X',       'B2X',     0x80,   (0x00,'1'),       (0x05,'3'),       True, -1),
	('BitcoinGold',           'BCG',     0x80,   (0x00,'1'),       (0x05,'3'),       True, -1),
	('Bcash',                 'BCH',     0x80,   (0x00,'1'),       (0x05,'3'),       False,-1),
	('2GiveCoin',             '2GIVE',   0xa7,   (0x27,('G','H')), None,             False, 0),
	('42Coin',                '42',      0x88,   (0x08,'4'),       None,             False, 1),
	('ACoin',                 'ACOIN',   0xe6,   (0x17,'A'),       None,             False, 0),
	('Alphacoin',             'ALF',     0xd2,   (0x52,('Z','a')), None,             False, 0),
	('Anoncoin',              'ANC',     0x97,   (0x17,'A'),       None,             False, 1),
	('Apexcoin',              'APEX',    0x97,   (0x17,'A'),       None,             False, 0),
	('Aquariuscoin',          'ARCO',    0x97,   (0x17,'A'),       None,             False, 0),
	('Argentum',              'ARG',     0x97,   (0x17,'A'),       (0x05,'3'),       False, 1),
	('AsiaCoin',              'AC',      0x97,   (0x17,'A'),       (0x08,'4'),       False, 1),
	('Auroracoin',            'AUR',     0x97,   (0x17,'A'),       None,             False, 1),
	('BBQcoin',               'BQC',     0xd5,   (0x55,'b'),       None,             False, 1),
	('BitcoinDark',           'BTCD',    0xbc,   (0x3c,'R'),       (0x55,'b'),       False, 1),
	('BitcoinFast',           'BCF',     0xe0,   (0x60,('f','g')), None,             False, 0),
	('BitQuark',              'BTQ',     0xba,   (0x3a,'Q'),       None,             False, 0),
	('Blackcoin',             'BLK',     0x99,   (0x19,'B'),       (0x55,'b'),       False, 1),
	('BlackmoonCrypto',       'BMC',     0x83,   (0x03,'2'),       None,             False, 0),
	('BlockCat',              'CAT',     0x95,   (0x15,'9'),       None,             False, 0),
	('CanadaECoin',           'CDN',     0x9c,   (0x1c,'C'),       (0x05,'3'),       False, 1),
	('CannabisCoin',          'CANN',    0x9c,   (0x1c,'C'),       None,             False, 0),
	('CannaCoin',             'CCN',     0x9c,   (0x1c,'C'),       (0x05,'3'),       False, 1),
	('Capricoin',             'CPC',     0x9c,   (0x1c,'C'),       None,             False, 0),
	('CashCoin',              'CASH',    0xa2,   (0x22,('E','F')), None,             False, 0),
	('CashOut',               'CSH',     0xa2,   (0x22,('E','F')), None,             False, 0),
	('ChainCoin',             'CHC',     0x9c,   (0x1c,'C'),       None,             False, 0),
	('Clams',                 'CLAM',    0x85,   (0x89,'x'),       (0x0d,'6'),       False, 1),
	('CoinMagi',              'XMG',     0x94,   (0x14,'9'),       None,             False, 0),
	('Condensate',            'RAIN',    0xbc,   (0x3c,'R'),       None,             False, 0),
	('CryptoBullion',         'CBX',     0x8b,   (0x0b,'5'),       None,             False, 0),
	('Cryptonite',            'XCN',     0x80,   (0x1c,'C'),       None,             False, 0),
	('CryptoPennies',         'CRPS',    0xc2,   (0x42,'T'),       None,             False, 0),
	('Dash',                  'DASH',    0xcc,   (0x4c,'X'),       (0x10,'7'),       False, 1),
	('Decred',                'DCR',     0x22de, (0x073f,'D'),     (0x071a,'D'),     False, 1),
	('DeepOnion',             'ONION',   0x9f,   (0x1f,'D'),       None,             False, 1),
	('Defcoin',               'DFC',     0x9e,   (0x1e,'D'),       (0x05,'3'),       False, 1),
	('Devcoin',               'DVC',     0x80,   (0x00,'1'),       None,             False, 1),
	('DigiByte',              'DGB',     0x80,   (0x1e,'D'),       (0x05,'3'),       False, 1),
	('DigiCoin',              'DGC',     0x9e,   (0x1e,'D'),       (0x05,'3'),       False, 1),
	('DogecoinDark',          'DOGED',   0x9e,   (0x1e,'D'),       (0x21,'E'),       False, 1),
	('Dogecoin',              'DOGE',    0x9e,   (0x1e,'D'),       (0x16,('9','A')), False, 2),
	('DopeCoin',              'DOPE',    0x88,   (0x08,'4'),       (0x05,'3'),       False, 1),
	('EGulden',               'EFL',     0xb0,   (0x30,'L'),       (0x05,'3'),       False, 1),
	('Emerald',               'EMD',     0xa2,   (0x22,('E','F')), None,             False, 0),
	('Emercoin',              'EMC',     0x80,   (0x21,'E'),       (0x5c,'e'),       False, 2),
	('EnergyCoin',            'ENRG',    0xdc,   (0x5c,'e'),       None,             False, 0),
	('Espers',                'ESP',     0xa1,   (0x21,'E'),       None,             False, 0),
	('Faircoin',              'FAI',     0xdf,   (0x5f,'f'),       (0x24,'F'),       False, 1),
	('Fastcoin',              'FST',     0xe0,   (0x60,('f','g')), None,             False, 0),
	('Feathercoin',           'FTC',     0x8e,   (0x0e,('6','7')), (0x05,'3'),       False, 2),
	('Fibre',                 'FIBRE',   0xa3,   (0x23,'F'),       None,             False, 0),
	('FlorinCoin',            'FLO',     0xb0,   (0x23,'F'),       None,             False, 0),
	('Fluttercoin',           'FLT',     0xa3,   (0x23,'F'),       None,             False, 0),
	('Fuel2Coin',             'FC2',     0x80,   (0x24,'F'),       None,             False, 0),
	('Fujicoin',              'FJC',     0xa4,   (0x24,'F'),       None,             False, 0),
	('Fujinto',               'NTO',     0xa4,   (0x24,'F'),       None,             False, 0),
	('GlobalBoost',           'BSTY',    0xa6,   (0x26,'G'),       None,             False, 0),
	('GlobalCurrencyReserve', 'GCR',     0x9a,   (0x26,'G'),       (0x61,'g'),       False, 1),
	('GoldenBird',            'XGB',     0xaf,   (0x2f,('K','L')), None,             False, 0),
	('Goodcoin',              'GOOD',    0xa6,   (0x26,'G'),       None,             False, 0),
	('GridcoinResearch',      'GRC',     0xbe,   (0x3e,('R','S')), None,             False, 1),
	('Gulden',                'NLG',     0xa6,   (0x26,'G'),       None,             False, 1),
	('Guncoin',               'GUN',     0xa7,   (0x27,('G','H')), None,             False, 1),
	('HamRadioCoin',          'HAM',     0x80,   (0x00,'1'),       None,             False, 1),
	('HTML5Coin',             'HTML5',   0xa8,   (0x28,'H'),       None,             False, 0),
	('HyperStake',            'HYP',     0xf5,   (0x75,'p'),       None,             False, 0),
	('iCash',                 'ICASH',   0xcc,   (0x66,'i'),       None,             False, 0),
	('ImperiumCoin',          'IPC',     0xb0,   (0x30,'L'),       None,             False, 0),
	('IncaKoin',              'NKA',     0xb5,   (0x35,'N'),       None,             False, 0),
	('Influxcoin',            'INFX',    0xe6,   (0x66,'i'),       None,             False, 0),
	('InPay',                 'INPAY',   0xb7,   (0x37,'P'),       None,             False, 0),
#	('iXcoin',                'IXC',     0x80,   (0x8a,'x'),       None,             False, 1),
	('Judgecoin',             'JUDGE',   0xab,   (0x2b,'J'),       None,             False, 0),
	('Jumbucks',              'JBS',     0xab,   (0x2b,'J'),       (0x69,'j'),       False, 2),
	('Lanacoin',              'LANA',    0xb0,   (0x30,'L'),       None,             False, 0),
	('Latium',                'LAT',     0x80,   (0x17,'A'),       None,             False, 0),
	('Litecoin',              'LTC',     0xb0,   (0x30,'L'),       (0x05,'3'),       True,  3),
	('LiteDoge',              'LDOGE',   0xab,   (0x5a,'d'),       None,             False, 0),
	('LomoCoin',              'LMC',     0xb0,   (0x30,'L'),       None,             False, 0),
	('Marscoin',              'MARS',    0xb2,   (0x32,'M'),       None,             False, 0),
	('MarsCoin',              'MRS',     0xb2,   (0x32,'M'),       None,             False, 0),
	('MartexCoin',            'MXT',     0xb2,   (0x32,'M'),       None,             False, 0),
	('MasterCar',             'MCAR',    0xe6,   (0x17,'A'),       None,             False, 0),
	('MazaCoin',              'MZC',     0xe0,   (0x32,'M'),       (0x09,('4','5')), False, 2),
	('MegaCoin',              'MEC',     0xb2,   (0x32,'M'),       None,             False, 1),
	('MintCoin',              'MINT',    0xb3,   (0x33,'M'),       None,             False, 0),
	('Mobius',                'MOBI',    0x80,   (0x00,'1'),       None,             False, 0),
	('MonaCoin',              'MONA',    0xb0,   (0x32,'M'),       (0x05,'3'),       False, 1),
	('MonetaryUnit',          'MUE',     0x8f,   (0x0f,'7'),       (0x09,('4','5')), False, 1),
	('MoonCoin',              'MOON',    0x83,   (0x03,'2'),       None,             False, 0),
	('MyriadCoin',            'MYR',     0xb2,   (0x32,'M'),       (0x09,('4','5')), False, 1),
	('Myriadcoin',            'MYRIAD',  0xb2,   (0x32,'M'),       None,             False, 1),
	('Namecoin',              'NMC',     0xb4,   (0x34,('M','N')), (0x0d,'6'),       False, 1),
	('Neoscoin',              'NEOS',    0xef,   (0x3f,'S'),       (0xbc,'2'),       False, 1),
	('NevaCoin',              'NEVA',    0xb1,   (0x35,'N'),       None,             False, 0),
	('Novacoin',              'NVC',     0x88,   (0x08,'4'),       (0x14,'9'),       False, 1),
	('OKCash',                'OK',      0xb7,   (0x37,'P'),       (0x1c,'C'),       False, 1),
	('Omnicoin',              'OMC',     0xf3,   (0x73,'o'),       None,             False, 1),
	('Omni',                  'OMNI',    0xf3,   (0x73,'o'),       None,             False, 0),
	('Onix',                  'ONX',     0x80,   (0x8a,'x'),       None,             False, 0),
	('PandaCoin',             'PND',     0xb7,   (0x37,'P'),       (0x16,('9','A')), False, 1),
	('ParkByte',              'PKB',     0xb7,   (0x37,'P'),       (0x1c,'C'),       False, 1),
	('Particl',               'PART',    0x6c,   (0x38,'P'),       None,             False, 0),
	('Paycoin',               'CON',     0xb7,   (0x37,'P'),       None,             False, 1),
	('Peercoin',              'PPC',     0xb7,   (0x37,'P'),       (0x75,'p'),       False, 1),
	('PesetaCoin',            'PTC',     0xaf,   (0x2f,('K','L')), None,             False, 1),
	('PhoenixCoin',           'PXC',     0xb8,   (0x38,'P'),       None,             False, 0),
	('PinkCoin',              'PINK',    0x83,   (0x03,'2'),       None,             False, 1),
	('PIVX',                  'PIVX',    0xd4,   (0x1e,'D'),       None,             False, 0),
	('PokeChain',             'XPOKE',   0x9c,   (0x1c,'C'),       None,             False, 0),
	('Potcoin',               'POT',     0xb7,   (0x37,'P'),       (0x05,'3'),       False, 1),
	('Primecoin',             'XPM',     0x97,   (0x17,'A'),       (0x53,'a'),       False, 1),
	('Quark',                 'QRK',     0xba,   (0x3a,'Q'),       None,             False, 0),
	('ReddCoin',              'RDD',     0xbd,   (0x3d,'R'),       None,             False, 1),
	('Riecoin',               'RIC',     0x80,   (0x3c,'R'),       (0x05,'3'),       False, 2),
	('Rimbit',                'RBT',     0xbc,   (0x3c,'R'),       None,             False, 0),
	('Rubycoin',              'RBY',     0xbd,   (0x3d,'R'),       (0x55,'b'),       False, 1),
	('ShadowCash',            'SDC',     0xbf,   (0x3f,'S'),       (0x7d,'s'),       False, 1),
	('Sibcoin',               'SIB',     0x80,   (0x3f,'S'),       None,             False, 0),
	('SixEleven',             '611',     0x80,   (0x34,('M','N')), None,             False, 0),
	('SmileyCoin',            'SMLY',    0x99,   (0x19,'B'),       None,             False, 0),
	('Songcoin',              'SONG',    0xbf,   (0x3f,'S'),       None,             False, 0),
	('Spreadcoin',            'SPR',     0xbf,   (0x3f,'S'),       None,             False, 1),
	('Startcoin',             'START',   0xfd,   (0x7d,'s'),       (0x05,'3'),       False, 1),
	('StealthCoin',           'XST',     0xbe,   (0x3e,('R','S')), None,             False, 0),
	('SwagBucks',             'BUCKS',   0x99,   (0x3f,'S'),       None,             False, 0),
	('SysCoin',               'SYS',     0x80,   (0x00,'1'),       None,             False, 0),
	('TajCoin',               'TAJ',     0x6f,   (0x41,'T'),       None,             False, 0),
	('Templecoin',            'TPC',     0xc1,   (0x41,'T'),       (0x05,'3'),       False, 1),
	('Terracoin',             'TRC',     0x80,   (0x00,'1'),       None,             False, 0),
	('Titcoin',               'TIT',     0x80,   (0x00,'1'),       None,             False, 0),
	('TittieCoin',            'TTC',     0xc1,   (0x41,'T'),       None,             False, 0),
	('Transfer',              'TX',      0x99,   (0x42,'T'),       None,             False, 0),
	('Unobtanium',            'UNO',     0xe0,   (0x82,'u'),       (0x1e,'D'),       False, 2),
	('Vcash',                 'XVC',     0xc7,   (0x47,'V'),       None,             False, 0),
	('Vertcoin',              'VTC',     0xc7,   (0x47,'V'),       (0x05,'3'),       False, 1),
	('Viacoin',               'VIA',     0xc7,   (0x47,'V'),       (0x21,'E'),       False, 2),
	('VpnCoin',               'VPN',     0xc7,   (0x47,'V'),       (0x05,'3'),       False, 1),
	('WankCoin',              'WKC',     0x80,   (0x00,'1'),       None,             False, 1),
	('WashingtonCoin',        'WASH',    0xc9,   (0x49,'W'),       None,             False, 0),
	('WeAreSatoshi',          'WSX',     0x97,   (0x87,'w'),       None,             False, 0),
	('WisdomCoin',            'WISC',    0x87,   (0x49,'W'),       None,             False, 0),
	('WorldCoin',             'WDC',     0xc9,   (0x49,'W'),       None,             False, 1),
	('XRealEstateDevcoin',    'XRED',    0x80,   (0x00,'1'),       None,             False, 0),
	('ZetaCoin',              'ZET',     0xe0,   (0x50,'Z'),       None,             False, 0),
	('ZiftrCoin',             'ZRC',     0xd0,   (0x50,'Z'),       (0x05,'3'),       False, 1),
	('ZLiteQubit',            'ZLQ',     0xe0,   (0x26,'G'),       None,             False, 0),
	('Zoomcoin',              'ZOOM',    0xe7,   (0x67,'i'),       (0x5c,'e'),       False, 1),
	)

	coin_constants['testnet'] = (
	('Dash',        'DASH',  0xef,   (0x8c,'y'),       (0x13,('8','9')), False, 1),
	('Decred',      'DCR',   0x230e, (0x0f21,'T'),     (0x0e6c,'S'),     False, 1),
	('Dogecoin',    'DOGE',  0xf1,   (0x71,'n'),       (0xc4,'2'),       False, 2),
	('Feathercoin', 'FTC',   0xc1,   (0x41,'T'),       (0xc4,'2'),       False, 2),
	('Viacoin',     'VIA',   0xff,   (0x7f,'t'),       (0xc4,'2'),       False, 2),
	('Emercoin',    'EMC',   0xef,   (0x6f,('m','n')), (0xc4,'2'),       False, 2),
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

	# Sources (see above) that are in agreement for these coins
	# No check for segwit, p2sh check skipped if source doesn't support it
	cross_checks = {
		'2GIVE':  ['wn'],
		'42':     ['vg','wn'],
		'611':    ['wn'],
		'AC':     ['lb','vg'],
		'ACOIN':  ['wn'],
		'ALF':    ['wn'],
		'ANC':    ['vg','wn'],
		'APEX':   ['wn'],
		'ARCO':   ['wn'],
		'ARG':    ['pc'],
		'AUR':    ['vg','wn'],
		'BCH':    ['wn'],
		'BLK':    ['lb','vg','wn'],
		'BQC':    ['vg','wn'],
		'BSTY':   ['wn'],
		'BTC':    ['lb','vg','wn'],
		'BTCD':   ['lb','vg','wn'],
		'BUCKS':  ['wn'],
		'CASH':   ['wn'],
		'CBX':    ['wn'],
		'CCN':    ['lb','vg','wn'],
		'CDN':    ['lb','vg','wn'],
		'CHC':    ['wn'],
		'CLAM':   ['lb','vg'],
		'CON':    ['vg','wn'],
		'CPC':    ['wn'],
		'DASH':   ['lb','pc','vg','wn'],
		'DCR':    ['pc'],
		'DFC':    ['pc'],
		'DGB':    ['lb','vg'],
		'DGC':    ['lb','vg','wn'],
		'DOGE':   ['lb','pc','vg','wn'],
		'DOGED':  ['lb','vg','wn'],
		'DOPE':   ['lb','vg'],
		'DVC':    ['vg','wn'],
		'EFL':    ['lb','vg','wn'],
		'EMC':    ['vg'],
		'EMD':    ['wn'],
		'ESP':    ['wn'],
		'FAI':    ['pc'],
		'FC2':    ['wn'],
		'FIBRE':  ['wn'],
		'FJC':    ['wn'],
		'FLO':    ['wn'],
		'FLT':    ['wn'],
		'FST':    ['wn'],
		'FTC':    ['lb','pc','vg','wn'],
		'GCR':    ['lb','vg'],
		'GOOD':   ['wn'],
		'GRC':    ['vg','wn'],
		'GUN':    ['vg','wn'],
		'HAM':    ['vg','wn'],
		'HTML5':  ['wn'],
		'HYP':    ['wn'],
		'ICASH':  ['wn'],
		'INFX':   ['wn'],
		'IPC':    ['wn'],
		'JBS':    ['lb','pc','vg','wn'],
		'JUDGE':  ['wn'],
		'LANA':   ['wn'],
		'LAT':    ['wn'],
		'LDOGE':  ['wn'],
		'LMC':    ['wn'],
		'LTC':    ['lb','vg','wn'],
		'MARS':   ['wn'],
		'MEC':    ['pc','wn'],
		'MINT':   ['wn'],
		'MOBI':   ['wn'],
		'MONA':   ['lb','vg'],
		'MOON':   ['wn'],
		'MUE':    ['lb','vg'],
		'MXT':    ['wn'],
		'MYR':    ['pc'],
		'MYRIAD': ['vg','wn'],
		'MZC':    ['lb','pc','vg','wn'],
		'NEOS':   ['lb','vg'],
		'NEVA':   ['wn'],
		'NKA':    ['wn'],
		'NLG':    ['vg','wn'],
		'NMC':    ['lb','vg'],
		'NVC':    ['lb','vg','wn'],
		'OK':     ['lb','vg'],
		'OMC':    ['vg','wn'],
		'ONION':  ['vg','wn'],
		'PART':   ['wn'],
		'PINK':   ['vg','wn'],
		'PIVX':   ['wn'],
		'PKB':    ['lb','vg','wn'],
		'PND':    ['lb','vg','wn'],
		'POT':    ['lb','vg','wn'],
		'PPC':    ['lb','vg','wn'],
		'PTC':    ['vg','wn'],
		'PXC':    ['wn'],
		'QRK':    ['wn'],
		'RAIN':   ['wn'],
		'RBT':    ['wn'],
		'RBY':    ['lb','vg'],
		'RDD':    ['vg','wn'],
		'RIC':    ['pc','vg','wn'],
		'SDC':    ['lb','vg'],
		'SIB':    ['wn'],
		'SMLY':   ['wn'],
		'SONG':   ['wn'],
		'SPR':    ['vg','wn'],
		'START':  ['lb','vg'],
		'SYS':    ['wn'],
		'TAJ':    ['wn'],
		'TIT':    ['wn'],
		'TPC':    ['lb','vg'],
		'TRC':    ['wn'],
		'TTC':    ['wn'],
		'TX':     ['wn'],
		'UNO':    ['pc','vg','wn'],
		'VIA':    ['lb','pc','vg','wn'],
		'VPN':    ['lb','vg'],
		'VTC':    ['lb','vg','wn'],
		'WDC':    ['vg','wn'],
		'WISC':   ['wn'],
		'WKC':    ['vg','wn'],
		'WSX':    ['wn'],
		'XCN':    ['wn'],
		'XGB':    ['wn'],
		'XPM':    ['lb','vg','wn'],
		'XST':    ['wn'],
		'XVC':    ['wn'],
		'ZET':    ['wn'],
		'ZOOM':   ['lb','vg'],
		'ZRC':    ['lb','vg']
	}

	# data is one of the coin_constants lists above
	# normalize ints to hex, format width, add missing leading letters, set trust level from external_tests
	# Insert a coin entry from outside source, set leading letters to '?' and trust to 0, then run fix_table()
	# segwit column is updated manually for now
	@classmethod
	def fix_table(cls,data):
		import re

		def myhex(n):
			return '0x{:0{}x}'.format(n,2 if n < 256 else 4)

		def fix_col(line,n):
			line[n] = list(line[n])
			line[n][0] = myhex(line[n][0])
			s1 = cls.find_addr_leading_symbol(int(line[n][0][2:],16))
			m = 'Fixing coin {} [in data: {!r}] [computed: {}]'.format(line[0],line[n][1],s1)
			if line[n][1] != '?':
				assert s1 == line[n][1],'First letters do not match! {}'.format(m)
			else:
				msg(m)
				line[n][1] = s1
			line[n] = tuple(line[n])

		old_sym = None
		for sym in sorted([e[1] for e in data]):
			if sym == old_sym:
				msg("'{}': duplicate coin symbol in data!".format(sym))
				sys.exit(2)
			old_sym = sym

		tt = cls.create_trust_table()

		w = max(len(e[0]) for e in data)
		fs = '\t({{:{}}} {{:10}} {{:7}} {{:17}} {{:17}} {{:6}} {{}}),'.format(w+3)
		for line in data:
			line = list(line)
			line[2] = myhex(line[2])

			fix_col(line,3)
			if type(line[4]) == tuple: fix_col(line,4)

			sym,trust = line[1],line[6]

			for n in range(len(line)):
				line[n] = repr(line[n])
				line[n] = re.sub(r"'0x(..)'",r'0x\1',line[n])
				line[n] = re.sub(r"'0x(....)'",r'0x\1',line[n])
				line[n] = re.sub(r' ',r'',line[n]) + ('',',')[n != len(line)-1]

			from mmgen.util import pmsg,pdie
#			pmsg(sym)
#			pdie(tt)
			if trust != -1:
				if sym in tt:
					src = tt[sym]
					if src != trust:
						msg("Updating trust for coin '{}': {} -> {}".format(sym,trust,src))
						line[6] = src
				else:
					if trust != 0:
						msg("Downgrading trust for coin '{}': {} -> {}".format(sym,trust,0))
						line[6] = 0

				if sym in cls.cross_checks:
					if int(line[6]) == 0 and len(cls.cross_checks[sym]) > 1:
						msg("Upgrading trust for coin '{}': {} -> {}".format(sym,line[6],1))
						line[6] = 1

			print((fs.format(*line)))
		msg('Processed {} entries'.format(len(data)))

	@classmethod
	def find_addr_leading_symbol(cls,ver_num,verbose=False):

		def phash2addr(ver_num,pk_hash):
			from mmgen.protocol import _b58chk_encode
			s = '{:0{}x}'.format(ver_num,2 if ver_num < 256 else 4) + pk_hash
			lzeroes = (len(s) - len(s.lstrip('0'))) / 2 # non-zero only for ver num '00' (BTC p2pkh)
			return ('1' * lzeroes) + _b58chk_encode(s)

		low = phash2addr(ver_num,'00'*20)
		high = phash2addr(ver_num,'ff'*20)

		if verbose:
			print(('low address:  ' + low))
			print(('high address: ' + high))

		l1,h1 = low[0],high[0]
		return (l1,h1) if l1 != h1 else l1

	@classmethod
	def print_symbols(cls,include_names=False,reverse=False):
		w = max(len(e[0]) for e in cls.coin_constants['mainnet'])
		for line in cls.coin_constants['mainnet']:
			if reverse:
				print(('{:6} {}'.format(line[1],line[0])))
			else:
				print((('','{:{}} '.format(line[0],w))[include_names] + line[1]))

	@classmethod
	def create_trust_table(cls):
		tt = {}
		mn = cls.external_tests['mainnet']
		for ext_prog in mn:
			assert len(set(mn[ext_prog])) == len(mn[ext_prog]),"Duplicate entry in '{}'!".format(ext_prog)
			for coin in mn[ext_prog]:
				if coin in tt:
					tt[coin] += 1
				else:
					tt[coin] = 1
		for k in cls.trust_override:
			tt[k] = cls.trust_override[k]
		return tt

	trust_override = {'BTC':3,'BCH':3,'LTC':3,'DASH':1,'EMC':2}
	external_tests = {
		'mainnet': {
			'pycoin': (
				# broken: DASH - only compressed, LTC segwit old fmt
				'BTC','LTC','VIA','FTC','DOGE','MEC','MYR','UNO',
				'JBS','MZC','RIC','DFC','FAI','ARG','ZEC','DCR'),
			'pyethereum': ('ETH','ETC'),
			'zcash_mini': ('ZEC',),
			'keyconv': ( # all supported by vanitygen-plus 'keyconv' util
				# broken: PIVX
				'42','AC','AIB','ANC','ARS','ATMOS','AUR','BLK','BQC','BTC','TEST','BTCD','CCC','CCN','CDN',
				'CLAM','CNC','CNOTE','CON','CRW','DEEPONION','DGB','DGC','DMD','DOGED','DOGE','DOPE',
				'DVC','EFL','EMC','EXCL','FAIR','FLOZ','FTC','GAME','GAP','GCR','GRC','GRS','GUN','HAM','HODL',
				'IXC','JBS','LBRY','LEAF','LTC','MMC','MONA','MUE','MYRIAD','MZC','NEOS','NLG','NMC','NVC',
				'NYAN','OK','OMC','PIGGY','PINK','PKB','PND','POT','PPC','PTC','PTS','QTUM','RBY','RDD',
				'RIC','SCA','SDC','SKC','SPR','START','SXC','TPC','UIS','UNO','VIA','VPN','VTC','WDC','WKC',
				'WUBS', 'XC', 'XPM', 'YAC', 'ZOOM', 'ZRC')
		},
		'testnet': {
			'pycoin': {
				# broken: DASH - only compressed { 'DASH':'tDASH' }
				'BTC':'XTN','LTC':'XLT','VIA':'TVI','FTC':'FTX','DOGE':'XDT','DCR':'DCRT'
				},
			'pyethereum': {},
			'keyconv': {}
		}
	}
	external_tests_segwit_compressed = {
		'segwit': ('BTC'),
		'compressed': (
		'BTC','LTC','VIA','FTC','DOGE','DASH','MEC','MYR','UNO',
		'JBS','MZC','RIC','DFC','FAI','ARG','ZEC','DCR','ZEC'),
	}

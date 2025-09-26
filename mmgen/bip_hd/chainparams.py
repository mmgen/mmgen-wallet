#!/usr/bin/env python3
#
# Created using scripts/create-bip-hd-chain-params.py
# Source data:
#   https://github.com/MetaMask/slip44/blob/main/slip44.json (1bc984bee)
#   https://github.com/ebellocchia/bip_utils (5649541c6)

from collections import namedtuple

def parse_data():

	_d = namedtuple(
		'bip_hd_data',
		'idx chain curve network addr_cls vb_prv vb_pub vb_wif vb_addr def_path name')
	_u = namedtuple(
		'bip_hd_data_partial',
		'idx chain name')

	def parse_line(line):
		match line.split():
			case [idx, chain, col3, *name] if col3 == '-':
				return _u(
					idx   = int(idx),
					chain = chain,
					name  = ' '.join(name))
			case [idx, chain, curve, net, acls, vprv, vpub, vwif, vaddr, dpath, *name]:
				return _d(
					idx      = int(idx),
					chain    = chain,
					curve    = defaults.curve if curve == 'x' else curve,
					network  = 'mainnet' if net == 'm' else 'testnet' if net == 'T' else None,
					addr_cls = acls,
					vb_prv   = defaults.vb_prv if vprv == 'x' else vprv,
					vb_pub   = defaults.vb_pub if vpub == 'x' else vpub,
					vb_wif   = vwif,
					vb_addr  = vaddr,
					def_path = defaults.def_path if dpath == 'x' else dpath,
					name     = ' '.join(name))
			case _:
				raise ValueError(f'{line!r}: invalid line')

	out = {}
	for line in _data_in.strip().splitlines():
		if not line or line.startswith('IDX'):
			continue
		if line.startswith('['):
			key = line[1:-1]
			continue
		p = parse_line(line)
		match key:
			case k if k in out:
				out[key][p[1]] = p
			case 'defaults':
				out['defaults'] = p
				defaults = p
			case _:
				out[key] = {p[1]: p}

	return out

# RUNE derivation is SLIP-10, not BIP-44, but we treat them as equivalent

_data_in = """

[defaults]
IDX    CHAIN  CURVE NW ADDR_CLS         VB_PRV   VB_PUB   VB_WIF VB_ADDR  DFL_PATH NAME
0      -      secp  -  -                0488ade4 0488b21e -      -        0'/0/0   -

[bip-44]
IDX    CHAIN  CURVE NW ADDR_CLS         VB_PRV   VB_PUB   VB_WIF VB_ADDR  DFL_PATH NAME
0      BTC    x     m  P2PKH            x        x        80     00       x        Bitcoin
1      ---    x     T  P2PKH            04358394 043587cf ef     1d25     x        Testnet (all coins)
2      LTC    x     m  P2PKH            x        x        b0     spec     x        Litecoin
3      DOGE   x     m  P2PKH            02fac398 02facafd 9e     1e       x        Dogecoin
5      DASH   x     m  P2PKH            x        x        cc     4c       x        Dash
60     ETH    x     m  Eth              x        x        -      -        x        Ethereum
61     ETC    x     m  Eth              x        x        -      -        x        Ether Classic
74     ICX    x     m  Icx              x        x        -      -        x        ICON
77     XVG    x     m  P2PKH            x        x        9e     1e       x        Verge Currency
118    ATOM   x     m  Atom             x        x        -      h:stafi  x        Atom
128    XMR    x     m  Xmr              x        x        -      -        x        Monero
133    ZEC    x     m  P2PKH            x        x        80     1cb8     x        Zcash
144    XRP    x     m  Xrp              x        x        -      -        x        Ripple
145    BCH    x     m  BchP2PKH         x        x        80     spec     x        Bitcoin Cash
148    XLM    edw   m  Xlm              x        x        -      spec     0'       Stellar Lumens
165    XNO    blk   m  Nano             x        x        -      -        0'       Nano
194    EOS    x     m  Eos              x        x        -      -        x        EOS
195    TRX    x     m  Trx              x        x        -      -        x        Tron
236    BSV    x     m  P2PKH            x        x        80     00       x        BitcoinSV
283    ALGO   edw   m  Algo             x        x        -      -        0'/0'/0' Algorand
313    ZIL    x     m  Zil              x        x        -      -        x        Zilliqa
330    LUNA   x     m  Atom             x        x        -      h:terra  x        Terra
354    DOT    edw   m  SubstrateEd25519 x        x        -      spec     0'/0'/0' Polkadot
397    NEAR   edw   m  Near             x        x        -      -        0'       NEAR Protocol
429    ERG    x     T  ErgoP2PKH        04358394 043587cf -      spec     x        Ergo
434    KSM    edw   m  SubstrateEd25519 x        x        -      spec     0'/0'/0' Kusama
459    KAVA   x     m  Atom             x        x        -      h:kava   x        Kava
461    FIL    x     m  FilSecp256k1     x        x        -      -        x        Filecoin
494    BAND   x     m  Atom             x        x        -      h:band   x        Band
500    THETA  x     m  Eth              x        x        -      -        x        Theta
501    SOL    edw   m  Sol              x        x        -      -        0'       Solana
508    EGLD   edw   m  Egld             x        x        -      -        0'/0'/0' MultiversX
529    SCRT   x     m  Atom             x        x        -      h:secret x        Secret Network
567    NCG    x     m  Eth              x        x        -      -        x        Nine Chronicles
637    APTOS  edw   m  Aptos            x        x        -      -        0'/0'/0' Aptos
714    BNB    x     m  Atom             x        x        -      h:bnb    x        Binance
784    SUI    edw   m  Sui              x        x        -      -        0'/0'/0' Sui
818    VET    x     m  Eth              x        x        -      -        x        VeChain Token
888    NEO    nist  m  Neo              x        x        -      spec     x        NEO
931    RUNE   x     m  BechP2PKH        x        x        -      h:thor   x        THORChain
996    OKT    x     m  Okex             x        x        -      -        x        OKChain Token
1023   ONE    x     m  One              x        x        -      -        x        HARMONY-ONE (Legacy)
1024   ONT    nist  m  Neo              x        x        -      spec     x        Ontology
1729   XTZ    edw   m  Xtz              x        x        -      spec     0'/0'    Tezos
1815   ADA    khol  m  AdaByronIcarus   0f4331d4 x        -      spec     x        Cardano
9000   AVAX   x     m  AvaxXChain       x        x        -      -        x        Avalanche
52752  CELO   x     m  Eth              x        x        -      -        x        Celo
314159 PI     edw   m  Xlm              x        x        -      spec     0'       Pi Network

[bip-49]
IDX    CHAIN  CURVE NW ADDR_CLS         VB_PRV   VB_PUB   VB_WIF VB_ADDR  DFL_PATH NAME
0      BTC    x     m  P2SH             049d7878 049d7cb2 80     05       x        Bitcoin
1      ZEC    x     T  P2SH             044a4e28 044a5262 ef     1cba     x        Zcash TestNet
2      LTC    x     m  P2SH             049d7878 049d7cb2 b0     spec     x        Litecoin
3      DOGE   x     m  P2SH             02fac398 02facafd 9e     16       x        Dogecoin
5      DASH   x     m  P2SH             049d7878 049d7cb2 cc     10       x        Dash
133    ZEC    x     m  P2SH             049d7878 049d7cb2 80     1cbd     x        Zcash
145    XEC    x     m  BchP2SH          049d7878 049d7cb2 80     spec     x        eCash
236    BSV    x     m  P2SH             049d7878 049d7cb2 80     05       x        BitcoinSV

[bip-84]
IDX    CHAIN  CURVE NW ADDR_CLS         VB_PRV   VB_PUB   VB_WIF VB_ADDR  DFL_PATH NAME
0      BTC    x     m  P2WPKH           04b2430c 04b24746 80     h:bc     x        Bitcoin
1      LTC    x     T  P2WPKH           0436ef7d 0436f6e1 ef     h:tltc   x        Litecoin TestNet
2      LTC    x     m  P2WPKH           04b2430c 04b24746 b0     h:ltc    x        Litecoin

[bip-86]
IDX    CHAIN  CURVE NW ADDR_CLS         VB_PRV   VB_PUB   VB_WIF VB_ADDR  DFL_PATH NAME
0      BTC    x     m  P2TR             x        x        80     h:bc     x        Bitcoin
1      BTC    x     T  P2TR             04358394 043587cf ef     h:tb     x        Bitcoin TestNet

[bip-44-unsupported]
IDX    CHAIN    NAME
4      RDD    - Reddcoin
6      PPC    - Peercoin
7      NMC    - Namecoin
8      FTC    - Feathercoin
9      XCP    - Counterparty
10     BLK    - Blackcoin
11     NSR    - NuShares
12     NBT    - NuBits
13     MZC    - Mazacoin
14     VIA    - Viacoin
15     XCH    - ClearingHouse
16     RBY    - Rubycoin
17     GRS    - Groestlcoin
18     DGC    - Digitalcoin
19     CCN    - Cannacoin
20     DGB    - DigiByte
21     ---    - Open Assets
22     MONA   - Monacoin
23     CLAM   - Clams
24     XPM    - Primecoin
25     NEOS   - Neoscoin
26     JBS    - Jumbucks
27     ZRC    - ziftrCOIN
28     VTC    - Vertcoin
29     NXT    - NXT
30     BURST  - Burst
31     MUE    - MonetaryUnit
32     ZOOM   - Zoom
33     VASH   - Virtual Cash
34     CDN    - Canada eCoin
35     SDC    - ShadowCash
36     PKB    - ParkByte
37     PND    - Pandacoin
38     START  - StartCOIN
39     MOIN   - MOIN
40     EXP    - Expanse
41     EMC2   - Einsteinium
42     DCR    - Decred
43     XEM    - NEM
44     PART   - Particl
45     ARG    - Argentum (dead)
46     ---    - Libertas
47     ---    - Posw coin
48     SHR    - Shreeji
49     GCR    - Global Currency Reserve (GCRcoin)
50     NVC    - Novacoin
51     AC     - Asiacoin
52     BTCD   - BitcoinDark
53     DOPE   - Dopecoin
54     TPC    - Templecoin
55     AIB    - AIB
56     EDRC   - EDRCoin
57     SYS    - Syscoin
58     SLR    - Solarcoin
59     SMLY   - Smileycoin
62     PSB    - Pesobit
63     LDCN   - Landcoin (dead)
64     ---    - Open Chain
65     XBC    - Bitcoinplus
66     IOP    - Internet of People
67     NXS    - Nexus
68     INSN   - InsaneCoin
69     OK     - OKCash
70     BRIT   - BritCoin
71     CMP    - Compcoin
72     CRW    - Crown
73     BELA   - BelaCoin
75     FJC    - FujiCoin
76     MIX    - MIX
78     EFL    - Electronic Gulden
79     CLUB   - ClubCoin
80     RICHX  - RichCoin
81     POT    - Potcoin
82     QRK    - Quarkcoin
83     TRC    - Terracoin
84     GRC    - Gridcoin
85     AUR    - Auroracoin
86     IXC    - IXCoin
87     NLG    - Gulden
88     BITB   - BitBean
89     BTA    - Bata
90     XMY    - Myriadcoin
91     BSD    - BitSend
92     UNO    - Unobtanium
93     MTR    - MasterTrader
94     GB     - GoldBlocks
95     SHM    - Saham
96     CRX    - Chronos
97     BIQ    - Ubiquoin
98     EVO    - Evotion
99     STO    - SaveTheOcean
100    BIGUP  - BigUp
101    GAME   - GameCredits
102    DLC    - Dollarcoins
103    ZYD    - Zayedcoin
104    DBIC   - Dubaicoin
105    STRAT  - Stratis
106    SH     - Shilling
107    MARS   - MarsCoin
108    UBQ    - Ubiq
109    PTC    - Pesetacoin
110    NRO    - Neurocoin
111    ARK    - ARK
112    USC    - UltimateSecureCashMain
113    THC    - Hempcoin
114    LINX   - Linx
115    ECN    - Ecoin
116    DNR    - Denarius
117    PINK   - Pinkcoin
119    PIVX   - Pivx
120    FLASH  - Flashcoin
121    ZEN    - Zencash
122    PUT    - Putincoin
123    ZNY    - BitZeny
124    UNIFY  - Unify
125    XST    - StealthCoin
126    BRK    - Breakout Coin
127    VC     - Vcash
129    VOX    - Voxels
130    NAV    - NavCoin
131    FCT    - Factom Factoids
132    EC     - Factom Entry Credits
134    LSK    - Lisk
135    STEEM  - Steem
136    XZC    - ZCoin
137    RBTC   - RSK
138    ---    - Giftblock
139    RPT    - RealPointCoin
140    LBC    - LBRY Credits
141    KMD    - Komodo
142    BSQ    - bisq Token
143    RIC    - Riecoin
146    NEBL   - Neblio
147    ZCL    - ZClassic
149    NLC2   - NoLimitCoin2
150    WHL    - WhaleCoin
151    ERC    - EuropeCoin
152    DMD    - Diamond
153    BTM    - Bytom
154    BIO    - Biocoin
155    XWCC   - Whitecoin Classic
156    BTG    - Bitcoin Gold
157    BTC2X  - Bitcoin 2x
158    SSN    - SuperSkynet
159    TOA    - TOACoin
160    BTX    - Bitcore
161    ACC    - Adcoin
162    BCO    - Bridgecoin
163    ELLA   - Ellaism
164    PIRL   - Pirl
166    VIVO   - Vivo
167    FRST   - Firstcoin
168    HNC    - Helleniccoin
169    BUZZ   - BUZZ
170    MBRS   - Ember
171    HC     - Hcash
172    HTML   - HTMLCOIN
173    ODN    - Obsidian
174    ONX    - OnixCoin
175    RVN    - Ravencoin
176    GBX    - GoByte
177    BTCZ   - BitcoinZ
178    POA    - Poa
179    NYC    - NewYorkCoin
180    MXT    - MarteXcoin
181    WC     - Wincoin
182    MNX    - Minexcoin
183    BTCP   - Bitcoin Private
184    MUSIC  - Musicoin
185    BCA    - Bitcoin Atom
186    CRAVE  - Crave
187    STAK   - STRAKS
188    WBTC   - World Bitcoin
189    LCH    - LiteCash
190    EXCL   - ExclusiveCoin
191    ---    - Lynx
192    LCC    - LitecoinCash
193    XFE    - Feirm
196    KOBO   - Kobocoin
197    HUSH   - HUSH
198    BAN    - Banano
199    ETF    - ETF
200    OMNI   - Omni
201    BIFI   - BitcoinFile
202    UFO    - Uniform Fiscal Object
203    CNMC   - Cryptonodes
204    BCN    - Bytecoin
205    RIN    - Ringo
206    ATP    - Alaya
207    EVT    - everiToken
208    ATN    - ATN
209    BIS    - Bismuth
210    NEET   - NEETCOIN
211    BOPO   - BopoChain
212    OOT    - Utrum
213    ALIAS  - Alias
214    MONK   - Monkey Project
215    BOXY   - BoxyCoin
216    FLO    - Flo
217    MEC    - Megacoin
218    BTDX   - BitCloud
219    XAX    - Artax
220    ANON   - ANON
221    LTZ    - LitecoinZ
222    BITG   - Bitcoin Green
223    ICP    - Internet Computer (DFINITY)
224    SMART  - Smartcash
225    XUEZ   - XUEZ
226    HLM    - Helium
227    WEB    - Webchain
228    ACM    - Actinium
229    NOS    - NOS Stable Coins
230    BITC   - BitCash
231    HTH    - Help The Homeless Coin
232    TZC    - Trezarcoin
233    VAR    - Varda
234    IOV    - IOV
235    FIO    - FIO
237    DXN    - DEXON
238    QRL    - Quantum Resistant Ledger
239    PCX    - ChainX
240    LOKI   - Loki
241    ---    - Imagewallet
242    NIM    - Nimiq
243    SOV    - Sovereign Coin
244    JCT    - Jibital Coin
245    SLP    - Simple Ledger Protocol
246    EWT    - Energy Web
247    UC     - Ulord
248    EXOS   - EXOS
249    ECA    - Electra
250    SOOM   - Soom
251    XRD    - Redstone
252    FREE   - FreeCoin
253    NPW    - NewPowerCoin
254    BST    - BlockStamp
255    ---    - SmartHoldem
256    NANO   - Bitcoin Nano
257    BTCC   - Bitcoin Core
258    ---    - Zen Protocol
259    ZEST   - Zest
260    ABT    - ArcBlock
261    PION   - Pion
262    DT3    - DreamTeam3
263    ZBUX   - Zbux
264    KPL    - Kepler
265    TPAY   - TokenPay
266    ZILLA  - ChainZilla
267    ANK    - Anker
268    BCC    - BCChain
269    HPB    - HPB
270    ONE    - ONE
271    SBC    - SBC
272    IPC    - IPChain
273    DMTC   - Dominantchain
274    OGC    - Onegram
275    SHIT   - Shitcoin
276    ANDES  - Andescoin
277    AREPA  - Arepacoin
278    BOLI   - Bolivarcoin
279    RIL    - Rilcoin
280    HTR    - Hathor Network
281    ACME   - Accumulate
282    BRAVO  - BRAVO
284    BZX    - Bitcoinzero
285    GXX    - GravityCoin
286    HEAT   - HEAT
287    XDN    - DigitalNote
288    FSN    - FUSION
289    CPC    - Capricoin
290    BOLD   - Bold
291    IOST   - IOST
292    TKEY   - Tkeycoin
293    USE    - Usechain
294    BCZ    - BitcoinCZ
295    IOC    - Iocoin
296    ASF    - Asofe
297    MASS   - MASS
298    FAIR   - FairCoin
299    NUKO   - Nekonium
300    GNX    - Genaro Network
301    DIVI   - Divi Project
302    CMT    - Community
303    EUNO   - EUNO
304    IOTX   - IoTeX
305    ONION  - DeepOnion
306    8BIT   - 8Bit
307    ATC    - AToken Coin
308    BTS    - Bitshares
309    CKB    - Nervos CKB
310    UGAS   - Ultrain
311    ADS    - Adshares
312    ARA    - Aura
314    MOAC   - MOAC
315    SWTC   - SWTC
316    VNSC   - vnscoin
317    PLUG   - Pl^g
318    MAN    - Matrix AI Network
319    ECC    - ECCoin
320    RPD    - Rapids
321    RAP    - Rapture
322    GARD   - Hashgard
323    ZER    - Zero
324    EBST   - eBoost
325    SHARD  - Shard
326    MRX    - Metrix Coin
327    CMM    - Commercium
328    BLOCK  - Blocknet
329    AUDAX  - AUDAX
331    ZPM    - zPrime
332    KUVA   - Kuva Utility Note
333    MEM    - MemCoin
334    CS     - Credits
335    SWIFT  - SwiftCash
336    FIX    - FIX
337    CPC    - CPChain
338    VGO    - VirtualGoodsToken
339    DVT    - DeVault
340    N8V    - N8VCoin
341    MTNS   - OmotenashiCoin
342    BLAST  - BLAST
343    DCT    - DECENT
344    AUX    - Auxilium
345    USDP   - USDP
346    HTDF   - HTDF
347    YEC    - Ycash
348    QLC    - QLC Chain
349    TEA    - Icetea Blockchain
350    ARW    - ArrowChain
351    MDM    - Medium
352    CYB    - Cybex
353    LTO    - LTO Network
355    AEON   - Aeon
356    RES    - Resistance
357    AYA    - Aryacoin
358    DAPS   - Dapscoin
359    CSC    - CasinoCoin
360    VSYS   - V Systems
361    NOLLAR - Nollar
362    XNOS   - NOS
363    CPU    - CPUchain
364    LAMB   - Lambda Storage Chain
365    VCT    - ValueCyber
366    CZR    - Canonchain
367    ABBC   - ABBC
368    HET    - HET
369    XAS    - Asch
370    VDL    - Vidulum
371    MED    - MediBloc
372    ZVC    - ZVChain
373    VESTX  - Vestx
374    DBT    - DarkBit
375    SEOS   - SuperEOS
376    MXW    - Maxonrow
377    ZNZ    - ZENZO
378    XCX    - XChain
379    SOX    - SonicX
380    NYZO   - Nyzo
381    ULC    - ULCoin
382    RYO    - Ryo Currency
383    KAL    - Kaleidochain
384    XSN    - Stakenet
385    DOGEC  - DogeCash
386    BMV    - Bitcoin Matteo's Vision
387    QBC    - Quebecoin
388    IMG    - ImageCoin
389    QOS    - QOS
390    PKT    - PKT
391    LHD    - LitecoinHD
392    CENNZ  - CENNZnet
393    HSN    - Hyper Speed Network
394    CRO    - Crypto Chain
395    UMBRU  - Umbru
396    EVER   - Everscale
398    XPC    - XPChain
399    ZOC    - 01coin
400    NIX    - NIX
401    UC     - Utopiacoin
402    GALI   - Galilel
403    OLT    - Oneledger
404    XBI    - XBI
405    DONU   - DONU
406    EARTHS - Earths
407    HDD    - HDDCash
408    SUGAR  - Sugarchain
409    AILE   - AileCoin
410    TENT   - TENT
411    TAN    - Tangerine Network
412    AIN    - AIN
413    MSR    - Masari
414    SUMO   - Sumokoin
415    ETN    - Electroneum
416    BYTZ   - BYTZ
417    WOW    - Wownero
418    XTNC   - XtendCash
419    LTHN   - Lethean
420    NODE   - NodeHost
421    AGM    - Argoneum
422    CCX    - Conceal Network
423    TNET   - Title Network
424    TELOS  - TelosCoin
425    AION   - Aion
426    BC     - Bitcoin Confidential
427    KTV    - KmushiCoin
428    ZCR    - ZCore
430    PESO   - Criptopeso
431    BTC2   - Bitcoin 2
432    XRPHD  - XRPHD
433    WE     - WE Coin
435    PCN    - Peepcoin
436    NCH    - NetCloth
437    ICU    - CHIPO
438    FNSA   - FINSCHIA
439    DTP    - DeVault Token Protocol
440    BTCR   - Bitcoin Royale
441    AERGO  - AERGO
442    XTH    - Dothereum
443    LV     - Lava
444    PHR    - Phore
445    VITAE  - Vitae
446    COCOS  - Cocos-BCX
447    DIN    - Dinero
448    SPL    - Simplicity
449    YCE    - MYCE
450    XLR    - Solaris
451    KTS    - Klimatas
452    DGLD   - DGLD
453    XNS    - Insolar
454    EM     - EMPOW
455    SHN    - ShineBlocks
456    SEELE  - Seele
457    AE     - æternity
458    ODX    - ObsidianX
460    GLEEC  - GLEEC
462    RUTA   - Rutanio
463    CSDT   - CSDT
464    ETI    - EtherInc
465    ZSLP   - Zclassic Simple Ledger Protocol
466    ERE    - EtherCore
467    DX     - DxChain Token
468    CPS    - Capricoin+
469    BTH    - Bithereum
470    MESG   - MESG
471    FIMK   - FIMK
472    AR     - Arweave
473    OGO    - Origo
474    ROSE   - Oasis Network
475    BARE   - BARE Network
476    GLEEC  - GleecBTC
477    CLR    - Color Coin
478    RNG    - Ring
479    OLO    - Tool Global
480    PEXA   - Pexa
481    MOON   - Mooncoin
482    OCEAN  - Ocean Protocol
483    BNT    - Bluzelle Native
484    AMO    - AMO Blockchain
485    FCH    - FreeCash
486    LAT    - PlatON
487    COIN   - Bitcoin Bank
488    VEO    - Amoveo
489    CCA    - Counos Coin
490    GFN    - Graphene
491    BIP    - Minter Network
492    KPG    - Kunpeng Network
493    FIN    - FINL Chain
495    DROP   - Dropil
496    BHT    - Bluehelix Chain
497    LYRA   - Scrypta
498    CS     - Credits
499    RUPX   - Rupaya
502    THT    - ThoughtAI
503    CFX    - Conflux
504    KUMA   - Kumacoin
505    HASH   - Provenance
506    CSPR   - Casper
507    EARTH  - EARTH
509    CHI    - Xaya
510    KOTO   - Koto
511    OTC    - θ
512    XRD    - Radiant
513    SEELEN - Seele-N
514    AETH   - AETH
515    DNA    - Idena
516    VEE    - Virtual Economy Era
517    SIERRA - SierraCoin
518    LET    - Linkeye
519    BSC    - Bitcoin Smart Contract
520    BTCV   - BitcoinVIP
521    ABA    - Dabacus
522    SCC    - StakeCubeCoin
523    EDG    - Edgeware
524    AMS    - AmsterdamCoin
525    GOSS   - GOSSIP Coin
526    BU     - BUMO
527    GRAM   - GRAM
528    YAP    - Yapstone
530    NOVO   - Novo
531    GHOST  - Ghost
532    HST    - HST
533    PRJ    - ProjectCoin
534    YOU    - YOUChain
535    XHV    - Haven Protocol
536    BYND   - Beyondcoin
537    JOYS   - Joys Digital
538    VAL    - Valorbit
539    FLOW   - Flow
540    SMESH  - Spacemesh Coin
541    SCDO   - SCDO
542    IQS    - IQ-Cash
543    BIND   - Compendia
544    COINEVO - Coinevo
545    SCRIBE - Scribe
546    HYN    - Hyperion
547    BHP    - BHP
548    BBC    - BigBang Core
549    MKF    - MarketFinance
550    XDC    - XinFin
551    STR    - Straightedge
552    SUM    - Sumcoin
553    HBC    - HuobiChain
554    ---    - reserved
555    BCS    - Bitcoin Smart
556    KTS    - Kratos
557    LKR    - Lkrcoin
558    TAO    - Tao
559    XWC    - Whitecoin
560    DEAL   - DEAL
561    NTY    - Nexty
562    TOP    - TOP NetWork
563    ---    - reserved
564    AG     - Agoric
565    CICO   - Coinicles
566    IRIS   - Irisnet
568    LRG    - Large Coin
569    SERO   - Super Zero Protocol
570    BDX    - Beldex
571    CCXX   - Counos X
572    SLS    - Saluscoin
573    SRM    - Serum
574    ---    - reserved
575    VIVT   - VIDT Datalink
576    BPS    - BitcoinPoS
577    NKN    - NKN
578    ICL    - ILCOIN
579    BONO   - Bonorum
580    PLC    - PLATINCOIN
581    DUN    - Dune
582    DMCH   - Darmacash
583    CTC    - Creditcoin
584    KELP   - Haidai Network
585    GBCR   - GoldBCR
586    XDAG   - XDAG
587    PRV    - Incognito Privacy
588    SCAP   - SafeCapital
589    TFUEL  - Theta Fuel
590    GTM    - Gentarium
591    RNL    - RentalChain
592    GRIN   - Grin
593    MWC    - MimbleWimbleCoin
594    DOCK   - Dock
595    POLYX  - Polymesh
596    DIVER  - Divergenti
597    XEP    - Electra Protocol
598    APN    - Apron
599    TFC    - Turbo File Coin
600    UTE    - Unit-e
601    MTC    - Metacoin
602    NC     - NobodyCash
603    XINY   - Xinyuehu
604    DYN    - Dynamo
605    BUFS   - Buffer
606    STOS   - Stratos
607    TON    - TON
608    TAFT   - TAFT
609    HYDRA  - HYDRA
610    NOR    - Noir
611    ---    - Manta Network Private Asset
612    ---    - Calamari Network Private Asset
613    WCN    - Widecoin
614    OPT    - Optimistic Ethereum
615    PSWAP  - PolkaSwap
616    VAL    - Validator
617    XOR    - Sora
618    SSP    - SmartShare
619    DEI    - DeimosX
620    ---    - reserved
621    ZERO   - Singularity
622    ALPHA  - AlphaDAO
623    BDECO  - BDCashProtocol Ecosystem
624    NOBL   - Nobility
625    EAST   - Eastcoin
626    KDA    - Kadena
627    SOUL   - Phantasma
628    LORE   - Gitopia
629    FNR    - Fincor
630    NEXUS  - Nexus
631    QTZ    - Quartz
632    MAS    - Massa
633    CALL   - Callchain
634    VAL    - Validity
635    POKT   - Pocket Network
636    EMIT   - EMIT
638    ADON   - ADON
639    BTSG   - BitSong
640    LFC    - Leofcoin
641    KCS    - KuCoin Shares
642    KCC    - KuCoin Community Chain
643    AZERO  - Aleph Zero
644    TREE   - Tree
645    LX     - Lynx
646    XLN    - Lunarium
647    CIC    - CIC Chain
648    ZRB    - Zarb
649    ---    - reserved
650    UCO    - Archethic
651    SFX    - Safex Cash
652    SFT    - Safex Token
653    WSFX   - Wrapped Safex Cash
654    USDG   - US Digital Gold
655    WMP    - WAMP
656    EKTA   - Ekta
657    YDA    - YadaCoin
659    KOIN   - Koinos
660    PIRATE - PirateCash
661    UNQ    - Unique
663    SFRX   - EtherGem Sapphire
666    ACT    - Achain
667    PRKL   - Perkle
668    SSC    - SelfSell
669    GC     - GateChain
670    PLGR   - Pledger
671    MPLGR  - Pledger
672    KNOX   - Knox
673    ZED    - ZED
674    CNDL   - Candle
675    WLKR   - Walker Crypto Innovation Index
676    WLKRR  - Walker
677    YUNGE  - Yunge
678    Voken  - Voken
679    APL    - Apollo
680    Evrynet - Evrynet
681    NENG   - Nengcoin
682    CHTA   - Cheetahcoin
683    ALEO   - Aleo Network
685    OAS    - Oasys
686    KAR    - Karura Network
688    CET    - CoinEx Chain
690    KLV    - KleverChain
694    VTBC   - VTB Community
698    VEIL   - Veil
699    GTB    - GotaBit
700    XDAI   - xDai
701    COM    - Commercio
702    CCC    - Commercio Cash Credit
707    MCOIN  - Moneta Coin
710    FURY   - Highbury
711    CHC    - Chaincoin
712    SERF   - Serfnet
713    XTL    - Katal Chain
715    SIN    - Sinovate
716    DLN    - Delion
717    BONTE  - Bontecoin
718    PEER   - Peer
719    ZET    - Zetacoin
720    ABY    - Artbyte
721    PGX    - Mirai Chain
722    IL8P   - InfiniLooP
724    XVC    - Vanillacash
725    MCX    - MultiCash
727    BLU    - BluCrates
730    HEALIOS - Tenacity
731    BMK    - Bitmark
734    DENTX  - DENTNet
737    ATOP   - Financial Blockchain
747    CFG    - Centrifuge
750    XPRT   - Persistence
753    ---    - Age X25519 Encryption
754    ---    - Age NIST Encryption
757    HONEY  - HoneyWood
768    BALLZ  - Ballzcoin
770    COSA   - Cosanta
771    BR     - BR
775    PLSR   - Pulsar Coin
776    KEY    - Keymaker Coin
777    BTW    - Bitcoin World
780    PLCUC  - PLC Ultima Classic
781    PLCUX  - PLC Ultima X
782    PLCU   - PLC Ultima
783    SMARTBC - SMART Blockchain
786    UIDD   - UIDD
787    ACA    - Acala
788    BNC    - Bifrost
789    TAU    - Lamden
799    PDEX   - Polkadex
800    BEET   - Beetle Coin
801    DST    - DSTRA
802    CY     - Cyberyen
804    ZKS    - zkSync
808    QVT    - Qvolta
809    SDN    - Shiden Network
810    ASTR   - Astar Network
811    ---    - reserved
813    MEER   - Qitmeer
819    REEF   - Reef
820    CLO    - Callisto
822    BDB    - BigchainDB
827    ACE    - Endurance
828    CCN    - ComputeCoin
829    BBA    - BBACHAIN
831    CRUZ   - cruzbit
832    SAPP   - Sapphire
833    777    - Jackpot
834    KYAN   - Kyanite
835    AZR    - Azzure
836    CFL    - CryptoFlow
837    DASHD  - Dash Diamond
838    TRTT   - Trittium
839    UCR    - Ultra Clear
840    PNY    - Peony
841    BECN   - Beacon
842    MONK   - Monk
843    SAGA   - CryptoSaga
844    SUV    - Suvereno
845    ESK    - EskaCoin
846    OWO    - OneWorld Coin
847    PEPS   - PEPS Coin
848    BIR    - Birake
849    MOBIC  - MobilityCoin
850    FLS    - Flits
852    DSM    - Desmos
853    PRCY   - PRCY Coin
858    HVH    - HAVAH
866    MOB    - MobileCoin
868    IF     - Infinitefuture
877    NAM    - Namada
878    SCR    - Scorum Network
880    LUM    - Lum Network
883    ZBC    - ZooBC
886    ADF    - AD Token
889    TOMO   - TOMO
890    XSEL   - Seln
896    LKSC   - LKSCoin
898    AS     - Assetchain
899    XEC    - eCash
900    LMO    - Lumeneo
901    NXT    - NxtMeta
904    HNT    - Helium
907    FIS    - StaFi
909    SGE    - Saage
911    GERT   - Gert
913    VARA   - Vara Network
916    META   - Metadium
917    FRA    - Findora
919    CCD    - Concordium
921    AVN    - Avian Network
925    DIP    - Dipper Network
928    GHM    - HermitMatrixNetwork
941    ---    - reserved
945    UNLOCK - Jasiri protocol
955    LTP    - LifetionCoin
958    ---    - KickSoccer
960    VKAX   - Vkax
966    MATIC  - Matic
968    UNW    - UNW
970    TWINS  - TWINS
977    TLOS   - Telos
981    TAFECO - Taf ECO Chain
985    AU     - Autonomy
987    VCG    - VipCoin
988    XAZAB  - Xazab core
989    AIOZ   - AIOZ
990    CORE   - Coreum
991    PEC    - Phoenix
992    UNT    - Unit
993    XRB    - X Currency
994    QUAI   - Quai Network
995    CAPS   - Ternoa
997    SUM    - Solidum
998    LBTC   - Lightning Bitcoin
999    BCD    - Bitcoin Diamond
1000   BTN    - Bitcoin New
1001   TT     - ThunderCore
1002   BKT    - BanKitt
1003   NODL   - Nodle
1004   PCOIN  - PCOIN
1005   TAO    - Bittensor
1006   HSK    - HashKey Chain
1007   FTM    - Fantom
1008   RPG    - RPG
1009   LAKE   - iconLake
1010   HT     - Huobi ECO Chain
1011   ELV    - Eluvio
1012   JOC    - Japan Open Chain
1013   BIC    - Beincrypto
1016   ---    - reserved
1020   EVC    - Evrice
1022   XRD    - Radix DLT
1025   CZZ    - Classzz
1026   KEX    - Kira Exchange Token
1027   MCM    - Mochimo
1028   PLS    - Pulse Coin
1032   BTCR   - BTCR
1042   MFID   - Moonfish ID
1111   BBC    - Big Bitcoin
1116   CORE   - Core
1120   RISE   - RISE
1122   CMT    - CyberMiles Token
1128   ETSC   - Ethereum Social
1129   DFI    - DeFiChain
1130   DFI    - DeFiChain EVM Network
1137   $DAG   - Constellation Labs
1145   CDY    - Bitcoin Candy
1155   ENJ    - Enjin Coin
1170   HOO    - Hoo Smart Chain
1234   ALPH   - Alephium
1236   ---    - Masca
1237   ---    - Nostr
1280   ---    - Kudos Setler
1284   GLMR   - Moonbeam
1285   MOVR   - Moonriver
1298   WPC    - Wpc
1308   WEI    - WEI
1337   DFC    - Defcoin
1348   ISLM   - IslamicCoin
1397   HYC    - Hycon
1410   TENTSLP - TENT Simple Ledger Protocol
1510   XSC    - XT Smart Chain
1512   AAC    - Double-A Chain
1524   ---    - Taler
1533   BEAM   - Beam
1551   SDK    - Sovereign SDK
1555   APC    - Apc Chain
1616   ELF    - AELF
1618   AUDL   - AUDL
1620   ATH    - Atheios
1627   LUME   - Lume Web
1642   NEW    - Newton
1657   BTA    - Btachain
1668   NEOX   - Neoxa
1669   MEWC   - Meowcoin
1688   BCX    - BitcoinX
1776   LBTC   - Liquid BTC
1777   BBP    - Biblepay
1784   JPYS   - JPY Stablecoin
1789   VEGA   - Vega Protocol
1818   CUBE   - Cube Chain Native Token
1856   TES    - Teslacoin
1888   ZTX    - Zetrix
1899   XEC    - eCash token
1901   CLC    - Classica
1907   BITCI  - Bitcicoin
1919   VIPS   - VIPSTARCOIN
1926   CITY   - City Coin
1955   XX     - xx coin
1977   XMX    - Xuma
1984   TRTL   - TurtleCoin
1985   SLRT   - Solarti Chain
1986   QTH    - Qing Tong Horizon
1987   EGEM   - EtherGem
1988   MIRA   - Mira Chain
1989   HODL   - HOdlcoin
1990   PHL    - Placeholders
1991   SC     - Sia
1996   MYT    - Mineyourtime
1997   POLIS  - Polis
1998   XMCC   - Monoeci
1999   COLX   - ColossusXT
2000   GIN    - GinCoin
2001   MNP    - MNPCoin
2002   MLN    - Miraland
2017   KIN    - Kin
2018   EOSC   - EOSClassic
2019   GBT    - GoldBean Token
2020   PKC    - PKC
2021   SKT    - Sukhavati
2022   XHT    - Xinghuo Token
2023   COC    - Chat On Chain
2024   USBC   - Universal Ledger USBC
2046   ANY    - Any
2048   MCASH  - MCashChain
2049   TRUE   - TrueChain
2050   MOVO   - Movo Smart Chain
2086   KILT   - KILT Spiritnet
2109   SAMA   - Exosama Network
2112   IoTE   - IoTE
2125   BAY    - BitBay
2137   XRG    - Ergon
2182   CHZ    - Chiliz
2199   SAMA   - Moonsama Network
2221   ASK    - ASK
2222   CWEB   - Coinweb
2285   ---    - Qiyi Chain
2301   QTUM   - QTUM
2302   ETP    - Metaverse
2303   GXC    - GXChain
2304   CRP    - CranePay
2305   ELA    - Elastos
2338   SNOW   - Snowblossom
2365   XIN    - Mixin
2500   NEXI   - Nexi
2570   AOA    - Aurora
2718   NAS    - Nebulas
2894   REOSC  - REOSC Ecosystem
2941   BND    - Blocknode
3000   SM     - Stealth Message
3003   LUX    - LUX
3030   HBAR   - Hedera HBAR
3077   COS    - Contentos
3276   CCC    - CodeChain
3333   SXP    - Solar
3377   ROI    - ROIcoin
3381   DYN    - Dynamic
3383   SEQ    - Sequence
3552   DEO    - Destocoin
3564   DST    - DeStream
3601   CY     - Cybits
3757   MPC    - Partisia Blockchain
4040   FC8    - FCH Network
4096   YEE    - YeeCo
4218   IOTA   - IOTA
4219   SMR    - Shimmer
4242   AXE    - Axe
4343   XYM    - Symbol
4444   C4E    - Chain4Energy
4919   XVM    - Venidium
4999   BXN    - BlackFort Exchange Network
5006   SBC    - Senior Blockchain
5248   FIC    - FIC
5353   HNS    - Handshake
5404   ISK    - ISKRA
5467   ALTME  - ALTME
5555   FUND   - Unification
5757   STX    - Stacks
5895   VOW    - VowChain VOW
5920   SLU    - SILUBIUM
6060   GO     - GoChain GO
6174   MOI    - My Own Internet
6532   UM     - Penumbra
6599   RSC    - Royal Sports City
6666   BPA    - Bitcoin Pizza
6688   SAFE   - SAFE
6779   COTI   - COTI
6969   ROGER  - TheHolyrogerCoin
7027   ELLA   - Ella the heart
7028   AA     - Arthera
7091   TOPL   - Topl
7331   KLY    - KLYNTAR
7341   SHFT   - Shyft
7518   MEV    - MEVerse
7576   ADIL   - ADIL Chain
7777   BTV    - Bitvote
8000   SKY    - Skycoin
8080   ---    - DSRV
8181   BOC    - BeOne Chain
8192   PAC    - pacprotocol
8217   KLAY   - KLAY
8339   BTQ    - BitcoinQuark
8444   XCH    - Chia
8520   ---    - reserved
8680   PLMNT  - Planetmint
8866   GGX    - Golden Gate
8886   GGXT   - Golden Gate Sydney
8888   SBTC   - Super Bitcoin
8964   NULS   - NULS
8997   BBC    - Babacoin
8998   JGC    - JagoanCoin
8999   BTP    - Bitcoin Pay
9001   ARB1   - Arbitrum
9002   BOBA   - Boba
9003   LOOP   - Loopring
9004   STRK   - StarkNet
9005   AVAXC  - Avalanche C-Chain
9006   BSC    - Binance Smart Chain
9797   NRG    - Energi
9888   BTF    - Bitcoin Faith
9999   GOD    - Bitcoin God
10000  FO     - FIBOS
10111  DHP    - dHealth
10226  RTM    - Raptoreum
10291  XRC    - XRhodium
10507  NUM    - Numbers Protocol
10605  XPI    - Lotus
11111  ESS    - Essentia One
11742  VARCH  - InvArch
11743  TNKR   - Tinkernet
12345  IPOS   - IPOS
12586  MINA   - Mina
13107  BTY    - BitYuan
13108  YCC    - Yuan Chain Coin
14001  WAX    - Worldwide Asset Exchange
15845  SDGO   - SanDeGo
16181  XTX    - Totem Live Network
16754  ARDR   - Ardor
18000  MTR    - Meter
19165  SAFE   - Safecoin
19167  FLUX   - Flux
19169  RITO   - Ritocoin
19788  ML     - Mintlayer
20036  XND    - ndau
21004  C4EI   - c4ei
21888  PAC    - Pactus
22504  PWR    - PWRcoin
23000  EPIC   - Epic Cash
25252  BELL   - Bellcoin
25718  CHX    - Own
29223  NEXA   - Nexa
30001  ---    - reserved
31102  ESN    - EtherSocial Network
31337  ---    - ThePower
33416  TEO    - Trust Eth reOrigin
33878  BTCS   - Bitcoin Stake
34952  BTT    - ByteTrade
37992  FXTC   - FixedTradeCoin
39321  AMA    - Amabig
42069  FACT   - FACT0RN
43028  AXIV   - AXIV
49262  EVE    - evan
49344  STASH  - STASH
61616  TH     - TianHe
65536  KETH   - Krypton World
69420  GRLC   - Garlicoin
70007  GWL    - Gewel
77777  ZYN    - Wethio
88888  RYO    - c0ban
99999  WICC   - Waykichain
100500 HOME   - HomeCoin
101010 STC    - Starcoin
105105 STRAX  - Strax
111111 KAS    - Kaspa
161803 APTA   - Bloqs4Good
200625 AKA    - Akroma
200665 GENOM  - GENOM
246529 ATS    - ARTIS sigma1
261131 ZAMA   - Zama
333332 VALUE  - Value Chain
333333 3333   - Pi Value Consensus
424242 X42    - x42
534352 SCR    - Scroll
666666 VITE   - Vite
888888 SEA    - Second Exchange Alliance
999999 WTC    - WaltonChain
1048576 AMAX   - Armonia Meta Chain
1171337 ILT    - iOlite
1313114 ETHO   - Etho Protocol
1313500 XERO   - Xerom
1712144 LAX    - LAPO
3924011 EPK    - EPIK Protocol
4741444 HYD    - Hydra Token
5249353 BCO    - BitcoinOre
5249354 BHD    - BitcoinHD
5264462 PTN    - PalletOne
5655640 VLX    - Velas
5718350 WAN    - Wanchain
5741564 WAVES  - Waves
5741565 WEST   - Waves Enterprise
6382179 ABC    - Abcmint
6517357 CRM    - Creamcoin
7171666 BROCK  - Bitrock
7562605 SEM    - Semux
7567736 ION    - ION
7777777 FCT    - FirmaChain
7825266 WGR    - WGR
7825267 OBSR   - OBServer
8163271 AFS    - ANFS
11259375 LBR    - 0L
15118976 XDS    - XDS
61717561 AQUA   - Aquachain
88888888 HATCH  - Hatch
91927009 kUSD   - kUSD
99999996 GENS   - GENS
99999997 EQ     - EQ
99999998 FLUID  - Fluid Chains
99999999 QKC    - QuarkChain
608589380 FVDC   - ForumCoin
1179993420 ---    - Fuel

"""

## Table of Contents

#### [Introduction](#a_g)

#### [Ethereum (ETH), Ethereum Classic (ETC) and ERC20 Tokens](#a_eth)
* [Install the Ethereum dependencies](#a_ed)
* [Install and run Geth, Parity or OpenEthereum](#a_oe)
* [Transacting and other basic operations](#a_tx)
* [Creating and deploying ERC20 tokens](#a_dt)

#### [Bitcoin Cash Node (BCH) and Litecoin (LTC)](#a_bch)

#### [Monero (XMR)](#a_xmr)

#### [Key/address generation for Zcash (ZEC)](#a_zec)

#### [Key/address generation for 144 Bitcoin-derived altcoins](#a_kg)

### <a name='a_g'>Introduction</a>

Depending on your setup, the instructions on this page may apply to your
offline machine, your online machine, or both.  If you’re confused as to
which, please familiarize yourself with the basics of MMGen by reading the
[**Getting Started**][gs] guide.

### <a name='a_eth'>Ethereum (ETH), Ethereum Classic (ETC) and ERC20 Tokens</a>

MMGen supports all operations for Ethereum, Ethereum Classic and ERC20 tokens.
In addition, ERC20 token creation and deployment are supported via the
`create-token.py` script.

#### <a name='a_ed'>Install the Ethereum dependencies</a>

From the MMGen repository root, type:

	$ python3 -m pip install --no-deps --user -r eth-requirements.txt

#### <a name='a_oe'>Install and run Geth, Parity or OpenEthereum</a>

MMGen can use either Go-Ethereum (Geth) or OpenEthereum to communicate with
the Ethereum network.  For information on installing Geth or OE on your
system, visit the the Geth [Github repo][ge], or the OpenEthereum [wiki][ow]
or [Github repo][og].  On Arch Linux systems, Go-Ethereum and OpenEthereum are
packages and may be installed with `pacman`.

Note that Ethereum daemons are not used for transaction signing, so you
needn’t install them on your offline machine.

For Geth, the following command-line options are required:

	--http --http.api=eth,web3,txpool --http.port=8745

Geth and OE have dropped support for Ethereum Classic, but MMGen supports
transacting ETC via the legacy [Parity][pd] daemon.  Invoke Parity with
`--chain=classic --jsonrpc-port=8645`.  Other command-line options are the
same as for OpenEthereum.

If you’re running OE or Parity on a different machine from MMGen, add the
following options to the daemon command line:

	--jsonrpc-hosts=all --jsonrpc-interface=<daemon IP address>

To run OE or Parity offline, use `--mode=offline`, otherwise `--mode=active`.

MMGen can also be used with Parity’s light client mode, which queries other
nodes on the network for blockchain data.  Add the `--light` option to the
Parity command line and read the applicable note in the [Transacting](#a_tx)
section below.

You may require other options as well.  Invoke your daemon with the `--help`
switch for more complete information.

#### <a name='a_tx'>Transacting and other basic operations</a>

Basic operations with ETH, ETC and ERC20 tokens work as described in the
[Getting Started][bo] guide, with some differences.  Please note the following:

* Don’t forget to invoke all commands with `--coin=eth` or `--coin=etc`.
* Use the `--token` option with the token symbol as parameter for all token
  operations.  When importing addresses for a new token into your tracking
  wallet, use the `--token-addr` option with the token address instead.
* Addresses and other hexadecimal values are given without the leading `0x`.
* Fees are expressed in Gas price, e.g. `12G` for 12 Gwei or `1000M` for 1000
  Mwei.  This works at both the command line and interactive prompt.
* When using OpenEthereum in light client mode, the `--cached-balances` option
  will greatly speed up operations of the `mmgen-txcreate`, `mmgen-txdo` and
  `mmgen-tool twview` commands by reducing network queries to a minimum.  If
  your account balances have changed, they may be refreshed interactively within
  the TRACKED ACCOUNTS menu.  Cached balances are stored persistently in your
  tracking wallet.

##### Transacting example:

*Note: All addresses and filenames in the examples to follow are bogus and
must be replaced with real ones.*

Generate some ETH addresses with your default wallet:

	$ mmgen-addrgen --coin=eth 1-5

Create an EOS token tracking wallet and import the addresses into it:

	$ mmgen-addrimport --coin=eth --token-addr=86fa049857e0209aa7d9e616f7eb3b3b78ecfdb0 ABCDABCD-ETH[1-5].addrs

*Unlike the case with BTC and derivatives, ETH and ETC tracking wallets are
created and managed by MMGen itself and located under the MMGen data directory.
Token tracking wallets are located inside their underlying coin’s
`tracking-wallet.json` file.  Address (account) balances are retrieved directly
from the blockchain.  Tracking wallet views are separate for each token.*

Now send 10+ EOS from an exchange or another wallet to address `ABCDABCD:E:1`.
Then create a TX sending 10 EOS to third-party address `aabbccdd...`, with
change to `ABCDABCD:E:2`:

	$ mmgen-txcreate --coin=eth --token=eos aabbccddaabbccddaabbccddaabbccddaabbccdd,10 ABCDABCD:E:2

On your offline machine, sign the TX:

	$ mmgen-txsign --coin=eth --token=eos ABC123-EOS[10,50000].rawtx

*You can also set up and use [autosigning][X] on the offline machine.*

On your online machine, send the TX:

	$ mmgen-txsend --coin=eth --token=eos ABC123-EOS[10,50000].sigtx

View your EOS tracking wallet:

	$ mmgen-tool --coin=eth --token=eos twview

To transact ETH instead of EOS, omit the `--token` and `--token-addr` arguments.

#### <a name='a_dt'>Creating and deploying ERC20 tokens</a>

##### Install the Solidity compiler

To deploy Ethereum contracts with MMGen, you need version **0.8.7** of the
Solidity compiler (`solc`) installed on your system.  Although binary builds
may be available for some distributions, the best way to ensure you have the
correct version is to compile it from source.

Clone the repository and build:

	$ git clone --recursive https://github.com/ethereum/solidity.git
	$ cd solidity
	$ git checkout v0.8.7
	$ ./scripts/install_deps.sh
	$ mkdir build
	$ cd build
	$ cmake -DUSE_CVC4=OFF -DUSE_Z3=OFF ..
	$ make -j4 solc
	$ sudo install -v --strip solc/solc /usr/local/bin

##### Create and deploy a token

*Note: All addresses and filenames in the examples to follow are bogus.  You
must replace them with real ones.*

Create a token 'MFT' with default parameters, owned by `ddeeff...` (`ABCDABCD:E:1`):

	# Do this in the MMGen repository root:
	$ scripts/create-token.py --coin=ETH --symbol=MFT --name='My First Token' ddEEFFDdEEFfddEeffDDEefFdDeeFFDDEeFFddEe

Deploy the token on the ETH blockchain:

	$ mmgen-txdo --coin=eth --tx-gas=200000 --contract-data=SafeMath.bin
	$ mmgen-txdo --coin=eth --tx-gas=250000 --contract-data=Owned.bin
	$ mmgen-txdo --coin=eth --tx-gas=1100000 --contract-data=Token.bin
	...
	Token address: abcd1234abcd1234abcd1234abcd1234abcd1234

*These Gas amounts seem to work for these three contracts, but feel free to
experiment.  Make sure you understand the difference between Gas amount and Gas
price!*

Create an MFT token tracking wallet and import your ETH addresses into it:

	$ mmgen-addrimport --coin=eth --token-addr=abcd1234abcd1234abcd1234abcd1234abcd1234 ABCDABCD-ETH[1-5].addrs

View your MFT tracking wallet:

	$ mmgen-tool --coin=eth --token=mft twview

Other token parameters can be customized too.  Type `scripts/create-token.py --help`
for details.

### <a name='a_bch'>Bitcoin Cash Node (BCH) and Litecoin (LTC)</a>

Bitcoin Cash Node (BCH) and Litecoin are fully supported by MMGen, on the same
level as Bitcoin.

To use MMGen with BCH or Litecoin, first make sure the Bitcoin Cash Node or
Litecoin daemons are properly installed ([source][si])([binaries][bi]),
[running][p8] and synced.

MMGen requires that the bitcoin-bchn daemon be listening on non-standard
[RPC port 8442][p8].  If your daemon version is >= 0.16.2, you must use the
`--usecashaddr=0` option.

Then just add the `--coin=bch` or `--coin=ltc` option to all your MMGen
commands.  It’s that simple!

### <a name='a_xmr'>Monero (XMR)</a>

MMGen’s Monero support includes automated wallet creation/syncing and
transaction creation/relaying via the `mmgen-xmrwallet` command.  Make sure
that [Monerod][M] is installed and running and that `monero-wallet-rpc` is
located in your executable path.

*NOTE: by storing the Monero blockchain on a removable drive and installing
Monerod on both your online and offline machines, it’s possible to perform
wallet and transaction creation operations offline and thus avoid exposing
private data on your online machine.*

To generate five Monero key/address pairs from your default wallet, invoke the
following, making sure to answer ‘y’ at the Encrypt prompt:

	$ mmgen-keygen --coin=xmr 1-5

In addition to spend and view keys, the resulting key/address file also
includes a wallet password for each address (the double SHA256 hash of the
spend key, truncated to 16 bytes).

Now create a Monero wallet for each address in the file by invoking the
following command:

	$ mmgen-xmrwallet create *XMR*.akeys.mmenc

Each wallet will be uniquely named using the address index and encrypted with
the address’ unique wallet password.  No user interaction is required during
the creation process.  By default, wallets are synced to the current block
height, as they’re assumed to be empty, but this behavior can be overridden:

	$ mmgen-xmrwallet --restore-height=123456 create *XMR*.akeys.mmenc

To keep your wallets in sync as the Monero blockchain grows, use the `sync`
subcommand:

	$ mmgen-xmrwallet sync *XMR*.akeys.mmenc

No user interaction is required here either, which is very helpful when you
have multiple wallets requiring long sync times.

`mmgen-xmrwallet` supports transacting via the `sweep` and `transfer`
subcommands.  Type `mmgen-xmrwallet --help` for details.

### <a name='a_zec'>Key/address generation for Zcash (ZEC)</a>

MMGen’s enhanced support for Zcash includes generation of **z-addresses.**

Generate ten Zcash z-address key/address pairs from your default wallet:

	$ mmgen-keygen --coin=zec --type=zcash_z 1-10

The addresses’ view keys are included in the output file as well.

NOTE: Since your key/address file will probably be used on an online computer,
you should encrypt it with a good password when prompted to do so. The file can
decrypted as required using the `mmgen-tool decrypt` command.  If you choose a
non-standard Scrypt hash preset, take care to remember it.

To generate Zcash t-addresses, just omit the `--type` argument:

	$ mmgen-keygen --coin=zec 1-10

### <a name='a_kg'>Key/address generation for 144 Bitcoin-derived altcoins</a>

To generate key/address pairs for these coins, just specify the coin’s symbol
with the `--coin` argument:

	# For DASH:
	$ mmgen-keygen --coin=dash 1-10
	# For Emercoin:
	$ mmgen-keygen --coin=emc 1-10

For compressed public keys, add the `--type=compressed` option:

	$ mmgen-keygen --coin=dash --type=compressed 1-10

If it’s just the addresses you want, then use `mmgen-addrgen` instead:

	$ mmgen-addrgen --coin=dash --type=compressed 1-10

Regarding encryption of key/address files, see the note for Zcash above.

Here’s a complete list of supported altcoins as of this writing:

	2give,42,611,ac,acoin,alf,anc,apex,arco,arg,aur,bcf,blk,bmc,bqc,bsty,btcd,
	btq,bucks,cann,cash,cat,cbx,ccn,cdn,chc,clam,con,cpc,crps,csh,dash,dcr,dfc,
	dgb,dgc,doge,doged,dope,dvc,efl,emc,emd,enrg,esp,fai,fc2,fibre,fjc,flo,flt,
	fst,ftc,gcr,good,grc,gun,ham,html5,hyp,icash,infx,inpay,ipc,jbs,judge,lana,
	lat,ldoge,lmc,ltc,mars,mcar,mec,mint,mobi,mona,moon,mrs,mue,mxt,myr,myriad,
	mzc,neos,neva,nka,nlg,nmc,nto,nvc,ok,omc,omni,onion,onx,part,pink,pivx,pkb,
	pnd,pot,ppc,ptc,pxc,qrk,rain,rbt,rby,rdd,ric,sdc,sib,smly,song,spr,start,
	sys,taj,tit,tpc,trc,ttc,tx,uno,via,vpn,vtc,wash,wdc,wisc,wkc,wsx,xcn,xgb,
	xmg,xpm,xpoke,xred,xst,xvc,zet,zlq,zoom,zrc,bch,etc,eth,ltc,xmr,zec

Note that support for most of these coins is EXPERIMENTAL.  Many of them have
received only minimal testing, or no testing at all.  At startup you’ll be
informed of the level of your selected coin’s support reliability as deemed by
the MMGen Project.

[ow]: https://openethereum.github.io/wiki
[og]: https://github.com/openethereum/openethereum/releases
[pd]: https://github.com/openethereum/parity-ethereum/releases/tag/v2.7.2
[y]: https://github.com/ethereum/pyethereum
[P]: https://pypi.org/project/pip
[M]: https://getmonero.org/downloads/#linux
[U]: https://github.com/mmgen/MMGenLive/blob/master/home.mmgen/bin/mmlive-daemon-upgrade
[X]: autosign-[MMGen-command-help]
[gs]: Getting-Started-with-MMGen
[bo]: Getting-Started-with-MMGen#a_bo
[si]: Install-Bitcoind-from-Source-on-Debian-or-Ubuntu-Linux
[bi]: Install-Bitcoind#a_d
[p8]: Install-Bitcoind#a_r
[ge]: https://github.com/ethereum/go-ethereum

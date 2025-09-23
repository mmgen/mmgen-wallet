## Table of Contents

#### [Introduction](#a_g)

#### [Ethereum (ETH), Ethereum Classic (ETC) and ERC20 Tokens](#a_eth)
* [Install the Ethereum dependencies](#a_ed)
* [Install and run Reth, Geth or Parity](#a_geth)
* [Transacting and other basic operations](#a_tx)
* [Creating and deploying ERC20 tokens](#a_dt)

#### [Bitcoin Cash Node (BCH) and Litecoin (LTC)](#a_bch)

#### [Monero (XMR)](#a_xmr)

#### [THORChain (RUNE)](#a_rune)

#### [Asset swaps via THORChain](#a_tcswap)

#### [Key/address generation for Zcash (ZEC)](#a_zec)

#### [Key/address generation for 144 Bitcoin-derived altcoins](#a_kg)

### <a id="a_g">Introduction</a>

Depending on your setup, the instructions on this page may apply to your
offline machine, your online machine, or both.  If you’re confused as to
which, please familiarize yourself with the basics of MMGen Wallet by
reading the [**Getting Started**][gs] guide.

### <a id="a_eth">Ethereum (ETH), Ethereum Classic (ETC) and ERC20 Tokens</a>

MMGen Wallet supports all operations for Ethereum, Ethereum Classic and ERC20
tokens.  In addition, ERC20 token creation and deployment are supported via the
`create-token.py` script.

#### <a id="a_ed">Install the Ethereum dependencies</a>

Skip this step for MSYS2 or if your Python version is 3.13 or greater.

From the MMGen Wallet repository root, type:

```text
$ python3 -m pip install -r keccak-requirements.txt
```

#### <a id="a_geth">Install and run Reth, Geth or Parity</a>

MMGen Wallet uses Rust Ethereum (Reth) or Go-Ethereum (Geth) to communicate with
the Ethereum network, with Reth now being preferred by the MMGen Project.

Installation and usage instructions for Reth can be found [here][RE] and
prebuilt binaries [here][rb].

Information for Geth can be found at its [homepage][gh] or [Github repo][ge].
On Arch Linux systems, Geth is a package and may be installed with `pacman`.  On
RISC-V platforms, for which no prebuilt binaries are available, Geth must be
built from source, preferably using the most recent version of [Go][gd].

Note that the Ethereum daemon is not used for transaction signing, so you
needn’t install it on your offline machine.

For Reth, the following command-line options are required, among others:

```text
--http --http.api=eth,rpc,web3,txpool
```

For Geth, the following command-line options are required, among others:

```text
--http --http.api=eth,web3,txpool --http.port=8745
```

Geth has dropped support for Ethereum Classic, however transacting ETC is
still supported by the legacy [Parity][pd] daemon.  Invoke Parity with
`--chain=classic --jsonrpc-port=8645`.

If you’re running Parity on a different machine from MMGen Wallet, add the
following options to the command line:

```text
--jsonrpc-hosts=all --jsonrpc-interface=<daemon IP address>
```

To run Parity offline, use `--mode=offline`, otherwise `--mode=active`.

Parity’s light client mode, which queries other nodes on the network for
blockchain data, is supported.  Add the `--light` option to the Parity command
line and read the applicable note in the [Transacting](#a_tx) section below.

Other command-line options will certainly be required.  Invoke your daemon with
the `--help` option for more complete information.

#### <a id="a_tx">Transacting and other basic operations</a>

Basic operations with ETH, ETC and ERC20 tokens work as described in the
[**Getting Started**][bo] guide, with some differences.  Please note the
following:

* Don’t forget to invoke relevant commands with `--coin=eth` or `--coin=etc`.
* Use the `--token` option with the token symbol as parameter for all token
  operations.  When importing addresses for a new token into your tracking
  wallet, use the `--token-addr` option with the token address instead.
* Addresses and other hexadecimal values are given without the leading `0x`.
* Fees are expressed in Gas price, e.g. `12G` for 12 Gwei or `1000M` for 1000
  Mwei.  This works at both the command line and interactive prompt.
* When using Parity in light client mode, the `--cached-balances` option
  will greatly speed up operations of the `mmgen-txcreate`, `mmgen-txdo` and
  `mmgen-tool twview` commands by reducing network queries to a minimum.  If
  your account balances have changed, they may be refreshed interactively within
  the TRACKED ACCOUNTS menu.  Cached balances are stored persistently in your
  tracking wallet.
* Note that sending transactions with your Ethereum node can easily deanonymize
  you by linking the transaction with your IP address (running a Reth node
  over Tor or Tor+VPN is theoretically possible, but problematic in practice).
  As a solution to this problem, MMGen Wallet supports broadcasting transactions
  via the etherscan.io website with the `--tx-proxy` option.  Sending is done
  using the site’s public web form, so no registration or API key is required.
  For anonymity, the connection can be routed via Tor or I2P using the `--proxy`
  option.  See `mmgen-txsend --help` for details.

##### Transacting example:

*Note: All addresses and filenames in the examples to follow are bogus and
must be replaced with real ones.*

Generate some ETH addresses with your default wallet:

```text
$ mmgen-addrgen --coin=eth 1-5
```

Create an EOS token tracking wallet and import the addresses into it:

```text
$ mmgen-addrimport --coin=eth --token-addr=86fa049857e0209aa7d9e616f7eb3b3b78ecfdb0 ABCDABCD-ETH[1-5].addrs
```

*Unlike the case with BTC and derivatives, ETH and ETC tracking wallets are
created and managed by MMGen Wallet itself and located under the MMGen data
directory.  Token tracking wallets are located inside their underlying coin’s
`tracking-wallet.json` file.  Address (account) balances are retrieved directly
from the blockchain.  Tracking wallet views are separate for each token.*

Now send 10+ EOS from an exchange or another wallet to address `ABCDABCD:E:1`.
Then create a TX sending 10 EOS to third-party address `aabbccdd...`, with
change to `ABCDABCD:E:2`:

```text
$ mmgen-txcreate --coin=eth --token=eos aabbccddaabbccddaabbccddaabbccddaabbccdd,10 ABCDABCD:E:2
```

On your offline machine, sign the TX:

```text
$ mmgen-txsign --coin=eth --token=eos ABC123-EOS[10,50000].rawtx
```

*You can also set up and use [autosigning][X] on the offline machine.*

On your online machine, send the TX:

```text
$ mmgen-txsend --coin=eth --token=eos ABC123-EOS[10,50000].sigtx
```

View your EOS tracking wallet:

```text
$ mmgen-tool --coin=eth --token=eos twview
```

To transact ETH instead of EOS, omit the `--token` and `--token-addr` arguments.

#### <a id="a_dt">Creating and deploying ERC20 tokens</a>

##### Install the Solidity compiler

To deploy Ethereum contracts with MMGen Wallet, you need version **0.8.26** or
newer of the Solidity compiler (`solc`) installed on your system.  Static binary
builds are available from the Solidity [Github repository][sb].  For other ways
to install solc on your platform, refer to the [Solidity documentation][sd].

##### Create and deploy a token

*Note: All addresses and filenames in the examples to follow are bogus.  You
must replace them with real ones.*

Create a token 'MFT' with default parameters, owned by `ddeeff...` (`ABCDABCD:E:1`):

```text
# Do this in the MMGen Wallet repository root:
$ scripts/create-token.py --coin=ETH --symbol=MFT --name='My First Token' ddEEFFDdEEFfddEeffDDEefFdDeeFFDDEeFFddEe
```

Deploy the token on the ETH blockchain:

```text
$ mmgen-txdo --coin=eth --tx-gas=200000 --contract-data=SafeMath.bin
$ mmgen-txdo --coin=eth --tx-gas=250000 --contract-data=Owned.bin
$ mmgen-txdo --coin=eth --tx-gas=1100000 --contract-data=Token.bin
...
Token address: abcd1234abcd1234abcd1234abcd1234abcd1234
```

*These Gas amounts seem to work for these three contracts, but feel free to
experiment.  Make sure you understand the difference between Gas amount and Gas
price!*

Create an MFT token tracking wallet and import your ETH addresses into it:

```text
$ mmgen-addrimport --coin=eth --token-addr=abcd1234abcd1234abcd1234abcd1234abcd1234 ABCDABCD-ETH[1-5].addrs
```

View your MFT tracking wallet:

```text
$ mmgen-tool --coin=eth --token=mft twview
```

Other token parameters can be customized too.  Type `scripts/create-token.py --help`
for details.

### <a id="a_bch">Bitcoin Cash Node (BCH) and Litecoin (LTC)</a>

Bitcoin Cash Node (BCH) and Litecoin are fully supported by MMGen Wallet.

To transact BCH or Litecoin, first make sure the Bitcoin Cash Node or Litecoin
daemons are properly installed ([source][si])([binaries][bi]), [running][p8] and
synced.

On RISC-V platforms, Bitcoin Cash Node must be compiled from source, as no
precompiled binaries are available.

MMGen Wallet requires that the bitcoin-bchn daemon be listening on non-standard
[RPC port 8432][p8].  If your daemon version is >= 0.16.2, you must use the
`--usecashaddr=0` option.

Then just add the `--coin=bch` or `--coin=ltc` option to applicable MMGen Wallet
commands.  It’s that simple!

### <a id="a_xmr">Monero (XMR)</a>

MMGen Wallet’s Monero support includes automated wallet creation/syncing and
transacting via the [`mmgen-xmrwallet`][mx] command.  Make sure that
[Monerod][M] is installed and running and that `monero-wallet-rpc` is located
in your executable path.

<a id="a_xmr_req">Install the Python XMR requirements:</a>

Skip this step for MSYS2, as these requirements were already installed by
pacman.

Skip ‘keccak-requirements.txt’ if your Python version 3.13 or greater and
you don’t plan to run the test suite.

```text
$ python3 -m pip install -r keccak-requirements.txt  # see above
$ python3 -m pip install -r xmr-requirements.txt
```

*The following instructions are applicable for a hot wallet setup.  To learn
how to cold sign transactions using MMGen Wallet’s autosign feature, first
familiarize yourself with the basic concepts here and then consult the OFFLINE
AUTOSIGNING tutorial on the [`mmgen-xmrwallet`][mx] help screen.*

To generate five Monero key/address pairs from your default wallet, invoke the
following, making sure to answer ‘y’ at the Encrypt prompt:

```text
$ mmgen-keygen --coin=xmr 1-5
```

In addition to spend and view keys, the resulting key/address file also
includes a wallet password for each address (the double SHA256 hash of the
spend key, truncated to 16 bytes).

Now create a Monero wallet for each address in the file by invoking the
following command:

```text
$ mmgen-xmrwallet create *XMR*.akeys.mmenc
```

Each wallet will be uniquely named using the address index and encrypted with
the address’ unique wallet password.  No user interaction is required during
the creation process.  By default, wallets are synced to the current block
height, as they’re assumed to be empty, but this behavior can be overridden:

```text
$ mmgen-xmrwallet --restore-height=123456 create *XMR*.akeys.mmenc
```

To keep your wallets in sync as the Monero blockchain grows, use the `sync`
subcommand:

```text
$ mmgen-xmrwallet sync *XMR*.akeys.mmenc
```

No user interaction is required here either, which is very helpful when you
have multiple wallets requiring long sync times.

To learn how to transact using your wallets, continue on to the
[`mmgen-xmrwallet`][mx] help screen.

### <a id="a_rune">THORChain (RUNE)</a>

Install the RUNE requirements:

```text
$ python3 -m pip install -r rune-requirements.txt
```

Transacting RUNE with MMGen Wallet is similar to transacting BTC as described in
the [**Getting Started**][gs] guide.  Just add the `--coin=rune` option to all
relevant commands.  With `mmgen-autosign`, add `rune` to the list of coins in
the `--coins` parameter.

Note that MMGen Wallet’s RUNE support requires no locally running node; instead,
balances are fetched and transactions sent via a public node at ninerealms.com.
As this can compromise your privacy, it’s recommended to proxy all
communications via Tor or I2P: refer to the helpscreens of `mmgen-txcreate`,
`mmgen-swaptxcreate` and `mmgen-txsend` for more information.

### <a id="a_tcswap">Asset swaps via THORChain</a>

Install the RUNE requirements as shown above.

21 assets (as of this writing) may be swapped directly within MMGen Wallet via
THORChain.  Swapping assets is just like normal transacting, except transactions
are created using `mmgen-swaptxcreate` instead of `mmgen-txcreate`.  Note that
coin daemons for both the send and receive assets must be running and synced
before carrying out a swap.  Depending on your setup, communication with two
daemons simultaneously may require the use of *coin-specific options* (see
`mmgen-swaptxcreate --longhelp`).  For usage information, examples, and a list
of supported assets, invoke `mmgen-swaptxcreate --help`.

### <a id="a_zec">Key/address generation for Zcash (ZEC)</a>

MMGen Wallet supports generation of Zcash **z-addresses.**

Generate ten Zcash z-address key/address pairs from your default wallet:

```text
$ mmgen-keygen --coin=zec --type=zcash_z 1-10
```

The addresses’ view keys are included in the output file as well.

NOTE: Since your key/address file will probably be used on an online computer,
you should encrypt it with a good password when prompted to do so. The file can
decrypted as required using the `mmgen-tool decrypt` command.  If you choose a
non-standard Scrypt hash preset, take care to remember it.

To generate Zcash t-addresses, just omit the `--type` argument:

```text
$ mmgen-keygen --coin=zec 1-10
```

### <a id="a_kg">Key/address generation for 144 Bitcoin-derived altcoins</a>

To generate key/address pairs for these coins, just specify the coin’s symbol
with the `--coin` argument:

```text
# For DASH:
$ mmgen-keygen --coin=dash 1-10

# For Emercoin:
$ mmgen-keygen --coin=emc 1-10
```

For compressed public keys, add the `--type=compressed` option:

```text
$ mmgen-keygen --coin=dash --type=compressed 1-10
```

If it’s just the addresses you want, then use `mmgen-addrgen` instead:

```text
$ mmgen-addrgen --coin=dash --type=compressed 1-10
```

Regarding encryption of key/address files, see the note for Zcash above.

Here’s a complete list of supported altcoins as of this writing:

```text
2give,42,611,ac,acoin,alf,anc,apex,arco,arg,aur,bcf,blk,bmc,bqc,bsty,btcd,
btq,bucks,cann,cash,cat,cbx,ccn,cdn,chc,clam,con,cpc,crps,csh,dash,dcr,dfc,
dgb,dgc,doge,doged,dope,dvc,efl,emc,emd,enrg,esp,fai,fc2,fibre,fjc,flo,flt,
fst,ftc,gcr,good,grc,gun,ham,html5,hyp,icash,infx,inpay,ipc,jbs,judge,lana,
lat,ldoge,lmc,ltc,mars,mcar,mec,mint,mobi,mona,moon,mrs,mue,mxt,myr,myriad,
mzc,neos,neva,nka,nlg,nmc,nto,nvc,ok,omc,omni,onion,onx,part,pink,pivx,pkb,
pnd,pot,ppc,ptc,pxc,qrk,rain,rbt,rby,rdd,ric,sdc,sib,smly,song,spr,start,
sys,taj,tit,tpc,trc,ttc,tx,uno,via,vpn,vtc,wash,wdc,wisc,wkc,wsx,xcn,xgb,
xmg,xpm,xpoke,xred,xst,xvc,zet,zlq,zoom,zrc,bch,etc,eth,ltc,xmr,zec
```

Note that support for most of these coins is EXPERIMENTAL.  Many of them have
received only minimal testing, or no testing at all.  At startup you’ll be
informed of the level of your selected coin’s support reliability as deemed by
the MMGen Project.

[pd]: https://github.com/openethereum/parity-ethereum/releases/tag/v2.7.2
[y]: https://github.com/ethereum/pyethereum
[P]: https://pypi.org/project/pip
[M]: https://getmonero.org/downloads/#linux
[X]: cmds/command-help-autosign.md
[gs]: Getting-Started-with-MMGen-Wallet.md
[bo]: Getting-Started-with-MMGen-Wallet.md#a_bo
[si]: Install-Bitcoind-from-Source-on-Linux.md
[bi]: Install-Bitcoind.md#a_d
[p8]: Install-Bitcoind.md#a_r
[gh]: https://geth.ethereum.org
[ge]: https://github.com/ethereum/go-ethereum
[mx]: cmds/command-help-xmrwallet.md
[sb]: https://github.com/ethereum/solidity/releases
[sd]: https://docs.soliditylang.org
[RE]: https://reth.rs/overview
[rb]: https://github.com/paradigmxyz/reth/releases
[gd]: https://go.dev

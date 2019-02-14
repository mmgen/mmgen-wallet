## Table of Contents

#### [Full support for Ethereum (ETH), Ethereum Classic (ETC) and ERC20 Tokens](#a_eth)
* [Install and run Parity Ethereum](#a_par)
* [Install the Pyethereum library](#a_pe)
* [Transacting and other basic operations](#a_tx)
* [Creating and deploying ERC20 tokens](#a_dt)

#### [Full support for Bcash (BCH) and Litecoin](#a_bch)

#### [Key/address generation for Zcash (ZEC)](#a_zec)

#### [Key/address generation and wallet creation/syncing for Monero (XMR)](#a_xmr)

#### [Key/address generation support for 144 Bitcoin-derived altcoins](#a_kg)

### <a name='a_eth'>Full support for Ethereum (ETH), Ethereum Classic (ETC) and ERC20 Tokens</a>

Ethereum, Ethereum Classic and ERC20 tokens are fully supported by MMGen, on the
same level as Bitcoin.  In addition, ERC20 token creation and deployment are
supported via the `create-token.py` script.

#### <a name='a_par'>Install and run Parity Ethereum</a>

MMGen uses Parity to communicate with the Ethereum blockchain.  For information
on installing Parity on your system, visit the Parity Ethereum [homepage][h] or
[Git repository][g].  [MMGenLive][l] users can install Parity automatically from
signed binaries using the [`mmlive-daemon-upgrade`][U] script.  Parity is not
used for transaction signing, so you needn't install it on your offline machine.

Parity must be invoked with the `--jsonrpc-apis=all` option so that MMGen can
communicate with it.  If you're running the daemon and MMGen on different
machines you'll also need the following:

	--jsonrpc-hosts=all --jsonrpc-interface=<IP of Parity's host>

To transact Ethereum Classic, use `--chain=classic --jsonrpc-port=8555`

To run the daemon offline, use `--mode=offline`, otherwise `--mode=active`.

You may require other options as well.  Consult `parity --help` for the full
list.

#### <a name='a_pe'>Install the Pyethereum library</a>

Signing of ETH and ETC transactions is handled by the [pyethereum][y] library.

First, using the [pip3][P] Python package installer, install the following
dependencies:

*Note: Ubuntu Xenial users will have to upgrade the Python interpreter and
Python dependencies listed in the [Install wiki][iw] from version 3.5 to 3.6
before proceeding.  This can be done by adding the Bionic repository to
'sources.list' and reinstalling the relevant packages with '-t bionic'*

	$ sudo -H pip3 install wheel future pysha3 PyYAML py_ecc rlp

As of this writing, the current “stable” version of pyethereum (2.3.2) is
broken, so we must check out a more recent version from Github:

	$ git clone https://github.com/ethereum/pyethereum
	$ cd pyethereum
	$ git checkout b704a5c

To prevent the library from auto-installing a lot of unneeded dependencies
(Pycryptodome in particular, which would stomp on our existing Pycrypto
installation) we need to edit the file 'requirements.txt' and remove the
following unneeded packages:

	coincurve
	pbkdf2
	pyethash
	pycryptodome
	repoze.lru

Now we can proceed with the install:

	$ sudo python3 ./setup.py install

#### <a name='a_tx'>Transacting and other basic operations</a>

Basic operations with ETH, ETC and ERC20 tokens work as described in the
[Getting Started][bo] guide, with some differences.  Please note the following:

* Don't forget to invoke all commands with either `--coin=eth` or `--coin=etc`.
* Use the `--token` switch with all token operations.  When importing addresses
  into your token tracking wallet you must use the token's address as the
  argument.  After this, the token symbol, e.g. `--token=eos`, is sufficient.
* Addresses and other hexadecimal values are given without the leading `0x`.
* Fees are expressed in Gas price, e.g. `12G` for 12 Gwei or `1000M` for 1000
  Mwei.  This works both at the command line and interactive prompt.

##### Transacting example:

*Note: All addresses and filenames in the examples to follow are bogus.  You
must replace them with real ones.*

Generate some ETH addresses with your default wallet:

	$ mmgen-addrgen --coin=eth 1-5

Create an EOS token tracking wallet and import the addresses into it:

	$ mmgen-addrimport --coin=eth --token=86fa049857e0209aa7d9e616f7eb3b3b78ecfdb0 ABCDABCD-ETH[1-5].addrs

*Unlike the case with BTC and derivatives, ETH and ETC tracking wallets are
created and managed by MMGen itself and located under the MMGen data directory.
Token tracking wallets are located inside their underlying coin's
`tracking-wallet.json` file.  Address (account) balances are retrieved directly
from the blockchain.  Tracking wallet views are separate for each token.*

Now send 10+ EOS from an exchange or another wallet to address `ABCDABCD:E:1`.
Then create a TX sending 10 EOS to third-party address `aabbccdd...`, with
change to `ABCDABCD:E:2`:

	$ mmgen-txcreate --coin=eth --token=eos aabbccddaabbccddaabbccddaabbccddaabbccdd,10 ABCDABCD:E:2

On your offline machine, sign the TX:

	$ mmgen-txsign --coin=eth --token=eos ABC123-EOS[10,50000].rawtx

*You can also set up and use [autosigning][X] on the offline machine, of
course.*

On your online machine, send the TX:

	$ mmgen-txsend --coin=eth --token=eos ABC123-EOS[10,50000].sigtx

View your EOS tracking wallet:

	$ mmgen-tool --coin=eth --token=eos twview

To transact ETH instead of EOS, omit the `--token` arguments.

#### <a name='a_dt'>Creating and deploying ERC20 tokens</a>

##### Install the Solidity compiler

To deploy Ethereum contracts with MMGen, you need between **v0.5.1** and
**v0.5.3** of the the Solidity compiler (`solc`) installed on your system.  The
best way to ensure you have the correct version is to compile it from source.
Alternatively, on Ubuntu 18.04 systems a binary distribution is also available.
Instructions for installing it are provided below.

##### *To compile solc from source:*

Clone the repository and build:

	$ git clone --recursive https://github.com/ethereum/solidity.git
	$ cd solidity
	$ git checkout v0.5.1 # or v0.5.3, if not Raspbian Stretch
	$ ./scripts/install_deps.sh # Raspbian Stretch: add `DISTRO='Debian'` after line 55
	$ mkdir build
	$ cd build
	$ cmake -DUSE_CVC4=OFF -DUSE_Z3=OFF ..
	$ make solc
	$ sudo install -v --strip solc/solc /usr/local/bin

##### *To install solc from binary distribution (Ubuntu 18.04):*

First add the following line to your /etc/apt/sources.list:

	deb http://ppa.launchpad.net/ethereum/ethereum/ubuntu bionic main

Now obtain the Ethereum PPA key `2A518C819BE37D2C2031944D1C52189C923F6CA9`
from a PGP keyserver using your method of choice.  Save the key to file, and
then add it to your APT keyring as follows:

	$ sudo apt-key add <key file>

Now you can proceed with the install:

	$ sudo apt-get update
	$ sudo apt-get install solc
	$ solc --version # make sure the version is correct!

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

	$ mmgen-addrimport --coin=eth --token=abcd1234abcd1234abcd1234abcd1234abcd1234 ABCDABCD-ETH[1-5].addrs

View your MFT tracking wallet:

	$ mmgen-tool --coin=eth --token=mft twview

Other token parameters can also be customized.  Type `scripts/create-token.py --help`
for details.

### <a name='a_bch'>Full support for Bcash (BCH) and Litecoin</a>

Bcash and Litecoin are fully supported by MMGen, on the same level as Bitcoin.

To use MMGen with Bcash or Litecoin, first make sure the respective Bitcoin ABC
and Litecoin daemons are properly installed ([source][si])([binaries][bi]),
[running][p8] and synced.

MMGen requires that the bitcoin-abc daemon be listening on non-standard
[RPC port 8442][p8].  If your daemon version is >= 0.16.2, you must use the
`--usecashaddr=0` option.

Then just add the `--coin=bch` or `--coin=ltc` option to all your MMGen
commands.  It's that simple!

### <a name='a_zec'>Key/address generation for Zcash (ZEC)</a>

MMGen's enhanced support for Zcash includes generation of **z-addresses.**

Generate ten Zcash z-address key/address pairs from your default wallet:

	$ mmgen-keygen --coin=zec --type=zcash_z 1-10

The addresses' view keys are included in the output file as well.

NOTE: Since your key/address file will probably be used on an online computer,
you should encrypt it with a good password when prompted to do so. The file can
decrypted as required using the `mmgen-tool decrypt` command.  If you choose a
non-standard Scrypt hash preset, take care to remember it.

To generate Zcash t-addresses, just omit the `--type` argument:

	$ mmgen-keygen --coin=zec 1-10

### <a name='a_xmr'>Key/address generation and wallet creation/syncing for Monero (XMR)</a>

MMGen's enhanced support for Monero includes automated Monero wallet creation
and syncing.

Install the following dependencies:

	$ sudo -H pip3 install pysha3
	$ sudo -H pip3 install ed25519ll # optional, but greatly speeds up address generation

Generate ten Monero address pairs from your default wallet:

	$ mmgen-keygen --coin=xmr 1-10

In addition to spend and view keys, Monero key/address files also include a
wallet password for each address (the password is the double SHA256 of the spend
key, truncated to 16 bytes).  This allows you to generate a wallet from each
key in the key/address file by running the following command:

	$ monero-wallet-cli --generate-from-spend-key MyMoneroWallet

and pasting in the key and password data when prompted.  [Monerod][M] must be
installed and running and `monero-wallet-cli` be located in your executable
path.

To save your time and labor, the `mmgen-tool` utility includes a command that
completely automates this process:

	$ mmgen-tool keyaddrlist2monerowallets *XMR*.akeys.mmenc

This will generate a uniquely-named Monero wallet for each key/address pair in
the key/address file and encrypt it with its respective password.  No user
interaction is required.  By default, wallets are synced to the current block
height, as they're assumed to be empty, but this behavior can be overridden:

	$ mmgen-tool keyaddrlist2monerowallets *XMR*.akeys.mmenc blockheight=123456

To keep your wallets in sync as the Monero blockchain grows, `mmgen-tool`
includes another utility:

	$ mmgen-tool syncmonerowallets *XMR*.akeys.mmenc

This command also requires no user interaction, a very handy feature when you
have a large batch of wallets requiring long sync times.

### <a name='a_kg'>Key/address generation support for 144 Bitcoin-derived altcoins</a>

To generate key/address pairs for these coins, just specify the coin's symbol
with the `--coin` argument:

	# For DASH:
	$ mmgen-keygen --coin=dash 1-10
	# For Emercoin:
	$ mmgen-keygen --coin=emc 1-10

For compressed public keys, add the `--type=compressed` option:

	$ mmgen-keygen --coin=dash --type=compressed 1-10

If it's just the addresses you want, then use `mmgen-addrgen` instead:

	$ mmgen-addrgen --coin=dash 1-10

Regarding encryption of key/address files, see the note for Zcash above.

Here's a complete list of supported altcoins as of this writing:

	2give,42,611,ac,acoin,alf,anc,apex,arco,arg,aur,bcf,blk,bmc,bqc,bsty,btcd,
	btq,bucks,cann,cash,cat,cbx,ccn,cdn,chc,clam,con,cpc,crps,csh,dash,dcr,dfc,
	dgb,dgc,doge,doged,dope,dvc,efl,emc,emd,enrg,esp,fai,fc2,fibre,fjc,flo,flt,
	fst,ftc,gcr,good,grc,gun,ham,html5,hyp,icash,infx,inpay,ipc,jbs,judge,lana,
	lat,ldoge,lmc,ltc,mars,mcar,mec,mint,mobi,mona,moon,mrs,mue,mxt,myr,myriad,
	mzc,neos,neva,nka,nlg,nmc,nto,nvc,ok,omc,omni,onion,onx,part,pink,pivx,pkb,
	pnd,pot,ppc,ptc,pxc,qrk,rain,rbt,rby,rdd,ric,sdc,sib,smly,song,spr,start,
	sys,taj,tit,tpc,trc,ttc,tx,uno,via,vpn,vtc,wash,wdc,wisc,wkc,wsx,xcn,xgb,
	xmg,xpm,xpoke,xred,xst,xvc,zet,zlq,zoom,zrc,bch,etc,eth,ltc,xmr,zec

Note that support for these coins is EXPERIMENTAL.  Many of them have received
only minimal testing, or no testing at all.  At startup you'll be informed of
the level of your selected coin's support reliability as deemed by the MMGen
Project.

[h]: https://www.parity.io/ethereum
[g]: https://github.com/paritytech/parity-ethereum/releases
[l]: https://github.com/mmgen/MMGenLive
[y]: https://github.com/ethereum/pyethereum
[P]: https://pypi.org/project/pip
[M]: https://getmonero.org/downloads/#linux
[U]: https://github.com/mmgen/MMGenLive/blob/master/home.mmgen/bin/mmlive-daemon-upgrade
[X]: autosign-[MMGen-command-help]
[bo]: Getting-Started-with-MMGen#a_bo
[si]: Install-Bitcoind-from-Source-on-Debian-or-Ubuntu-Linux
[bi]: Install-Bitcoind#a_d
[p8]: Install-Bitcoind#a_r
[iw]: Install-MMGen-on-Debian-or-Ubuntu-Linux

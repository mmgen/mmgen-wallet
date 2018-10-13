## Table of Contents

#### [Full support for Ethereum (ETH), Ethereum Classic (ETC) and ERC20 Tokens](#a_eth)
* [Install and run Parity Ethereum](#a_par)
* [Install the Pyethereum library](#a_pe)
* [Transacting and other basic operations](#a_tx)
* [Creating and deploying ERC20 tokens](#a_dt)

#### [Full support for Bcash (BCH) and Litecoin](#a_bch)

#### [Enhanced key/address generation support for Monero (XMR) and Zcash (ZEC)](#a_es)

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
Unfortunately, Python 2 is not reliably supported by recent versions of
pyethereum and some of its dependencies, so older versions must be installed.
This can be done easily with the [pip][P] Python package installer.

First install the following dependencies:

	$ pip install rlp==0.6.0 # the version is important here!
	$ pip install future pysha3 PyYAML py_ecc

Now install the library itself.  You could try doing this the usual way:

	$ pip install ethereum==2.1.2 # the version is important here!

However, pyethereum pulls in a whole bunch of silly dependencies, some of which
may fail to install, and we need only a subset of the library anyway, so it's
better to do the following instead:

	$ pip download ethereum==2.1.2

This will download the package archive and dependencies.  When pip starts
downloading the dependency archives, just bail out with Ctrl-C, since you don't
need them.

Now unpack the ethereum-2.1.2.tar.gz archive and remove unneeded deps from
'requirements.txt', making the file look exactly like this:

	pysha3>=1.0.1
	PyYAML
	scrypt
	py_ecc
	rlp>=0.4.7
	future

Now install:

	$ sudo python ./setup.py install

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

Install the Solidity compiler (`solc`) on your system:

	$ sudo apt-get install solc

##### Token creation/deployment example:

*Note: All addresses and filenames in the examples to follow are bogus.  You
must replace them with real ones.*

Create a token 'MFT' with default parameters, owned by `ddeeff...` (`ABCDABCD:E:1`):

	# Do this in the MMGen repository root:
	$ scripts/create-token.py --symbol=MFT --name='My First Token' ddeeffddeeffddeeffddeeffddeeffddeeffddee

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

### <a name='a_es'>Enhanced key/address generation support for Monero (XMR) and Zcash (ZEC)</a>

MMGen's enhanced key/address generation support for Zcash and Monero includes
**Zcash z-addresses** and automated Monero wallet creation.

Generate ten Zcash z-address key/address pairs from your default wallet:

	$ mmgen-keygen --coin=zec --type=zcash_z 1-10

The addresses' view keys are included in the file as well.

NOTE: Since your key/address file will probably be used on an online computer,
you should encrypt it with a good password when prompted to do so. The file can
decrypted as required using the `mmgen-tool decrypt` command.  If you choose a
non-standard Scrypt hash preset, take care to remember it.

To generate Zcash t-addresses, just omit the `--type` argument:

	$ mmgen-keygen --coin=zec 1-10

Generate ten Monero address pairs from your default wallet:

	$ mmgen-keygen --coin=xmr 1-10

In addition to spend and view keys, Monero key/address files also include a
wallet password for each address (the password is the double SHA256 of the spend
key, truncated to 16 bytes).  This allows you to generate a wallet from each
key in the key/address file by running the following command:

	$ monero-wallet-cli --generate-from-spend-key MyMoneroWallet

and pasting in the key and password data when prompted.  Monerod must be
running and `monero-wallet-cli` be located in your executable path.

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
[U]: https://github.com/mmgen/MMGenLive/blob/master/home.mmgen/bin/mmlive-daemon-upgrade
[X]: autosign-[MMGen-command-help]
[bo]: Getting-Started-with-MMGen#a_bo
[si]: Install-Bitcoind-from-Source-on-Debian-or-Ubuntu-Linux
[bi]: Install-Bitcoind#a_d
[p8]: Install-Bitcoind#a_r

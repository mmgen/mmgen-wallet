### MMGen Version 0.10.0 Release Notes

#### New features:

 - Python 3 support (3.5 to 3.7).  Python 2 is no longer supported!

 - Users should upgrade their Python dependencies as follows:

		sudo apt-get install python3-dev python3-ecdsa python3-pexpect python3-setuptools python3-crypto python3-nacl python3-pip
		sudo -H pip3 install scrypt

 - Ethereum, ERC20 and Monero dependencies must be upgraded as well, if
   support for these coins is desired.  See the [Altcoin and Forkcoin
   Support][f] wiki page for details.

   This is a Linux-only release.  It has been tested on the following platforms:

	   Ubuntu Bionic / x86_64, qemu-x86_64 
	   Ubuntu Xenial (+Python 3.6.7) / x86_64 
	   Armbian Bionic / Orange Pi PC2
	   Raspbian Stretch / Raspberry Pi B 

	with the following coin daemons:

		Bitcoin Core v0.17.1
		Bitcoin ABC v0.18.8
		Litecoin Core v0.16.3
		Monerod v0.13.0.4
		Parity Ethereum v1.11.1 & v2.3.2

	and the following altcoin libraries / address generation tools: 

		pyethereum b704a5c (https://github.com/ethereum/pyethereum)
		zcash-mini a2b3504 (https://github.com/FiloSottile/zcash-mini)
		pycoin 6fb55ec (https://github.com/richardkiss/pycoin)
		vanitygen-plus e5b104e (https://github.com/exploitagency/vanitygen-plus)

[f]: https://github.com/mmgen/mmgen/wiki/Altcoin-and-Forkcoin-Support

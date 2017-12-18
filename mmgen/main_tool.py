#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2017 Philemon <mmgen-py@yandex.com>
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
mmgen-tool:  Perform various MMGen- and cryptocoin-related operations.
             Part of the MMGen suite
"""

from mmgen.common import *

stdin_msg = """
To force a command to read from STDIN in place of its first argument (for
supported commands), use '-' as the first argument.
""".strip()

cmd_help = """
Cryptocoin address/key operations (compressed public keys supported):
  addr2hexaddr   - convert coin address from base58 to hex format
  hex2wif        - convert a private key from hex to WIF format (use 'pubkey_type=zcash_z' for zcash-z key)
  pubhash2addr   - convert public key hash to address
  privhex2addr   - generate coin address from private key in hex format
  privhex2pubhex - generate a hex public key from a hex private key
  pubhex2addr    - convert a hex pubkey to an address
  pubhex2redeem_script - convert a hex pubkey to a witness redeem script
  wif2redeem_script - convert a WIF private key to a witness redeem script
  wif2segwit_pair - generate both a Segwit redeem script and address from WIF
  pubkey2addr    - convert coin public key to address
  randpair       - generate a random private key/address pair
  randwif        - generate a random private key in WIF format
  wif2addr       - generate a coin address from a key in WIF format
  wif2hex        - convert a private key from WIF to hex format

Wallet/TX operations (coin daemon must be running):
  getbalance    - like '{pn}-cli getbalance' but shows confirmed/unconfirmed,
                  spendable/unspendable balances for individual {pnm} wallets
  listaddress   - list the specified {pnm} address and its balance
  listaddresses - list {pnm} addresses and their balances
  txview        - show raw/signed {pnm} transaction in human-readable form
  twview        - view tracking wallet

General utilities:
  hexdump      - encode data into formatted hexadecimal form (file or stdin)
  unhexdump    - decode formatted hexadecimal data (file or stdin)
  bytespec     - convert a byte specifier such as '1GB' into an integer
  hexlify      - display string in hexadecimal format
  hexreverse   - reverse bytes of a hexadecimal string
  rand2file    - write 'n' bytes of random data to specified file
  randhex      - print 'n' bytes (default 32) of random data in hex format
  hash256      - compute sha256(sha256(data)) (double sha256)
  hash160      - compute ripemd160(sha256(data)) (converts hexpubkey to hexaddr)
  b58randenc   - generate a random 32-byte number and convert it to base 58
  b58tostr     - convert a base 58 number to a string
  strtob58     - convert a string to base 58
  b58tohex     - convert a base 58 number to hexadecimal
  hextob58     - convert a hexadecimal number to base 58
  b32tohex     - convert a base 32 number to hexadecimal
  hextob32     - convert a hexadecimal number to base 32

File encryption:
  encrypt      - encrypt a file
  decrypt      - decrypt a file
    {pnm} encryption suite:
      * Key: Scrypt (user-configurable hash parameters, 32-byte salt)
      * Enc: AES256_CTR, 16-byte rand IV, sha256 hash + 32-byte nonce + data
      * The encrypted file is indistinguishable from random data

{pnm}-specific operations:
  add_label    - add descriptive label for {pnm} address in tracking wallet
  remove_label - remove descriptive label for {pnm} address in tracking wallet
  addrfile_chksum    - compute checksum for {pnm} address file
  keyaddrfile_chksum - compute checksum for {pnm} key-address file
  passwdfile_chksum  - compute checksum for {pnm} password file
  find_incog_data    - Use an Incog ID to find hidden incognito wallet data
  id6          - generate 6-character {pnm} ID for a file (or stdin)
  id8          - generate 8-character {pnm} ID for a file (or stdin)
  str2id6      - generate 6-character {pnm} ID for a string, ignoring spaces

Mnemonic operations (choose 'electrum' (default), 'tirosh' or 'all'
  wordlists):
  mn_rand128   - generate random 128-bit mnemonic
  mn_rand192   - generate random 192-bit mnemonic
  mn_rand256   - generate random 256-bit mnemonic
  mn_stats     - show stats for mnemonic wordlist
  mn_printlist - print mnemonic wordlist
  hex2mn       - convert a 16, 24 or 32-byte number in hex format to a mnemonic
  mn2hex       - convert a 12, 18 or 24-word mnemonic to a number in hex format

  IMPORTANT NOTE: Though {pnm} mnemonics use the Electrum wordlist, they're
  computed using a different algorithm and are NOT Electrum-compatible!

  {sm}
"""

opts_data = lambda: {
	'desc':    'Perform various {pnm}- and cryptocoin-related operations'.format(pnm=g.proj_name),
	'usage':   '[opts] <command> <command args>',
	'options': """
-d, --outdir=       d Specify an alternate directory 'd' for output
-h, --help            Print this help message
--, --longhelp        Print help message for long options (common options)
-P, --passwd-file= f  Get passphrase from file 'f'.
-q, --quiet           Produce quieter output
-r, --usr-randchars=n Get 'n' characters of additional randomness from
                      user (min={g.min_urandchars}, max={g.max_urandchars})
-t, --type=t          Specify address type (valid options: 'compressed','segwit','zcash_z')
-v, --verbose         Produce more verbose output
""".format(g=g),
	'notes': """

                               COMMANDS
{ch}
Type '{pn} help <command> for help on a particular command
""".format( pn=g.prog_name,
			ch=cmd_help.format(
				pn=g.proto.name,
				pnm=g.proj_name,
				sm='\n  '.join(stdin_msg.split('\n')))
	)
}

cmd_args = opts.init(opts_data,add_opts=['hidden_incog_input_params','in_fmt'])

if len(cmd_args) < 1: opts.usage()

Command = cmd_args.pop(0).capitalize()

import mmgen.tool as tool

if Command == 'Help' and not cmd_args: tool.usage(None)

if Command not in tool.cmd_data:
	die(1,"'%s': no such command" % Command.lower())

args,kwargs = tool.process_args(Command,cmd_args)
try:
	ret = tool.__dict__[Command](*args,**kwargs)
except Exception as e:
	die(1,'{}'.format(e))

sys.exit(0 if ret in (None,True) else 1) # some commands die, some return False on failure

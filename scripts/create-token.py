#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
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
scripts/create-token.py: Automated ERC20 token creation for the MMGen suite
"""

import sys, json, re
from subprocess import run, PIPE
from collections import namedtuple

import script_init
from mmgen.main import launch
from mmgen.cfg import Config
from mmgen.util import Msg, msg, rmsg, ymsg, die

ti = namedtuple('token_param_info', ['default', 'conversion', 'test'])
class TokenData:
	fields = ('decimals', 'supply', 'name', 'symbol', 'owner_addr')
	decimals   = ti('18', int, lambda s: s.isascii() and s.isdigit() and 0 < int(s) <= 36)
	name       = ti(None, str, lambda s: s.isascii() and s.isprintable() and len(s) < 256)
	supply     = ti(None, int, lambda s: s.isascii() and s.isdigit() and 0 < int(s) < 2**256)
	symbol     = ti(None, str, lambda s: s.isascii() and s.isalnum() and len(s) <= 20)
	owner_addr = ti(None, str, lambda s: s.isascii() and s.isalnum() and len(s) == 40) # checked separately

token_data = TokenData()

req_solc_ver_pat = '^0.8.25'

opts_data = {
	'text': {
		'desc': 'Create an ERC20 token contract',
		'usage':'[opts] <owner address>',
		'options': f"""
-h, --help        Print this help message
-o, --outdir=D    Specify output directory for *.bin files
-d, --decimals=D  Number of decimals for the token (default: {token_data.decimals.default})
-n, --name=N      Token name (REQUIRED)
-p, --preprocess  Print the preprocessed code to stdout
-t, --supply=T    Total supply of the token (REQUIRED)
-s, --symbol=S    Token symbol (REQUIRED)
-S, --stdout      Output JSON data to stdout instead of files
-v, --verbose     Produce more verbose output
-c, --check-solc-version Check the installed solc version
""",
	'notes': """
The owner address must be in checksummed format.

Use ‘mmgen-tool eth_checksummed_addr’ to create it if necessary.
"""
	}
}

# ERC Token Standard #20 Interface
# https://github.com/ethereum/EIPs/blob/master/EIPS/eip-20-token-standard.md

solidity_code_template = """
// SPDX-License-Identifier: GPL-3.0-or-later

pragma solidity %s;

contract SafeMath {
    function safeAdd(uint a, uint b) public pure returns (uint c) {
        c = a + b;
        require(c >= a);
    }
    function safeSub(uint a, uint b) public pure returns (uint c) {
        require(b <= a);
        c = a - b;
    }
    function safeMul(uint a, uint b) public pure returns (uint c) {
        c = a * b;
        require(a == 0 || c / a == b);
    }
    function safeDiv(uint a, uint b) public pure returns (uint c) {
        require(b > 0);
        c = a / b;
    }
}

abstract contract ERC20Interface {
    function totalSupply() public virtual returns (uint);
    function balanceOf(address tokenOwner) public virtual returns (uint balance);
    function allowance(address tokenOwner, address spender) public virtual returns (uint remaining);
    function transfer(address to, uint tokens) public virtual returns (bool success);
    function approve(address spender, uint tokens) public virtual returns (bool success);
    function transferFrom(address from, address to, uint tokens) public virtual returns (bool success);

    event Transfer(address indexed from, address indexed to, uint tokens);
    event Approval(address indexed tokenOwner, address indexed spender, uint tokens);
}

contract Owned {
    address public owner;
    address public newOwner;

    event OwnershipTransferred(address indexed _from, address indexed _to);

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner {
        require(msg.sender == owner);
        _;
    }

    function transferOwnership(address _newOwner) public onlyOwner {
        newOwner = _newOwner;
    }
    function acceptOwnership() public {
        require(msg.sender == newOwner);
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
        newOwner = address(0);
    }
}

// ----------------------------------------------------------------------------
// ERC20 Token, with the addition of symbol, name and decimals and assisted
// token transfers
// ----------------------------------------------------------------------------
contract Token is ERC20Interface, Owned, SafeMath {
    string public symbol;
    string public  name;
    uint8 public decimals;
    uint public _totalSupply;

    mapping(address => uint) balances;
    mapping(address => mapping(address => uint)) allowed;

    constructor() {
        symbol = "$symbol";
        name = "$name";
        decimals = $decimals;
        _totalSupply = $supply;
        balances[$owner_addr] = _totalSupply;
        emit Transfer(address(0), $owner_addr, _totalSupply);
    }
    function totalSupply() public view override returns (uint) {
        return _totalSupply  - balances[address(0)];
    }
    function balanceOf(address tokenOwner) public view override returns (uint balance) {
        return balances[tokenOwner];
    }
    function transfer(address to, uint tokens) public override returns (bool success) {
        balances[msg.sender] = safeSub(balances[msg.sender], tokens);
        balances[to] = safeAdd(balances[to], tokens);
        emit Transfer(msg.sender, to, tokens);
        return true;
    }
    function approve(address spender, uint tokens) public override returns (bool success) {
        allowed[msg.sender][spender] = tokens;
        emit Approval(msg.sender, spender, tokens);
        return true;
    }
    function transferFrom(address from, address to, uint tokens) public override returns (bool success) {
        balances[from] = safeSub(balances[from], tokens);
        allowed[from][msg.sender] = safeSub(allowed[from][msg.sender], tokens);
        balances[to] = safeAdd(balances[to], tokens);
        emit Transfer(from, to, tokens);
        return true;
    }
    function allowance(address tokenOwner, address spender) public view override returns (uint remaining) {
        return allowed[tokenOwner][spender];
    }
    // Owner can transfer out any accidentally sent ERC20 tokens
    function transferAnyERC20Token(address tokenAddress, uint tokens) public onlyOwner returns (bool success) {
        return ERC20Interface(tokenAddress).transfer(owner, tokens);
    }
}
""" % req_solc_ver_pat

def create_src(cfg, template, token_data):

	def gen():
		for k in token_data.fields:
			field = getattr(token_data, k)
			if k == 'owner_addr':
				owner_addr = cfg._args[0]
				from mmgen.addr import is_coin_addr
				if not is_coin_addr(cfg._proto, owner_addr.lower()):
					die(1, f'{owner_addr}: not a valid {cfg._proto.coin} coin address')
				val = '0x' + owner_addr
			else:
				val = (
					getattr(cfg, k)
					or getattr(field, 'default', None)
					or die(1, f'The --{k} option must be specified')
				)
				if not field.test(val):
					die(1, f'{val!r}: invalid parameter for option --{k}')

			yield (k, field.conversion(val))

	from string import Template
	return Template(template).substitute(**dict(gen()))

def check_solc_version():
	"""
	The output is used by other programs, so write to stdout only
	"""
	try:
		cp = run(['solc', '--version'], check=True, stdout=PIPE)
	except:
		msg('solc missing or could not be executed') # this must go to stderr
		return False

	if cp.returncode != 0:
		Msg('solc exited with error')
		return False

	line = cp.stdout.decode().splitlines()[1]
	version_str = re.sub(r'Version:\s*', '', line)
	m = re.match(r'(\d+)\.(\d+)\.(\d+)', version_str)

	if not m:
		Msg(f'Unrecognized solc version string: {version_str}')
		return False

	from semantic_version import Version, NpmSpec
	version = Version('{}.{}.{}'.format(*m.groups()))

	if version in NpmSpec(req_solc_ver_pat):
		Msg(str(version))
		return True
	else:
		Msg(f'solc version ({version_str}) does not match requirement ({req_solc_ver_pat})')
		return False

def compile_code(cfg, code):
	cmd = ['solc', '--optimize', '--bin', '--overwrite', '--evm-version=constantinople']
	if not cfg.stdout:
		cmd += ['--output-dir', cfg.outdir or '.']
	cmd += ['-']
	msg(f"Executing: {' '.join(cmd)}")
	cp = run(cmd, input=code.encode(), stdout=PIPE, stderr=PIPE)
	out = cp.stdout.decode().replace('\r', '')
	err = cp.stderr.decode().replace('\r', '').strip()
	if cp.returncode != 0:
		rmsg('Solidity compiler produced the following error:')
		msg(err)
		die(4, f'Solidity compiler exited with error (return val: {cp.returncode})')
	if err:
		ymsg('Solidity compiler produced the following warning:')
		msg(err)
	if cfg.stdout:
		o = out.split('\n')
		return {k:o[i+2] for k in ('SafeMath', 'Owned', 'Token') for i in range(len(o)) if k in o[i]}
	else:
		cfg._util.vmsg(out)

def main():
	cfg = Config(opts_data=opts_data)

	if cfg.check_solc_version:
		sys.exit(0 if check_solc_version() else 1)

	if not cfg._proto.coin in ('ETH', 'ETC'):
		die(1, '--coin option must be ETH or ETC')

	if not len(cfg._args) == 1:
		cfg._usage()

	code = create_src(cfg, solidity_code_template, token_data)

	if cfg.preprocess:
		Msg(code)
		sys.exit(0)

	out = compile_code(cfg, code)

	if cfg.stdout:
		print(json.dumps(out))

	msg('Contract successfully compiled')

if __name__ == '__main__':

	launch(func=main)

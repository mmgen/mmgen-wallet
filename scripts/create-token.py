#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2019 The MMGen Project <mmgen@tuta.io>
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

import sys,os,json,re
from subprocess import run,PIPE
from mmgen.common import *
from mmgen.obj import CoinAddr,is_coin_addr

decimals = 18
supply   = 10**26
name   = 'MMGen Token'
symbol = 'MMT'
solc_version_pat = r'0.5.[123]'

opts_data = {
	'text': {
		'desc': 'Create an ERC20 token contract',
		'usage':'[opts] <owner address>',
		'options': """
-h, --help       Print this help message
-o, --outdir=  d Specify output directory for *.bin files
-d, --decimals=d Number of decimals for the token (default: {d})
-n, --name=n     Token name (default: {n})
-t, --supply=  t Total supply of the token (default: {t})
-s, --symbol=  s Token symbol (default: {s})
-S, --stdout     Output data in JSON format to stdout instead of files
-v, --verbose    Produce more verbose output
"""
	},
	'code': {
		'options': lambda s: s.format(
			d=decimals,
			n=name,
			s=symbol,
			t=supply)
	}
}

cmd_args = opts.init(opts_data)
assert g.coin in ('ETH','ETC'),'--coin option must be set to ETH or ETC'

if not len(cmd_args) == 1 or not is_coin_addr(cmd_args[0].lower()):
	opts.usage()

owner_addr = '0x' + cmd_args[0]

# ERC Token Standard #20 Interface
# https://github.com/ethereum/EIPs/blob/master/EIPS/eip-20-token-standard.md

code_in = """

pragma solidity >0.5.0 <0.5.4;

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

contract ERC20Interface {
    function totalSupply() public returns (uint);
    function balanceOf(address tokenOwner) public returns (uint balance);
    function allowance(address tokenOwner, address spender) public returns (uint remaining);
    function transfer(address to, uint tokens) public returns (bool success);
    function approve(address spender, uint tokens) public returns (bool success);
    function transferFrom(address from, address to, uint tokens) public returns (bool success);

    event Transfer(address indexed from, address indexed to, uint tokens);
    event Approval(address indexed tokenOwner, address indexed spender, uint tokens);
}

contract Owned {
    address public owner;
    address public newOwner;

    event OwnershipTransferred(address indexed _from, address indexed _to);

    constructor() public {
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

    constructor() public {
        symbol = "<SYMBOL>";
        name = "<NAME>";
        decimals = <DECIMALS>;
        _totalSupply = <SUPPLY>;
        balances[<OWNER_ADDR>] = _totalSupply;
        emit Transfer(address(0), <OWNER_ADDR>, _totalSupply);
    }
    function totalSupply() public returns (uint) {
        return _totalSupply  - balances[address(0)];
    }
    function balanceOf(address tokenOwner) public returns (uint balance) {
        return balances[tokenOwner];
    }
    function transfer(address to, uint tokens) public returns (bool success) {
        balances[msg.sender] = safeSub(balances[msg.sender], tokens);
        balances[to] = safeAdd(balances[to], tokens);
        emit Transfer(msg.sender, to, tokens);
        return true;
    }
    function approve(address spender, uint tokens) public returns (bool success) {
        allowed[msg.sender][spender] = tokens;
        emit Approval(msg.sender, spender, tokens);
        return true;
    }
    function transferFrom(address from, address to, uint tokens) public returns (bool success) {
        balances[from] = safeSub(balances[from], tokens);
        allowed[from][msg.sender] = safeSub(allowed[from][msg.sender], tokens);
        balances[to] = safeAdd(balances[to], tokens);
        emit Transfer(from, to, tokens);
        return true;
    }
    function allowance(address tokenOwner, address spender) public returns (uint remaining) {
        return allowed[tokenOwner][spender];
    }
    // Owner can transfer out any accidentally sent ERC20 tokens
    function transferAnyERC20Token(address tokenAddress, uint tokens) public onlyOwner returns (bool success) {
        return ERC20Interface(tokenAddress).transfer(owner, tokens);
    }
}
"""

def create_src(code):
	for k in ('decimals','supply','name','symbol','owner_addr'):
		if hasattr(opt,k) and getattr(opt,k): globals()[k] = getattr(opt,k)
		code = code.replace('<{}>'.format(k.upper()),str(globals()[k]))
	return code

def check_version():
	res = run(['solc','--version'],stdout=PIPE).stdout.decode()
	ver = re.search(r'Version:\s*(.*)',res).group(1)
	msg("Installed solc version: {}".format(ver))
	if not re.search(r'{}\b'.format(solc_version_pat),ver):
		ydie(1,'Incorrect Solidity compiler version (need version {})'.format(solc_version_pat))

def compile_code(code):
	check_version()
	cmd = ['solc','--optimize','--bin','--overwrite']
	if not opt.stdout:
		cmd += ['--output-dir', opt.outdir or '.']
	cmd += ['-']
	msg('Executing: {}'.format(' '.join(cmd)))
	cp = run(cmd,input=code.encode(),stdout=PIPE,stderr=PIPE)
	out = cp.stdout.decode().replace('\r','')
	err = cp.stderr.decode().replace('\r','').strip()
	if cp.returncode != 0:
		rmsg('Solidity compiler produced the following error:')
		msg(err)
		rdie(2,'Solidity compiler exited with error (return val: {})'.format(cp.returncode))
	if err:
		ymsg('Solidity compiler produced the following warning:')
		msg(err)
	if opt.stdout:
		o = out.split('\n')
		return {k:o[i+2] for k in ('SafeMath','Owned','Token') for i in range(len(o)) if k in o[i]}
	else:
		vmsg(out)

src = create_src(code_in)
out = compile_code(src)
if opt.stdout:
	print(json.dumps(out))

msg('Contract successfully compiled')

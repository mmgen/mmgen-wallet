#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2021 The MMGen Project <mmgen@tuta.io>
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

class TokenData:
	attrs = ('decimals','supply','name','symbol','owner_addr')
	decimals = 18
	supply = 10**26
	name = 'MMGen Token'
	symbol = 'MMT'
	owner_addr = None

token_data = TokenData()

req_solc_ver_pat = '^0.5.2'

opts_data = {
	'text': {
		'desc': 'Create an ERC20 token contract',
		'usage':'[opts] <owner address>',
		'options': f"""
-h, --help        Print this help message
-o, --outdir=D    Specify output directory for *.bin files
-d, --decimals=D  Number of decimals for the token (default: {token_data.decimals})
-n, --name=N      Token name (default: {token_data.name!r})
-t, --supply=T    Total supply of the token (default: {token_data.supply})
-s, --symbol=S    Token symbol (default: {token_data.symbol!r})
-S, --stdout      Output JSON data to stdout instead of files
-v, --verbose     Produce more verbose output
-c, --check-solc-version Check the installed solc version
""",
	'notes': """
The owner address must be in checksummed format
"""
	}
}

# ERC Token Standard #20 Interface
# https://github.com/ethereum/EIPs/blob/master/EIPS/eip-20-token-standard.md

solidity_code_template = """

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
""" % req_solc_ver_pat

def create_src(code,token_data,owner_addr):
	token_data.owner_addr = '0x' + owner_addr
	for k in token_data.attrs:
		if getattr(opt,k,None):
			setattr( token_data, k, getattr(opt,k) )
		code = code.replace( f'<{k.upper()}>', str(getattr(token_data,k)) )
	return code

def check_solc_version():
	"""
	The output is used by other programs, so write to stdout only
	"""
	try:
		cp = run(['solc','--version'],check=True,stdout=PIPE)
	except:
		msg('solc missing or could not be executed') # this must go to stderr
		return False

	if cp.returncode != 0:
		Msg('solc exited with error')
		return False

	line = cp.stdout.decode().splitlines()[1]
	version_str = re.sub(r'Version:\s*','',line)
	m = re.match(r'(\d+)\.(\d+)\.(\d+)',version_str)

	if not m:
		Msg(f'Unrecognized solc version string: {version_str}')
		return False

	from semantic_version import Version,NpmSpec
	version = Version('{}.{}.{}'.format(*m.groups()))

	if version in NpmSpec(req_solc_ver_pat):
		Msg(str(version))
		return True
	else:
		Msg(f'solc version ({version_str}) does not match requirement ({req_solc_ver_pat})')
		return False

def compile_code(code):
	cmd = ['solc','--optimize','--bin','--overwrite']
	if not opt.stdout:
		cmd += ['--output-dir', opt.outdir or '.']
	cmd += ['-']
	msg(f"Executing: {' '.join(cmd)}")
	cp = run(cmd,input=code.encode(),stdout=PIPE,stderr=PIPE)
	out = cp.stdout.decode().replace('\r','')
	err = cp.stderr.decode().replace('\r','').strip()
	if cp.returncode != 0:
		rmsg('Solidity compiler produced the following error:')
		msg(err)
		rdie(2,f'Solidity compiler exited with error (return val: {cp.returncode})')
	if err:
		ymsg('Solidity compiler produced the following warning:')
		msg(err)
	if opt.stdout:
		o = out.split('\n')
		return {k:o[i+2] for k in ('SafeMath','Owned','Token') for i in range(len(o)) if k in o[i]}
	else:
		vmsg(out)

if __name__ == '__main__':

	cmd_args = opts.init(opts_data)

	if opt.check_solc_version:
		sys.exit(0 if check_solc_version() else 1)

	from mmgen.protocol import init_proto_from_opts
	proto = init_proto_from_opts()

	if not proto.coin in ('ETH','ETC'):
		die(1,'--coin option must be ETH or ETC')

	if not len(cmd_args) == 1:
		opts.usage()

	owner_addr = cmd_args[0]

	from mmgen.obj import is_coin_addr
	if not is_coin_addr( proto, owner_addr.lower() ):
		die(1,f'{owner_addr}: not a valid {proto.coin} coin address')

	out = compile_code(
		create_src( solidity_code_template, token_data, owner_addr )
	)

	if opt.stdout:
		print(json.dumps(out))

	msg('Contract successfully compiled')

#!/usr/bin/env python3

import sys,os,json
from subprocess import Popen,PIPE
from mmgen.common import *
from mmgen.obj import CoinAddr,is_coin_addr

decimals = 18
supply   = 10**26
name   = 'MMGen Token'
symbol = 'MMT'

opts_data = lambda: {
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
""".format(d=decimals,n=name,s=symbol,t=supply)
}

cmd_args = opts.init(opts_data)
assert g.coin in ('ETH','ETC'),'--coin option must be set to ETH or ETC'

if not len(cmd_args) == 1 or not is_coin_addr(cmd_args[0]):
	opts.usage()

owner_addr = '0x' + CoinAddr(cmd_args[0])

# ERC Token Standard #20 Interface
# https://github.com/ethereum/EIPs/blob/master/EIPS/eip-20-token-standard.md
code_in = """
pragma solidity ^0.4.18;

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
    function totalSupply() public constant returns (uint);
    function balanceOf(address tokenOwner) public constant returns (uint balance);
    function allowance(address tokenOwner, address spender) public constant returns (uint remaining);
    function transfer(address to, uint tokens) public returns (bool success);
    function approve(address spender, uint tokens) public returns (bool success);
    function transferFrom(address from, address to, uint tokens) public returns (bool success);

    event Transfer(address indexed from, address indexed to, uint tokens);
    event Approval(address indexed tokenOwner, address indexed spender, uint tokens);
}

// Contract function to receive approval and execute function in one call
contract ApproveAndCallFallBack {
    function receiveApproval(address from, uint256 tokens, address token, bytes data) public;
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
    function totalSupply() public constant returns (uint) {
        return _totalSupply  - balances[address(0)];
    }
    function balanceOf(address tokenOwner) public constant returns (uint balance) {
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
    function allowance(address tokenOwner, address spender) public constant returns (uint remaining) {
        return allowed[tokenOwner][spender];
    }
    function approveAndCall(address spender, uint tokens, bytes data) public returns (bool success) {
        allowed[msg.sender][spender] = tokens;
        emit Approval(msg.sender, spender, tokens);
        ApproveAndCallFallBack(spender).receiveApproval(msg.sender, tokens, this, data);
        return true;
    }
    // Don't accept ETH
    function () public payable {
        revert();
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

def compile_code(code):
	cmd = ['solc','--optimize','--bin','--overwrite']
	if not opt.stdout: cmd += ['--output-dir', opt.outdir or '.']
	p = Popen(cmd,stdin=PIPE,stdout=PIPE,stderr=PIPE)
	res = p.communicate(code)
	o = res[0].replace('\r','').split('\n')
	dmsg(res[1])
	if opt.stdout:
		return dict((k,o[i+2]) for k in ('SafeMath','Owned','Token') for i in range(len(o)) if k in o[i])

src = create_src(code_in)
out = compile_code(src)
if opt.stdout:
	print(json.dumps(out))

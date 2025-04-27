// MMGen Wallet, a terminal-based cryptocurrency wallet
// Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
// Licensed under the GNU General Public License, Version 3:
//   https://www.gnu.org/licenses
// Public project repositories:
//   https://github.com/mmgen/mmgen-wallet
//   https://gitlab.com/mmgen/mmgen-wallet
//
// Minimal THORChain router for testing
//
// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.8.25;

interface iERC20 {
	function transferFrom(
		address from,
		address to,
		uint tokens) external payable returns (bool success);
}

contract THORChain_Router {
	string public saved_memo;
	function depositWithExpiry(
		address payable vault,
		address asset,
		uint amount,
		string memory memo,
		uint expiration
	) external payable returns (bool success) {
		require(block.timestamp < expiration, "THORChain_Router: expired");
		saved_memo = memo;
		return iERC20(asset).transferFrom(msg.sender, vault, amount);
	}
}

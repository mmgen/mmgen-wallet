#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
swap.asset: THORChain swap asset class for the MMGen Wallet suite
"""

from ...asset import SwapAsset

class THORChainSwapAsset(SwapAsset):

	_ad = SwapAsset._ad
	assets_data = {
		'BTC':       _ad('Bitcoin',                 'BTC',  None,        'b',  None, True),
		'LTC':       _ad('Litecoin',                'LTC',  None,        'l',  None, True),
		'BCH':       _ad('Bitcoin Cash',            'BCH',  None,        'c',  None, True),
		'ETH':       _ad('Ethereum',                'ETH',  None,        'e',  None, True),
		'DOGE':      _ad('Dogecoin',                'DOGE', None,        'd',  None, False),
		'RUNE':      _ad('Rune (THORChain)',        'RUNE', 'THOR.RUNE', 'r',  None, True),
		'ETH.AAVE':  _ad('Aave (ETH)',              None,   'ETH.AAVE',  None, 18,   True),
		'ETH.DAI':   _ad('MakerDAO USD (ETH)',      None,   'ETH.DAI',   None, 18,   True),
		'ETH.DPI':   _ad('DeFi Pulse Index (ETH)',  None,   'ETH.DPI',   None, 18,   True),
		'ETH.FOX':   _ad('ShapeShift FOX (ETH)',    None,   'ETH.FOX',   None, 18,   True),
		'ETH.GUSD':  _ad('Gemini Dollar (ETH)',     None,   'ETH.GUSD',  None, 2,    True),
		'ETH.LINK':  _ad('Chainlink (ETH)',         None,   'ETH.LINK',  None, 18,   True),
		'ETH.LUSD':  _ad('Liquity USD (ETH)',       None,   'ETH.LUSD',  None, 18,   True),
		'ETH.SNX':   _ad('Synthetix (ETH)',         None,   'ETH.SNX',   None, 18,   True),
		'ETH.TGT':   _ad('THORWallet (ETH)',        None,   'ETH.TGT',   None, 18,   True),
		'ETH.THOR':  _ad('THORSwap (ETH)',          None,   'ETH.THOR',  None, 18,   True),
		'ETH.USDC':  _ad('USDC (ETH)',              None,   'ETH.USDC',  None, 6,    True),
		'ETH.USDP':  _ad('Pax Dollar (ETH)',        None,   'ETH.USDP',  None, 18,   True),
		'ETH.USDT':  _ad('Tether (ETH)',            None,   'ETH.USDT',  None, 6,    True),
		'ETH.vTHOR': _ad('THORSwap Staking (ETH)',  None,   'ETH.vTHOR', None, 18,   True),
		'ETH.WBTC':  _ad('Wrapped BTC (ETH)',       None,   'ETH.WBTC',  None, 8,    True),
		'ETH.XRUNE': _ad('Thorstarter (ETH)',       None,   'ETH.XRUNE', None, 18,   True),
		'ETH.YFI':   _ad('yearn.finance (ETH)',     None,   'ETH.YFI',   None, 18,   True)}

	evm_contracts = {
		'ETH.AAVE':  '7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9',
		'ETH.DAI':   '6b175474e89094c44da98b954eedeac495271d0f',
		'ETH.DPI':   '1494ca1f11d487c2bbe4543e90080aeba4ba3c2b',
		'ETH.FOX':   'c770eefad204b5180df6a14ee197d99d808ee52d',
		'ETH.GUSD':  '056fd409e1d7a124bd7017459dfea2f387b6d5cd',
		'ETH.LINK':  '514910771af9ca656af840dff83e8264ecf986ca',
		'ETH.LUSD':  '5f98805a4e8be255a32880fdec7f6728c6568ba0',
		'ETH.SNX':   'c011a73ee8576fb46f5e1c5751ca3b9fe0af2a6f',
		'ETH.TGT':   '108a850856db3f85d0269a2693d896b394c80325',
		'ETH.THOR':  'a5f2211b9b8170f694421f2046281775e8468044',
		'ETH.USDC':  'a0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
		'ETH.USDP':  '8e870d67f660d95d5be530380d0ec0bd388289e1',
		'ETH.USDT':  'dac17f958d2ee523a2206206994597c13d831ec7',
		'ETH.vTHOR': '815c23eca83261b6ec689b60cc4a58b54bc24d8d',
		'ETH.WBTC':  '2260fac5e5542a773aa44fbcfedf7c193bc2c599',
		'ETH.XRUNE': '69fa0fee221ad11012bab0fdb45d444d3d2ce71c',
		'ETH.YFI':   '0bc529c00c6401aef6d220be8c6ea1667f6ad93e'}

	unsupported = ('DOGE',)

	blacklisted = {}

	evm_chains = ('ETH', 'AVAX', 'BSC', 'BASE')

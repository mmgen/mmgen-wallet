#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
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
exception: Exception classes for the MMGen suite
"""

class MMGenError(Exception):

	def __init__(self, errno, strerror, stdout):
		self.mmcode = errno
		self.stdout = stdout
		super().__init__(strerror)

	def __repr__(self):
		return f'{type(self).__name__}({self.mmcode}):\n{self}'

class MMGenSystemExit(MMGenError):

	def __repr__(self):
		return f'{type(self).__name__}({self.mmcode}): {self}'

# 1: no hl, message only
class UserNonConfirmation(Exception):     mmcode = 1
class BadAgeFormat(Exception):            mmcode = 1
class BadFilename(Exception):             mmcode = 1
class BadFileExtension(Exception):        mmcode = 1
class SocketError(Exception):             mmcode = 1
class UserAddressNotInWallet(Exception):  mmcode = 1
class MnemonicError(Exception):           mmcode = 1
class RangeError(Exception):              mmcode = 1
class FileNotFound(Exception):            mmcode = 1
class InvalidPasswdFormat(Exception):     mmcode = 1
class CfgFileParseError(Exception):       mmcode = 1
class UserOptError(Exception):            mmcode = 1
class CmdlineOptError(Exception):         mmcode = 1
class NoLEDSupport(Exception):            mmcode = 1
class MsgFileFailedSID(Exception):        mmcode = 1
class TestSuiteException(Exception):      mmcode = 1
class TestSuiteSpawnedScriptException(Exception): mmcode = 1

# 2: yellow hl, message only
class InvalidContractAddress(Exception):  mmcode = 2
class UnrecognizedTokenSymbol(Exception): mmcode = 2
class TokenNotInBlockchain(Exception):    mmcode = 2
class TokenNotInWallet(Exception):        mmcode = 2
class BadTwComment(Exception):            mmcode = 2
class BadTwLabel(Exception):              mmcode = 2
class BaseConversionError(Exception):     mmcode = 2
class BaseConversionPadError(Exception):  mmcode = 2
class TransactionChainMismatch(Exception):mmcode = 2
class ObjectInitError(Exception):         mmcode = 2
class ClassFlagsError(Exception):         mmcode = 2
class ExtensionModuleError(Exception):    mmcode = 2
class MoneroMMGenTXFileParseError(Exception): mmcode = 2
class AutosignTXError(Exception):         mmcode = 2
class MMGenImportError(Exception):        mmcode = 2
class SwapMemoParseError(Exception):      mmcode = 2
class SwapAssetError(Exception):          mmcode = 2
class SwapCfgValueError(Exception):       mmcode = 2

# 3: yellow hl, 'MMGen Error' + exception + message
class RPCFailure(Exception):              mmcode = 3
class RPCChainMismatch(Exception):        mmcode = 3
class TxIDMismatch(Exception):            mmcode = 3
class BadTxSizeEstimate(Exception):       mmcode = 3
class MaxInputSizeExceeded(Exception):    mmcode = 3
class MaxFileSizeExceeded(Exception):     mmcode = 3
class MaxFeeExceeded(Exception):          mmcode = 3
class WalletFileError(Exception):         mmcode = 3
class HexadecimalStringError(Exception):  mmcode = 3
class SeedLengthError(Exception):         mmcode = 3
class PrivateKeyError(Exception):         mmcode = 3
class MMGenCalledProcessError(Exception): mmcode = 3
class TestSuiteFatalException(Exception): mmcode = 3

# 4: red hl, 'MMGen Fatal Error' + exception + message
class BadMMGenTxID(Exception):            mmcode = 4
class IllegalWitnessFlagValue(Exception): mmcode = 4
class TxHexParseError(Exception):         mmcode = 4
class TxHexMismatch(Exception):           mmcode = 4
class SubSeedNonceRangeExceeded(Exception): mmcode = 4

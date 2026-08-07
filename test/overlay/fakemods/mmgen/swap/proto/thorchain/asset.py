from .asset_orig import *

class overlay_fake_THORChainSwapAsset:

	assets_data = {
		'ETH.MM1':  THORChainSwapAsset._ad('MM1 Token (ETH)',  None, 'ETH.MM1',  None, True),
		'ETH.JUNK': THORChainSwapAsset._ad('Junk Token (ETH)', None, 'ETH.JUNK', None, True),
		'ETH.NONE': THORChainSwapAsset._ad('Unavailable Token (ETH)', None, 'ETH.NONE', None, True)
	}
	evm_contracts = {
		'ETH.MM1':  'deadbeefdeadbeefdeadbeefdeadbeefdeadbeef'
	}
	unsupported = ('ETH.NONE',)

	blacklisted = {
		'ETH.JUNK': 'Because it’s junk',
	}

THORChainSwapAsset.assets_data |= overlay_fake_THORChainSwapAsset.assets_data
THORChainSwapAsset.unsupported += overlay_fake_THORChainSwapAsset.unsupported
THORChainSwapAsset.blacklisted.update(overlay_fake_THORChainSwapAsset.blacklisted)
THORChainSwapAsset.evm_contracts.update(overlay_fake_THORChainSwapAsset.evm_contracts)

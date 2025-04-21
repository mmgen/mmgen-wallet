from .asset_orig import *

class overlay_fake_THORChainSwapAsset:

	assets_data = {
		'ETH.MM1':  THORChainSwapAsset._ad('MM1 Token (ETH)',  None,   'ETH.MM1',   None),
		'ETH.USDT': THORChainSwapAsset._ad('Tether (ETH)',     None,   'ETH.USDT',  None)
	}
	send = ('ETH.MM1',)
	recv = ('ETH.MM1', 'ETH.USDT')

THORChainSwapAsset.assets_data |= overlay_fake_THORChainSwapAsset.assets_data
THORChainSwapAsset.send += overlay_fake_THORChainSwapAsset.send
THORChainSwapAsset.recv += overlay_fake_THORChainSwapAsset.recv

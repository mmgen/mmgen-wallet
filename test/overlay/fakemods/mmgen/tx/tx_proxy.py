from .tx_proxy_orig import *

class overlay_fake_EtherscanTxProxyClient:
	proto  = 'http'
	host   = 'localhost:28800'
	verify = False

EtherscanTxProxyClient.proto = overlay_fake_EtherscanTxProxyClient.proto
EtherscanTxProxyClient.host = overlay_fake_EtherscanTxProxyClient.host
EtherscanTxProxyClient.verify = overlay_fake_EtherscanTxProxyClient.verify

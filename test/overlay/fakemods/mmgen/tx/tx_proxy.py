from .tx_proxy_orig import *

class overlay_fake_EtherscanTxProxyClient:
	network_proto = 'http'
	host = 'localhost:28800'
	verify = False

EtherscanTxProxyClient.network_proto = overlay_fake_EtherscanTxProxyClient.network_proto
EtherscanTxProxyClient.host = overlay_fake_EtherscanTxProxyClient.host
EtherscanTxProxyClient.verify = overlay_fake_EtherscanTxProxyClient.verify

from .thornode_orig import *

class overlay_fake_ThornodeRPCClient:

	network_proto = 'http'
	host = 'localhost:18800'
	verify = False

ThornodeRPCClient.network_proto = overlay_fake_ThornodeRPCClient.network_proto
ThornodeRPCClient.host = overlay_fake_ThornodeRPCClient.host
ThornodeRPCClient.verify = overlay_fake_ThornodeRPCClient.verify

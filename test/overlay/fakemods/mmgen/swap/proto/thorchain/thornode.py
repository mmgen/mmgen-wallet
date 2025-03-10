from .thornode_orig import *

class overlay_fake_ThornodeRPCClient:

	proto  = 'http'
	host   = 'localhost:18800'
	verify = False

ThornodeRPCClient.proto = overlay_fake_ThornodeRPCClient.proto
ThornodeRPCClient.host = overlay_fake_ThornodeRPCClient.host
ThornodeRPCClient.verify = overlay_fake_ThornodeRPCClient.verify

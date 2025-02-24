from .midgard_orig import *

class overlay_fake_MidgardRPCClient:

	proto  = 'http'
	host   = 'localhost:18800'
	verify = False

MidgardRPCClient.proto = overlay_fake_MidgardRPCClient.proto
MidgardRPCClient.host = overlay_fake_MidgardRPCClient.host
MidgardRPCClient.verify = overlay_fake_MidgardRPCClient.verify

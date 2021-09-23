#!/usr/bin/env python3
"""
test.unit_tests_d.ut_rpc: dependency unit tests for the MMGen suite
"""

from mmgen.common import *

class unit_tests:

	def pysocks(self,name,ut):
		import requests,urllib3
		urllib3.disable_warnings()
		session = requests.Session()
		session.proxies.update({'https':'socks5h://127.243.172.8:20677'})
		try:
			session.get('https://127.188.29.17')
		except Exception as e:
			if type(e).__name__ == 'ConnectionError':
				return True
			else:
				print(e)
		return False

#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
http: HTTP client base class
"""

import requests

class HTTPClient:

	network_proto = 'https'
	host = None
	timeout = 60
	http_hdrs = {
		'User-Agent': 'curl/8.7.1',
		'Proxy-Connection': 'Keep-Alive'}
	extra_http_hdrs = {}
	verify = True
	text_mode = True

	def __init__(self, cfg, *, network_proto=None, host=None):
		self.cfg = cfg
		if network_proto:
			self.network_proto = network_proto
		if host:
			self.host = host
		self.session = requests.Session()
		self.session.trust_env = False # ignore *_PROXY environment vars
		self.session.headers = (self.http_hdrs | self.extra_http_hdrs)
		if cfg.proxy == 'env':
			self.session.trust_env = True
		elif cfg.proxy:
			self.session.proxies.update({
				'http':  f'socks5h://{cfg.proxy}',
				'https': f'socks5h://{cfg.proxy}'})

	def call(self, name, path, err_fs, timeout, *, data=None):
		url = self.network_proto + '://' + self.host + path
		kwargs = {
			'url': url,
			'timeout': self.cfg.http_timeout or timeout or self.timeout,
			'verify': self.verify}
		if data:
			kwargs['data'] = data
		res = getattr(self.session, name)(**kwargs)
		if res.status_code != 200:
			from .util import die
			die(2, '\n' + err_fs.format(s=res.status_code, u=url, d=data))
		return res.content.decode() if self.text_mode else res.content

	def get(self, *, path, timeout=None):
		return self.call(
			'get',
			path,
			'HTTP GET failed with status code {s}\n  URL: {u}',
			timeout)

	def post(self, *, path, data, timeout=None):
		return self.call(
			'post',
			path,
			'HTTP POST failed with status code {s}\n  URL: {u}\n  DATA: {d}',
			timeout,
			data = data)

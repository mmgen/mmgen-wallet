from .tw_orig import *

if os.getenv('MMGEN_TEST_SUITE_DETERMINISTIC'):
	def _time_gen():
		""" add a minute to each successive time value """
		for i in range(1000000):
			yield 1321009871 + (i*60)

	_time_iter = _time_gen()

	TwUnspentOutputs.date_formatter = {
		'days':      lambda rpc,secs: (next(_time_iter) - secs) // 86400,
		'date':      lambda rpc,secs: '{}-{:02}-{:02}'.format(*time.gmtime(next(_time_iter))[:3])[2:],
		'date_time': lambda rpc,secs: '{}-{:02}-{:02} {:02}:{:02}'.format(*time.gmtime(next(_time_iter))[:5]),
	}

	TwAddrList.date_formatter = TwUnspentOutputs.date_formatter

if os.getenv('MMGEN_BOGUS_WALLET_DATA'):
	# 1831006505 (09 Jan 2028) = projected time of block 1000000
	TwUnspentOutputs.date_formatter['days'] = lambda rpc,secs: (1831006505 - secs) // 86400

	async def fake_set_dates(foo,rpc,us):
		for o in us:
			o.date = 1831006505 - int(9.7 * 60 * (o.confs - 1))

	async def fake_get_unspent_rpc(foo):
		return json.loads(get_data_from_file(os.getenv('MMGEN_BOGUS_WALLET_DATA')),parse_float=Decimal)

	TwUnspentOutputs.set_dates = fake_set_dates
	TwUnspentOutputs.get_unspent_rpc = fake_get_unspent_rpc

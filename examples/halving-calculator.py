#!/usr/bin/env python3

# Demonstrates use of the MMGen asyncio/aiohttp JSON-RPC interface
# https://github.com/mmgen/mmgen
# Requires a running Bitcoin Core node
# If necessary, invoke with --rpc-host/--rpc-port/--rpc-user/--rpc-password
# Specify aiohttp backend with --rpc-backend=aiohttp (Linux only)

import time
from decimal import Decimal
from mmgen.common import *

opts.init({ 'text': { 'desc':'', 'usage':'', 'options':'' }})

HalvingInterval = 210000 # src/chainparams.cpp

def date(t):
	return '{}-{:02}-{:02} {:02}:{:02}:{:02}'.format(*time.gmtime(t)[:6])

def dhms(t):
	return f'{t//60//60//24} days, {t//60//60%24:02}:{t//60%60:02}:{t%60:02} h/m/s'

def time_diff_warning(t_diff):
	if abs(t_diff) > 60*60:
		print('Warning: block tip time is {} {} clock time!'.format(
			dhms(abs(t_diff)),
			('behind','ahead of')[t_diff<0]))

async def main():
	from mmgen.rpc import rpc_init
	c = await rpc_init()
	tip = await c.call('getblockcount')
	remaining = HalvingInterval - tip % HalvingInterval
	sample_size = max(remaining,144)

	# aiohttp backend will perform these two calls concurrently:
	cur,old = await c.gathered_call('getblockstats',((tip,),(tip - sample_size,)))

	clock_time = int(time.time())
	time_diff_warning(clock_time - cur['time'])

	bdr = (cur['time'] - old['time']) / sample_size
	t_rem = remaining * int(bdr)
	sub = cur['subsidy'] * Decimal('0.00000001')

	print(f'Current block:      {tip}')
	print(f'Next halving block: {tip + remaining}')
	print(f'Blocks until halving: {remaining}')
	print('Current block subsidy: {} BTC'.format(str(sub).rstrip('0')))
	print(f'Current block discovery rate (over last {sample_size} blocks): {bdr/60:0.1f} minutes')
	print(f'Current clock time (UTC): {date(clock_time)}')
	print(f'Est. halving date (UTC):  {date(cur["time"] + t_rem)}')
	print(f'Est. time until halving:  {dhms(cur["time"] + t_rem - clock_time)}')

run_session(main(),do_rpc_init=False)

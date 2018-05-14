MMGen version 0.8.3

New features/improvements:

	* New native Bitcoin RPC library.
	* Support for cookie-based RPC authentication (new in Bitcoin Core v0.12.0).
	* Batch mode available when listing and importing addresses.
	* mmgen-tool listaddresses: 'addrs' argument allows you to specify an
	  address or range of addresses.

NOTE: if MMGen is already installed on your system, you must remove your
existing installation by hand before installing this new version.  On Linux,
this means deleting everything under the directory
'/usr/local/lib/python2.7/dist-packages/mmgen/'.  Also, if you did a 'git pull'
instead of a fresh clone, you must delete the 'build' directory in the
repository root before installing.

The 'mmgen-pywallet' utility has been removed.  It's no longer needed, as the
'bitcoin-cli dumpwallet' command (available since Core v0.9.0) provides
equivalent functionality.

The Windows port isn't being actively maintained at the moment.  Use at your own
risk, and report any problems on the Bitcointalk forum.

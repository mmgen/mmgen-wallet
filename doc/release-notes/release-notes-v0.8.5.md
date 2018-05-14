MMGen version 0.8.5

New features/improvements:

	* Colored output
	* Label editing in mmgen-txcreate

This release includes a major object-oriented rewrite of much of the code.

NOTE: The transaction file format has changed.  Since TX files are temporary, this
shouldn't be a problem for most.  However, the script 'tx-old2new.py' in the
scripts directory will convert old old TX files to the new format for those who
need to do so.

The Windows implementation is functional again.  Use at your own risk, and
report any problems on the Bitcointalk forum.

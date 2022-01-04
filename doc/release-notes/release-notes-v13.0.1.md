### MMGen Version 13.0.1 Release Notes

This is a minor bugfix/compatibility release.  ETH and Bitcoin Cash Node
users should upgrade.  Users of the test suite should also upgrade.

#### Changes from v13.0.0:

 - support Python 3.10
 - eth rlp: fix import for Python 3.10 (collections -> collections.abc)
 - support Bitcoin Cash Node v24.0.0, Geth v1.10.14
 - unit_tests.py dep: continue without LED support

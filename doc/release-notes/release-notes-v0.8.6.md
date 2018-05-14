### MMGen version 0.8.6 Release Notes

#### New features/improvements:

  - Address generation using secp256k1 library (Linux only)

Instructions for installing the secp256k1 library on your system can be found at
doc/wiki/install-linux/Install-MMGen-on-Debian-or-Ubuntu-Linux.md

If secp256k1 is not installed on the system, MMGen will still be usable. It just
falls back to 'keyconv', or failing that, python-ecdsa for generating addresses.

### MMGen MS Windows Notes

The following MMGen features are unsupported or broken on the MSWin/MinGW platform:

- Autosign (not supported)
- Zcash z-address generation (requires libsodium)
- Monero wallet creation/syncing\* (IO stream issues with pexpect and the password prompt)
- UTF-8 filename and path support

\*Monero address and viewkey generation are fully supported.

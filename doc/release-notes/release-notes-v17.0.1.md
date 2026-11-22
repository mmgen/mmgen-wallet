### MMGen Wallet Version 17.0.1 Release Notes

This security point release fixes two critical vulnerabilities whereby an
attacker with access to the online machine could craft transactions that
bypass the address-belongs-to-wallet checks performed by the offline signer.

These bugs were reported to the MMGen Project by an anonymous researcher, who
found them with the help of AI and disclosed them securely and without asking
for remuneration.

All users are urgently advised to upgrade.

#### Important security fixes:

 - ffffffff `tx.file`: require `have_wif` field to be absent
 - ffffffff `check_swap_memo()`: require `is_swap` to be set if memo present in transaction

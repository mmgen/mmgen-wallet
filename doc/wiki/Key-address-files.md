*NOTE: Key-address files have now been obsoleted by [subwallets][U].  The
information on this page is provided for the benefit of legacy installations
only*

Chances are you’ll want to use MMGen Wallet not only for cold storage but for
day-to-day transactions too.  For this you’ll need to place a portion of your
funds in a “hot wallet” on your online computer.  With hot wallet funds you
can use the command `mmgen-txdo` to quickly create, sign and send transactions
in one operation.

You can partition your wallet by mentally setting aside “hot” and “cold” address
ranges.  For example, you might choose to reserve all addresses in the range
1-1000 for cold storage and everything above that for your hot wallet.

The next step is to create a key-address file for a sufficient number of “hot”
addresses to cover your day-to-day transaction needs for the foreseeable future.
A key-address file is just like an address file except that it contains keys as
well as addresses, thus functioning as a hot wallet for a range of addresses.
Assuming your hot address range begins at 1001, you could start by creating a
key-address file for a hundred hot addresses like this:

```text
$ mmgen-keygen --type=segwit 1001-1100
...
Secret keys written to file '89ABCDEF-S[1001-1100].akeys.mmenc'
```

`mmgen-keygen` prompts you for a password to encrypt the key-address file with.
This is a wise precaution, as it provides at least some security for keys that
will be stored on an online machine.

Now copy the key-address file to your online machine and import the addresses
into your tracking wallet:

```text
$ mmgen-addrimport --batch --keyaddr-file '89ABCDEF-S[1001-1100].akeys.mmenc'
```

After funding your hot wallet by spending into some addresses in this range you
can do quickie transactions with these funds using the `mmgen-txdo` command:

```text
$ mmgen-txdo -M '89ABCDEF-S[1001-1100].akeys.mmenc' 1AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc,0.1 89ABCDEF:S:1010
...
Transaction sent: dcea1357....
```

The `--mmgen-keys-from-file` or `-M` option is required when using a key-address
file in place of a wallet.  Note that your change address `89ABCDEF:S:1010` is
within the range covered by the key-address file, so your change funds will
remain “hot spendable”.

[U]: Subwallets.md

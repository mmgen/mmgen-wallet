MMGen Wallet’s regtest mode, also known as Bob and Alice mode, uses the
regression test feature of the Bitcoin, Litecoin, and Bitcoin Cash daemons
to create a virtual network of two users who transact on a private blockchain.

All of MMGen Wallet’s functionality for these coins is available in regtest
mode, making it an ideal way to learn to use MMGen Wallet without risking real
assets.

To send a transaction or perform any other operation as Bob or Alice, just add
the `--bob` or `--alice` option to the applicable MMGen Wallet command.

This tutorial provides a quick, hands-on introduction.

1. Initialize regtest mode and start the regtest daemon:

```text
$ mmgen-regtest setup
$ mmgen-regtest start
```

2. Generate Bob’s wallet:

```text
$ mmgen-walletgen --bob
...
Make this wallet your default and move it to the data directory? (Y/n): y
```

3. Generate three type `C` (compressed) addresses with Bob’s wallet:

```text
$ mmgen-addrgen --bob --type=compressed 1-3
...
Addresses written to file '1163DDF1-C[1-3].addrs'
# 1163DDF1 is Bob’s Seed ID; since it’s generated randomly, yours will be different
```

4. Import the addresses into Bob’s tracking wallet:

```text
$ mmgen-addrimport --bob 1163DDF1-C[1-3].addrs
...
Type uppercase 'YES' to confirm: YES
```

	Since your Bob has a different Seed ID, your address filename will of course
	be different than this one.

5. List the addresses in Bob’s tracking wallet.  You’ll see the addresses you
just imported:

```text
$ mmgen-tool --bob listaddresses
MMGenID        ADDRESS                             COMMENT BALANCE
1163DDF1:C:1   mw42oJ94yRA6ZUNSzmMpjZDR74JNyvqzzZ     -      0
1163DDF1:C:2   n1oszhfAyRrHi7qJupyzaWXTcpMQGsGJEf     -      0
1163DDF1:C:3   mhYYHM7renPpNi8SUj5yeEZ54eAUJ5HyQ1     -      0
```

	Note that regtest mode uses testnet-format addresses, which differ from the
	familiar mainnet addresses beginning with ’1’.

6. Fund one of the addresses (let’s choose the first one) with some BTC:

```text
$ mmgen-regtest send mw42oJ94yRA6ZUNSzmMpjZDR74JNyvqzzZ 500
```

	Don’t forget to substitute your `C:1` address for the one above!

7. Make sure the funds reached their destination:

```text
$ mmgen-tool --bob listaddresses
MMGenID        ADDRESS                             COMMENT BALANCE
1163DDF1:C:1   mw42oJ94yRA6ZUNSzmMpjZDR74JNyvqzzZ     -    500
1163DDF1:C:2   n1oszhfAyRrHi7qJupyzaWXTcpMQGsGJEf     -      0
1163DDF1:C:3   mhYYHM7renPpNi8SUj5yeEZ54eAUJ5HyQ1     -      0
TOTAL: 500 BTC
```

8. You can view Bob’s total balance this way too:

```text
$ mmgen-tool --bob getbalance
```

9. Generate Alice’s wallet:

```text
$ mmgen-walletgen --alice
...
Make this wallet your default and move it to the data directory? (Y/n): y
```

10. Generate three type `S` (segwit) addresses with Alice’s wallet:

```text
$ mmgen-addrgen --alice --type=segwit 1-3
...
Addresses written to file '9304C211-S[1-3].addrs'
```

11. Repeat steps 4-7 for Alice by substituting `--bob` for `--alice`.  Don’t
forget to change the address filename and send address to suit.  The result of
step 7 will look something like this:

```text
MMGenID        ADDRESS                             COMMENT BALANCE
9304C211:S:1   2N3HhxasbRvrJyHg72JNVCCPi9EUGrEbFnu    -    500
9304C211:S:2   2N8w8qTupvd9L9wLFbrn6UhdfF1gadDAmFD    -      0
9304C211:S:3   2NF4y3y4CEjQCcssjX2BDLHT88XHn8z53JS    -      0
TOTAL: 500 BTC
```

12. Split Alice’s funds, sending 200 BTC to address `S:2` and the change to
`S:3`.  Specify a fee of 20 satoshis/byte and make the output quieter:

```text
$ mmgen-txdo --alice --fee=20s --quiet 9304C211:S:2,300 9304C211:S:3
...
Type uppercase 'YES' to confirm: YES
Transaction sent: 78ca853816b55527b42ca8784c887a5f482c752522f914d2f17d6afcd8a3b076
```

	Don’t forget to use your Alice’s Seed ID here, instead of `9304C211`.

	Note that for simplicity’s sake this tutorial uses the `mmgen-txdo` command
	to create, sign and send transactions in one operation.  In normal, cold
	wallet mode, you’d create the transaction with `mmgen-txcreate`, sign it
	offline with `mmgen-txsign` and send it with `mmgen-txsend`.  Use of these
	commands is explained in detail in the [**Getting Started**][gs] guide.

13. View the transaction in the mempool:

```text
$ mmgen-regtest mempool
['78ca853816b55527b42ca8784c887a5f482c752522f914d2f17d6afcd8a3b076']
```

14. Mine a block:

```text
$ mmgen-regtest generate
```

15. Check the mempool again:

```text
$ mmgen-regtest mempool
[]
```

16. List Alice’s addresses.  Note that Alice has lost a bit to transaction fees:

```text
$ mmgen-tool --alice listaddresses
MMGenID        ADDRESS                             COMMENT BALANCE
9304C211:S:1   2N3HhxasbRvrJyHg72JNVCCPi9EUGrEbFnu    -      0
9304C211:S:2   2N8w8qTupvd9L9wLFbrn6UhdfF1gadDAmFD    -    300
9304C211:S:3   2NF4y3y4CEjQCcssjX2BDLHT88XHn8z53JS    -    199.999967
TOTAL: 499.999967 BTC
```

17. Have Alice send 10 BTC to Bob’s `C:2` address and the change back to her
`S:1` address.  This time Alice specifies an absolute fee in BTC.

```text
$ mmgen-txdo --alice --fee=0.0001 --quiet 9304C211:S:1 n1oszhfAyRrHi7qJupyzaWXTcpMQGsGJEf,10
...
Enter a range or space-separated list of outputs to spend: 1
...
```

	Note that Alice is reusing address `S:1` here, and address reuse is
	generally a bad idea.  You’d be better off generating and importing some
	new addresses for Alice by repeating steps 3 and 4 with a different address
	range.  I’ll leave that to you as an exercise.

18. Mine a block:

```text
$ mmgen-regtest generate
```

19. List Alice’s addresses, omitting the empty ones:

```text
$ mmgen-tool --alice listaddresses
MMGenID        ADDRESS                             COMMENT BALANCE
9304C211:S:1   2N3HhxasbRvrJyHg72JNVCCPi9EUGrEbFnu    -    189.999867
9304C211:S:2   2N8w8qTupvd9L9wLFbrn6UhdfF1gadDAmFD    -    300
TOTAL: 489.999867 BTC
```

19. List Bob’s addresses:

```text
$ mmgen-tool --bob listaddresses
MMGenID        ADDRESS                             COMMENT BALANCE
1163DDF1:C:1   mw42oJ94yRA6ZUNSzmMpjZDR74JNyvqzzZ     -    500
1163DDF1:C:2   n1oszhfAyRrHi7qJupyzaWXTcpMQGsGJEf     -     10
TOTAL: 510 BTC
```

20. Add a label to Bob’s tracking wallet:

```text
$ mmgen-tool --bob add_label 1163DDF1:C:2 'From Alice'
```

21. List Bob’s addresses:

```text
$ mmgen-tool --bob listaddresses
MMGenID        ADDRESS                             COMMENT    BALANCE
1163DDF1:C:1   mw42oJ94yRA6ZUNSzmMpjZDR74JNyvqzzZ      -      500
1163DDF1:C:2   n1oszhfAyRrHi7qJupyzaWXTcpMQGsGJEf  From Alice  10
TOTAL: 510 BTC
```

22. When you’re finished, stop the regtest daemon:

```text
$ mmgen-regtest stop
```

[gs]: Getting-Started-with-MMGen-Wallet.md#a_ct

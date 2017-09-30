MMGen's regtest mode, also known as Bob and Alice mode, provides a convenient
front-end for bitcoind's regression test mode.  It creates a private blockchain
and a virtual network of two users who can perform all MMGen operations,
including sending bitcoins to each other.

To transact as Bob or Alice, just add the '--bob' or '--alice' option to any
MMGen command.  MMGen will start and stop the Bitcoin daemon automatically as
required.  All of MMGen's functionality is available in this mode, making it an
ideal, risk-free way to acquaint yourself with the MMGen wallet's features and
transacting on the Bitcoin blockchain in general.

This tutorial provides a quick, hands-on introduction.

1. Create the blockchain and Bob and Alice's tracking wallets:

		$ mmgen-regtest setup

2. Generate Bob's MMGen wallet:

		$ mmgen-walletgen --bob
		...
		Make this wallet your default and move it to the data directory? (Y/n): y

3. Generate three type 'C' (compressed) addresses with Bob's MMGen wallet:

		$ mmgen-addrgen --bob --type=compressed 1-3
		...
		Addresses written to file '1163DDF1-C[1-3].addrs'
		# 1163DDF1 is Bob's Seed ID; since it's generated randomly, your Bob's will be different

4. Import the addresses into Bob's tracking wallet:

		$ mmgen-addrimport --bob 1163DDF1-C[1-3].addrs
		...
		Type uppercase 'YES' to confirm: YES

5. List the addresses in Bob's tracking wallet.  You should see the addresses
you just imported:

		$ mmgen-tool --bob listaddresses showempty=1
		MMGenID        ADDRESS                             COMMENT BALANCE
		1163DDF1:C:1   mw42oJ94yRA6ZUNSzmMpjZDR74JNyvqzzZ     -      0
		1163DDF1:C:2   n1oszhfAyRrHi7qJupyzaWXTcpMQGsGJEf     -      0
		1163DDF1:C:3   mhYYHM7renPpNi8SUj5yeEZ54eAUJ5HyQ1     -      0

6. Fund one of the addresses (let's choose the first one) with some BTC:

		$ mmgen-regtest send mw42oJ94yRA6ZUNSzmMpjZDR74JNyvqzzZ 500

7. Make sure the funds arrived:

		$ mmgen-tool --bob listaddresses showempty=1
		MMGenID        ADDRESS                             COMMENT BALANCE
		1163DDF1:C:1   mw42oJ94yRA6ZUNSzmMpjZDR74JNyvqzzZ     -    500
		1163DDF1:C:2   n1oszhfAyRrHi7qJupyzaWXTcpMQGsGJEf     -      0
		1163DDF1:C:3   mhYYHM7renPpNi8SUj5yeEZ54eAUJ5HyQ1     -      0

8. You can view Bob's total balance this way too:

		$ mmgen-tool --bob getbalance

9. Generate Alice's MMGen wallet:

		$ mmgen-walletgen --alice
		...
		Make this wallet your default and move it to the data directory? (Y/n): y

10. Generate three type 'S' (segwit) addresses with Alice's MMGen wallet:

		$ mmgen-addrgen --alice --type=segwit 1-3
		...
		Addresses written to file '9304C211-S[1-3].addrs'

11. Repeat steps 4-7 for Alice by substituting '--bob' for '--alice'.  Don't
forget to adjust the address filename and send address as well.  The result of
step 7 should look something like this:

		MMGenID        ADDRESS                             COMMENT BALANCE
		9304C211:S:1   2N3HhxasbRvrJyHg72JNVCCPi9EUGrEbFnu    -    500
		9304C211:S:2   2N8w8qTupvd9L9wLFbrn6UhdfF1gadDAmFD    -      0
		9304C211:S:3   2NF4y3y4CEjQCcssjX2BDLHT88XHn8z53JS    -      0
		TOTAL: 500 BTC

12. Split Alice's funds, sending 200 BTC to address S:2 and the change to S:3.
Specify a fee of 20 satoshis/byte and '--quiet' for less noisy output:

		$ mmgen-txdo --alice --tx-fee=20s --quiet 9304C211:S:2,300 9304C211:S:3
		...
		Type uppercase 'YES' to confirm: YES
		Transaction sent: 78ca853816b55527b42ca8784c887a5f482c752522f914d2f17d6afcd8a3b076

13. Check the mempool for the transaction:

		$ mmgen-regtest show_mempool
		['78ca853816b55527b42ca8784c887a5f482c752522f914d2f17d6afcd8a3b076']

14. Mine a block:

		$ mmgen-regtest generate

15. Check the mempool again:

		$ mmgen-regtest show_mempool
		[]

16. List Alice's addresses.  Note that Alice has lost a bit to transaction fees:

		$ mmgen-tool --alice listaddresses showempty=1
		MMGenID        ADDRESS                             COMMENT BALANCE
		9304C211:S:1   2N3HhxasbRvrJyHg72JNVCCPi9EUGrEbFnu    -      0
		9304C211:S:2   2N8w8qTupvd9L9wLFbrn6UhdfF1gadDAmFD    -    300
		9304C211:S:3   2NF4y3y4CEjQCcssjX2BDLHT88XHn8z53JS    -    199.999967
		TOTAL: 499.999967 BTC

17. Have Alice send 10 BTC to Bob's C:2 address, with the change back to her S:1
address.  This time Alice specifies an absolute fee in BTC.

		$ mmgen-txdo --alice --tx-fee=0.0001 --quiet 9304C211:S:1 n1oszhfAyRrHi7qJupyzaWXTcpMQGsGJEf,10
		...
		Enter a range or space-separated list of outputs to spend: 1
		...

    Note that Alice is reusing address S:1 here, and address reuse is generally a
	bad idea.  You'd be better off generating and importing some new addresses for
	Alice by repeating steps 3 and 4 with a different address range.  I'll leave
	that to you as an exercise.

18. Mine a block:

		$ mmgen-regtest generate

19. List Alice's addresses, omitting the empty ones:

		$ mmgen-tool --alice listaddresses
		MMGenID        ADDRESS                             COMMENT BALANCE
		9304C211:S:1   2N3HhxasbRvrJyHg72JNVCCPi9EUGrEbFnu    -    189.999867
		9304C211:S:2   2N8w8qTupvd9L9wLFbrn6UhdfF1gadDAmFD    -    300
		TOTAL: 489.999867 BTC

19. List Bob's addresses:

		$ mmgen-tool --bob listaddresses
		MMGenID        ADDRESS                             COMMENT BALANCE
		1163DDF1:C:1   mw42oJ94yRA6ZUNSzmMpjZDR74JNyvqzzZ     -    500
		1163DDF1:C:2   n1oszhfAyRrHi7qJupyzaWXTcpMQGsGJEf     -     10
		TOTAL: 510 BTC

20. Add a label to Bob's tracking wallet:

		$ mmgen-tool --bob add_label 1163DDF1:C:2 'From Alice'

21. List Bob's addresses:

		$ mmgen-tool --bob listaddresses
		MMGenID        ADDRESS                             COMMENT    BALANCE
		1163DDF1:C:1   mw42oJ94yRA6ZUNSzmMpjZDR74JNyvqzzZ      -      500
		1163DDF1:C:2   n1oszhfAyRrHi7qJupyzaWXTcpMQGsGJEf  From Alice  10
		TOTAL: 510 BTC

[q]: MMGen-Quick-Start-with-Regtest-Mode

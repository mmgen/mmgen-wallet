## Contents

+ [XOR Seed Splitting: A Theoretical Introduction](#a_xor)
   - [Deterministic Shares](#a_ds)
   - [Named Splits](#a_ns)
   - [Master Shares](#a_ms)
+ [Seed Splitting with MMGen Wallet](#a_ss)

### <a id="a_xor">XOR Seed Splitting: A Theoretical Introduction</a>

The bitwise exclusive-or operation (usually denoted as `XOR`, or “![⊕]”)
has interesting properties that make it very useful in cryptography.

Suppose we have two bytes, *a* and *b*:

![]["a: 1 0 0 1 0 1 0 0"]

![]["b: 0 1 0 1 1 1 1 0"]

To XOR the two bytes, we compare each of their bits.  If the bit is the same for
both *a* and *b,* the corresponding bit of the result is 0.  If it differs, the
result is 1:

![]["a ⊖ b: 1 1 0 0 1 0 1 0"]

Thus XOR can be thought of logically as “one or the other but not both”, or
arithmetically as addition [modulo][wm] 2 without carry, since 1 plus 1 equals 0
in base-2 arithmetic.

As is clear from our above example, switching the order of *a* and *b* has no
effect on the result. So XOR, like addition, is commutative:

![]["a ⊕ b = b ⊕ a"]

And like addition, grouping has no effect on the result.  XOR is associative:

![]["a ⊕ (b ⊕ c) = (a ⊕ b) ⊕ c"]

But unlike addition, XOR has an extra property: *invertibility.* The result can
be switched with any of the operands, making XOR sort of like addition and
subtraction rolled into one.  Thus, if

![]["a ⊕ b = c"]

then

![]["c ⊕ a = b"]

![]["b ⊕ c = a"]

and so forth.

This last property makes XOR very handy for encryption and decryption.  Given
a plaintext *P* and a random value *r* with the same bit length as *P*, we
encrypt *P* by XOR’ing it with *r* to obtain the ciphertext *C:*

![]["P ⊕ r = C"]

To decrypt, we just XOR the ciphertext with *r* to recover the plaintext:

![]["C ⊕ r = P"]

The randomness of the ciphertext is guaranteed to be no less than that of the
random value.  Thus if *r* is perfectly random, then *C* is perfectly
undecipherable, given no knowledge of *r.*  This is the principle underlying the
[one-time pads][otp] used by spies and diplomats before the computer age, as
well as modern [stream ciphers][sc].

To demonstrate how this can be used for seed splitting, all we do is change
the names of the variables:

![]["seed ⊕ share1 = share2"]

Here *seed* is analogous to the plaintext *P,* *share*<sub>1</sub> is a random
value with the same bit length as *seed,* and *share*<sub>2</sub> is the
resulting ciphertext.  Just as the *C* reveals nothing about *P* in the previous
example, *share*<sub>2</sub> reveals nothing about *seed* without knowledge of
*share*<sub>1</sub>. To recover the seed, we just XOR the two shares.  Since XOR
is commutative, the order in which we combine them isn’t important:

![]["share2 ⊕ share1 = seed"]

Thanks to XOR’s associativity, splits of any arbitrary length *n* can be created
by using *n*-1 random shares, with the *n*-th share being the result of the
chained XOR operations:

Perform an *n*-way split:

![]["seed ⊕ share1 ⊕ share2 ... ⊕ shareN-1 = shareN"]

Join shares 1 through *n* to recover the seed:

![]["share1 ⊕ share2 ... ⊕ shareN = seed"]

Knowledge of any combination of *n*-1 shares reveals nothing about the seed.

#### <a id="a_ds">Deterministic Shares</a>

So we’ve seen that the mathematics behind XOR seed splitting is basically
trivial.  In practice, though, there are several issues that need to be
resolved.  For example, how do we obtain the random values for the shares?
The easy answer is to just use the random number generator provided by our
operating system.  Generating the values deterministically is a better solution,
however, providing us with two key advantages: 1) we avoid reliance on such
factors as the quality of our OS RNG, the underlying hardware, and the entropy
pool; and 2) we gain reproducibility—the ability to generate identical shares
repeatedly, and as a consequence, to generate shares independently of each
other.

This latter feature is especially useful.  Suppose I want to do a 2-way split
of my seed for backup purposes, giving one share to my friend Bob and storing
the other share at some location accessible to me but unknown to Bob.  With
deterministic shares, I can generate Bob’s share now, giving it to Bob, and my
own share later, once I’ve determined a good location for its safekeeping.  And
if either of us loses our share, it can just be regenerated.

OK, so now that we’re sold on the idea of deterministic shares, how do we go
about creating them?  A naive approach would be to just generate a secure
cryptographic hash of our seed using the SHA256 algorithm and use that directly
as the first share:

![]["share1 = SHA256(seed)"]

This would work fine for a 2-way split: assuming SHA256 is secure and our seed
is strongly random (if either assumption is false, we’re in big trouble anyway),
then *share*<sub>1</sub> is strongly random too and reveals nothing about our
seed.  And being derived from the seed alone, it’s regenerable on demand by the
seed’s owner.

For *n*-way splits where *n* is greater than 2, however, we run into a problem
when attempting to generate the additional random values.  We might be tempted
to just keep hashing:

![]["share2 = SHA256(share1), share3 = SHA256(share2), ..."]

But you may have already spotted the mistake here: the owner of the first share
can generate all the successive shares up to *n*-1.  Without the final <em>n</em>’th
share he can’t recover the seed, but the whole benefit of having the additional
shares has been nullified.

***Important disclaimer:*** *there are other reasons, beyond the scope of this
discussion, why using a bare hash of the seed as our random number source might
not be a good idea.  Bear in mind that this is a simplified* **theoretical**
*introduction, and the examples presented herein are not suitable for
implementation in real production code.*

The above example illustrates what happens when we violate the golden rule of
the wallet developer: *never derive a secret from another secret that someone
besides the wallet’s owner could potentially gain access to.*  This goes for
the private keys of the addresses in a wallet, which could be compromised in a
security breach.  And it certainly goes for seed shares, which are intended for
distribution to others from the outset.

The solution to this problem is to derive the shares directly from the seed, but
with an added identifier that’s unique to each share.  The [HMAC] message-digest
algorithm is ideally suited for this:

![]["share1 = HMAC(seed,'share1'), share2 = HMAC(seed,'share2'), ... shareN-1 = HMAC(seed,'share<N-1>')"]

Using these unique pseudorandom values, we can now split and rejoin our seed in
the manner described at the end of the previous section.

#### <a id="a_ns">Named Splits</a>

Now, we’d like to use seed splitting as part of our backup strategy, entrusting
shares of our seed with various people we know.  Multiple 2-way splits seems
like the best approach—if one of our trustees loses their share, moves to
another city, or gets run over by a bus, then we have the others left as a
fallback.

However, we have no mechanism as yet for generating multiple splits: using the
deterministic method outlined above, we can only generate the same set of
pseudorandom shares over and over again.  The obvious solution here is to give
each split a name: for our split with Bob, we’ll add “bob” to the share
identifier, for our split with Alice, we’ll add “alice”, and so forth.  Using
this approach, we can create an arbitrary number of uniquely named splits.

Create a 2-way split with Bob:

![]["share_me = HMAC(seed,'bob:share1'), share_bob = seed ⊕ share_me"]

Create a 2-way split with Alice:

![]["share_me = HMAC(seed,'alice:share1'), share_alice = seed ⊕ share_me"]

In addition, we should handle the case of multiple splits with different length
but the same name.  To exclude the reuse of shares in this case, we’ll add an
additional identifier field specifying the total number of shares in the split.

Create a 3-way split “friends” with Bob and Alice:

![]["share_me = HMAC(seed,'friends:share1:of3'), share_bob = HMAC(seed,'friends:share2:of3'), share_alice = seed ⊕ share_me ⊕ share_bob"]

Create a 4-way split “friends” with Bob, Alice and Carol:

![]["share_me = HMAC(seed,'friends:share1:of4'), share_bob = HMAC(seed,'friends:share2:of4'), share_alice = HMAC(seed,'friends:share3:of4'), share_carol = seed ⊕ share_me ⊕ share_bob ⊕ share_alice"]

Thus we’ve ensured the uniqueness of all shares across all possible splits.

#### <a id="a_ms">Master Shares</a>

As the number of splits we create grows, the question of how to store our shares
becomes especially problematic.  Each new split creates another new share that
must be securely stored somewhere.  What we need is some mechanism to generate
our share of each split from a single master share.  This master share would
need to be generated and stored just once, saving us a great deal of trouble.

Having multiple master shares could be useful too.  For example, if we ever
wanted to revoke our splits, all we’d have to do is destroy our copy of the
current master share, ensuring that none of the splits made with its
participation could be joined.  To create new splits, we’d use the next master
share.

This is all easy to implement using the tools we’re already familiar with from
the preceding sections.  Using HMAC-SHA256, we’ll generate a range of indexed
master shares from our seed as follows:

![]["master1 = HMAC(seed,'master1'), master2 = HMAC(seed,'master2'), ..."]

Using master share #1 as our share, our 4-way split “friends” with Bob, Alice
and Carol now looks like this:

![]["share_me = master1, share_bob = HMAC(seed,'friends:share2:of4:master1'), share_alice = HMAC(seed,'friends:share2:of4:master1'), share_carol = seed ⊕ HMAC(master1,'friends:share1:of4') ⊕ share_bob ⊕ share_alice"]

And rejoining the seed looks like this:

![]["seed = HMAC(master1,'friends:share1:of4') ⊕ share_bob ⊕ share_alice ⊕ share_carol"]

The rejoining process now involves more than a simple XOR’ing of shares: The
name of the split must be input to the join function, so it should something
that’s easy to memorize.  If you *really* don’t trust yourself to remember
the word “friends”, you could write it down somewhere.

Also note that an additional field, `master<n>`, has been appended to the share
identifiers.  This is to ensure that the shares of each master share split are
unique, and differ from their non-master-share counterparts.

### <a id="a_ss">Seed Splitting with MMGen Wallet</a>

MMGen Wallet implements the seed splitting and joining functionality described
above via the commands [`mmgen-seedsplit`][SS] and [`mmgen-seedjoin`][SJ].
Usage examples can be found on the `mmgen-seedsplit` help screen.

Shares can be made from and exported to all supported MMGen Wallet formats.
This means you can split a BIP39 seed phrase, for example, and output the share
back to BIP39 in one easy command:

```text
# Create share 1 of a 2-way split of the provided BIP39 seed phrase:
$ mmgen-seedsplit -o bip39 sample.bip39 1:2
```

Each share of a split has a unique share ID.  The share IDs are displayed by
`mmgen-seedsplit` so that the user may record them for later reference.  They
may also be viewed with the `mmgen-tool list_shares` command:

```bash
# List the share IDs of a 2-way named split 'alice' of your default wallet:
$ mmgen-tool list_shares 2 id_str=alice

Seed: 71CA5049 (256 bits)
Split Type: 2-of-2 (XOR)
ID String: alice

Shares
------
1: D0BBD210
2: 25F0BD65
```

```bash
# List the share IDs of a 3-way default split of provided BIP39 seed phrase:
$ mmgen-tool list_shares 3 wallet=sample.bip39

Seed: 03BAE887 (128 bits)
Split Type: 3-of-3 (XOR)
ID String: default

Shares
------
1: 83B9AF74
2: 109485F4
3: 424522DC
```

Share IDs are handy for checking the correctness of shares when rejoining a
split.  Let’s say you’ve decided to rejoin your 2-way split with Alice, whose
share you exported to BIP39 format.  This can be done by contacting Alice by
phone, for example, and having her read the mnemonic phrase to you.  If the ID
of Alice’s share as displayed by `mmgen-seedjoin` matches the value you recorded
when making the split, then you know Alice has given you the correct phrase.

***Note:*** *when recovering shares over an insecure channel like the telephone,
it’s advisable to destroy all copies of your share once you’ve rejoined the
seed to safeguard against a possible eavesdropping attacker.*

Ordinary named splits can easily be rejoined even without the MMGen software.
First, each share must be converted to hexadecimal data.  If your shares are in
BIP39 format, for example, there are command-line tools available to do this.
Then a single line of Python code is all that’s required to finish the job:

```python
$ python3
>>> seed_hex = hex(int(share1_hex,16) ^ int(share2_hex,16)) # rejoin a 2-way split
```

(Note that the XOR operator in Python is `^`.)

Unfortunately, rejoining master-share splits is considerably harder to do at
the Python command prompt.  This is because converting the master share into the
temporary share used to make the split involves an additional step, as you’ll
recall from the above discussion.  In addition, this step is implemented by
MMGen Wallet somewhat differently than as described above.  For advanced users,
an example will be provided in a future version of this document.

[⊕]: https://mmgen.github.io/images/ss/o_xor.svg "⊕"
["a: 1 0 0 1 0 1 0 0"]: https://mmgen.github.io/images/ss/byte_a.svg "a: 1 0 0 1 0 1 0 0"
["b: 0 1 0 1 1 1 1 0"]: https://mmgen.github.io/images/ss/byte_b.svg "b: 0 1 0 1 1 1 1 0"
["a ⊖ b: 1 1 0 0 1 0 1 0"]: https://mmgen.github.io/images/ss/byte_ab.svg "a ⊖ b: 1 1 0 0 1 0 1 0"
["a ⊕ b = b ⊕ a"]: https://mmgen.github.io/images/ss/ab-ba.svg "a ⊕ b = b ⊕ a"
["a ⊕ (b ⊕ c) = (a ⊕ b) ⊕ c"]: https://mmgen.github.io/images/ss/abc.svg "a ⊕ (b ⊕ c) = (a ⊕ b) ⊕ c"
["a ⊕ b = c"]: https://mmgen.github.io/images/ss/ab-c.svg "a ⊕ b = c"
["c ⊕ a = b"]: https://mmgen.github.io/images/ss/ca-b.svg "c ⊕ a = b"
["b ⊕ c = a"]: https://mmgen.github.io/images/ss/bc-a.svg "b ⊕ c = a"
["P ⊕ r = C"]: https://mmgen.github.io/images/ss/Pr-C.svg "P ⊕ r = C"
["C ⊕ r = P"]: https://mmgen.github.io/images/ss/Cr-P.svg "C ⊕ r = P"
["seed ⊕ share1 = share2"]: https://mmgen.github.io/images/ss/ss-enc.svg "seed ⊕ share1 = share2"
["share2 ⊕ share1 = seed"]: https://mmgen.github.io/images/ss/ss-dec.svg "share2 ⊕ share1 = seed"
["seed ⊕ share1 ⊕ share2 ... ⊕ shareN-1 = shareN"]: https://mmgen.github.io/images/ss/ssN-enc.svg "seed ⊕ share1 ⊕ share2 ... ⊕ shareN-1 = shareN"
["share1 ⊕ share2 ... ⊕ shareN = seed"]: https://mmgen.github.io/images/ss/ssN-dec.svg "share1 ⊕ share2 ... ⊕ shareN = seed"
["share1 = SHA256(seed)"]: https://mmgen.github.io/images/ss/sha256.svg "share1 = SHA256(seed)"
["share2 = SHA256(share1), share3 = SHA256(share2), ..."]: https://mmgen.github.io/images/ss/sha256b.svg "share2 = SHA256(share1), share3 = SHA256(share2), ..."
["share1 = HMAC(seed,'share1'), share2 = HMAC(seed,'share2'), ... shareN-1 = HMAC(seed,'share<N-1>')"]: https://mmgen.github.io/images/ss/hmac.svg "share1 = HMAC(seed,'share1'), share2 = HMAC(seed,'share2'), ... shareN-1 = HMAC(seed,'share<N-1>')"
["share_me = HMAC(seed,'bob:share1'), share_bob = seed ⊕ share_me"]: https://mmgen.github.io/images/ss/bob.svg "share_me = HMAC(seed,'bob:share1'), share_bob = seed ⊕ share_me"
["share_me = HMAC(seed,'alice:share1'), share_alice = seed ⊕ share_me"]: https://mmgen.github.io/images/ss/alice.svg "share_me = HMAC(seed,'alice:share1'), share_alice = seed ⊕ share_me"
["share_me = HMAC(seed,'friends:share1:of3'), share_bob = HMAC(seed,'friends:share2:of3'), share_alice = seed ⊕ share_me ⊕ share_bob"]: https://mmgen.github.io/images/ss/friends1.svg "share_me = HMAC(seed,'friends:share1:of3'), share_bob = HMAC(seed,'friends:share2:of3'), share_alice = seed ⊕ share_me ⊕ share_bob"
["share_me = HMAC(seed,'friends:share1:of4'), share_bob = HMAC(seed,'friends:share2:of4'), share_alice = HMAC(seed,'friends:share3:of4'), share_carol = seed ⊕ share_me ⊕ share_bob ⊕ share_alice"]: https://mmgen.github.io/images/ss/friends2.svg "share_me = HMAC(seed,'friends:share1:of4'), share_bob = HMAC(seed,'friends:share2:of4'), share_alice = HMAC(seed,'friends:share3:of4'), share_carol = seed ⊕ share_me ⊕ share_bob ⊕ share_alice"
["master1 = HMAC(seed,'master1'), master2 = HMAC(seed,'master2'), ..."]: https://mmgen.github.io/images/ss/master.svg "master1 = HMAC(seed,'master1'), master2 = HMAC(seed,'master2'), ..."
["share_me = master1, share_bob = HMAC(seed,'friends:share2:of4:master1'), share_alice = HMAC(seed,'friends:share2:of4:master1'), share_carol = seed ⊕ HMAC(master1,'friends:share1:of4') ⊕ share_bob ⊕ share_alice"]: https://mmgen.github.io/images/ss/friends3.svg "share_me = master1, share_bob = HMAC(seed,'friends:share2:of4:master1'), share_alice = HMAC(seed,'friends:share2:of4:master1'), share_carol = seed ⊕ HMAC(master1,'friends:share1:of4') ⊕ share_bob ⊕ share_alice"
["seed = HMAC(master1,'friends:share1:of4') ⊕ share_bob ⊕ share_alice ⊕ share_carol"]: https://mmgen.github.io/images/ss/friends4.svg "seed = HMAC(master1,'friends:share1:of4') ⊕ share_bob ⊕ share_alice ⊕ share_carol"

<!-- https://mmgen.github.io/images/ss/ -->

[HMAC]: https://en.wikipedia.org/wiki/HMAC
[wm]: https://en.wikipedia.org/wiki/Modular_arithmetic
[otp]: https://en.wikipedia.org/wiki/One-time_pad
[sc]: https://en.wikipedia.org/wiki/Stream_cipher
[SS]: cmds/command-help-seedsplit.md
[SJ]: cmds/command-help-seedjoin.md

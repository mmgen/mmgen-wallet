### [Manual transacting](#as_r) | [Autosigning v1](#as_v1) | [Autosigning v2](#as_v2)

For most situations, Version 2 autosigning is the best way to transact with
MMGen Wallet.

## <a id="as_r">Transacting, the manual way</a>

Transacting manually involves the following steps:

#### Preparation of signing session:
1. Boot and log in to offline signing machine

#### Transacting:
1. On online machine, create transaction with [`mmgen-txcreate`][tc]
   (or [`mmgen-swaptxcreate`][sc])
1. Insert removable device
1. Mount removable device
1. Copy transaction file to removable device
1. Unmount removable device
1. Extract removable device and transfer it to offline machine
1. Mount removable device
1. Locate transaction file on removable device, sign it with
   [`mmgen-txsign`][ts]
1. Unmount removable device
1. Extract removable device and transfer it to online machine
1. Mount removable device
1. Locate signed transaction file on removable device, send it with
   [`mmgen-txsend`][tx]

Admittedly, this is all quite tedious. To simplify the transaction workflow,
Version 1 Autosigning was introduced.

## <a id="as_v1">Autosigning, Version 1</a>

Here the main innovation was to eliminate keyboard interaction with the
offline signing machine during the signing process.

#### <a id="as_v1_s">Preparation of signing session:
1. Boot and log in to offline signing machine
1. Set up autosigning session ([`mmgen-autosign setup`][as])
1. Start signing loop ([`mmgen-autosign wait`][as])

#### Transacting:
1. On online machine, create transaction with [`mmgen-txcreate`][tc]
   (or [`mmgen-swaptxcreate`][sc])
1. Insert removable device
1. Mount removable device
1. Copy transaction file to `/mnt/mmgen_autosign/tx` on removable device
   (or `/mnt/mmgen_autosign/xmr/tx` for Monero)
1. Unmount removable device
1. Extract removable device and transfer it to offline machine
1. Wait for [autosigning][as] to complete
1. Extract removable device and transfer it to online machine
1. Mount removable device
1. Locate signed transaction file on removable device, send it with
   [`mmgen-txsend`][tx]

#### Differences compared to manual method:

- signing session preparation involves additional steps
- signing requires no keyboard interaction
- removable device and, for Linux, mountpoints must be prepared as described
  in [`mmgen-autosign --help`][as]

While this is already much better, there was still room for improvement.
Enter Version 2 Autosigning.

## <a id="as_v2">Autosigning, Version 2</a>

Here the main innovation was to automate all mounting, unmounting, and file
copying operations.  Version 2 autosigning is sometimes referred to in the
program output and documentation by the term “automount”.

#### Preparation of signing session:
1. Same as for [Version 1](#as_v1_s)

#### Transacting:
1. On online machine, insert removable device
1. Create transaction with [`mmgen-txcreate`][tc]
   (or [`mmgen-swaptxcreate`][sc])
1. Extract removable device and transfer it to offline machine
1. Wait for [autosigning][as] to complete
1. Extract removable device and transfer it to online machine
1. Send transaction with [`mmgen-txsend`][tx]

#### Differences compared to Version 1:
- filename arguments are omitted from all commands
- for online operations, the `--autosign` option must be supplied, or
  `autosign` set to `true` in the config file
- only one transaction may be created-signed-sent at a time (Version 1 allows
  for multiple signables per signing operation)
- unsent transactions may be aborted and ranges of sent transactions viewed or
  checked for confirmation status (see [`mmgen-txsend --help`][tx])

[tc]: cmds/command-help-txcreate.md
[ts]: cmds/command-help-txsign.md
[tx]: cmds/command-help-txsend.md
[sc]: cmds/command-help-swaptxcreate.md
[as]: cmds/command-help-autosign.md

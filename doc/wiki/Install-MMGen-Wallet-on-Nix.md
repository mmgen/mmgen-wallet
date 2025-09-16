Perform the following steps:

```text
$ git clone https://github.com/mmgen/mmgen-wallet.git
$ cd mmgen-wallet
$ mkdir -p ~/.mmgen
$ cp nix/user-packages.nix ~/.mmgen
```

For altcoin support, edit `~/.mmgen/user-packages.nix` to taste, uncommenting
the relevant lines for whatever support you require.  For a BTC-only setup,
you can leave the file untouched.

Build required derivations and enter the custom Nix shell environment:

```text
$ nix-shell nix # for full isolation, add the ‘--pure’ option
```

Within nix-shell you may now test and use MMGen Wallet as with any normal
installation.

Refer to `nix/README` in the MMGen Wallet repo for more information, including
a speedup tip and instructions for installation on NixOS.

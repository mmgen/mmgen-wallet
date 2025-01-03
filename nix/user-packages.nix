# Nix environment user configuration for the MMGen Project
#
# In addition to setting new attributes, this file may be used to override the defaults
# in nix/packages.nix of the mmgen-wallet repository

{ pkgs, python, bdir }:

rec {
    ### Set nixpkgs globally for the MMGen environment.
    ### If you set it, make sure to uncomment the python variable assignment below.
    # pkgs = import (bdir + /nixpkgs-24.05.nix) {};

    ### Set python version globally for the MMGen environment.
    ### Must be set if pkgs is set.
    # python = pkgs.python312;

    system-packages = with pkgs; {
        # monero-cli  = monero-cli;                      # Monero daemon
        # # go-ethereum = go-ethereum;                     # Geth - latest version for transacting on mainnet
        # go-ethereum = callPackage (bdir + /go-ethereum.nix) { # Geth - old version for test suite (ethdev)
        #     buildGoModule = buildGo122Module;
        #     tag_version = "v1.13.15";
        #     vendor_hash = "sha256-LWNFuF66KudxrpWBBXjMbrWP5CwEuPE2h3kGfILIII0";
        # };
        # litecoin     = callPackage (bdir + /litecoin.nix) {};           # Litecoin daemon
        # bitcoin-cash = callPackage (bdir + /bitcoin-cash-node.nix) {};  # Bitcoin Cash Node daemon
        # zcash-mini   = callPackage (bdir + /zcash-mini.nix) {};         # ZEC (test suite)

        ### For development with --pure (add/remove packages for your setup):
        # neovim-qt    = neovim-qt;
        # rxvt-unicode = rxvt-unicode;
        # which        = which;
        # ctags        = ctags;
        # xclip        = xclip;

        ### For test suite with --pure:
        # openssh      = openssh; # XMR tests
    };

    python-packages = with python.pkgs; {
        # pycryptodome     = pycryptodome;    # altcoins
        # py-ecc           = py-ecc;          # ETH, ETC
        # mypy-extensions  = mypy-extensions; # ETH, ETC
        # pysocks          = pysocks;         # XMR
        # monero           = monero;          # XMR (test suite)
        # eth-keys         = eth-keys;        # ETH, ETC (test suite)
    };
}

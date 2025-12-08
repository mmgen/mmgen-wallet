# Nix environment user configuration for the MMGen Project
#
# In addition to setting new attributes, this file may be used to override the defaults
# in nix/packages.nix of the mmgen-wallet repository

{ pkgs, python, bdir }:

rec {
    ### Set nixpkgs globally for the MMGen environment.
    ### If you set it, make sure to uncomment the python variable assignment below.
    # pkgs = import (bdir + /nixpkgs-25.11.nix) {};

    ### Set python version globally for the MMGen environment.
    ### Must be set if pkgs is set.
    # python = pkgs.python313;

    system-packages = with pkgs; {
        # monero-cli   = monero-cli;                                      # Monero daemon
        # go-ethereum  = go-ethereum;                                     # Geth
        # reth         = callPackage (bdir + /reth.nix) {};               # Rust Ethereum daemon
        # solc         = callPackage (bdir + /solc.nix) {};               # Solidity compiler
        # litecoin     = callPackage (bdir + /litecoin.nix) {};           # Litecoin daemon
        # bitcoin-cash = callPackage (bdir + /bitcoin-cash-node.nix) {};  # Bitcoin Cash Node daemon
        # zcash-mini   = callPackage (bdir + /zcash-mini.nix) {};         # ZEC (test suite)

        ### For development with --pure (add/remove packages for your setup):
        # neovim       = neovim;
        # neovim-qt    = neovim-qt;
        # rxvt-unicode = rxvt-unicode;
        # which        = which;
        # ctags        = ctags;
        # xclip        = xclip;
        # ruff         = ruff;
        # perl         = perl;
        # netcat       = netcat-openbsd;
        # jq           = jq;
        # ed           = ed;
        # rsync        = rsync;
        # pandoc       = pandoc;
        # gnupg        = gnupg;
        # iproute2     = iproute2;
        # tinyxxd      = tinyxxd;
        # ranger       = ranger;
        # hostname     = hostname;

        ### For test suite with --pure:
        # openssh      = openssh;
    };

    python-packages = with python.pkgs; {
        # pycryptodome     = pycryptodome;  # altcoins
        # pysocks          = pysocks;       # XMR
        # monero           = monero;        # XMR (test suite)
        # eth-keys         = eth-keys;      # ETH, ETC (test suite)
        # pure-protobuf    = pure-protobuf; # THORChain
        # bip-utils        = bip-utils;     # bip_hd
    };
}

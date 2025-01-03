# mmgen-wallet-nix: Nix packages directory for mmgen-wallet
#
# Copy the ‘mmgen-wallet-nix’ directory and its files to a location outside the
# mmgen-wallet repo and edit the file ‘packages.nix’, which contains all the
# system and Python packages MMGen Wallet depends on.  By default, altcoin
# packages are commented out.  To enable the coins you need, uncomment the
# relevant lines.  For an XMR-enabled setup, for example, you’ll need the
# system package ‘monero-cli’ and Python packages ‘monero’, ‘pycryptodome’
# and ‘pysocks’.
#
# Individual system packages are built as follows:
#
#    $ nix-build /path/to/mmgen-wallet-nix/packages.nix --attr <package name>
#
# The last line of nix-build’s output is a store path in ‘/nix/store/’, which
# you may optionally install into your default environment as follows:
#
#    $ nix-env --install <store path>
#
# To build all configured packages in one go, run nix-build without ‘--attr’ and
# package name.
#
# The file ‘shell.nix’ contains a shell environment specially created for use
# with MMGen Wallet.  From the mmgen-wallet repo root, execute:
#
#    $ nix-shell /path/to/mmgen-wallet-nix/shell.nix
#
# This will build any unbuilt configured packages and drop you to the custom
# environment.  At this point you may run the test suite:
#
#    [nix-shell:... $] test/test-release -FA
#
# or proceed to use MMGen Wallet as with any conventional installation.
#
# For greater isolation, you can invoke nix-shell with the ‘--pure’ option. This
# will make executables in your native environment inaccessible within the
# shell, so you may need to install some additional tools, such as a text
# editor. See the related comments below.
#
# NixOS:
#
#   To install mmgen-wallet under NixOS, copy the ‘mmgen-wallet-nix’ directory
#   to ‘/etc/nixos’, edit ‘packages.nix’ to suit and add
#   ‘mmgen-wallet-nix/nixos-packages.nix’ to your imports list in
#   ‘configuration.nix’.  From the mmgen-wallet repo root, execute:
#
#       export PYTHONPATH=$(pwd)
#       export PATH=$(pwd)/cmds:$PATH
#
#   You can now use MMGen Wallet in your native shell environment.

let
    pkgs = import ./nixpkgs-24.05.nix {};
    pythonEnv = pkgs.python312.withPackages (ps: with ps; [
        pip
        setuptools
        build
        wheel
        gmpy2
        cryptography
        pynacl
        ecdsa
        aiohttp
        requests
        py-scrypt
        semantic-version
        # pycryptodome    # altcoins
        # py-ecc          # ETH, ETC
        # mypy-extensions # ETH, ETC
        # pysocks         # XMR
        pexpect         # test suite
        pycoin          # test suite
        # monero          # XMR (test suite)
        # eth-keys        # ETH, ETC (test suite)
    ]);
in

{
    pymods      = pythonEnv;
    bitcoind    = pkgs.bitcoind;                        # Bitcoin Core daemon
    # monero-cli  = pkgs.monero-cli;                      # Monero daemon
    # go-ethereum = pkgs.go-ethereum;                     # Geth - latest version for mainnet transacting
    # go-ethereum = (pkgs.callPackage ./go-ethereum.nix { # Geth - old version for test suite (ethdev)
    #     buildGoModule = pkgs.buildGo122Module;
    #     tag_version = "v1.13.15";
    #     vendor_hash = "sha256-LWNFuF66KudxrpWBBXjMbrWP5CwEuPE2h3kGfILIII0";
    # });
    # litecoin     = (pkgs.callPackage ./litecoin.nix {});           # Litecoin daemon
    # bitcoin-cash = (pkgs.callPackage ./bitcoin-cash-node.nix {});  # Bitcoin Cash Node daemon
    # zcash-mini   = (pkgs.callPackage ./zcash-mini.nix {});         # ZEC (test suite)
    vanitygen    = (pkgs.callPackage ./vanitygen-plusplus.nix {}); # test suite
    curl         = pkgs.curl;
    git          = pkgs.git;
    gcc          = pkgs.gcc;
    libtool      = pkgs.libtool;
    autoconf     = pkgs.autoconf;
    gmp          = pkgs.gmp;
    gmp4         = pkgs.gmp4;
    openssl      = pkgs.openssl;
    pcre         = pkgs.pcre;
    mpfr         = pkgs.mpfr;
    secp256k1    = pkgs.secp256k1;
    less         = pkgs.less;   # test suite (cmdtest.py regtest)
    procps       = pkgs.procps; # test suite (pgrep)
    ruff         = pkgs.ruff;

    ## For development with --pure (add/remove packages for your setup):
    neovim-qt    = pkgs.neovim-qt;
    rxvt-unicode = pkgs.rxvt-unicode;
    which        = pkgs.which;
    ctags        = pkgs.ctags;

    ## For test suite with --pure:
    openssh    = pkgs.openssh;    # XMR tests
    e2fsprogs  = pkgs.e2fsprogs;
    util-linux = pkgs.util-linux; # losetup
    ncurses    = pkgs.ncurses;    # infocmp
}

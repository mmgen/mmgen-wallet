{ pkgs, python }:

{
    system-packages = with pkgs; {
        bitcoind     = bitcoind;                        # Bitcoin Core daemon
        vanitygen    = (callPackage ./vanitygen-plusplus.nix {}); # test suite
        curl         = curl;
        git          = git;
        gcc          = gcc;
        libtool      = libtool;
        autoconf     = autoconf;
        gmp          = gmp;
        gmp4         = gmp4;
        openssl      = openssl;
        pcre         = pcre;
        mpfr         = mpfr;
        secp256k1    = secp256k1.overrideAttrs {
            pname = "secp256k1-v0.6.0";
            src = fetchGit {
                url = "https://github.com/bitcoin-core/secp256k1.git";
                ref = "refs/tags/v0.6.0";
            };
        };
        less         = less;   # test suite (cmdtest.py regtest)
        procps       = procps; # test suite (pgrep)
        ruff         = ruff;

        ## For test suite with --pure:
        e2fsprogs  = e2fsprogs;
        util-linux = util-linux; # losetup
        ncurses    = ncurses;    # infocmp
    };

    python-packages = with python.pkgs; {
        pip              = pip;
        setuptools       = setuptools;
        build            = build;
        wheel            = wheel;
        gmpy2            = gmpy2;
        cryptography     = cryptography;
        pynacl           = pynacl;
        ecdsa            = ecdsa;
        aiohttp          = aiohttp;
        requests         = requests;
        py-scrypt        = py-scrypt;
        semantic-version = semantic-version;
        pexpect          = pexpect;         # test suite
        pycoin           = pycoin;          # test suite
    };
}

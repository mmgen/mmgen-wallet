{ pkgs, python }:

{
    system-packages = with pkgs; {
        bitcoind     = (callPackage ./bitcoin.nix {});            # Bitcoin Core daemon
        vanitygen    = (callPackage ./vanitygen-plusplus.nix {}); # test suite
        curl         = curl;
        git          = git;
        gcc          = gcc;
        libtool      = libtool;
        autoconf     = autoconf;
        gmp          = gmp;
        openssl      = openssl;
        pcre         = pcre;
        mpfr         = mpfr;
        secp256k1    = secp256k1;
        less         = less;   # test suite (cmdtest.py regtest)
        procps       = procps; # test suite (pgrep)

        ## For test suite with --pure:
        e2fsprogs  = e2fsprogs;
        util-linux = util-linux; # losetup
        ncurses    = ncurses;    # infocmp
    };

    python-packages = with python.pkgs; {
        setuptools       = setuptools;
        build            = build;
        wheel            = wheel;
        pip              = pip;
        # setup.cfg:
        gmpy2            = gmpy2;
        cryptography     = cryptography;
        pynacl           = pynacl;
        aiohttp          = aiohttp;
        requests         = requests;
        lxml             = lxml;
        py-scrypt        = py-scrypt;
        semantic-version = semantic-version;
        # test suite:
        pycoin           = pycoin;
        ecdsa            = ecdsa;
        pexpect          = pexpect;
    };
}

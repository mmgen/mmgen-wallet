{ pkgs }:

pkgs.stdenv.mkDerivation rec {
    pname = "bitcoin-cash-node";
    version = "v28.0.1";
    src = fetchGit {
        url = "https://gitlab.com/bitcoin-cash-node/bitcoin-cash-node";
        # url = /path/to/repo/bitcoin-cash-node-28.0.1;
        ref = "refs/tags/${version}";
        shallow = true;
    };
    nativeBuildInputs = [
        pkgs.cmake
        pkgs.ninja
        pkgs.help2man
        pkgs.python313
    ];
    buildInputs = [
        pkgs.boost
        pkgs.libevent
        pkgs.db
        pkgs.gmp
        pkgs.openssl
        pkgs.miniupnpc
        pkgs.libnatpmp
        pkgs.zeromq
        pkgs.zlib
    ];
   cmakeFlags = [
      "-GNinja"
      "-DBUILD_BITCOIN_QT=OFF"
      "-DVERBOSE_CONFIGURE=ON"
   ];
    doCheck = false;
    postConfigure = ''
        chmod ug+x config/run_native_cmake.sh
        chmod ug+x src/secp256k1/build_native_gen_context.sh
        sed -e 's@/usr/bin/env python3@${pkgs.python3}/bin/python3@' -i ../cmake/utils/gen-ninja-deps.py
        sed -e 's@/usr/bin/env bash@${pkgs.bash}/bin/bash@' -i doc/man/gen-doc-man-footer.sh
        sed -e 's@/usr/bin/env bash@${pkgs.bash}/bin/bash@' -i doc/man/gen-doc-man.sh
    '';
    postInstall= ''
        rm -f $out/bin/*
        install -v --mode=755 src/bitcoind $out/bin/bitcoind-bchn
        install -v --mode=755 src/bitcoin-cli $out/bin/bitcoin-cli-bchn
        rm -f $out/share/man/man1/bitcoin-{tx,seeder}*
        mv $out/share/man/man1/bitcoind.1 $out/share/man/man1/bitcoind-bchn.1
        mv $out/share/man/man1/bitcoin-cli.1 $out/share/man/man1/bitcoin-cli-bchn.1
    '';
}

{ pkgs }:

pkgs.stdenv.mkDerivation rec {
    pname = "litecoin";
    version = "v0.21.4";
    src = fetchGit {
        url = "https://github.com/litecoin-project/litecoin.git";
        # url = /path/to/repo/litecoin-0.21.4.git;
        ref = "refs/tags/${version}";
        shallow = true;
    };
    nativeBuildInputs = [
        pkgs.autoconf
        pkgs.automake
        pkgs.libtool
        pkgs.pkg-config
        # pkgs.hexdump # for tests
    ];
    buildInputs = [
        pkgs.boost183 # 'fs::copy_option' was removed in Boost 1.84
        pkgs.libevent
        pkgs.fmt
        pkgs.db4
        pkgs.openssl
        pkgs.sqlite
    ];
    preConfigure = [
        "./autogen.sh"
    ];
    configureFlags = [
        "--without-gui"
        "--with-sqlite"
        "--disable-bench"
        "--disable-tests"
        "--with-boost-libdir=${pkgs.boost183.out}/lib"
    ];
    buildFlags = [
        "src/litecoind"
        "src/litecoin-cli"
    ];
    enableParallelBuilding = true;
    installPhase = ''
        mkdir -p $out/bin
        install -D --mode=755 src/litecoind src/litecoin-cli $out/bin
    '';
}

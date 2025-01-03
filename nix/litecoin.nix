{ pkgs }:

pkgs.stdenv.mkDerivation rec {
    pname = "litecoin";
    version = "v0.21.4";
    src = fetchGit {
        url = "https://github.com/litecoin-project/litecoin.git";
        ref = "refs/tags/${version}";
    };
    nativeBuildInputs = [
        pkgs.autoconf
        pkgs.automake
        pkgs.libtool
        pkgs.pkg-config
        # pkgs.hexdump # for tests
    ];
    buildInputs = [
        pkgs.boost
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
        "--with-boost-libdir=${pkgs.boost.out}/lib"
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

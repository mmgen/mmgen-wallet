{
    lib,
    stdenv,
    cmake,
    capnproto,
    pkg-config,
    darwin,
    boost,
    libevent,
    zeromq,
    zlib,
    sqlite,
}:

stdenv.mkDerivation (finalAttrs: {
    pname = "bitcoind";
    version = "30.0";

    src = fetchGit {
        url = "https://github.com/bitcoin/bitcoin.git";
        # url = /path/to/repo/bitcoin-30.0;
        ref = "refs/tags/v${finalAttrs.version}";
        shallow = true;
    };

    nativeBuildInputs = [
        cmake
        capnproto
        pkg-config
    ]
    ++ lib.optionals (stdenv.hostPlatform.isDarwin && stdenv.hostPlatform.isAarch64) [
        darwin.autoSignDarwinBinariesHook
    ];

    buildInputs = [
        boost
        libevent
        zeromq
        zlib
        sqlite
    ];

    cmakeFlags = [
        (lib.cmakeBool "BUILD_BENCH" false)
        (lib.cmakeBool "WITH_ZMQ" true)
        (lib.cmakeBool "BUILD_TESTS" false)
        (lib.cmakeBool "BUILD_FUZZ_BINARY" false)
    ];

    NIX_LDFLAGS = lib.optionals (
        stdenv.hostPlatform.isLinux && stdenv.hostPlatform.isStatic
    ) "-levent_core";

    doCheck = false;

    enableParallelBuilding = true;

    __darwinAllowLocalNetworking = true;

    doInstallCheck = false;

    meta = {
        description = "Peer-to-peer electronic cash system";
        longDescription = ''
            Bitcoin is a free open source peer-to-peer electronic cash system that is
            completely decentralized, without the need for a central server or trusted
            parties. Users hold the crypto keys to their own money and transact directly
            with each other, with the help of a P2P network to check for double-spending.
        '';
        homepage = "https://bitcoin.org/en/";
        downloadPage = "https://bitcoincore.org/bin/bitcoin-core-${finalAttrs.version}/";
        changelog = "https://bitcoincore.org/en/releases/${finalAttrs.version}/";
        maintainers = with lib.maintainers; [
            prusnak
            roconnor
        ];
        license = lib.licenses.mit;
        platforms = lib.platforms.unix;
    };
})

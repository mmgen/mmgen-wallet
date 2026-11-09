{
    lib,
    stdenv,
    cmake,
    pkg-config,
    boost186,
    libsodium,
    openssl,
    python3,
    randomx,
    rapidjson,
    readline,
    unbound,
    zeromq,

    trezorSupport ? true,
    hidapi,
    libusb1,
    protobuf_21,
    udev,
}:

let
    # submodules; revs are taken from monero repo's `/external`
    supercop = fetchGit {
        url = "https://github.com/monero-project/supercop.git";
        # url = /path/to/repo/supercop.git;
        rev = "e887b2fb4bfcfcc454b2005472ad1df6f2191f52";
        shallow = true;
    };
    trezor-common = fetchGit {
        url = "https://github.com/trezor/trezor-common.git";
        # url = /path/to/repo/trezor-common.git;
        rev = "9b48064ca38bd6403b9db2727d955325429b0131";
        shallow = true;
    };
in

stdenv.mkDerivation rec {
    pname = "monero-cli";
    version = "0.18.5.4";

    src = fetchGit {
        url = "https://github.com/monero-project/monero.git";
        # url = /path/to/repo/monero.git;
        ref = "refs/tags/v${version}";
        rev = "85f036ba7019cd36f08e8a38a27c37ea7b522618";
        shallow = true;
    };

    patches = [
        ./monero-use-system-libraries.patch
    ];

    postPatch = ''
        # manually install submodules
        rmdir external/{supercop,trezor-common}
        ln -sf ${supercop} external/supercop
        ln -sf ${trezor-common} external/trezor-common
        # export patched source for monero-gui
        cp -r . $source
    '';

    nativeBuildInputs = [
        cmake
        pkg-config
    ];

    buildInputs = [
        boost186 # uses boost/asio/io_service.hpp
        libsodium
        openssl
        randomx
        rapidjson
        readline
        unbound
        zeromq
    ]
    ++ lib.optionals trezorSupport [
        python3
        hidapi
        libusb1
        protobuf_21
    ]
    ++ lib.optionals (trezorSupport && stdenv.hostPlatform.isLinux) [ udev ];

    cmakeFlags = [
        # skip submodules init
        "-DMANUAL_SUBMODULES=ON"
        "-DBUILD_GUI_DEPS=OFF"
        "-DReadline_ROOT_DIR=${readline.dev}"
        "-Wno-dev"
    ]
    ++ lib.optional stdenv.hostPlatform.isDarwin "-DBoost_USE_MULTITHREADED=OFF"
    ++ lib.optionals trezorSupport [
        "-DUSE_DEVICE_TREZOR=ON"
    ];

    outputs = [
        "out"
        "source"
    ];

    meta = {
        description = "Private, secure, untraceable currency";
        homepage = "https://getmonero.org/";
        license = lib.licenses.bsd3;

        platforms = with lib.platforms; linux;

        # macOS/ARM has a working `monerod` (at least), but `monero-wallet-cli`
        # segfaults on start after entering the wallet password, when built in release mode.
        # Building the same revision in debug mode to root-cause the above problem doesn't work
        # because of https://github.com/monero-project/monero/issues/9486
        badPlatforms = [ "aarch64-darwin" ];

        maintainers = with lib.maintainers; [
            pmw
            rnhmjoj
        ];
        mainProgram = "monero-wallet-cli";
        # internal build tool generate_translations_header is tricky to compile for the build platform
        broken = !stdenv.buildPlatform.canExecute stdenv.hostPlatform;
    };
}

# adapted from go-ethereum.nix in nixpkgs repository
# not currently used, as nixpkgs 25.05 go-ethereum (v1.15.11) is OK

{
    pkgs,
    lib,
    stdenv,
    buildGoModule,
    # nixosTests,
    tag_version,
    vendor_hash,
}:

buildGoModule {
    pname = "go-ethereum";
    version = tag_version;

    src = fetchGit {
        url = "https://github.com/ethereum/go-ethereum.git";
        # url = /path/to/repo/go-ethereum.git;
        ref = "refs/tags/${tag_version}";
        shallow = true;
    };

    proxyVendor = false;

    vendorHash = vendor_hash;

    doCheck = false;

    subPackages = [ "cmd/geth" ];

    ## Following upstream: https://github.com/ethereum/go-ethereum/blob/v1.11.6/build/ci.go#L218
    tags = [ "urfave_cli_no_docs" ];

    ## Fix for usb-related segmentation faults on darwin
    propagatedBuildInputs = lib.optionals stdenv.hostPlatform.isDarwin [
        pkgs.libobjc
        pkgs.IOKit
    ];

    # passthru.tests = { inherit (nixosTests) geth; };

    meta = with lib; {
        homepage = "https://geth.ethereum.org/";
        description = "Official golang implementation of the Ethereum protocol";
        license = with licenses; [
            lgpl3Plus
            gpl3Plus
        ];
        maintainers = with maintainers; [ RaghavSood ];
        mainProgram = "geth";
    };
}

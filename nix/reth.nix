{
    lib,
}:

let
    # cargo and rustc packages from 25.11 are out of date,
    # so fetch them from a more recent commit:
    pinnedPkgs = fetchGit {
        url = "https://github.com/NixOS/nixpkgs.git";
        # url = /path/to/repo/nixpkgs-116266.git;
        rev = "116266f52682e7b975426c66204b3dada19be502";
        shallow = true;
    };
    pkgs = import pinnedPkgs {};

in

pkgs.rustPlatform.buildRustPackage rec {
    pname = "reth";
    version = "2.1.0";

    src = fetchGit {
        url = "https://github.com/paradigmxyz/reth";
        # url = /path/to/repo/reth;
        ref = "refs/tags/v${version}";
        shallow = true;
    };

    cargoHash = "sha256-//UOHtknfhq33bA3/xzwS0K9FPbn4Tkwx3kkNuluoAM=";

    doCheck = false;
    doInstallCheck = false;

    nativeBuildInputs = [
        pkgs.perl
        pkgs.clang
        pkgs.libclang
        pkgs.rustc
        pkgs.cargo
    ];

    env.LIBCLANG_PATH = pkgs.libclang.lib  + "/lib/";

    meta = with lib; {
        description = "Rust Ethereum daemon";
        homepage = "https://github.com/paradigmxyz/reth";
        license = licenses.mit;
        mainProgram = "reth";
    };
}

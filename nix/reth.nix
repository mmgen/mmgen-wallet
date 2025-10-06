{
    lib,
    rustPlatform,
}:

let
    # cargo and rustc packages from 25.05 are out of date,
    # so fetch them from a more recent commit:
    pinnedPkgs = fetchGit {
        url = "https://github.com/NixOS/nixpkgs.git";
        # url = /path/to/repo/nixpkgs-fe8997.git;
        rev = "fe89979ad5e8fd233ae0aac0e7e56f465945ae70";
        shallow = true;
    };
    pkgs = import pinnedPkgs {};

in

rustPlatform.buildRustPackage rec {
    pname = "reth";
    version = "1.7.0";

    src = fetchGit {
        url = "https://github.com/paradigmxyz/reth";
        # url = /path/to/repo/reth;
        ref = "refs/tags/v${version}";
        shallow = true;
    };

    cargoHash = "sha256-2zdilVIHCW0N2yZNfLNoVpTASjXU1ABcZzQLzpAGEsY=";

    nativeBuildInputs = [
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

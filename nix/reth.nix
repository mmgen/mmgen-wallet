{
    lib,
    pkgs,
}:

pkgs.rustPlatform.buildRustPackage rec {
    pname = "reth";
    version = "1.10.2";

    src = fetchGit {
        url = "https://github.com/paradigmxyz/reth";
        # url = /path/to/repo/reth;
        ref = "refs/tags/v${version}";
        shallow = true;
    };

    cargoHash = "sha256-X3OGsN+JRFW2As9W6r8vEYXaeJA/qpVFOzZxHaEYF3I=";

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

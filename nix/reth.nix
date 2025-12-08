{
    lib,
    pkgs,
}:

pkgs.rustPlatform.buildRustPackage rec {
    pname = "reth";
    version = "1.9.3";

    src = fetchGit {
        url = "https://github.com/paradigmxyz/reth";
        # url = /path/to/repo/reth;
        ref = "refs/tags/v${version}";
        shallow = true;
    };

    cargoHash = "sha256-WDe75Sg7y4GfH3dSfY48aXrIBe89skj1VW0NcgtLEVU=";

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

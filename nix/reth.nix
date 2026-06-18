{
    lib,
    pkgs,
}:

pkgs.rustPlatform.buildRustPackage rec {
    pname = "reth";
    version = "2.3.0";

    src = fetchGit {
        url = "https://github.com/paradigmxyz/reth";
        # url = /path/to/repo/reth;
        ref = "refs/tags/v${version}";
        shallow = true;
    };

    cargoHash = "sha256-D2DuofmPWXJT1dTRH1iOeJQ6DGbWu8FxOWNcPYMv3go=";

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

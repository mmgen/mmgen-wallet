{
    lib,
    stdenv,
    rustPlatform,
    fetchFromGitHub,
    installShellFiles,

    rust-jemalloc-sys,
    buildPackages,
    versionCheckHook,

    nixosTests,
}:

rustPlatform.buildRustPackage rec {
    pname = "ruff";
    version = "0.16.1";

    __structuredAttrs = true;

    src = fetchFromGitHub {
        owner = "astral-sh";
        repo = "ruff";
        tag = version;
        hash = "sha256-77h1f8LV9ZTYqs5SymLij6CXe3TzrXEMcCPASOHj/UU=";
    };

    cargoBuildFlags = [ "--package=ruff" ];

    cargoHash = "sha256-fgcl0JhGkzbXD+ajDdIwnIUHEuKj3XwDH81JkDEqntc=";

    nativeBuildInputs = [ installShellFiles ];

    buildInputs = [ rust-jemalloc-sys ];

    # Run cargo tests
    checkType = "debug";

    # tests do not appear to respect linker options on doctests
    # Upstream issue: https://github.com/rust-lang/cargo/issues/14189
    # This causes errors like "error: linker `cc` not found" on static builds
    doCheck = !stdenv.hostPlatform.isStatic;

    # Exclude tests from `ty`-related crates, run everything else.
    # Ordinarily we would run all the tests, but there is significant overlap with the `ty` package in nixpkgs,
    # which ruff shares a monorepo with.
    # As such, we leave running `ty` tests to the `ty` package, and concentrate on everything else.
    cargoTestFlags = [
        "--workspace"
        "--exclude=ty"
        "--exclude=ty_ide"
        "--exclude=ty_project"
        "--exclude=ty_python_semantic"
        "--exclude=ty_server"
        "--exclude=ty_static"
        "--exclude=ty_test"
        "--exclude=ty_vendored"
        "--exclude=ty_wasm"
    ];

    nativeInstallCheckInputs = [ versionCheckHook ];
    doInstallCheck = true;

    meta = {
        description = "Extremely fast Python linter and code formatter";
        homepage = "https://github.com/astral-sh/ruff";
        changelog = "https://github.com/astral-sh/ruff/releases/tag/${version}";
        license = lib.licenses.mit;
        mainProgram = "ruff";
        maintainers = with lib.maintainers; [
            bengsparks
            GaetanLepage
        ];
    };
}

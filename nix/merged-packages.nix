{ add_pkgs_path }:

let
    dfl_nixpkgs = import ./nixpkgs-25.11.nix {};
    dfl_python = pkgs.python313;
    null_pkgs = {
        system-packages = {};
        python-packages = {};
    };
    usr_pkgs_path = if builtins.pathExists ~/.mmgen/user-packages.nix then
        ~/.mmgen/user-packages.nix else ./user-packages.nix;
    usr_pkgs = import usr_pkgs_path { pkgs = dfl_nixpkgs; python = dfl_python; bdir = ./.; };
    pkgs = if usr_pkgs?pkgs then usr_pkgs.pkgs else dfl_nixpkgs;
    python = if usr_pkgs?pkgs then usr_pkgs.python else dfl_python;
    wallet_pkgs = import ./packages.nix { pkgs = pkgs; python = python; };
    add_pkgs = if add_pkgs_path == null then null_pkgs else
        (import add_pkgs_path { pkgs = pkgs; python = python; });
in

wallet_pkgs.system-packages //
add_pkgs.system-packages //
usr_pkgs.system-packages //
{
    pyenv = python.withPackages (ps:
        builtins.attrValues (
            wallet_pkgs.python-packages //
            add_pkgs.python-packages //
            usr_pkgs.python-packages)
    );
}

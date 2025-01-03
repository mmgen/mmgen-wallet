# Nix shell environment for mmgen-wallet

{ add_pkgs_path ? null }:

let
    pkgs = import <nixpkgs> {};
in

pkgs.mkShellNoCC {
    packages = builtins.attrValues (import ./merged-packages.nix { add_pkgs_path = add_pkgs_path; });
    shellHook = ''
        do_sudo_override() {
            (
                rm -rf .bin-override
                mkdir .bin-override
                cd .bin-override
                if [ -x /bin/sudo ]; then
                    ln -s /bin/sudo
                elif [ -x /run/wrappers/bin/sudo ]; then
                    ln -s /run/wrappers/bin/sudo
                fi
            )
        }

        read _ _ name <<<$(grep ^name setup.cfg)

        [[ "$name" =~ ^mmgen-(wallet|node-tools)$ ]] || {
            echo "Error: this script must be executed in the mmgen-wallet or mmgen-node-tools repository root"
            exit 1
        }

        pwd=$(pwd)
        export PYTHONPATH=$pwd
        export PATH=$pwd/cmds:$pwd/.bin-override:$HOME/.local/bin:$PATH

        [ "$UID" == 0 ] || do_sudo_override
    '';
}

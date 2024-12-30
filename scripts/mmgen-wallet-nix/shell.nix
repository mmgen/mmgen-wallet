# Nix shell environment for mmgen-wallet

let
    pkgs = import <nixpkgs> {};
in

pkgs.mkShellNoCC {
    packages = builtins.attrValues (import ./packages.nix);
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

        [ "$(python3 ./setup.py --name 2>/dev/null)" == "mmgen-wallet" ] || {
            echo "Error: this script must be executed in the mmgen-wallet repository root"
            exit 1
        }

        pwd=$(pwd)
        export PYTHONPATH=$pwd
        export PATH=$pwd/cmds:$pwd/.bin-override:$PATH

        [ "$UID" == 0 ] || do_sudo_override
    '';
}

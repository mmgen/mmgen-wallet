# Nix shell environment for mmgen-wallet

{
    repo ? "mmgen-wallet",
    add_pkgs_path ? null
}:

let
    pkgs = import <nixpkgs> {};
in

pkgs.mkShellNoCC {
    packages = builtins.attrValues (import ./merged-packages.nix { add_pkgs_path = add_pkgs_path; });
    shellHook = ''
        do_bin_override() {
            (
                rm -rf .bin-override
                mkdir .bin-override
                cd .bin-override
                if [ -x /bin/sudo ]; then
                    ln -s /bin/sudo
                    ln -s /bin/mount
                    ln -s /bin/umount
                elif [ -x /run/wrappers/bin/sudo ]; then
                    ln -s /run/wrappers/bin/sudo
                    ln -s /run/wrappers/bin/mount
                    ln -s /run/wrappers/bin/umount
                fi
            )
        }

        read _ _ name <<<$(grep ^name setup.cfg)

        [ "$name" == "${repo}" ] || {
            echo "Error: this script must be executed in the ${repo} repository root"
            exit 1
        }

        pwd=$(pwd)
        export PYTHONPATH=$pwd
        export PYTHONPYCACHEPREFIX=$HOME/.cache/pycache
        export PATH=$pwd/cmds:$pwd/.bin-override:$HOME/.local/bin:$PATH
        export LANG="en_US.UTF-8"
        export HISTFILESIZE=2000
        export HISTSIZE=2000
        export HISTCONTROL="ignoreboth"
        export HISTFILE=$pwd/.bash_history

        [ "$UID" == 0 ] || do_bin_override
    '';
}

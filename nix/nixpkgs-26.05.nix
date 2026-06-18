import (
    fetchGit {
        url = "https://github.com/NixOS/nixpkgs.git";
        # url = /path/to/repo/nixpkgs-26.05.git;
        ref = "release-26.05";
        rev = "aa42bf7ceec62347e0962a461071ba81d39bdf37";
        shallow = true;
    }
)

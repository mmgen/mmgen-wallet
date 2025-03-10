import (
    fetchGit {
        url = "https://github.com/NixOS/nixpkgs.git";
        ref = "release-24.11";
        rev = "8b27c1239e5c421a2bbc2c65d52e4a6fbf2ff296"; # refs/tags/24.11
        shallow = true;
    }
)

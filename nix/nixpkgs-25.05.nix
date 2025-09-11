import (
    fetchGit {
        url = "https://github.com/NixOS/nixpkgs.git";
        # url = /path/to/repo/nixpkgs-25.05.git;
        ref = "release-25.05";
        rev = "11cb3517b3af6af300dd6c055aeda73c9bf52c48"; # refs/tags/25.05
        shallow = true;
    }
)

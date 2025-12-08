import (
    fetchGit {
        url = "https://github.com/NixOS/nixpkgs.git";
        # url = /path/to/repo/nixpkgs-25.11.git;
        ref = "release-25.11";
        rev = "52de6ea1db373aac4aec2ca926638db524ea7acf";
        shallow = true;
    }
)

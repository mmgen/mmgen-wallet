{ pkgs }:

pkgs.stdenvNoCC.mkDerivation {
    pname = "zcash-mini";
    version = "a2b35042";
    src = fetchGit {
        url = "https://github.com/FiloSottile/zcash-mini";
        # url = /path/to/repo/zcash-mini-a2b350;
        rev = "a2b35042ad3a3bc22b925ecfc45e768a376bd29a";
        shallow = true;
    };
    buildInputs = [ pkgs.go pkgs.binutils ];
    patchPhase = ''
        sed -e "s@github.com/FiloSottile/@@"       -i main.go
        sed -e "s@github.com/FiloSottile/@@"       -i zcash/address.go
        sed -e "s@github.com/btcsuite@zcash-mini@" -i zcash/address.go
        sed -e "s@golang.org/x@zcash-mini@"        -i zcash/address.go
        mv vendor/github.com/btcsuite/btcutil .
        mv vendor/golang.org/x/crypto .
    '';
    dontConfigure = true;
    dontBuild = true;
    installPhase = ''
        export HOME=$TMPDIR
        go mod init zcash-mini
        go build -mod=mod
        mkdir --parents $out/bin
        install --strip --mode=755 zcash-mini $out/bin
    '';
    dontFixup = true;
}

{ pkgs }:

pkgs.stdenv.mkDerivation {
    pname = "vanitygen-plusplus";
    version = "e7858035";
    src = fetchGit {
        url = "https://github.com/10gic/vanitygen-plusplus";
        # url = /path/to/repo/vanitygen-plusplus-e78580;
        rev = "e7858035d092f9b9d6468e2b812475faaf7c69c6";
        shallow = true;
    };
    buildInputs = [ pkgs.openssl pkgs.pcre ];
    installPhase = ''
        mkdir -p $out/bin
        install -sv --mode=755 vanitygen keyconv $out/bin
    '';
}

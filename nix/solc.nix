{ pkgs, fetchzip, fetchurl }:

pkgs.stdenv.mkDerivation rec {
    pname = "solc";
    version = "0.8.26";
    src = fetchzip {
        url = "https://github.com/ethereum/solidity/releases/download/v0.8.26/solidity_0.8.26.tar.gz";
        sha256 = "sha256-4lrxwjEg1/TPWt2WB/kQNYvdOEt5aEbnGaEcNMz9pv4=";
    };
    range_pkg = fetchurl {
        url = "https://github.com/ericniebler/range-v3/archive/0.12.0.tar.gz";
        sha256 = "sha256-AVrbIwCpjt/OrwclvuwzN/VCr0kVzsTQuJ+giG9Lqcs=";
    };
    fmtlib_pkg = fetchurl {
        url = "https://github.com/fmtlib/fmt/archive/9.1.0.tar.gz";
        sha256 = "sha256-XepI0fzdw+xXHOIFjhORCg1Ka6tMwJqAnYsd0ciK5vI=";
    };
    json_pkg = fetchurl {
        url = "https://github.com/nlohmann/json/releases/download/v3.11.3/json.hpp";
        sha256 = "sha256-m+pMgGbvShwgayvlo2MC+JJvf9xgh69dILQX0M8QPqY=";
    };
    nativeBuildInputs = [ pkgs.cmake ];
    buildInputs = [ pkgs.boost ];
    cmakeFlags = [ "-DBoost_USE_STATIC_LIBS=OFF" ];
    patchPhase = ''
        mkdir -p deps/downloads
        mkdir -p deps/nlohmann/nlohmann
        cp ${range_pkg} deps/downloads/range-v3-0.12.0.tar.gz
        cp ${fmtlib_pkg} deps/downloads/fmt-9.1.0.tar.gz
        cp ${json_pkg} deps/nlohmann/nlohmann/json.hpp
    '';
}

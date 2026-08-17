{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = with pkgs; [
    gcc
    lld
    cmake
    gnumake
    git
    (python3.withPackages (python-pkgs: with python-pkgs; [ pandas matplotlib ]))
  ];
  shellHook = ''
      export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
    '';

}

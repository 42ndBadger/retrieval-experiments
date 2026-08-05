{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = with pkgs; [
    gcc
    clang
    lld
    cmake
    llvmPackages.openmp
    gnumake
    git
  ];
}

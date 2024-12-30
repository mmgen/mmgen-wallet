{ config, lib, pkgs, ... }:

{
    environment.systemPackages = builtins.attrValues (import ./packages.nix);
}

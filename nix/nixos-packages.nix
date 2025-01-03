{ config, lib, pkgs, ... }:

{
    environment.systemPackages = builtins.attrValues (import ./default.nix);
}

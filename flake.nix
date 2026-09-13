{
  description = "StudySpot development environment";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

  outputs =
    { nixpkgs, ... }:
    let
      supportedSystems = [
        "aarch64-darwin"
        "aarch64-linux"
        "x86_64-darwin"
        "x86_64-linux"
      ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    in
    {
      devShells = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
          toolchain = with pkgs; [
            bun
            curl
            docker
            git
            just
            pre-commit
            python312
            uv
          ];
        in
        {
          default = pkgs.mkShellNoCC {
            packages = toolchain;
            UV_PYTHON_DOWNLOADS = "never";
          };
        }
      );

      checks = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
          toolchain = pkgs.runCommand "studyspot-toolchain" {
            nativeBuildInputs = with pkgs; [
              bun
              docker
              just
              python312
              uv
            ];
          } ''
            bun --version
            docker --version
            just --version
            python3.12 --version
            uv --version
            touch "$out"
          '';
        }
      );
    };
}

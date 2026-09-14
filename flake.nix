{
  description = "StudySpot development environment";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

  outputs =
    { self, nixpkgs, ... }:
    let
      supportedSystems = [
        "aarch64-darwin"
        "aarch64-linux"
        "x86_64-darwin"
        "x86_64-linux"
      ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
      toolchainFor =
        pkgs: with pkgs; [
          bun
          curl
          direnv
          docker
          git
          just
          pre-commit
          python312
          uv
        ];
    in
    {
      devShells = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
          default = pkgs.mkShellNoCC {
            packages = toolchainFor pkgs;
            UV_PYTHON_DOWNLOADS = "never";
          };
        }
      );

      packages = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
          default = pkgs.writeShellApplication {
            name = "studyspot";
            runtimeInputs = toolchainFor pkgs;
            text = ''
              if [ "$#" -eq 0 ]; then
                exec just --list
              fi

              exec just "$@"
            '';
          };
        }
      );

      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/studyspot";
        };
      });

      checks = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
          toolchain = pkgs.runCommand "studyspot-toolchain" {
            nativeBuildInputs = with pkgs; [
              bun
              direnv
              docker
              just
              python312
              uv
            ];
          } ''
            bun --version
            docker --version
            direnv --version
            just --version
            python3.12 --version
            uv --version
            touch "$out"
          '';
        }
      );
    };
}

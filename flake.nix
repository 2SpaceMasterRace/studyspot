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

      # Terraform has been under the BUSL since 2023, so nixpkgs marks it
      # unfree. Permitted for that one package rather than by setting
      # allowUnfree globally, which would silently permit anything else later.
      pkgsFor =
        system:
        import nixpkgs {
          inherit system;
          config.allowUnfreePredicate = package: nixpkgs.lib.getName package == "terraform";
        };

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

          # Deploying to AWS: see infra/README.md. Pinned here for the same
          # reason as everything above, so that `just aws-apply` behaves the
          # same for everyone who runs it.
          awscli2
          terraform
        ];
    in
    {
      devShells = forAllSystems (
        system:
        let
          pkgs = pkgsFor system;
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
          pkgs = pkgsFor system;
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
          pkgs = pkgsFor system;
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
              awscli2
              terraform
            ];
          } ''
            bun --version
            docker --version
            direnv --version
            just --version
            python3.12 --version
            uv --version
            aws --version
            terraform version
            touch "$out"
          '';
        }
      );
    };
}

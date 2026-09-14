# Nix development and packaging

Nix provides StudySpot's reproducible development and CI toolchain. Docker remains the container format, while Vercel remains the application deployment platform.

## Flake model

```text
flake.nix  -> declared inputs and outputs
flake.lock -> exact pinned input revisions
/nix/store -> immutable build results
```

The StudySpot flake exposes development shells, checks, a packaged command, and a runnable default app for Linux and macOS on x86-64 and ARM64.

## Development shell

Enter the pinned environment:

```shell
nix develop
```

If a legacy Nix installation has not enabled flakes, either enable `nix-command` and `flakes` in its configuration or pass `--extra-experimental-features "nix-command flakes"` to the command. `just nix-check` supplies this compatibility flag automatically.

Run one command without opening an interactive shell:

```shell
nix develop -c just check
```

Nix supplies the Docker CLI, but a Docker daemon must run on the host.

## Packaged command surface

Build the StudySpot command package:

```shell
nix build
```

The `result` symlink points to the immutable Nix store output. The package contains a `studyspot` command that delegates to the repository's supported `just` recipes.

Run it without installing it:

```shell
nix run . -- check
nix run . -- dev
nix run . -- docs
```

This keeps Nix and non-Nix workflows on one command surface rather than maintaining two independent build systems.

## Validation

```shell
just nix-check
```

The flake check verifies that the expected Bun, Python, uv, Docker, direnv, and just tools resolve on every supported system.

## Deployment

Nix makes the deployment toolchain reproducible but does not host the application:

```shell
nix run . -- deploy-preview
nix run . -- deploy-staging
nix run . -- deploy-production
```

The command calls the pinned Vercel CLI through the `justfile`. Vercel then builds the SvelteKit and FastAPI services with the versioned public-data snapshot. PostgreSQL/PostGIS and Meilisearch remain local integration services until StudySpot owns non-reproducible state.

## Why Nix does not build the application images yet

The application already has Bun and uv lockfiles plus working Dockerfiles. Repackaging both dependency graphs with Nix would create a second implementation to maintain without changing the deployed artifact on Vercel.

If StudySpot moves to an OCI-native host, `dockerTools.buildLayeredImage` outputs could become worthwhile. A NixOS deployment could go further and define complete staging and production machines. That would trade managed hosting for direct responsibility over TLS, backups, upgrades, monitoring, and recovery.

## Secrets

Never place credentials in `flake.nix`, derivation inputs, or the Nix store. Local secrets belong in ignored environment files; CI and deployment secrets belong in GitHub and Vercel secret stores.

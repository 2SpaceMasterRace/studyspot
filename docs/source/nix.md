# Nix development environment and command wrapper

Nix provides StudySpot's reproducible development and CI toolchain. Docker remains the container format, while Vercel remains the application deployment platform.

## Flake model

```text
flake.nix  -> declared inputs and outputs
flake.lock -> exact pinned input revisions
/nix/store -> immutable build results
```

The StudySpot flake exposes development shells, checks, and a command wrapper for Linux and macOS on x86-64 and ARM64.

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

## Command wrapper

Build the StudySpot command wrapper:

```shell
nix build
```

The `result` symlink points to the immutable Nix store output. It contains a `studyspot` command that delegates to the repository's supported `just` recipes. Run it from a StudySpot checkout; the wrapper does not copy the application source or `justfile` into the Nix store.

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

Nix supplies the local tools used around deployment but does not host or package the Vercel application:

```shell
nix run . -- deploy-preview
nix run . -- deploy-production
```

The command calls the exact Vercel CLI version named in the `justfile`. `bunx` may download that CLI on first use, so manual deployment still needs network access and Vercel authentication; the CLI is not stored in the Nix flake. Vercel builds the SvelteKit and FastAPI applications; neither hosted Turso database is loaded yet, and search behavior is unimplemented. Local development uses an embedded Turso file, while Vercel uses environment-scoped Turso Cloud credentials, both behind one repository interface.

## Why Nix does not build the application images yet

The application already has Bun and uv lockfiles plus working Dockerfiles. Repackaging both dependency graphs with Nix would create a second implementation to maintain without changing the deployed artifact on Vercel.

If StudySpot moves to an OCI-native host, `dockerTools.buildLayeredImage` outputs could become worthwhile. A NixOS deployment could go further and define complete staging and production machines. That would trade managed hosting for direct responsibility over TLS, backups, upgrades, monitoring, and recovery.

## Secrets

Never place credentials in `flake.nix`, derivation inputs, or the Nix store. A local Turso file needs no secret. Hosted `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN` values belong in Vercel environment settings, with separate values for Preview and Production.

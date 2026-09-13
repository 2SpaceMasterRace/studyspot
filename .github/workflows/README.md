# Workflows

- `ci.yml` installs locked dependencies and runs `just check` on every pull request and push to `main`. After a successful push to `main`, it builds, deploys, and checks the production Vercel application.
- `compose.yml` builds the four-service local topology, waits for healthy containers, and checks the frontend and API liveness endpoint.
- `nix.yml` evaluates the pinned Nix development shell.

The Vercel deployment job requires the repository variables `VERCEL_ORG_ID` and `VERCEL_PROJECT_ID` and the repository secret `VERCEL_TOKEN`.

Configure the `main` branch to require these checks before merging:

- `Repository checks`
- `Container smoke test`
- `Nix flake`

Also require one approving review and resolved conversations. Disable force pushes and branch deletion.

# Workflows

- `ci.yml` installs locked dependencies and runs `just check` on every pull request and push to `staging` or `main`. A successful `staging` push creates and checks a branch-linked Vercel Preview deployment. A successful `main` push builds, deploys, and checks production.
- `compose.yml` builds the four-service local topology, waits for healthy containers, and checks the frontend and API liveness endpoint.
- `docs.yml` publishes the warning-free Sphinx build from `main` to GitHub Pages; pull requests are already covered by `just check` in `ci.yml`.
- `nix.yml` evaluates the pinned Nix development shell.

The Vercel deployment jobs require the repository variables `VERCEL_ORG_ID` and `VERCEL_PROJECT_ID` and the repository secret `VERCEL_TOKEN`. Set the repository variable `VERCEL_DEPLOY_ENABLED` to `true` only after all three values are configured; until then, deployment jobs are safely skipped while checks continue to run.

Configure the `staging` and `main` branches to require these checks before merging:

- `Repository checks`
- `Container smoke test`
- `Nix flake`

Also require one approving review and resolved conversations. Disable force pushes and branch deletion.

The canonical settings are stored in `.github/branch-protection.json` and can be reapplied through the GitHub branch-protection API.

Feature pull requests target `staging`. Release pull requests merge `staging` into `main`. Configure Preview environment variables specifically for the `staging` branch, and assign the desired staging domain to that branch in Vercel.

This repository's GitHub Pages site uses **GitHub Actions** as its source. Forks must enable that setting before their first documentation deployment.

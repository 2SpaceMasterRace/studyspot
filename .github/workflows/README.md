# Workflows

- `ci.yml` installs locked dependencies and runs `just check` on every pull request and push to `staging` or `main`.
- `compose.yml` builds the four-service local topology, waits for healthy containers, and checks the frontend and API liveness endpoint.
<<<<<<< HEAD
- `docs.yml` publishes the warning-free Sphinx build from `main` to GitHub Pages; pull requests are already covered by `just check` in `ci.yml`.
=======
- `ci.yml` builds the warning-free Sphinx documentation as part of `just check`; Vercel publishes it with the staging app at `/docs/`.
>>>>>>> origin/staging
- `nix.yml` evaluates the pinned Nix development shell.

Vercel's Git integration is the only automatic deployment path. It creates a Preview deployment for every pull request and branch push, and deploys `main` to production. GitHub Actions does not need a Vercel token, project ID, or team ID.

Configure the `staging` and `main` branches to require these checks before merging:

- `Repository checks`
- `Container smoke test`
- `Nix flake`
- `Vercel`

Require resolved conversations and disable force pushes and branch deletion. GitHub does not permit pull-request authors to approve their own work, so a solo maintainer must use zero required approvals. Teams with an independent reviewer can require one or more approvals.

The canonical settings are stored in `.github/branch-protection.json` and can be reapplied through the GitHub branch-protection API.

Feature pull requests target `staging`. Release pull requests merge `staging` into `main`. In Vercel, set `main` as the Production Branch, assign the desired staging domain to `staging`, and choose a Deployment Protection setting that matches the intended audience.

This repository's GitHub Pages site uses **GitHub Actions** as its source. Forks must enable that setting before their first documentation deployment.

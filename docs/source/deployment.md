# Deployment

StudySpot deploys the SvelteKit frontend and FastAPI application as one Vercel project. Requests to `/` use the frontend service, while `/api/*` uses FastAPI. The normalized public-data snapshot is included in the deployment artifact, so the first release requires no external runtime service.

## Environments

```text
feature/* -> pull request preview
                  |
                  v
              staging -> staging deployment
                  |
                  v
                main -> production deployment
```

Developers work on short-lived feature branches and open pull requests into `staging`. Nobody pushes feature work directly to `staging`. A reviewed release pull request promotes `staging` into `main`.

Protect both long-lived branches with required checks, resolved conversations, and disabled force pushes and deletion. Repositories with independent reviewers can require approvals; a solo maintainer should leave the approval count at zero because GitHub does not allow authors to approve their own pull requests. A hotfix merged into `main` must immediately be merged back into `staging`.

## Staging

Pushes to `staging` run all checks, build with branch-specific Preview configuration, create a Vercel Preview deployment, and verify its frontend and API liveness endpoints.

Configure these GitHub repository values:

- Actions variable `VERCEL_ORG_ID`
- Actions variable `VERCEL_PROJECT_ID`
- Actions secret `VERCEL_TOKEN`
- Actions variable `VERCEL_DEPLOY_ENABLED`, set to `true` only after the other three values are ready

Until `VERCEL_DEPLOY_ENABLED` is `true`, the deployment jobs are skipped and the repository checks still run normally. This prevents a newly configured repository from producing failed deploy jobs while credentials are incomplete.

Finish the repository setup manually:

1. Create a narrowly scoped Vercel access token.
2. Add it to GitHub Actions as the `VERCEL_TOKEN` repository secret.
3. Confirm the public `VERCEL_ORG_ID` and `VERCEL_PROJECT_ID` repository variables.
4. Set the `VERCEL_DEPLOY_ENABLED` repository variable to `true`.
5. In the Vercel project settings, assign `dev-studyspot-nyu.vercel.app` to the `staging` branch if that domain is available.

Do not put the token in `.env`, commit it, or paste it into an issue or pull request.

No hosted database or search variables are required. When non-reproducible data is introduced later, scope its environment values to the `staging` branch and never point staging at writable production data.

Vercel automatically provides a stable generated branch URL when Git integration is enabled. To use `dev-studyspot-nyu.vercel.app`, add that domain to the project and assign it to the `staging` branch; the exact `.vercel.app` name must be available.

## Production

Pushes to `main` run the same checks, build one production artifact, deploy that artifact, and verify the frontend and API liveness endpoint. The current production demo is [studyspot-nyu.vercel.app](https://studyspot-nyu.vercel.app).

## Manual commands

```shell
just deploy-preview
just deploy-staging
just deploy-production
```

Nix users can invoke the same commands reproducibly:

```shell
nix run . -- deploy-preview
nix run . -- deploy-staging
nix run . -- deploy-production
```

## Data and search state

NYC and NYU source records are normalized into a versioned snapshot before deployment. FastAPI loads that snapshot and builds disposable runtime search structures. A new deployment can therefore recreate its complete state without a persistent filesystem or database.

PostgreSQL/PostGIS and Meilisearch remain part of the local Compose topology for integration work. They are not production dependencies until StudySpot stores user-generated corrections, favorites, accounts, import cursors, or other state that cannot be rebuilt from public inputs.

## Rollback

List deployments and point production back to a known working deployment:

```shell
bunx vercel@59.16.0 list
bunx vercel@59.16.0 rollback DEPLOYMENT_URL
```

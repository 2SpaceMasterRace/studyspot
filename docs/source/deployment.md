# Deployment

StudySpot deploys the SvelteKit frontend and FastAPI application as one Vercel project. Requests to `/` use the frontend service, while `/api/*` uses FastAPI. PostgreSQL/PostGIS and Meilisearch remain external stateful services.

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

Protect both long-lived branches with required checks, approving review, resolved conversations, and disabled force pushes and deletion. A hotfix merged into `main` must immediately be merged back into `staging`.

## Staging

Pushes to `staging` run all checks, build with branch-specific Preview configuration, create a Vercel Preview deployment, and verify its frontend and API liveness endpoints.

Configure these GitHub repository values:

- Actions variable `VERCEL_ORG_ID`
- Actions variable `VERCEL_PROJECT_ID`
- Actions secret `VERCEL_TOKEN`
- Actions variable `VERCEL_DEPLOY_ENABLED`, set to `true` only after the other three values are ready

Until `VERCEL_DEPLOY_ENABLED` is `true`, the deployment jobs are skipped and the repository checks still run normally. This prevents a newly configured repository from producing failed deploy jobs while credentials are incomplete.

Configure `DATABASE_URL`, `MEILISEARCH_URL`, and other environment values for the Vercel Preview environment, scoped to the `staging` branch. Never point staging at writable production data.

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

## Stateful dependencies

Vercel deploys application services, not the local PostgreSQL and Meilisearch containers. Provision hosted services in a region close to the API and inject their connection information through environment variables. Run migrations as a controlled release operation and keep search indexing repeatable.

## Rollback

List deployments and point production back to a known working deployment:

```shell
bunx vercel@59.16.0 list
bunx vercel@59.16.0 rollback DEPLOYMENT_URL
```

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

Finish the repository setup manually:

1. Create a narrowly scoped Vercel access token.
2. Add it to GitHub Actions as the `VERCEL_TOKEN` repository secret.
3. Confirm the public `VERCEL_ORG_ID` and `VERCEL_PROJECT_ID` repository variables.
4. Set the `VERCEL_DEPLOY_ENABLED` repository variable to `true`.
5. In the Vercel project settings, assign `dev-studyspot-nyu.vercel.app` to the `staging` branch if that domain is available.

Do not put the token in `.env`, commit it, or paste it into an issue or pull request.

No hosted database or search variables are required by the current liveness-only scaffold. When those integrations are implemented, scope their environment values to the `staging` branch and never point staging at writable production data.

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

Vercel deploys application services, not the local PostgreSQL and Meilisearch containers. For the current scaffold, PostgreSQL/PostGIS and Meilisearch remain local-only through Docker Compose. Do not provision a paid hosted dependency before the application actually uses it.

A future container deployment for the backend and Meilisearch is intentionally deferred. Fly.io can run the same container images, but account, application, billing, and secret setup remain manual and may incur charges. No provisioning script is maintained in this repository. Revisit the hosting configuration when persistent staging data and implemented search make it necessary. Run migrations as a controlled release operation and keep search indexing repeatable.

When Fly.io is introduced, create separate staging and production applications, attach separate persistent volumes, and keep secrets scoped to their application. Record only non-secret application names and regions in the repository.

## Rollback

List deployments and point production back to a known working deployment:

```shell
bunx vercel@59.16.0 list
bunx vercel@59.16.0 rollback DEPLOYMENT_URL
```

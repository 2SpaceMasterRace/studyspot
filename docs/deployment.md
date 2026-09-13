# Deployment

StudySpot deploys the Svelte frontend and FastAPI application as one Vercel project. Requests to `/` use the frontend service. Requests to `/api/*` use FastAPI, with Vercel removing the `/api` prefix before invoking the application.

## First deployment

Run from the repository root:

```shell
bunx vercel@59.16.0 link --yes --project studyspot
bunx vercel@59.16.0 deploy --prod
```

The Vercel project must use the **Services** framework preset.

## Continuous deployment

Pushes to `main` run repository checks, build the Vercel artifact, deploy that exact artifact to production, and check both the frontend and `/api/health/live`.

Configure these GitHub repository values from `.vercel/project.json`:

- Actions variable `VERCEL_ORG_ID`
- Actions variable `VERCEL_PROJECT_ID`
- Actions secret `VERCEL_TOKEN`

The token must belong to an account with deployment access to the project. Never commit it.

## Stateful dependencies

Vercel deploys the web applications, not the local PostgreSQL and Meilisearch containers. Before the search demo is deployed, provision reachable hosted instances and configure their production URLs in Vercel. The API liveness endpoint does not require those dependencies; the future readiness endpoint must.

## Rollback

List deployments and point production back to a known working deployment:

```shell
bunx vercel@59.16.0 list
bunx vercel@59.16.0 rollback DEPLOYMENT_URL
```

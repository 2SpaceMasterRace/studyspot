# Deployment

StudySpot deploys the SvelteKit frontend and FastAPI application as one Vercel project. Requests to `/` use the frontend service, while `/api/*` uses FastAPI. A backend service rewrite removes the public `/api` prefix before FastAPI route matching, so `/api/health/live` reaches the application's `/health/live` endpoint. The deployed scaffold contains no study-spot dataset or search index and therefore has no external runtime data dependency yet.

Vercel's Git integration is the only automatic deployment path. GitHub Actions independently validates the repository, Compose topology, documentation, and Nix flake; it does not build or upload a duplicate Vercel deployment.

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

Every push to `staging` creates a Vercel Preview deployment. The branch domain `dev-studyspot-nyu.vercel.app` tracks the newest successful `staging` deployment.

Configure Vercel manually:

1. Connect the GitHub repository to the Vercel project.
2. Set `main` as the Production Branch.
3. Assign `dev-studyspot-nyu.vercel.app` to the Preview environment and Git branch `staging`.
4. Assign `studyspot-nyu.vercel.app` to Production.
5. Under **Settings -> Deployment Protection**, choose **None** when both demo domains must be public. **Standard Protection** keeps Preview URLs, including staging, authenticated while leaving production domains public.

No Vercel token or project identifiers are required in GitHub Actions. If the repository previously used the duplicate CLI deployment workflow, delete its `VERCEL_TOKEN` secret and `VERCEL_DEPLOY_ENABLED`, `VERCEL_ORG_ID`, and `VERCEL_PROJECT_ID` variables after this change reaches `staging`, then revoke the unused token in Vercel.

Configure GitHub manually:

1. Protect `staging` and `main`.
2. Require `Repository checks`, `Container smoke test`, `Nix flake`, and `Vercel`.
3. Require resolved conversations and linear history; disable force pushes and deletion.
4. Use zero required approvals for a solo maintainer, or require approvals only when an independent reviewer is available.

The current Vercel project has both aliases assigned, but Deployment Protection redirects anonymous requests to Vercel SSO. Public verification will fail until the protection scope is changed.

No hosted database or search variables are required. When non-reproducible data is introduced later, scope its environment values to the `staging` branch and never point staging at writable production data.

After making staging public, verify both boundaries and require an exact HTTP 200 rather than accepting redirects:

```shell
test "$(curl --silent --output /dev/null --write-out '%{http_code}' https://dev-studyspot-nyu.vercel.app/)" = 200
curl --fail-with-body --silent --show-error https://dev-studyspot-nyu.vercel.app/api/health/live | grep -Fx '{"status":"ok"}'
```

## Production

Pushes to `main` deploy through the same Vercel Git integration and update [studyspot-nyu.vercel.app](https://studyspot-nyu.vercel.app). Promote only after the shared staging deployment is public and verified.

## Manual commands

```shell
just deploy-preview
just deploy-production
```

Nix users can invoke the same commands reproducibly:

```shell
nix run . -- deploy-preview
nix run . -- deploy-production
```

## Data and search state

The deployed scaffold does not yet import NYC or NYU records, package a normalized snapshot, or build runtime search structures. The planned implementation will normalize public source records into a versioned deployment artifact and derive disposable search state from that artifact.

PostgreSQL/PostGIS and Meilisearch remain part of the local Compose topology for integration work. They are not current production dependencies. Revisit production persistence when the data and search behavior is implemented, and require it once StudySpot stores user-generated corrections, favorites, accounts, import cursors, or other state that cannot be rebuilt from public inputs.

## Rollback

List deployments and point production back to a known working deployment:

```shell
bunx vercel@59.16.0 list
bunx vercel@59.16.0 rollback DEPLOYMENT_URL
```

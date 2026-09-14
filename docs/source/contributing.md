# Contributing

Read the repository's [contribution guide](https://github.com/2SpaceMasterRace/studyspot/blob/main/CONTRIBUTING.md) before editing the project.



## Branch workflow

1. Branch from the latest `staging` revision.
2. Make one focused change.
3. Run `just check` and the relevant behavioral tests.
4. Open a pull request into `staging`.
5. Review the Vercel preview and required checks.
6. Merge only after the required checks pass and review conversations are resolved.

Release pull requests merge `staging` into `main`. Shared contract changes require review from all affected owners.

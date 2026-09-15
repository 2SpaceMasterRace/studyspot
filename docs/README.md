# StudySpot documentation

The documentation uses Sphinx, MyST Markdown, and the Furo theme. Dependencies are locked independently with uv.

From the repository root:

```shell
just docs
```

The build is written to `docs/build/html/` and served at <http://localhost:7503>.

Run the warning-strict documentation check as part of the complete repository check:

```shell
just check
```

<<<<<<< HEAD
Documentation merged into `main` is published to <https://2spacemasterrace.github.io/studyspot/> by GitHub Pages. Forks must configure Pages to use GitHub Actions as its source.
=======
Documentation is published alongside the staging app at <https://dev-studyspot-nyu.vercel.app/docs/> by Vercel.
>>>>>>> origin/staging

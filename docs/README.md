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

Documentation is published alongside the staging app at <https://dev-studyspot-nyu.vercel.app/docs/> by Vercel.

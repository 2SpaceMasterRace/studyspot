# StudySpot documentation

The documentation uses Sphinx, MyST Markdown, and the Furo theme. Dependencies are locked independently with uv.

From the repository root:

```shell
just docs
just docs-serve
```

The build is written to `docs/build/html/`, and the local server is available at <http://localhost:7504>.

Run the warning-strict documentation check with:

```shell
just check-docs
```

Documentation merged into `main` is published to <https://2spacemasterrace.github.io/studyspot/> by GitHub Pages. Forks must configure Pages to use GitHub Actions as its source.

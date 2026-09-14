"""Sphinx configuration for the StudySpot documentation."""

project = "StudySpot"
author = "StudySpot contributors"
copyright = "2026, StudySpot contributors"

extensions = ["myst_parser"]
source_suffix = {".md": "markdown", ".rst": "restructuredtext"}
exclude_patterns = []

html_theme = "furo"
html_title = "StudySpot documentation"
html_static_path = ["_static"]
html_theme_options = {
    "navigation_with_keys": True,
    "source_repository": "https://github.com/2SpaceMasterRace/studyspot/",
    "source_branch": "main",
    "source_directory": "docs/source/",
    "light_css_variables": {
        "color-brand-primary": "#6f3f2c",
        "color-brand-content": "#6f3f2c",
    },
    "dark_css_variables": {
        "color-brand-primary": "#e8b59f",
        "color-brand-content": "#e8b59f",
    },
}

myst_enable_extensions = ["colon_fence", "deflist", "fieldlist"]
myst_heading_anchors = 3
suppress_warnings = ["myst.header"]

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from scholium import __version__ as ver

# -- Project information -----------------------------------------------------

project = "Scholium"
copyright = "2026, Scholium Contributors"
author = "Scholium Contributors"

# The full version, including alpha/beta/rc tags
# The short Major.Minor.Build version
_v = ver.split(".")
_build = "".join([c for c in _v[2] if c.isdigit()])
version = _v[0] + "." + _v[1] + "." + _build
release = ver


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.todo",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",  # See https://github.com/tox-dev/sphinx-autodoc-typehints/issues/15
    "sphinx_autodoc_typehints",
    "sphinx.ext.coverage",
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",
    "myst_parser",  # For Markdown support
]

autodoc_member_order = "bysource"
autosummary_generate = True  # Turn on sphinx.ext.autosummary
autoclass_content = "both"  # Add __init__ doc (ie. params) to class summaries
html_show_sourcelink = False  # Remove 'view source code' from top of page (for html, not python)
autodoc_inherit_docstrings = True  # If no docstring, inherit from base class
set_type_checking_flag = True  # Enable 'expensive' imports for sphinx_autodoc_typehints
add_module_names = False  # Remove namespaces from class/method signatures

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
source_suffix = [".rst", ".md"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "README*.md",
    "DEPLOYMENT*.md",
    "FORMAT*.md",
    "GITHUB*.md",
]

# MyST settings for Markdown
myst_enable_extensions = [
    "colon_fence",
    "deflist",
]

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "pydata_sphinx_theme"

html_theme_options = {
    "logo": {
        "image_light": "_static/logo-horizontal.svg",
        "image_dark": "_static/logo-horizontal-dark-navbar.svg",
    },
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/ccaprani/scholium",
            "icon": "fab fa-github-square",
        },
    ],
    "use_edit_page_button": True,
    "navigation_depth": 4,
}

html_context = {
    "github_user": "ccaprani",
    "github_repo": "scholium",
    "github_version": "main",
    "doc_path": "docs/",
}

# GitHub Pages configuration
html_baseurl = "https://ccaprani.github.io/scholium/"

html_favicon = "_static/favicon.svg"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# _static: web assets (favicon, CSS, icon PNG)
# brand:   canonical logo SVGs — merged into _static/ at build time
html_static_path = ["_static", "brand"]
html_css_files = ["custom.css"]

# GitHub Pages Setup for Sphinx Documentation

This Sphinx documentation is configured for GitHub Pages deployment.

## Automatic Deployment

The included GitHub Action (`.github/workflows/docs.yml`) automatically:

1. Builds Sphinx HTML documentation
2. Deploys to GitHub Pages
3. Runs on every push to `main` branch

## Setup Steps

### 1. Enable GitHub Pages

In your repository settings:

1. Go to **Settings** → **Pages**
2. Under **Source**, select:
   - Source: **GitHub Actions** (not branch!)
3. Save

### 2. Push to GitHub

```bash
git add .
git commit -m "Add Sphinx documentation"
git push origin main
```

### 3. Wait for Build

- GitHub Action runs automatically
- Check **Actions** tab for build status
- Takes ~2-3 minutes

### 4. Access Documentation

Your docs will be available at:

```
https://ccaprani.github.io/scholium/
```

## Manual Build (Local Testing)

```bash
cd docs
pip install -r requirements-docs.txt
make html
python -m http.server 8000 --directory _build/html
```

Open: http://localhost:8000

## File Structure for GitHub Pages

```
your-repo/
├── .github/
│   └── workflows/
│       └── docs.yml          # Auto-deploy workflow
├── docs/
│   ├── conf.py               # Sphinx config
│   ├── index.rst             # Homepage
│   ├── user/                 # User guides
│   ├── api/                  # API reference
│   ├── Makefile
│   └── requirements-docs.txt
├── .nojekyll                 # Tells GitHub Pages to use Sphinx HTML
└── README.md
```

## Customizing

### Change URL Path

If you want docs at root (`/`) instead of `/scholium/`:

Edit `docs/conf.py`:

```python
# For root path
html_baseurl = 'https://ccaprani.github.io/'

# For subpath (default)
html_baseurl = 'https://ccaprani.github.io/scholium/'
```

### Custom Domain

1. Add `CNAME` file in `docs/` directory:
   ```
   docs.scholium.io
   ```

2. Configure DNS:
   - Type: `CNAME`
   - Name: `docs`
   - Value: `ccaprani.github.io`

3. In repo settings → Pages → Custom domain: `docs.scholium.io`

### Build on PR

The workflow builds on pull requests too, but only deploys from `main`.

## Troubleshooting

### Build Failed

Check Actions tab for error details:
- Missing dependencies? Update `requirements-docs.txt`
- Module import errors? Check `sys.path` in `conf.py`
- RST syntax errors? Validate with `make html` locally

### 404 on GitHub Pages

Check:
1. GitHub Pages is set to "GitHub Actions" (not branch)
2. Workflow completed successfully
3. `.nojekyll` file exists in root
4. Wait 2-3 minutes for propagation

### Links Not Working

Use relative links in RST:

```rst
:doc:`installation`           # Correct
:doc:`/installation`          # Wrong (breaks on subpaths)
```

### Theme Not Loading

GitHub Pages serves from subdirectory. Ensure in `conf.py`:

```python
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'style_external_links': True,
}
```

## Updating Documentation

```bash
# 1. Edit .rst files in docs/
vim docs/user/narration-format.rst

# 2. Test locally
cd docs && make html

# 3. Commit and push
git add docs/
git commit -m "Update narration guide"
git push

# 4. GitHub Action auto-deploys in ~2 minutes
```

## Advantages of GitHub Actions

✅ **Automatic** - No manual upload
✅ **Version control** - Docs in same repo as code
✅ **Preview** - Build on PRs before merge
✅ **Free** - Included with GitHub
✅ **Fast** - ~2 minute builds

## Alternative: Manual Deployment

If you prefer manual control:

```bash
# Build locally
cd docs && make html

# Create gh-pages branch
git checkout --orphan gh-pages
git rm -rf .
cp -r docs/_build/html/* .
touch .nojekyll

# Push to gh-pages
git add .
git commit -m "Deploy docs"
git push origin gh-pages

# Configure Pages to use gh-pages branch
```

But the GitHub Action is much easier!

---

**Your documentation will auto-deploy on every push to main.** 🎉

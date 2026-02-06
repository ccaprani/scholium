# Deployment Guide: Sphinx Docs to GitHub Pages

Quick reference for deploying Scholium documentation.

## Quick Start (3 Steps)

### 1. Enable GitHub Actions

Repository Settings → Pages → Source: **GitHub Actions**

### 2. Push to GitHub

```bash
git add .
git commit -m "Add Sphinx documentation with GitHub Pages"
git push origin main
```

### 3. Access Docs

```
https://yourusername.github.io/scholium/
```

**Done!** Docs auto-deploy on every push.

## What Happens Automatically

1. **Push to main** → Triggers GitHub Action
2. **Action builds** → Runs `make html` in docs/
3. **Action deploys** → Publishes to GitHub Pages
4. **Live in 2-3 min** → Documentation accessible

## Workflow File

Located at: `.github/workflows/docs.yml`

```yaml
name: Build and Deploy Documentation

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

# Builds on push, deploys from main only
```

## Local Testing

Before pushing:

```bash
cd docs
pip install -r requirements-docs.txt
make html
python -m http.server 8000 --directory _build/html
```

## Updating Documentation

```bash
# Edit files
vim docs/user/narration-format.rst

# Test locally
cd docs && make html

# Commit and push
git add docs/
git commit -m "Update docs"
git push

# Auto-deploys in ~2 minutes
```

## Configuration Checklist

- [x] `.github/workflows/docs.yml` - Workflow
- [x] `.nojekyll` - GitHub Pages compatibility
- [x] `docs/conf.py` - Sphinx config
- [x] `docs/requirements-docs.txt` - Dependencies
- [ ] Update username in `conf.py` → `html_baseurl`

## Custom Domain (Optional)

1. Add `docs/CNAME`:
   ```
   docs.scholium.io
   ```

2. DNS CNAME record:
   - Name: `docs`
   - Value: `yourusername.github.io`

3. GitHub: Settings → Pages → Custom domain

## Troubleshooting

### Build fails in Actions

1. Click "Actions" tab
2. Click failed workflow
3. View error details
4. Fix locally, test with `make html`
5. Push fix

### 404 after deployment

- Wait 2-3 minutes for propagation
- Check Actions tab - build must succeed
- Verify Pages source is "GitHub Actions"
- Check `.nojekyll` exists

### Links broken

Use relative RST links:
```rst
:doc:`installation`      # Good
:doc:`/installation`     # Bad
```

## Benefits

✅ **Automatic** - Deploy on every push
✅ **Preview** - Build on PRs before merge
✅ **Free** - Included with GitHub
✅ **Fast** - 2-minute builds
✅ **Version controlled** - Docs with code

## Alternative: Manual gh-pages

If you prefer manual control:

```bash
# Build
cd docs && make html

# Deploy
git checkout gh-pages
cp -r docs/_build/html/* .
git add .
git commit -m "Update docs"
git push origin gh-pages
```

But GitHub Actions is **much** easier!

---

**Everything is configured. Just push to main!** 🚀

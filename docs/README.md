# Scholium Sphinx Documentation

Complete Sphinx documentation for Scholium, configured for **GitHub Pages**, using **Markdown for user guides**.

## 📦 Format: Markdown + RST

✅ **User guides**: Markdown (`.md` files) - More intuitive!
✅ **API reference**: RST (`.rst` files) - Auto-generated from code
✅ **Index**: RST (required by Sphinx)

See [FORMAT_CHOICE.md](FORMAT_CHOICE.md) for why this hybrid approach works best.

## 🚀 Quick Deploy to GitHub Pages

### 1. Enable GitHub Actions

Repository Settings → Pages → Source: **GitHub Actions**

### 2. Push to GitHub

```bash
git add .
git commit -m "Add Sphinx documentation"
git push origin main
```

### 3. Access Docs

```
https://yourusername.github.io/scholium/
```

**Done!** Docs auto-deploy on every push to main.

## 🔧 Local Development

### Build Documentation

```bash
cd docs
pip install -r requirements-docs.txt
make html
```

Output: `_build/html/index.html`

### Preview Locally

```bash
python -m http.server 8000 --directory _build/html
```

Open: http://localhost:8000

### Auto-Rebuild

```bash
pip install sphinx-autobuild
sphinx-autobuild . _build/html
```

## 📚 Documentation Structure

```
docs/
├── conf.py                      # Sphinx config (MyST enabled)
├── index.rst                    # Main index (RST)
├── Makefile                     # Build commands
├── requirements-docs.txt        # sphinx, myst_parser, theme
│
├── .github/workflows/
│   └── docs.yml                 # Auto-deploy to GitHub Pages
│
├── user/                        # User guides (Markdown!)
│   ├── quickstart.md
│   ├── markdown-format.md
│   ├── narration-format.md     ⭐ Complete :::notes::: guide
│   ├── incremental-lists.md    ⭐ Complete >- bullet guide
│   ├── timing-control.md
│   └── tts-providers.md
│
├── api/                         # API reference (RST)
│   ├── cli.rst                 # CLI commands
│   └── modules.rst             # Auto-generated from code
│
├── examples.md                  # Markdown
├── troubleshooting.md           # Markdown
└── contributing.md              # Markdown
```

## 🎯 Key Features

### Markdown for User Guides

All user-facing documentation is in **Markdown** (via MyST parser):
- More intuitive syntax
- Easier to write and maintain
- GitHub renders natively
- Full Sphinx features via `:::` directives

**Example Markdown with Sphinx features:**
```markdown
# Section Title

Regular markdown content.

:::{note}
This is a note using MyST syntax
:::

See [other page](other-file.md) for cross-reference.
```

### Two Essential Guides

**narration-format.md**
- Complete `:::notes:::` block syntax
- Metadata lines with `::` prefix
- All timing directives: `[PRE]`, `[POST]`, `[MIN]`, `[DUR]`, `[PAUSE]`
- Title slide narration
- Common patterns and troubleshooting

**incremental-lists.md**
- Complete `>-` bullet reveal syntax
- How Pandoc generates pages
- Narration segmentation
- Validation and warnings

### Auto-Generated API

API reference stays in **RST** (auto-generated from Python docstrings):
- `api/modules.rst` uses Sphinx autodoc
- Extracts documentation from source code
- Updates automatically when you rebuild

## 🔄 Workflow

### Update User Guides

```bash
# Edit Markdown files
vim docs/user/narration-format.md

# Test locally
cd docs && make html

# Commit and push
git add docs/
git commit -m "Update narration guide"
git push

# Auto-deploys in ~2 minutes
```

### Update API Docs

```bash
# 1. Add/update docstrings in Python source
vim src/unified_parser.py

# 2. Rebuild docs
cd docs && make html

# 3. Autodoc extracts updated documentation
```

## 🎨 MyST Markdown Features

MyST (Markedly Structured Text) provides all Sphinx features in Markdown:

**Admonitions:**
```markdown
:::{note}
This is a note
:::

:::{important}
Pay attention!
:::

:::{warning}
Be careful!
:::
```

**Cross-references:**
```markdown
See [Installation](installation.md) for setup.
See [API](../api/cli.md) for commands.
```

**Code blocks:**
```markdown
​```python
def example():
    return "Syntax highlighting works!"
​```
```

**Math:**
```markdown
Inline: $E = mc^2$

Block:
$$
\int_a^b f(x)\,dx
$$
```

**Definition lists:**
```markdown
**Term**
: Definition of the term
```

## 📊 Statistics

- **17 documentation files**
- **7 user guides** (all in Markdown)
- **2 API reference sections** (RST - auto-generated)
- **4 example lectures**
- **GitHub Actions** auto-deployment

## ✨ Why Markdown?

### Before (All RST)

```rst
Narration Format
================

The ``:::notes:::`` block is where you write narration.

Basic Syntax
------------

Every slide can have notes::

    # Slide
    
    ::: notes
    Narration
    :::

**Important**: Must be lowercase.
```

### After (Markdown with MyST)

```markdown
# Narration Format

The `:::notes:::` block is where you write narration.

## Basic Syntax

Every slide can have notes:

​```markdown
# Slide

::: notes
Narration
:::
​```

**Important**: Must be lowercase.
```

**Much more intuitive!** And it works identically with Sphinx.

## 🐛 Troubleshooting

### Markdown Not Rendering

Check `conf.py` includes:
```python
extensions = [
    ...
    'myst_parser',
]
```

Already configured! ✅

### Cross-References Broken

Use relative paths:
```markdown
[Text](other-file.md)         # ✅ Good
[Text](/other-file.md)        # ❌ Bad (breaks on subpaths)
```

### Admonitions Not Working

Use `:::` fence syntax:
```markdown
:::{note}
Content
:::
```

Not:
```markdown
!!! note
    Content
```

## 🔗 Resources

- **Sphinx**: https://www.sphinx-doc.org
- **MyST Parser**: https://myst-parser.readthedocs.io
- **GitHub Pages**: https://docs.github.com/en/pages

## 📝 Next Steps

1. **Update username** in `conf.py` → `html_baseurl`
2. **Build locally**: `make html`
3. **Test in browser**: Open `_build/html/index.html`
4. **Push to GitHub**: Enable Actions, push, done!

---

**Your Sphinx documentation with Markdown user guides is ready!** 🎉

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for deployment details.

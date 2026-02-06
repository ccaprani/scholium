# Documentation Format: Markdown vs RST

## Current Setup

✅ **User guides**: Markdown (`.md` files)
✅ **API reference**: RST (`.rst` files - auto-generated)
✅ **Index/structure**: RST (Sphinx requirement)

## Why This Works

### Markdown for User Guides

**Advantages:**
- ✅ More intuitive syntax
- ✅ Familiar to most developers
- ✅ Easier to write and maintain
- ✅ Better for prose and explanations
- ✅ GitHub renders natively

**MyST Parser enables:**
- All standard Markdown features
- Sphinx directives with `:::` syntax
- Cross-references
- Admonitions (notes, warnings)
- Math equations
- Everything you need for documentation

**Example:**
```markdown
# Section Title

Regular markdown content here.

:::{note}
This is a note using MyST syntax
:::

See [other page](other-file.md) for more info.
```

### RST for API Reference

**Why keep RST:**
- ✅ Sphinx autodoc requires RST
- ✅ Better for auto-generated content
- ✅ Superior directive system for API docs
- ✅ Users don't edit these files anyway

**Example:**
```rst
.. automodule:: unified_parser
   :members:
   :undoc-members:
```

## File Organization

```
docs/
├── index.rst                    # Main index (RST - structure)
├── conf.py                      # Sphinx config
│
├── user/                        # User guides (Markdown)
│   ├── quickstart.md           ✅
│   ├── markdown-format.md      ✅
│   ├── narration-format.md     ✅
│   ├── incremental-lists.md    ✅
│   ├── timing-control.md       ✅
│   └── tts-providers.md        ✅
│
├── api/                         # API reference (RST)
│   ├── cli.rst                 ✅ (hand-written)
│   └── modules.rst             ✅ (auto-generated)
│
├── examples.md                  ✅ Markdown
├── troubleshooting.md           ✅ Markdown
└── contributing.md              ✅ Markdown
```

## MyST Features Used

### Cross-References

Markdown:
```markdown
See [Narration Format](narration-format.md) for details.
```

RST equivalent:
```rst
See :doc:`narration-format` for details.
```

### Admonitions

Markdown:
```markdown
:::{note}
This is a note
:::

:::{important}
This is important
:::

:::{warning}
This is a warning
:::
```

### Definition Lists

Markdown:
```markdown
**Term**
: Definition of the term
```

### Code Blocks

Markdown:
```markdown
​```python
def example():
    return "Works perfectly!"
​```
```

## No Complications!

MyST parser handles everything seamlessly:
- ✅ Builds with `make html` just like RST
- ✅ GitHub Pages deployment works identically
- ✅ Cross-references between MD and RST work
- ✅ All Sphinx features available
- ✅ Looks identical in final HTML

## Benefits Summary

| Aspect | Markdown | RST |
|--------|----------|-----|
| **User guides** | ✅ Better | ❌ More verbose |
| **API docs** | ❌ Limited | ✅ Excellent |
| **Editing** | ✅ Easier | ❌ Harder |
| **GitHub preview** | ✅ Works | ⚠️ Partial |
| **Sphinx features** | ✅ Via MyST | ✅ Native |

## Recommendation

**Keep this hybrid approach:**
- Write user-facing docs in Markdown
- Keep API reference in RST
- Use RST only for structure (index.rst)

This gives you the best of both worlds!

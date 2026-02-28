# Contributing

Thank you for considering contributing to Scholium!

## Development Setup

### Clone and Install

```bash
git clone https://github.com/ccaprani/scholium.git
cd scholium

python3.11 -m venv venv
source venv/bin/activate

pip install -e ".[dev,piper]"
```

### Run Tests

```bash
pytest
pytest --cov=src --cov=tts_providers
```

### Build Documentation

```bash
cd docs
pip install -r requirements-docs.txt   # first time only
make html
```

### Regenerate Demo Assets

The demo video and GIF (`docs/demo/demo.mp4`, `docs/demo/demo.gif`) are committed
assets — they are **not** rebuilt automatically by `make html`. Regenerate them
manually after changing `docs/demo/lecture.md` or `docs/demo/make_gif.py`,
then rebuild the HTML docs to pick up the new files.

```bash
# Requires the runtime environment (Piper TTS installed)
bash docs/demo/build_demo.sh          # video + GIF (~30 s)
bash docs/demo/build_demo.sh --gif-only  # GIF only (fast, no TTS)

# Then rebuild docs
cd docs && make html
```

## Ways to Contribute

### Documentation

- Fix typos
- Add examples
- Clarify confusing sections
- Add troubleshooting tips

### Code

- Fix bugs
- Implement features
- Add TTS providers
- Improve performance

### Testing

- Add test cases
- Report bugs
- Test on different platforms

## Pull Request Process

1. Fork repository
2. Create feature branch
3. Make changes
4. Add tests
5. Run tests
6. Update documentation
7. Submit pull request

## Code Style

- Follow PEP 8
- Use type hints
- Add docstrings
- Keep functions focused

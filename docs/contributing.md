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
make html
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

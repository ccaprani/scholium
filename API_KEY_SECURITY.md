# API Key Security - IMPORTANT

## ⚠️  Never Commit API Keys

API keys should **NEVER** be stored in `config.yaml` or committed to version control.

## Correct Way to Use API Keys

### ElevenLabs

```bash
# Set environment variable (recommended)
export ELEVENLABS_API_KEY="your_api_key_here"

# Add to shell profile for persistence
echo 'export ELEVENLABS_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

### OpenAI

```bash
# Set environment variable (recommended)
export OPENAI_API_KEY="your_api_key_here"

# Add to shell profile
echo 'export OPENAI_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

## Files to Check Before Publishing

Before publishing or sharing your Scholium project:

1. ✅ **Check config.yaml** - Ensure `api_key: ""` is empty
2. ✅ **Check .gitignore** - Ensure it includes `config.local.yaml` and `*.key`
3. ✅ **Review commit history** - Make sure no keys were ever committed

```bash
# Search for potential API keys in git history
git log -p | grep -i "api_key"
```

## Using config.local.yaml (Optional)

If you really want to use a config file for API keys (not recommended), create `config.local.yaml`:

```yaml
elevenlabs:
  api_key: "your_actual_key"
```

Then load it in your code:
```python
cfg = Config('config.local.yaml')
```

**Important:** `config.local.yaml` is already in `.gitignore` so it won't be committed.

## Why Environment Variables Are Better

✅ **Secure**: Not stored in files that can be accidentally committed  
✅ **Flexible**: Different keys for dev/prod environments  
✅ **Standard**: Industry best practice  
✅ **Automatic**: Config.py already reads them  

## How Scholium Handles API Keys

The `config.py` module automatically reads environment variables:

```python
def _load_env_vars(self):
    # ElevenLabs API key from environment
    env_api_key = os.getenv('ELEVENLABS_API_KEY')
    if env_api_key:
        self.config['elevenlabs']['api_key'] = env_api_key
    
    # OpenAI API key from environment
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if openai_api_key:
        self.config['openai']['api_key'] = openai_api_key
```

So even if `config.yaml` has empty `api_key` values, the environment variables will be used automatically.

## Quick Test

```bash
# Set the key
export ELEVENLABS_API_KEY="test_key_123"

# Check it's loaded
python -c "from src.config import Config; c = Config(); print(c.get('elevenlabs.api_key'))"
# Should output: test_key_123
```

---

**Remember:** API keys are like passwords. Treat them with the same security!

# Install

## Normal user install

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
cp .env.example .env
```

Then edit `.env`, run:

```bash
gemini-telegram check
gemini-telegram run
```

## What this project is not

It does not install Gemini CLI for you.

That part is still on the host machine because Gemini CLI itself is terminal-based and needs its own authentication flow.

## GitHub Pages / website use

The website is docs and onboarding, not a web app replacement for Gemini CLI.

The install story from the site is:

1. Read setup docs
2. Copy install commands
3. Install on your host
4. Run the bridge locally, on a VPS, or on a VM

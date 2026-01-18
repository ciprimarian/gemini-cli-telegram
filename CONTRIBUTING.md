# Contributing

This project is meant to stay understandable from a terminal and from the code.

## Rules of thumb

- small patches beat sweeping rewrites
- keep defaults safe
- if the bot fails, it should say what broke and what to do next
- if a feature needs host-specific setup, document it plainly
- prefer boring reliability over cleverness

## Before you open a change

Run:

```bash
PYTHONPATH=src python -m unittest discover -s tests
python -m compileall src tests
```

If your change touches docs, make sure the docs still read like a person wrote them after a long week, not like a synthetic brochure.

## Commit shape

Good commits:

- one behavior change
- one docs change
- one test addition

Bad commits:

- rename half the project and add features in the same patch
- “misc cleanup”
- “final polish”

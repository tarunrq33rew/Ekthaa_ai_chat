# CodeRabbit Interaction Guide

CodeRabbit is now integrated into the Ekthaa AI Backend to provide automated, context-aware code reviews.

## Review Features
CodeRabbit is configured to:
- **Enforce Framework Logging**: It will remind you to update `progress.txt` for every PR.
- **Check Roadmap Alignment**: It verifies that your code changes match our `ROADMAP.md` goals.
- **Flag Security Issues**: Specifically looks for hardcoded identities (like `demo_user`).

## Common Commands
You can interact with CodeRabbit directly on a Pull Request by mentioning `@coderabbitai`:

- **Summary**: `@coderabbitai summary` - Get a concise summary of the PR.
- **Configuration**: `@coderabbitai configuration` - View current effective settings.
- **Review Again**: `@coderabbitai review` - Trigger a fresh review after push.
- **Generate Tests**: `@coderabbitai generate unit tests` - Ask for test suggestions.
- **Ask Questions**: `@coderabbitai How does this change affect AI latency?`

## GSD x Ralph Integration
CodeRabbit is "aware" of our specific files:
- It reads `CLAUDE.md` for coding style.
- It consults `progress.txt` for historical context.
- it helps maintain the `prd.json` execution state.

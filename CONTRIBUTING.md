# Contributing to Jarvis

Thanks for your interest in improving this project. It's a personal, local-first voice assistant — contributions that keep it lightweight, offline-friendly, and easy to run on modest hardware are especially welcome.

## Getting started

1. Fork the repo and clone your fork
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
3. Make sure [Ollama](https://ollama.com/) is installed and the model is pulled:
   ```bash
   ollama pull llama3.2:3b
   ```

## Making changes

- Create a branch: `git checkout -b feature/your-feature-name`
- Keep changes focused — one feature or fix per pull request
- Test your changes locally before opening a PR (there's no CI microphone in the cloud yet)
- Update the README if you change setup steps, dependencies, or usage

## Reporting issues

Open a GitHub issue with:
- Your OS and hardware (CPU/RAM/GPU)
- Python version
- Steps to reproduce
- Full error output if applicable

## Code style

- Keep functions small and readable
- Prefer clear variable names over cleverness — this is a hobby project meant to be hackable

# Contributing to Sentinel

Thanks for helping improve Sentinel.

## Before changing code

- Read the product principles and implementation roadmap in the repository.
- Keep setup understandable for first-time users and provide advanced options for experienced operators.
- Never commit `.env` files, API keys, vault keys, credentials, databases, or private keys.
- Prefer protocol-based connector implementations and preserve the original source message when translating events.

## Local development

Core runs from `core/` using its Python virtual environment. The dashboard runs from `frontend/` with `npm install` and `npm run dev`. See the README and `core/OPERATIONS.md` for current setup details.

## Changes and reports

Use the issue templates for bugs and feature requests. Keep pull requests focused and describe the user-visible behavior, deployment impact, and validation performed.

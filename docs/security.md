# SatQuery AI — Security Policy & Guidelines

## Secret Protection
- Never commit `.env` or API keys.
- `Settings` fields use `repr=False` to prevent logging secrets in stack traces.

## File Upload Security
- Strict extension whitelist (`.tif`, `.tiff`, `.png`, `.jpg`).
- Uploads assigned random UUID internal filenames.
- Path traversal protection enforced in `app/core/security.py`.
- Binary uploads are treated as non-executable data.

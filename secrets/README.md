# secrets/

Local credentials. **Nothing here is committed** except this file and `.env.example`.

`.gitignore` ignores `secrets/*` and re-includes only the two tracked files, so
anything you drop in this folder stays on your machine.

## Setup

```bash
cp secrets/.env.example secrets/.env
```

Then open `secrets/.env` and set `BCCH_TOKEN`.

Get the token from [si3.bcentral.cl](https://si3.bcentral.cl) → **Mi Cuenta** →
**Apikey Token**. It is valid for one year. The legacy `BCCH_USER` /
`BCCH_PASSWORD` pair still works if you prefer it, but BCCh recommends the token
for the REST API.

## Verify it is invisible to git

```bash
git status --short
```

`secrets/.env` must not appear. To check a specific file:

```bash
git check-ignore -v secrets/.env
```

That should print the matching `.gitignore` rule. If it prints nothing, **stop**
— the file is not ignored.

## Notes

- `secrets/token.txt` is also ignored, if you keep a bare token file there.
- The pipeline reads `secrets/.env` first, then falls back to a repo-root `.env`.
- Plain environment variables take precedence over both, so you can set
  `BCCH_TOKEN` in your shell profile and keep nothing on disk at all.
- If a credential is ever committed by accident, rotate it — removing the file
  in a later commit does not remove it from history.

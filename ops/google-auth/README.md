# Google OAuth (consumer Gmail) — audit + reauth helpers

This folder contains two things:

1) `audit_google_oauth.py`: offline audit of local OAuth setup (tokens/creds) to flag likely fragility
2) `google_reauth.sh`: a single headless-friendly reauth runner for Gmail + Drive + Docs + Sheets + Calendar

## Why
On consumer Gmail, access tokens always expire quickly. Stability comes from:
- having refresh tokens (`refresh_token` present)
- keeping OAuth consent screen in Production (outside this VM; cannot be audited locally)
- avoiding credential/client churn

## Run audit

```bash
python3 /home/desazure/.openclaw/workspace/ops/google-auth/audit_google_oauth.py
```

## Reauth (headless)

### Recommended for consumer Gmail: loopback redirect + SSH tunnel

1) On your laptop (separate terminal), start the tunnel:

```bash
ssh -N -L 18793:127.0.0.1:18793 <vm-ssh>
```

2) On the VM, run:

```bash
bash /home/desazure/.openclaw/workspace/ops/google-auth/google_reauth.sh assistantdesi@gmail.com interactive
```

### Laptop helper (guided)

If you want a guided laptop-side helper that prints the tunnel command, waits for confirmation, then kicks off the VM reauth:

```bash
# run on your laptop
./laptop_google_reauth.sh <vm-ssh> assistantdesi@gmail.com
```

Tip: `print-url-only` mode can be used to sanity-check without blocking:

```bash
bash /home/desazure/.openclaw/workspace/ops/google-auth/google_reauth.sh assistantdesi@gmail.com print-url-only
```

# Manual GitHub Copilot (Entra SSO) auth for OpenClaw

This note captures how to manually (re)authenticate OpenClaw to use the **GitHub Copilot** provider (e.g. `github-copilot/gpt-5.2`).

> The “Entra” part is typically enforced by your GitHub org (SAML/SSO). OpenClaw itself uses GitHub’s **device login flow** to obtain a `ghu_...` token; during approval you may be redirected through Entra SSO.

---

## Recommended method: OpenClaw device flow

Run in an interactive terminal (TTY required) on the VM:

```bash
openclaw models auth login-github-copilot
```

What happens:
- A URL + one-time code is printed
- Open the URL in a browser, enter the code, and approve access (SSO/Entra may be required)
- OpenClaw stores a token in:
  - `/home/desazure/.openclaw/agents/main/agent/auth-profiles.json`
  - profile id defaults to `github-copilot:github`

### Optional: separate profile id

```bash
openclaw models auth login-github-copilot --profile-id github-copilot:work
```

### Optional: overwrite without prompting

```bash
openclaw models auth login-github-copilot --yes
```

---

## Set the default model

```bash
openclaw models set github-copilot/gpt-5.2
```

---

## Alternative (only if you already have a token): paste token

If you already have a valid `ghu_...` token and just want OpenClaw to use it:

```bash
openclaw models auth paste-token
```

---

## Verification (no secrets)

Check that the auth profile exists:

```bash
cat /home/desazure/.openclaw/agents/main/agent/auth-profiles.json
```

Then run a quick model call (or just use the bot normally) and confirm no auth errors.

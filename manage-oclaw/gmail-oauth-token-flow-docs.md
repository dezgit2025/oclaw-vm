# Google OAuth Token Flow for oclaw VM

How the Google Drive OAuth authentication works for the openclaw VM, step by step.

## Overview

The oclaw VM needs access to Google Drive (openclawshared). Since the VM has no browser,
we use an SSH tunnel to route the Google OAuth redirect from the VM back to your Mac,
where you can complete the sign-in in a browser.

```
+----------------+          SSH Tunnel           +------------------+
|   Your Mac     | <=========================>   |   oclaw VM       |
|                |    ports 18792-18794           |                  |
|  Browser       |                                |  auth.py script  |
|  localhost:    |                                |  listens on      |
|    18794       |                                |    127.0.0.1:    |
|                |                                |      18794       |
+----------------+                                +------------------+
```

## The Three Key Files

```
On the VM (~/.config/openclaw-gdrive/):

  credentials.json                  <-- You provide this (from Google Cloud Console)
  |                                      Contains: client_id, client_secret
  |                                      Type: "Desktop app" OAuth client
  |
  +---> auth.py reads this
  |     to start the OAuth flow
  |
  v
  token-openclawshared.json         <-- auth.py creates this after successful auth
                                         Contains: access_token, refresh_token
                                         Used by: openclaw services to call Drive API
```

## Step-by-Step Flow

### Step 1: Start the SSH Tunnel

```
Your Mac                                         oclaw VM
========                                         ========

create-manage-tunnel-oclaw.py start

  ssh -N -L 18794:127.0.0.1:18794 oclaw
       |
       +-- This means:
           "Anything connecting to localhost:18794 on my Mac
            gets forwarded to 127.0.0.1:18794 on the VM"

Result:
  Mac:18794  <=== tunnel ===>  VM:18794
```

### Step 2: Run the Auth Script on the VM

```
oclaw VM
========

run-gdrive-auth.sh
  |
  v
auth.py starts up
  |
  +-- Reads credentials.json (client_id + client_secret)
  |
  +-- Checks if token-openclawshared.json already exists
  |     |
  |     +-- If yes and valid  --> refreshes token, done
  |     +-- If yes and expired --> uses refresh_token to get new access_token, done
  |     +-- If no / invalid   --> starts OAuth flow (continue to Step 3)
  |
  +-- Starts a local HTTP server on 127.0.0.1:18794
  |
  +-- Prints a Google auth URL to the terminal
  |
  v
  "Please visit this URL to authorize this application:
   https://accounts.google.com/o/oauth2/auth?client_id=...&redirect_uri=http://127.0.0.1:18794/..."

  Waiting for redirect...
```

### Step 3: You Open the URL in Your Browser

```
Your Mac (Browser)                    Google Servers
==================                    ==============

You paste the URL into
an incognito browser
         |
         +------- HTTPS -------->  Google sign-in page
                                        |
                                   "Choose account"
                                   You pick: desi4k@gmail.com
                                        |
                                   "Grant access to Google Drive?"
                                   You click: Allow
                                        |
                                        v
                                   Google says:
                                   "OK, here's an authorization code.
                                    Redirecting to: http://127.0.0.1:18794/?code=AUTH_CODE"
```

### Step 4: The Redirect Travels Through the Tunnel

This is the key part. Google redirects your browser to `localhost:18794`, but the
auth script is listening on port 18794 on the **VM**, not your Mac. The SSH tunnel
bridges the gap:

```
Browser on Mac              SSH Tunnel              auth.py on VM
==============              ==========              =============

GET http://127.0.0.1:
  18794/?code=AUTH_CODE
         |
         +-- connects to
             localhost:18794
             on your Mac
                  |
                  +-- tunnel forwards
                      to 127.0.0.1:18794
                      on the VM
                           |
                           +-- auth.py receives
                               the AUTH_CODE
                               |
                               v
                          "Got the code!"
```

### Step 5: Auth Script Exchanges Code for Tokens

```
auth.py on VM                                     Google Servers
=============                                     ==============

auth.py takes the AUTH_CODE
and sends it to Google
along with client_id +
client_secret
         |
         +------- HTTPS -------->  Google token endpoint
                                   https://oauth2.googleapis.com/token
                                        |
                                   Validates:
                                     - AUTH_CODE is valid
                                     - client_id matches
                                     - client_secret matches
                                        |
                                        v
                                   Returns:
         <------- HTTPS --------+    {
                                       "access_token":  "ya29.xxx...",
                                       "refresh_token": "1//0xxx...",
                                       "expires_in":    3599,
                                       "token_type":    "Bearer"
                                     }
```

### Step 6: Token Saved

```
auth.py on VM
=============

Writes token to:
  ~/.config/openclaw-gdrive/token-openclawshared.json

Contents:
  {
    "token":         "ya29.xxx...",     <-- access token (expires in ~1 hour)
    "refresh_token": "1//0xxx...",      <-- refresh token (long-lived)
    "client_id":     "xxx.apps...",
    "client_secret": "GOCSPx-xxx...",
    "scopes":        ["https://www.googleapis.com/auth/drive"]
  }

Prints: "OK: wrote token to ~/.config/openclaw-gdrive/token-openclawshared.json"

Browser shows: "The authentication flow has completed. You may close this window."
```

## Complete Flow Diagram

```
  YOUR MAC                          SSH TUNNEL                      OCLAW VM                        GOOGLE
  ========                          ==========                      ========                        ======

  1. Start tunnel
     ssh -N -L 18794:
     127.0.0.1:18794 oclaw -------- tunnel established ----------->

                                                                    2. Run auth.py
                                                                       Reads credentials.json
                                                                       Starts server on :18794
                                                                       Prints auth URL

  3. Open URL in browser ----------------------------------------------------------- HTTPS -------> Sign-in page
                                                                                                    User approves
  4. Browser receives redirect <----------------------------------------------------- 302 --------- redirect to
     to localhost:18794/?code=XXX                                                                   localhost:18794

  5. Browser connects to
     localhost:18794 -------------- forwarded through tunnel -----> 6. auth.py receives code

                                                                    7. auth.py exchanges code ---- HTTPS -------> Token endpoint
                                                                                                                  Validates
                                                                    8. Receives tokens <--------- HTTPS --------- Returns tokens

                                                                    9. Saves token JSON file
                                                                       Prints "OK"

  10. Browser shows
      "auth complete"
```

## Token Lifecycle

```
                     +------------------+
                     | credentials.json |  (permanent, you manage this)
                     | client_id        |
                     | client_secret    |
                     +--------+---------+
                              |
                    First run / token missing
                              |
                              v
                     +------------------+
                     |   OAuth Flow     |  (interactive, needs browser)
                     |   (Steps 1-10)  |
                     +--------+---------+
                              |
                              v
                     +------------------+
                     | token JSON       |  (auto-managed)
                     | access_token     |--- expires in ~1 hour
                     | refresh_token    |--- long-lived (months/years)
                     +--------+---------+
                              |
             +----------------+----------------+
             |                                 |
        Token valid                    Token expired
             |                                 |
             v                                 v
     Use access_token              Use refresh_token to
     for Drive API calls           get new access_token
                                   (automatic, no browser needed)
                                         |
                                         v
                                  Refresh token revoked?
                                   /              \
                                 No                Yes
                                  |                  |
                                  v                  v
                           Keep using it      Re-run OAuth flow
                                              (back to Steps 1-10)
```

## When Do You Need to Re-Auth?

| Scenario | Action Needed |
|----------|---------------|
| Token file deleted | Re-run auth flow |
| Refresh token revoked (Google Account > Security > Third-party apps) | Re-run auth flow |
| OAuth scopes changed in auth.py | Re-run auth flow |
| credentials.json replaced with new client | Re-run auth flow |
| Access token expired (normal) | Nothing -- auto-refreshes using refresh_token |
| VM rebooted | Nothing -- token file persists on disk |
| SSH tunnel restarted | Nothing -- only needed during auth flow, not for API calls |

## Security Notes

- **credentials.json** contains your OAuth client secret. Don't commit it to git.
- **token JSON** contains access and refresh tokens. Don't commit it to git.
- The auth flow uses `http://127.0.0.1:18794` (not HTTPS) which is safe because:
  - Traffic only goes over localhost on both ends
  - The SSH tunnel encrypts everything between your Mac and the VM
  - Google explicitly allows localhost redirects for Desktop app OAuth clients
- Use an **incognito window** for the auth URL to ensure you sign in with the correct account.

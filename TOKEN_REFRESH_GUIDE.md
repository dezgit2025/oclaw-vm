# Azure AD Token Refresh Guide

## TL;DR

**You don't need to manually refresh tokens.** The Azure Identity library does it automatically.

---

## How It Works

### The Setup

```python
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()

client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint="https://pitchbook-resource.openai.azure.com/",
    azure_ad_token_provider=lambda: credential.get_token(
        "https://cognitiveservices.azure.com/.default"
    ).token
)
```

### What Happens Behind the Scenes

```
Your Code                  Azure Identity             Azure AD
   │                            │                        │
   ├─ Make API call ────────────>│                        │
   │                             ├─ Check token          │
   │                             ├─ Token valid?         │
   │                             │  ├─ Yes: Use cached   │
   │                             │  └─ No: Request new ─>│
   │                             │                        ├─ Validate identity
   │                             │<── Fresh token ────────┤
   │<── API response ────────────┤                        │
   │                             │                        │
   ├─ Make another call ─────────>│                        │
   │                             ├─ Check token          │
   │                             ├─ Still valid!         │
   │<── API response ────────────┤ (use cached)          │
   │                             │                        │
```

**Key Points:**
- Token expiration: ~60 minutes
- Auto-refresh: ~5 minutes before expiration
- Caching: Tokens are cached to avoid hitting Azure AD constantly
- Your code: Just keeps working!

---

## Usage Patterns

### Pattern 1: Create Once, Use Many Times (Recommended)

```python
# Create client at application startup
client = create_client()

# Reuse for hours/days - tokens refresh automatically
for i in range(1000):
    response = client.chat.completions.create(...)
    # Token automatically refreshes when needed!
```

**✓ Best for:**
- Long-running services
- Web applications
- Batch processing
- CLI tools

### Pattern 2: Create Per Request (Also Fine)

```python
def process_request(user_input):
    # New client for each request
    client = create_client()
    response = client.chat.completions.create(...)
    return response
```

**✓ Best for:**
- Serverless functions (AWS Lambda, Azure Functions)
- Short-lived scripts
- When you want fresh credentials

**Note:** Slightly slower due to credential initialization, but still works great.

### Pattern 3: Credential Reuse (Advanced)

```python
# Create credential once
credential = DefaultAzureCredential()

# Create multiple clients with same credential
openai_client = AzureOpenAI(
    azure_endpoint="...",
    azure_ad_token_provider=lambda: credential.get_token(...).token
)

# Can reuse credential for other Azure services too
storage_client = BlobServiceClient(
    account_url="...",
    credential=credential
)
```

**✓ Best for:**
- Multi-service applications
- Optimizing credential acquisition
- Advanced scenarios

---

## Do I Ever Need to Manually Refresh?

**Short answer: No.**

**Long answer:**
- `credential.get_token()` handles refresh automatically
- The lambda is called before each API request
- Tokens are cached and only refreshed when needed
- You never touch the token directly

### When Tokens Become Invalid

The only times you might see authentication errors:

1. **Managed Identity disabled** - Re-enable in Azure Portal
2. **Permissions revoked** - Re-grant IAM role
3. **Azure AD outage** - Wait and retry (very rare)
4. **Code is running outside Azure** - Use `az login` or service principal

The library handles transient failures with built-in retries.

---

## Troubleshooting: "Token Expired" Errors

If you somehow see token expiration errors:

### Quick Fix
```python
# Recreate the credential and client
credential = DefaultAzureCredential()
client = AzureOpenAI(
    azure_endpoint="...",
    azure_ad_token_provider=lambda: credential.get_token(
        "https://cognitiveservices.azure.com/.default"
    ).token
)
```

### Diagnostic Code
```python
from azure.identity import DefaultAzureCredential

# Test credential directly
credential = DefaultAzureCredential()

try:
    token = credential.get_token("https://cognitiveservices.azure.com/.default")
    print(f"✓ Token acquired")
    print(f"  Expires: {token.expires_on}")

    # Check if token is valid
    import time
    if token.expires_on > time.time():
        print(f"  Valid for: {int((token.expires_on - time.time()) / 60)} minutes")
    else:
        print(f"  ✗ Token already expired!")

except Exception as e:
    print(f"✗ Failed to get token: {e}")
```

---

## Best Practices

### ✓ DO:
- Create client once and reuse it
- Let automatic token refresh handle everything
- Use `DefaultAzureCredential` (tries multiple auth methods)
- Trust the built-in caching and refresh logic

### ✗ DON'T:
- Manually manage tokens
- Create new clients for every API call (unless serverless)
- Store tokens yourself
- Try to predict token expiration
- Implement your own refresh logic

---

## Example: Web Application

```python
from flask import Flask
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential

app = Flask(__name__)

# Create client at startup - reuse for all requests
credential = DefaultAzureCredential()
openai_client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint="https://pitchbook-resource.openai.azure.com/",
    azure_ad_token_provider=lambda: credential.get_token(
        "https://cognitiveservices.azure.com/.default"
    ).token
)

@app.route('/chat', methods=['POST'])
def chat():
    # Use the same client for all requests
    # Tokens refresh automatically in the background
    response = openai_client.chat.completions.create(
        model="gpt-5.2",
        messages=[{"role": "user", "content": request.json['message']}],
        max_completion_tokens=500
    )

    return {"response": response.choices[0].message.content}

# Client lives for the entire application lifetime
# Tokens refresh automatically as needed
# No manual refresh required!
```

---

## Summary

| Aspect | Details |
|--------|---------|
| **Manual refresh needed?** | ❌ No |
| **Token lifetime** | ~60 minutes |
| **Refresh timing** | Automatic, ~5 minutes before expiration |
| **Caching** | ✅ Built-in |
| **Your action** | Nothing - just use the client |
| **Long-running apps** | ✅ Fully supported |
| **Cost** | Token acquisition is free |

**Bottom line:** Create your client once, use it forever. Token refresh is automatic.

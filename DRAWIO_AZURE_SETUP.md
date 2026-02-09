# Next AI Draw.io with Azure OpenAI GPT-5.2

AI-powered draw.io application using **Azure OpenAI GPT-5.2** instead of Anthropic Claude.

---

## Quick Start (3 Methods)

### Method 1: Shell Script (Easiest) ⭐

```bash
./run_drawio_azure.sh
```

**Setup first:** provide your Azure OpenAI credentials via environment variables (recommended: use the included env file template).

Access at: **http://localhost:3000**

---

### Method 2: Docker Command (Direct)

```bash
docker run -d \
  --name next-ai-drawio-azure \
  -p 3000:3000 \
  -e AI_PROVIDER=azure \
  -e AI_MODEL=gpt-5.2 \
  -e AZURE_API_KEY=YOUR_AZURE_OPENAI_API_KEY \
  -e AZURE_BASE_URL=https://pitchbook-resource.openai.azure.com \
  -e TEMPERATURE=0 \
  ghcr.io/dayuanjiang/next-ai-draw-io:latest
```

---

### Method 3: Docker Compose (Recommended for Production)

**Setup:**
```bash
# 1. Copy the example env file
cp .env.azure-drawio.example .env.azure-drawio

# 2. Edit and set AZURE_API_KEY
nano .env.azure-drawio

# 3. Start the container
docker-compose -f docker-compose.azure-drawio.yml --env-file .env.azure-drawio up -d
```

**Manage:**
```bash
# View logs
docker-compose -f docker-compose.azure-drawio.yml logs -f

# Stop
docker-compose -f docker-compose.azure-drawio.yml down

# Restart
docker-compose -f docker-compose.azure-drawio.yml restart
```

---

## Configuration Details

### Azure OpenAI Environment Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `AI_PROVIDER` | `azure` | Use Azure OpenAI (not OpenAI or Anthropic) |
| `AI_MODEL` | `gpt-5.2` | Your Azure deployment name |
| `AZURE_API_KEY` | `...` | Your Azure OpenAI API key |
| `AZURE_BASE_URL` | `https://pitchbook-resource.openai.azure.com` | Your Azure endpoint |
| `TEMPERATURE` | `0` | 0=deterministic (recommended for diagrams) |

### Entra ID (Azure AD) token auth

The draw.io container image referenced here is configured for API key auth (`AZURE_API_KEY`). If you need Entra ID token-based auth, use the Python samples in this repo (for example, `test_azure_openai_managed_identity.py`) or rebuild the upstream app to use `azure_ad_token_provider`.

### Optional Advanced Settings

```bash
# Reasoning effort (for models that support reasoning)
AZURE_REASONING_EFFORT=medium  # Options: low, medium, high

# Reasoning summary
AZURE_REASONING_SUMMARY=brief   # Options: none, brief, detailed
```

---

## Azure OpenAI vs Anthropic Claude

### Why Use Azure OpenAI?

✅ **Advantages:**
- Enterprise security & compliance
- Integration with Azure ecosystem
- Predictable pricing through Azure
- Data stays in your Azure tenant
- You already have it set up!

### Model Comparison

| Feature | Azure GPT-5.2 | Anthropic Claude |
|---------|---------------|------------------|
| **Diagram training** | ⚠️ Limited | ✅ Trained on draw.io |
| **Cloud logos** | ⚠️ Generic | ✅ AWS/Azure/GCP logos |
| **Text quality** | ✅ Excellent | ✅ Excellent |
| **Cost** | $$$ (varies by region) | $$$ (per token) |
| **Your setup** | ✅ Already working | ❌ Need API key |

**Note:** According to the project docs, Claude models are specifically trained on draw.io diagrams with cloud architecture logos (AWS, Azure, GCP). If you're creating cloud architecture diagrams, Claude might produce better results. However, GPT-5.2 should still work well for general diagrams.

---

## Useful Docker Commands

### View Container Status
```bash
docker ps | grep next-ai-drawio-azure
```

### View Logs
```bash
# All logs
docker logs next-ai-drawio-azure

# Follow logs (live)
docker logs -f next-ai-drawio-azure

# Last 50 lines
docker logs --tail 50 next-ai-drawio-azure
```

### Manage Container
```bash
# Stop
docker stop next-ai-drawio-azure

# Start (after stopped)
docker start next-ai-drawio-azure

# Restart
docker restart next-ai-drawio-azure

# Remove
docker rm -f next-ai-drawio-azure
```

---

## Troubleshooting

### Container Won't Start

**Check logs:**
```bash
docker logs next-ai-drawio-azure
```

**Common issues:**

1. **Port already in use**
   ```bash
   # Change port in script or docker command
   docker run -d -p 3001:3000 ...  # Use port 3001 instead
   ```

2. **Azure API authentication error**
   - Verify your API key is correct
   - Check endpoint URL matches your Azure resource
   - Confirm deployment name "gpt-5.2" exists

3. **Can't reach Azure endpoint**
   ```bash
   # Test connectivity
   curl https://pitchbook-resource.openai.azure.com/
   ```

### Test Azure Connection Directly

```bash
# Run the test script we created earlier
python3 test_azure_openai_managed_identity.py
```

### Application Not Loading

```bash
# Check if container is running
docker ps | grep next-ai-drawio-azure

# Check application logs
docker logs -f next-ai-drawio-azure

# Try accessing from inside container
docker exec next-ai-drawio-azure curl -f http://localhost:3000
```

### "Deployment not found" Error

- Verify your deployment name in Azure Portal:
  - Go to Azure OpenAI resource
  - Click "Model deployments"
  - Confirm "gpt-5.2" exists
  - If different, update `AI_MODEL` to match

---

## On Azure Linux VM

### Open Port in Network Security Group

**Via Azure Portal:**
1. Go to VM → **Networking** → **Network settings**
2. **Add inbound port rule**
   - Port: **3000**
   - Protocol: **TCP**
   - Action: **Allow**
   - Name: **AllowDrawIO**

**Via Azure CLI:**
```bash
az vm open-port \
  --resource-group YOUR_RESOURCE_GROUP \
  --name YOUR_VM_NAME \
  --port 3000
```

### Access from Internet

```bash
# Get VM public IP
az vm list-ip-addresses -g YOUR_RESOURCE_GROUP -n YOUR_VM_NAME --query "[].virtualMachine.network.publicIpAddresses[0].ipAddress" -o tsv

# Access at: http://YOUR_PUBLIC_IP:3000
```

### Security Recommendations

For production on Azure VM:

1. **Use HTTPS** - Set up nginx reverse proxy with SSL
2. **Restrict access** - Configure NSG to allow only specific IPs
3. **Use Azure AD authentication** - Instead of API keys (we tested this!)
4. **Use Private Link** - For internal-only access
5. **Enable logging** - Azure Monitor for container logs

---

## Cost Estimation

Azure OpenAI GPT-5.2 pricing (approximate, varies by region):
- Input: ~$3-5 per million tokens
- Output: ~$15-20 per million tokens

**Example usage:**
- 1000 diagram generations/month
- ~500 tokens average per diagram
- **Estimated cost: $5-15/month**

💡 **Tip:** Monitor usage in Azure Portal → OpenAI resource → Metrics

---

## Comparing with Anthropic Version

We created both versions for you:

| File | Provider | Notes |
|------|----------|-------|
| `run_drawio_azure.sh` | Azure OpenAI | ✅ Ready to use with your credentials |
| `run_drawio_container.sh` | Anthropic | Needs Anthropic API key |
| `docker-compose.azure-drawio.yml` | Azure OpenAI | Production-ready |
| `docker-compose.drawio.yml` | Anthropic | Production-ready |

**Recommendation:** Start with Azure since you already have it working. If you need better cloud architecture diagram generation, try Anthropic Claude.

---

## Testing the Setup

### Quick Test

```bash
# 1. Start container
./run_drawio_azure.sh

# 2. Wait 10 seconds for startup
sleep 10

# 3. Check if it's responding
curl http://localhost:3000

# 4. Open in browser
open http://localhost:3000  # macOS
# OR visit http://localhost:3000 in your browser
```

### Test Diagram Generation

1. Open http://localhost:3000
2. Enter a prompt like: "Create a simple flowchart with Start, Process, Decision, and End nodes"
3. Click "Generate"
4. Should see diagram appear using GPT-5.2

---

## Switching Between Azure and Anthropic

You can run both containers simultaneously on different ports:

```bash
# Azure on port 3000
docker run -d -p 3000:3000 \
  -e AI_PROVIDER=azure \
  -e AI_MODEL=gpt-5.2 \
  -e AZURE_API_KEY=... \
  -e AZURE_BASE_URL=... \
  --name drawio-azure \
  ghcr.io/dayuanjiang/next-ai-draw-io:latest

# Anthropic on port 3001
docker run -d -p 3001:3000 \
  -e AI_PROVIDER=anthropic \
  -e AI_MODEL=claude-sonnet-4-5 \
  -e ANTHROPIC_API_KEY=... \
  --name drawio-anthropic \
  ghcr.io/dayuanjiang/next-ai-draw-io:latest
```

Then compare results at:
- Azure: http://localhost:3000
- Anthropic: http://localhost:3001

---

## Files Created

| File | Purpose |
|------|---------|
| `run_drawio_azure.sh` | ⭐ Quick start script (Azure) |
| `.env.azure-drawio.example` | Environment template (Azure) |
| `docker-compose.azure-drawio.yml` | Docker Compose config (Azure) |
| `DRAWIO_AZURE_SETUP.md` | This documentation |

---

## References

- [Next AI Draw.io GitHub](https://github.com/DayuanJiang/next-ai-draw-io)
- [AI Providers Documentation](https://github.com/DayuanJiang/next-ai-draw-io/blob/main/docs/ai-providers.md)
- [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)

---

## Next Steps

1. ✅ Run the container: `./run_drawio_azure.sh`
2. ✅ Access the app: http://localhost:3000
3. 🎨 Start creating AI-powered diagrams with GPT-5.2!

**Questions?** Check the troubleshooting section or container logs.

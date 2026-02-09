# Next AI Draw.io Docker Setup

AI-powered draw.io application using Claude Sonnet 4.5

---

## Quick Start (3 Methods)

### Method 1: Shell Script (Easiest)

```bash
# Set your API key
export ANTHROPIC_API_KEY='your_actual_anthropic_api_key_here'

# Run the script
./run_drawio_container.sh
```

Access at: **http://localhost:3000**

---

### Method 2: Docker Command (Direct)

```bash
docker run -d \
  --name next-ai-drawio \
  -p 3000:3000 \
  -e AI_PROVIDER=anthropic \
  -e AI_MODEL=claude-sonnet-4-5 \
  -e ANTHROPIC_API_KEY='your_actual_key_here' \
  ghcr.io/dayuanjiang/next-ai-draw-io:latest
```

---

### Method 3: Docker Compose (Recommended for Production)

**Setup:**
```bash
# 1. Copy the example env file
cp .env.drawio.example .env.drawio

# 2. Edit .env.drawio with your actual API key
nano .env.drawio  # or use vim, code, etc.

# 3. Start the container
docker-compose -f docker-compose.drawio.yml --env-file .env.drawio up -d
```

**Manage:**
```bash
# View logs
docker-compose -f docker-compose.drawio.yml logs -f

# Stop
docker-compose -f docker-compose.drawio.yml down

# Restart
docker-compose -f docker-compose.drawio.yml restart

# Update to latest version
docker-compose -f docker-compose.drawio.yml pull
docker-compose -f docker-compose.drawio.yml up -d
```

---

## Getting an Anthropic API Key

1. Go to: https://console.anthropic.com/
2. Sign in or create account
3. Navigate to: **API Keys** section
4. Click: **Create Key**
5. Copy the key (starts with `sk-ant-...`)

⚠️ **Security:** Never commit API keys to git!

---

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_PROVIDER` | `anthropic` | AI provider (anthropic recommended) |
| `AI_MODEL` | `claude-sonnet-4-5` | Claude model to use |
| `ANTHROPIC_API_KEY` | *required* | Your Anthropic API key |
| `PORT` | `3000` | Port to expose (host side) |

### Available Models

- `claude-sonnet-4-5` (recommended - best balance)
- `claude-opus-4-5` (most capable, slower/costlier)
- `claude-haiku-4-5` (fastest, most economical)

To change model:
```bash
# In shell script: edit AI_MODEL variable
# In .env.drawio: change AI_MODEL=claude-opus-4-5
# In docker command: change -e AI_MODEL=claude-opus-4-5
```

---

## Useful Docker Commands

### View Container Status
```bash
docker ps | grep next-ai-drawio
```

### View Logs
```bash
# All logs
docker logs next-ai-drawio

# Follow logs (live)
docker logs -f next-ai-drawio

# Last 100 lines
docker logs --tail 100 next-ai-drawio
```

### Manage Container
```bash
# Stop
docker stop next-ai-drawio

# Start (after stopped)
docker start next-ai-drawio

# Restart
docker restart next-ai-drawio

# Remove
docker rm -f next-ai-drawio
```

### Update to Latest Version
```bash
# Pull latest image
docker pull ghcr.io/dayuanjiang/next-ai-draw-io:latest

# Remove old container
docker rm -f next-ai-drawio

# Run new container (use any method above)
./run_drawio_container.sh
```

---

## Troubleshooting

### Port Already in Use

**Error:** `Bind for 0.0.0.0:3000 failed: port is already allocated`

**Solution:** Change the port
```bash
# Method 1: Shell script - edit PORT variable in run_drawio_container.sh

# Method 2: Docker command - change port mapping
docker run -d -p 3001:3000 ...  # Maps host 3001 to container 3000

# Method 3: Docker compose - edit PORT in .env.drawio
PORT=3001
```

### Container Won't Start

**Check logs:**
```bash
docker logs next-ai-drawio
```

**Common issues:**
1. Invalid API key → Check `ANTHROPIC_API_KEY`
2. Port conflict → Change port (see above)
3. Image not pulled → Run `docker pull ghcr.io/dayuanjiang/next-ai-draw-io:latest`

### Can't Access http://localhost:3000

**Checks:**
```bash
# 1. Is container running?
docker ps | grep next-ai-drawio

# 2. Check port mapping
docker port next-ai-drawio

# 3. Test from inside container
docker exec next-ai-drawio curl -f http://localhost:3000

# 4. Check firewall (if on remote server)
curl http://localhost:3000
```

### API Key Not Working

**Verify key:**
```bash
# Check if key is set
docker exec next-ai-drawio env | grep ANTHROPIC_API_KEY

# Should show: ANTHROPIC_API_KEY=sk-ant-...
```

**Test key directly:**
```bash
curl https://api.anthropic.com/v1/messages \
  -H "anthropic-version: 2023-06-01" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "content-type: application/json" \
  -d '{"model":"claude-sonnet-4-5-20250514","messages":[{"role":"user","content":"test"}],"max_tokens":10}'
```

---

## On Azure Linux VM

### Open Port in Network Security Group

If running on Azure VM, allow inbound traffic:

**Via Azure Portal:**
1. Go to VM → **Networking** → **Network settings**
2. Click **Add inbound port rule**
3. Set:
   - Destination port: **3000** (or your custom port)
   - Protocol: **TCP**
   - Action: **Allow**
   - Name: **AllowDrawIO**
4. Save

**Via Azure CLI:**
```bash
az vm open-port \
  --resource-group YOUR_RESOURCE_GROUP \
  --name YOUR_VM_NAME \
  --port 3000 \
  --priority 1010
```

### Access from Internet

```bash
# Get VM public IP
az vm list-ip-addresses -g YOUR_RESOURCE_GROUP -n YOUR_VM_NAME

# Access at: http://YOUR_PUBLIC_IP:3000
```

⚠️ **Security:** Consider:
- Using HTTPS (add reverse proxy like nginx)
- Restricting source IPs in NSG
- Using Azure Private Link
- Adding authentication

---

## Files Created

| File | Purpose |
|------|---------|
| `run_drawio_container.sh` | Shell script to run container |
| `.env.drawio.example` | Example environment file |
| `docker-compose.drawio.yml` | Docker Compose configuration |
| `DRAWIO_DOCKER_SETUP.md` | This documentation |

---

## Security Best Practices

✓ **DO:**
- Store API keys in `.env` files (not in scripts)
- Add `.env.drawio` to `.gitignore`
- Use environment variables
- Rotate API keys regularly
- Use least-privilege API keys

✗ **DON'T:**
- Commit API keys to git
- Share API keys
- Use production keys in development
- Expose container to internet without authentication

---

## Cost Estimation

Approximate costs for Claude Sonnet 4.5:
- Input: $3 per million tokens
- Output: $15 per million tokens

**Example usage:**
- 1000 diagram generations/month
- ~500 tokens each (input + output)
- **Cost: ~$3-10/month** (depends on diagram complexity)

💡 **Tip:** Use Claude Haiku for lower costs if you don't need the most advanced model.

---

## Next Steps

1. ✅ Get Anthropic API key
2. ✅ Choose a setup method (shell script/docker/compose)
3. ✅ Run the container
4. ✅ Access http://localhost:3000
5. 🎨 Start creating AI-powered diagrams!

---

## Support

**Next AI Draw.io Project:**
- GitHub: https://github.com/dayuanjiang/next-ai-draw-io
- Issues: https://github.com/dayuanjiang/next-ai-draw-io/issues

**Anthropic API:**
- Docs: https://docs.anthropic.com/
- Console: https://console.anthropic.com/

**Docker:**
- Docs: https://docs.docker.com/

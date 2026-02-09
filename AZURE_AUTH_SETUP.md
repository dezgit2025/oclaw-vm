# Azure AD Authentication Setup for Linux VM

## Overview

Azure VMs can authenticate to Azure OpenAI using **Managed Identity** - no API keys or credentials needed in your code!

## Setup Steps

### Step 1: Enable Managed Identity on Your VM

**Via Azure Portal:**
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your VM → **Identity**
3. Under **System assigned** tab:
   - Status: **On**
   - Click **Save**
4. Note the **Object (principal) ID** shown

**Via Azure CLI:**
```bash
az vm identity assign --name YOUR_VM_NAME --resource-group YOUR_RESOURCE_GROUP
```

### Step 2: Grant OpenAI Access to Your VM

**Via Azure Portal:**
1. Go to your **Azure OpenAI resource**
2. Click **Access control (IAM)** in left menu
3. Click **+ Add** → **Add role assignment**
4. Select role:
   - **Cognitive Services OpenAI User** (recommended)
   - OR **Cognitive Services User** (broader access)
5. Click **Next**
6. **Assign access to**: Managed Identity
7. Click **+ Select members**
8. Filter by: **Virtual Machine**
9. Select your VM
10. Click **Select** → **Review + assign**

**Via Azure CLI:**
```bash
# Get your VM's managed identity principal ID
PRINCIPAL_ID=$(az vm identity show --name YOUR_VM_NAME --resource-group YOUR_RESOURCE_GROUP --query principalId -o tsv)

# Get your OpenAI resource ID
OPENAI_RESOURCE_ID=$(az cognitiveservices account show --name pitchbook-resource --resource-group YOUR_RESOURCE_GROUP --query id -o tsv)

# Assign the role
az role assignment create \
  --role "Cognitive Services OpenAI User" \
  --assignee $PRINCIPAL_ID \
  --scope $OPENAI_RESOURCE_ID
```

### Step 3: Install Required Packages on VM

SSH into your Linux VM and run:

```bash
# Install pip if not already installed
sudo apt-get update
sudo apt-get install python3-pip -y

# Install Azure OpenAI and Identity packages
pip3 install openai azure-identity
```

### Step 4: Run the Test Script

```bash
python3 test_azure_openai_managed_identity.py
```

---

## How Managed Identity Works

```
┌─────────────┐
│  Your Code  │
│  (on VM)    │
└──────┬──────┘
       │ 1. Request token
       ▼
┌─────────────────────┐
│ Azure AD            │
│ (checks VM identity)│
└──────┬──────────────┘
       │ 2. Returns token
       ▼
┌─────────────────────┐
│ Azure OpenAI        │
│ (validates token)   │
└─────────────────────┘
```

**Benefits:**
- ✓ No credentials in code
- ✓ No secrets to manage or rotate
- ✓ Automatic token refresh
- ✓ Audit trail in Azure AD
- ✓ Most secure option

---

## Alternative: Azure CLI Authentication

If Managed Identity doesn't work, you can use Azure CLI:

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login (opens browser or provides device code)
az login

# Verify
az account show

# Now run the script - it will use Azure CLI credentials
python3 test_azure_openai_managed_identity.py
```

---

## Troubleshooting

### Error: "No credential available"
- Verify Managed Identity is **enabled** on VM (Step 1)
- Restart your Python script after enabling
- Try explicit ManagedIdentityCredential (script includes this)

### Error: "Permission denied" or "403"
- Verify role assignment (Step 2)
- Wait 5-10 minutes for permissions to propagate
- Check correct resource and VM were selected

### Error: "Deployment not found"
- Verify deployment name is exactly "gpt-5.2"
- Check in Azure Portal → OpenAI → Model deployments

### Check if you're on an Azure VM:
```bash
# Should return VM metadata if on Azure
curl -H Metadata:true "http://169.254.169.254/metadata/instance?api-version=2021-02-01" | jq
```

---

## Deployment Name vs Model Name

⚠️ **Important:** The model name in your code should be your **deployment name**, not the model family.

- If you deployed "gpt-5.2-turbo" and named the deployment "my-gpt5-model"
- Use: `model="my-gpt5-model"` (not "gpt-5.2")

Check your deployment name:
1. Azure Portal → OpenAI resource → **Model deployments**
2. Find the deployment and note the **Deployment name** column

---

## Security Best Practices

✓ **DO:**
- Use Managed Identity for Azure VMs
- Use Azure CLI for local development
- Regularly review access via IAM
- Use least-privilege roles (OpenAI User, not Contributor)

✗ **DON'T:**
- Hard-code API keys in scripts
- Commit credentials to git
- Share API keys across environments
- Use overly permissive roles

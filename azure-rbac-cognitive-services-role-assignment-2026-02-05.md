# Azure RBAC Role Assignment for VM Managed Identity to AI Foundry

## What This Does
Assigns an Azure RBAC role to a VM's managed identity, granting it access to Azure Cognitive Services / AI Foundry models without needing API keys.

## Command Template

```bash
az role assignment create \
    --role "<ROLE_NAME>" \
    --assignee "<MANAGED_IDENTITY_PRINCIPAL_ID>" \
    --scope "/subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<RESOURCE_GROUP>/providers/Microsoft.CognitiveServices/accounts/<COGNITIVE_SERVICES_ACCOUNT>"
```

## Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--role` | Azure RBAC role name | `Cognitive Services OpenAI User` |
| `--assignee` | Principal ID of VM's managed identity | `56afe324-cd9e-4d5d-b7c3-3d5847e5bdc6` |
| `--scope` | Full resource ID of the Cognitive Services account | See below |

## Common Roles for AI/Cognitive Services

| Role | Permissions |
|------|-------------|
| `Cognitive Services OpenAI User` | Call OpenAI APIs (inference only) |
| `Cognitive Services OpenAI Contributor` | Create deployments, fine-tune models |
| `Cognitive Services User` | Access all Cognitive Services APIs |
| `Cognitive Services Contributor` | Full access except RBAC |

## Example Used

```bash
az role assignment create \
    --role "Cognitive Services OpenAI User" \
    --assignee "56afe324-cd9e-4d5d-b7c3-3d5847e5bdc6" \
    --scope "/subscriptions/c34d54e5-7eb9-4ba8-8424-c6ab8635ccdc/resourceGroups/rg-pitchbook/providers/Microsoft.CognitiveServices/accounts/pitchbook-resource"
```

## How to Find Values

### Get VM Managed Identity Principal ID
```bash
az vm identity show --name <VM_NAME> --resource-group <RG> --query principalId -o tsv
```

### Get Cognitive Services Account Resource ID
```bash
az cognitiveservices account show --name <ACCOUNT_NAME> --resource-group <RG> --query id -o tsv
```

### List Existing Role Assignments
```bash
az role assignment list --scope "<RESOURCE_ID>" --output table
```

## Notes
- Role assignments can take a few minutes to propagate
- VM must have system-assigned or user-assigned managed identity enabled
- This enables keyless authentication using `DefaultAzureCredential` in code

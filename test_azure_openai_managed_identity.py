"""
Azure OpenAI test using Managed Identity (for Azure VMs)

Prerequisites:
1. Install: pip install openai azure-identity
2. Enable Managed Identity on your VM:
   - Azure Portal → VM → Identity → System assigned → On
3. Grant access to OpenAI resource:
   - Azure Portal → OpenAI resource → Access control (IAM)
   - Add role assignment: "Cognitive Services OpenAI User"
   - Assign to: your VM's managed identity
"""

from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
import sys

# Azure OpenAI configuration
azure_endpoint = "https://pitchbook-resource.openai.azure.com/"
api_version = "2024-12-01-preview"
deployment_name = "gpt-5.2"  # Your deployment name

def test_with_managed_identity():
    """Test using Managed Identity (for Azure VMs)"""
    print("=" * 60)
    print("Testing Azure OpenAI with Managed Identity")
    print("=" * 60)
    print(f"Endpoint: {azure_endpoint}")
    print(f"API Version: {api_version}")
    print(f"Model/Deployment: {deployment_name}")
    print("-" * 60)

    try:
        # DefaultAzureCredential tries multiple auth methods in order:
        # 1. Environment variables (service principal)
        # 2. Managed Identity (Azure VM/App Service)
        # 3. Azure CLI (if logged in with `az login`)
        # 4. Azure PowerShell, Visual Studio Code, etc.

        credential = DefaultAzureCredential()

        print("\nAuthenticating with Azure AD...")
        print("(DefaultAzureCredential will try: Managed Identity → Azure CLI → etc.)")

        client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=azure_endpoint,
            azure_ad_token_provider=lambda: credential.get_token(
                "https://cognitiveservices.azure.com/.default"
            ).token
        )

        print("✓ Authentication successful!")
        print("\nSending test message to GPT-5.2...")

        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello! Azure AD authentication successful.' if you receive this."}
            ],
            max_completion_tokens=50  # GPT-5.2 uses max_completion_tokens instead of max_tokens
        )

        print("\n" + "=" * 60)
        print("✓ CONNECTION SUCCESSFUL!")
        print("=" * 60)
        print(f"\nResponse from {deployment_name}:")
        print(response.choices[0].message.content)
        print(f"\nModel: {response.model}")
        print(f"Tokens used: {response.usage.total_tokens}")
        print(f"  - Prompt: {response.usage.prompt_tokens}")
        print(f"  - Completion: {response.usage.completion_tokens}")

        return True

    except Exception as e:
        print("\n" + "=" * 60)
        print("✗ CONNECTION FAILED")
        print("=" * 60)
        print(f"Error: {type(e).__name__}")
        print(f"Details: {str(e)}")
        print("\n" + "=" * 60)
        print("TROUBLESHOOTING:")
        print("=" * 60)

        if "authentication" in str(e).lower() or "credential" in str(e).lower():
            print("""
1. If on Azure VM, enable Managed Identity:
   - Azure Portal → Your VM → Identity → System assigned → Status: On

2. Grant OpenAI access to the VM's identity:
   - Azure Portal → Your OpenAI Resource → Access control (IAM)
   - Click "Add role assignment"
   - Role: "Cognitive Services OpenAI User" (or "Cognitive Services User")
   - Assign access to: Managed Identity → Virtual Machine → [Your VM]
   - Save

3. If not on Azure VM, login with Azure CLI:
   sudo apt-get update
   sudo apt-get install azure-cli
   az login

4. Verify Azure CLI access:
   az account show
""")
        else:
            print("""
Check:
1. Endpoint URL is correct
2. Deployment name "gpt-5.2" exists in your Azure OpenAI resource
3. API version is supported
4. Network connectivity to Azure OpenAI endpoint
""")

        return False

def test_explicit_managed_identity():
    """Test using explicit Managed Identity (if DefaultAzureCredential doesn't work)"""
    print("\n" + "=" * 60)
    print("Trying explicit Managed Identity credential...")
    print("=" * 60)

    try:
        credential = ManagedIdentityCredential()

        client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=azure_endpoint,
            azure_ad_token_provider=lambda: credential.get_token(
                "https://cognitiveservices.azure.com/.default"
            ).token
        )

        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "user", "content": "Test"}
            ],
            max_completion_tokens=10
        )

        print("✓ Explicit Managed Identity worked!")
        return True

    except Exception as e:
        print(f"✗ Explicit Managed Identity failed: {e}")
        return False

if __name__ == "__main__":
    print("\nChecking required packages...")
    try:
        import openai
        import azure.identity
        print("✓ Required packages installed")
    except ImportError as e:
        print(f"✗ Missing package: {e}")
        print("\nInstall with:")
        print("  pip install openai azure-identity")
        sys.exit(1)

    print("\n")
    success = test_with_managed_identity()

    if not success:
        print("\nTrying explicit Managed Identity as fallback...")
        test_explicit_managed_identity()

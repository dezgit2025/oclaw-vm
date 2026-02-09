"""
Example: Long-running application with automatic token refresh

This demonstrates that tokens are automatically refreshed without any manual intervention.
The script makes API calls over time and tokens refresh automatically in the background.
"""

from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential
import time
from datetime import datetime

# Azure OpenAI configuration
azure_endpoint = "https://pitchbook-resource.openai.azure.com/"
api_version = "2024-12-01-preview"
deployment_name = "gpt-5.2"

def create_client():
    """Create Azure OpenAI client with automatic token refresh"""
    credential = DefaultAzureCredential()

    client = AzureOpenAI(
        api_version=api_version,
        azure_endpoint=azure_endpoint,
        # This lambda is called automatically before each request
        # Token refresh happens transparently in the background
        azure_ad_token_provider=lambda: credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        ).token
    )

    return client

def make_api_call(client, call_number):
    """Make a single API call"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "user", "content": f"Say 'Call #{call_number} successful at {timestamp}'"}
            ],
            max_completion_tokens=30
        )

        print(f"[{timestamp}] ✓ Call #{call_number}: {response.choices[0].message.content}")
        return True

    except Exception as e:
        print(f"[{timestamp}] ✗ Call #{call_number} failed: {e}")
        return False

def main():
    print("=" * 70)
    print("Long-Running Application Example")
    print("Demonstrating Automatic Token Refresh")
    print("=" * 70)
    print("\nCreating Azure OpenAI client...")

    # Create client once - reuse for multiple calls
    client = create_client()
    print("✓ Client created\n")

    print("Making API calls over time...")
    print("(Token will automatically refresh when needed)\n")

    # Simulate a long-running application
    # In real use, this would be your application making calls as needed
    for i in range(1, 6):
        success = make_api_call(client, i)

        if not success:
            print("\nRetrying with new client...")
            client = create_client()
            make_api_call(client, i)

        # Wait between calls (in real app, this would be your normal processing)
        if i < 5:
            print(f"  Waiting 5 seconds...\n")
            time.sleep(5)

    print("\n" + "=" * 70)
    print("✓ Complete!")
    print("=" * 70)
    print("\nKey Points:")
    print("- Client was created once and reused")
    print("- No manual token refresh needed")
    print("- Tokens refresh automatically in the background")
    print("- Your code just works, even for long-running processes")

if __name__ == "__main__":
    main()

import os

from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI


def build_client() -> AzureOpenAI:
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://pitchbook-resource.openai.azure.com/")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

    # Prefer Entra ID (Azure AD) token auth
    credential = DefaultAzureCredential()
    return AzureOpenAI(
        api_version=api_version,
        azure_endpoint=azure_endpoint,
        azure_ad_token_provider=lambda: credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        ).token,
    )


client = build_client()

try:
    print("Testing Azure OpenAI connection...")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://pitchbook-resource.openai.azure.com/")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5.2")

    print(f"Endpoint: {endpoint}")
    print(f"API Version: {api_version}")
    print(f"Model/Deployment: {deployment}")
    print("-" * 50)

    # Test with a simple completion
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello! Connection successful.' if you receive this message."}
        ],
        max_completion_tokens=50
    )

    print("\n✓ Connection successful!")
    print(f"\nResponse from GPT-5.2:")
    print(response.choices[0].message.content)
    print(f"\nModel used: {response.model}")
    print(f"Tokens used: {response.usage.total_tokens}")

except Exception as e:
    print(f"\n✗ Connection failed!")
    print(f"Error: {type(e).__name__}")
    print(f"Details: {str(e)}")

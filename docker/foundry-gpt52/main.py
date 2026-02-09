import os

from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI


def env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value else default


def main() -> None:
    azure_endpoint = env("AZURE_OPENAI_ENDPOINT", "https://pitchbook-resource.openai.azure.com/")
    deployment = env("AZURE_OPENAI_DEPLOYMENT", "gpt-5.2")
    api_version = env("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

    credential = DefaultAzureCredential()

    client = AzureOpenAI(
        api_version=api_version,
        azure_endpoint=azure_endpoint,
        azure_ad_token_provider=lambda: credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        ).token,
    )

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "I am going to Paris, what should I see?"},
        ],
        max_completion_tokens=int(env("MAX_COMPLETION_TOKENS", "512")),
    )

    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()

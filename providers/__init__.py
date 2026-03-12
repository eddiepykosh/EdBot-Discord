from providers.base import AIProvider


def get_provider(name: str) -> AIProvider:
    if name == "azure":
        from providers.azure_provider import AzureProvider
        return AzureProvider()
    elif name == "claude":
        from providers.claude_provider import ClaudeProvider
        return ClaudeProvider()
    else:
        raise ValueError(f"Unknown AI provider: '{name}'. Must be 'azure' or 'claude'.")

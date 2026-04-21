from providers.base import AIProvider


def get_provider() -> AIProvider:
    from providers.openai_provider import OpenAICompatibleProvider
    return OpenAICompatibleProvider()

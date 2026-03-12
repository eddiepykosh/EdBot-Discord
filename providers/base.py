from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    def initialize(self):
        """Set up API client. Called once in on_ready()."""

    @abstractmethod
    def is_ready(self) -> bool:
        """Return True if the provider is initialized and ready."""

    @abstractmethod
    def create_response(self, api_messages, image_attachments):
        """Build payload, call API, return (reply_text, history_content).

        api_messages: list of {"role": str, "content": str|list} dicts
        image_attachments: list of discord.Attachment for current message
        Returns: (reply_text: str, history_content: any)
        """

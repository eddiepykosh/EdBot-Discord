import os
import re

import anthropic

from common.logger import get_logger
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, ASSETS_TEXT_PATH
from providers.base import AIProvider

logger = get_logger("edbot_ai.claude")


class ClaudeProvider(AIProvider):
    def __init__(self):
        self.client = None
        self.system_prompt = ""

    def initialize(self):
        logger.info("Initializing Anthropic client (model: %s)", CLAUDE_MODEL)
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        # Load system prompt from file
        prompt_path = os.path.join(ASSETS_TEXT_PATH, "system_prompt.txt")
        with open(prompt_path, "r") as f:
            self.system_prompt = f.read().strip()
        logger.info("Anthropic client initialized, system prompt loaded (%d chars)", len(self.system_prompt))

    def is_ready(self) -> bool:
        return self.client is not None

    def create_response(self, api_messages, image_attachments):
        # Build Claude-format payload
        api_history = []
        for i, msg in enumerate(api_messages):
            role = msg["role"]
            content = msg["content"]

            if role == "user":
                if i == len(api_messages) - 1 and image_attachments:
                    # Current message with images: build content block array
                    content_parts = [{"type": "text", "text": content}]
                    for a in image_attachments:
                        content_parts.append({
                            "type": "image",
                            "source": {"type": "url", "url": a.url},
                        })
                    api_history.append({"role": "user", "content": content_parts})
                else:
                    api_history.append({"role": "user", "content": content})
            elif role == "assistant":
                # Both plain strings and content block lists are valid
                api_history.append({"role": "assistant", "content": content})

        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=self.system_prompt,
            messages=api_history,
            tools=[{
                "type": "web_search_20260209",
                "name": "web_search",
            }],
        )

        logger.debug("Claude response id: %s, usage: in=%d out=%d",
                      response.id, response.usage.input_tokens, response.usage.output_tokens)

        # Extract text from response content blocks and concatenate directly.
        # Web search interleaves tool_use/result blocks between text fragments,
        # so we concatenate all text without extra separators, then clean up.
        raw = "".join(block.text for block in response.content if block.type == "text")
        # Collapse runs of 3+ newlines into 2 (preserves intentional paragraph breaks)
        reply = re.sub(r'\n{3,}', '\n\n', raw).strip()

        # Store plain text only — tool blocks waste tokens in history
        return (reply, reply)

import json
import os
from urllib.parse import urlencode

from openai import OpenAI

from common.logger import get_logger
from config import (
    ASSETS_TEXT_PATH,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MAX_OUTPUT_TOKENS,
    OPENAI_MODEL,
    TAVILY_API_KEY,
    TAVILY_MCP_DEFAULT_PARAMETERS,
    TAVILY_MCP_SERVER_URL,
)
from providers.base import AIProvider

logger = get_logger("edbot_ai.openai")

DEFAULT_TAVILY_MCP_URL = "https://mcp.tavily.com/mcp/"
DEFAULT_TAVILY_PARAMETERS = {
    "search_depth": "advanced",
    "max_results": 8,
    "include_images": False,
    "include_raw_content": False,
    "include_favicon": False,
}


class OpenAICompatibleProvider(AIProvider):
    def __init__(self):
        self.client = None
        self.system_prompt = ""
        self.tavily_tool = None

    def initialize(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")
        if not OPENAI_MODEL:
            raise ValueError("OPENAI_MODEL is required")

        logger.info(
            "Initializing OpenAI-compatible client (base_url: %s, model: %s)",
            OPENAI_BASE_URL or "https://api.openai.com/v1",
            OPENAI_MODEL,
        )
        self.client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL or None)

        prompt_path = os.path.join(ASSETS_TEXT_PATH, "system_prompt.txt")
        with open(prompt_path, "r") as f:
            self.system_prompt = f.read().strip()
        logger.info("System prompt loaded (%d chars)", len(self.system_prompt))

        self.tavily_tool = self._build_tavily_tool()
        if self.tavily_tool:
            logger.info("Tavily MCP enabled")
        else:
            logger.info("Tavily MCP disabled (no Tavily MCP URL or API key configured)")

    def is_ready(self) -> bool:
        return self.client is not None

    def create_response(self, api_messages, image_attachments):
        api_history = []
        for i, msg in enumerate(api_messages):
            if msg["role"] == "user" and i == len(api_messages) - 1 and image_attachments:
                content_parts = [{"type": "input_text", "text": msg["content"]}]
                for attachment in image_attachments:
                    content_parts.append({
                        "type": "input_image",
                        "image_url": attachment.url,
                    })
                api_history.append({"role": "user", "content": content_parts})
            else:
                api_history.append({"role": msg["role"], "content": msg["content"]})

        request = {
            "model": OPENAI_MODEL,
            "instructions": self.system_prompt,
            "input": api_history,
            "max_output_tokens": OPENAI_MAX_OUTPUT_TOKENS,
        }
        if self.tavily_tool:
            request["tools"] = [self.tavily_tool]

        response = self.client.responses.create(**request)
        reply = (response.output_text or "").strip()
        return (reply, reply)

    def _build_tavily_tool(self):
        server_url = self._get_tavily_server_url()
        if not server_url:
            return None

        tool = {
            "type": "mcp",
            "server_label": "tavily",
            "server_description": "Tavily web search and extraction for current web information.",
            "server_url": server_url,
            "require_approval": "never",
        }

        default_parameters = self._get_tavily_default_parameters()
        if default_parameters:
            tool["headers"] = {
                "DEFAULT_PARAMETERS": json.dumps(default_parameters),
            }

        return tool

    def _get_tavily_server_url(self):
        if TAVILY_MCP_SERVER_URL:
            return TAVILY_MCP_SERVER_URL
        if TAVILY_API_KEY:
            return f"{DEFAULT_TAVILY_MCP_URL}?{urlencode({'tavilyApiKey': TAVILY_API_KEY})}"
        return None

    def _get_tavily_default_parameters(self):
        if not TAVILY_MCP_DEFAULT_PARAMETERS:
            return DEFAULT_TAVILY_PARAMETERS

        try:
            configured = json.loads(TAVILY_MCP_DEFAULT_PARAMETERS)
        except json.JSONDecodeError as exc:
            raise ValueError("TAVILY_MCP_DEFAULT_PARAMETERS must be valid JSON") from exc

        if not isinstance(configured, dict):
            raise ValueError("TAVILY_MCP_DEFAULT_PARAMETERS must decode to a JSON object")

        merged = DEFAULT_TAVILY_PARAMETERS.copy()
        merged.update(configured)
        return merged

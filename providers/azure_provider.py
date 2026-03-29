from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from common.logger import get_logger
from config import AZURE_AI_ENDPOINT, AZURE_AI_AGENT_NAME
from providers.base import AIProvider

logger = get_logger("edbot_ai.azure")

MAX_AGENTIC_LOOPS = 10


class AzureProvider(AIProvider):
    def __init__(self):
        self.openai_client = None
        self.agent = None

    def initialize(self):
        logger.info("Initializing Azure AI client (endpoint: %s, agent: %s)", AZURE_AI_ENDPOINT, AZURE_AI_AGENT_NAME)
        project_client = AIProjectClient(
            endpoint=AZURE_AI_ENDPOINT,
            credential=DefaultAzureCredential(),
        )
        self.agent = project_client.agents.get(agent_name=AZURE_AI_AGENT_NAME)
        self.openai_client = project_client.get_openai_client()
        logger.info("Azure AI client initialized (agent: %s, id: %s)", self.agent.name, self.agent.id)

    def is_ready(self) -> bool:
        return self.openai_client is not None and self.agent is not None

    def create_response(self, api_messages, image_attachments):
        # Build Azure-format payload
        api_history = []
        for i, msg in enumerate(api_messages):
            if i == len(api_messages) - 1 and image_attachments:
                content_parts = [{"type": "input_text", "text": msg["content"]}]
                for a in image_attachments:
                    content_parts.append({"type": "input_image", "image_url": a.url})
                api_history.append({"role": "user", "content": content_parts})
            else:
                api_history.append({"role": msg["role"], "content": msg["content"]})

        current_input = api_history
        for loop in range(MAX_AGENTIC_LOOPS):
            response = self.openai_client.responses.create(
                input=current_input,
                extra_body={"agent_reference": {"name": self.agent.name, "type": "agent_reference"}},
            )

            approval_requests = [
                item for item in response.output if item.type == "mcp_approval_request"
            ]
            if not approval_requests:
                break

            # Auto-approve all MCP tool calls and continue the loop
            logger.info(
                "Auto-approving %d MCP tool request(s) on loop %d: %s",
                len(approval_requests),
                loop + 1,
                [getattr(item, "name", item.type) for item in approval_requests],
            )
            approvals = [
                {"type": "mcp_approval_response", "approve": True, "approval_request_id": item.id}
                for item in approval_requests
            ]
            current_input = list(response.output) + approvals
        else:
            logger.warning("Reached max agentic loops (%d) without a text response", MAX_AGENTIC_LOOPS)

        reply = response.output_text
        if not reply:
            logger.warning(
                "output_text empty after agentic loop — response status: %s, output items: %s",
                response.status,
                [(item.type, getattr(item, "status", None)) for item in response.output],
            )
        # Azure stores plain text in history
        return (reply, reply)

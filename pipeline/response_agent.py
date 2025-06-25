from .base import PipelineStep
from mcp_context import MCPContext
from utils.gpt_client import get_gpt_response


class ResponseAgentStep(PipelineStep):
    def run(self, ctx: MCPContext) -> MCPContext:
        # Use translated English text for GPT
        gpt_input = ctx.translated_to_english if ctx.translated_to_english else ctx.text
        ctx.response = get_gpt_response(gpt_input, ctx.chat_history)
        return ctx

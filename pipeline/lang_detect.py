# pipeline/lang_detect.py
from .base import PipelineStep
from mcp_context import MCPContext
from utils.lang_detect import detect_language  # your function

class LangDetectStep(PipelineStep):
    def run(self, ctx: MCPContext) -> MCPContext:
        ctx.lang = detect_language(ctx.text)
        return ctx

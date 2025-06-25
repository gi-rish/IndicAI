# pipeline/asr.py
from .base import PipelineStep
from mcp_context import MCPContext
from utils.whisper_asr import transcribe  # or your own ASR module

class ASRStep(PipelineStep):
    def run(self, ctx: MCPContext) -> MCPContext:
        if ctx.input_mode == "voice" and ctx.audio_file_path:
            ctx.text = transcribe(ctx.audio_file_path)
        return ctx

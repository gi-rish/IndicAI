# pipeline/tts.py

from .base import PipelineStep
from mcp_context import MCPContext
from utils.tts_engine import generate_speech

class TTSStep(PipelineStep):
    def run(self, ctx: MCPContext) -> MCPContext:
        if not ctx.response_translated:
            print("[TTS] No response to synthesize")
            return ctx

        output_path = generate_speech(ctx.response_translated, ctx.lang)
        ctx.audio_response_path = output_path
        print(f"[TTS] Audio generated at: {output_path}")
        return ctx

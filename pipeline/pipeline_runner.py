# pipeline/pipeline_runner.py

from mcp_context import MCPContext
from .base import PipelineStep
from pipeline.asr import ASRStep
from pipeline.lang_detect import LangDetectStep
from pipeline.response_agent import ResponseAgentStep
from pipeline.translate_to_english import TranslateToEnglishStep
from pipeline.translate_from_english import TranslateFromEnglishStep
from pipeline.tts import TTSStep   # assuming you've created this step

class PipelineRunner:
    def __init__(self, steps: list[PipelineStep]):
        self.steps = steps

    def run(self, ctx: MCPContext) -> MCPContext:
        for step in self.steps:
            ctx = step.run(ctx)
        return ctx


pipeline = PipelineRunner([
    ASRStep(),
    LangDetectStep(),
    TranslateToEnglishStep(),
    ResponseAgentStep(),
    TranslateFromEnglishStep(),
    TTSStep()
])

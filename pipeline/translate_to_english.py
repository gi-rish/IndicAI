# pipeline/translate_to_english.py

from .base import PipelineStep
from mcp_context import MCPContext
from utils.translation import translate_to_english
from utils.lang_code_map import get_lang_code  # optional if needed

class TranslateToEnglishStep(PipelineStep):
    def run(self, ctx: MCPContext) -> MCPContext:
        lang_code = get_lang_code(ctx.lang)  # "hi", "kn", etc.
        ctx.translated_to_english = translate_to_english(ctx.text, lang_code)
        return ctx

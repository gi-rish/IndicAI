# pipeline/translate_from_english.py

from .base import PipelineStep
from mcp_context import MCPContext
from utils.translation import translate_from_english
from utils.lang_code_map import get_lang_code

class TranslateFromEnglishStep(PipelineStep):
    def run(self, ctx: MCPContext) -> MCPContext:
        lang_code = get_lang_code(ctx.lang)
        ctx.response_translated = translate_from_english(ctx.response, lang_code)
        return ctx

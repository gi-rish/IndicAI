# mcp_context.py
class MCPContext:
    def __init__(self, text=None, lang=None, chat_history=None, audio_file_path=None, input_mode=None):
        self.text = text
        self.lang = lang
        self.chat_history = chat_history or []
        self.audio_file_path = audio_file_path
        self.input_mode = input_mode
        self.response = None
        self.translated_to_english = None   # input translated to English
        self.response_translated = None

    def to_dict(self):
        return {
            "text": self.text,
            "lang": self.lang,
            "chat_history": self.chat_history,
            "audio_file_path": self.audio_file_path,
            "input_mode": self.input_mode,
            "response": self.response
        }

    def __repr__(self):
        return f"<MCPContext lang={self.lang}, mode={self.input_mode}>"


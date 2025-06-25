class LoggingStep(PipelineStep):
    def run(self, ctx: MCPContext) -> MCPContext:
        print(f"[MCP] {ctx}")
        return ctx

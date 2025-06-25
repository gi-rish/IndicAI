# pipeline/base.py
from abc import ABC, abstractmethod
from mcp_context import MCPContext

class PipelineStep(ABC):
    @abstractmethod
    def run(self, ctx: MCPContext) -> MCPContext:
        ...


from typing import Any, Dict


class Tool:
    def __init__(self, name: str, description: str, inputSchema: Dict[str, Any], server: str = None):
        self.name = name
        self.description = description
        self.inputSchema = inputSchema
        self.server = server  # Optional, can be added later

    def add_server_label(self, server_name: str):
        """Attach a server label to the tool."""
        self.server = server_name

    def to_dict(self) -> Dict[str, Any]:
        """Convert Tool to dict"""
        data = {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.inputSchema
        }
        if self.server:
            data["server"] = self.server
        return data

    def __repr__(self):
        return f"Tool(name={self.name}, server={self.server})"

class ToolCall:
    def __init__(self, id, name: str, args: dict):
        self.id = id
        self.name = name
        self.args = args

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "args": self.args
        }


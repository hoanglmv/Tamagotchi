"""
AI Brain & Agent Pipeline for myDeskAssistant.
Coordinates LLM (OpenRouter / Gemini) and MCP tool calling loop.
"""

from typing import Dict, Any, List, Optional, Callable
import os
import json
import asyncio
import inspect
from pathlib import Path
from dotenv import load_dotenv

from core.persona import get_system_prompt
from core.memory import MemoryManager
from mcp_servers import system_server, file_server

# Load environment variables
load_dotenv()


class AssistantBrain:
    """Coordinates reasoning, OpenRouter / Gemini API, and MCP tools."""

    def __init__(
        self,
        memory: Optional[MemoryManager] = None,
        on_status_change: Optional[Callable[[str, str], None]] = None,
        on_tool_call: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ):
        """
        Args:
            memory: SQLite MemoryManager instance.
            on_status_change: Callback function (status: 'thinking' | 'tool' | 'talking' | 'idle', message: str).
            on_tool_call: Callback function (tool_name, arguments).
        """
        self.memory = memory or MemoryManager()
        self.on_status_change = on_status_change
        self.on_tool_call = on_tool_call

        # Configuration
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.openrouter_base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")

        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.assistant_name = os.getenv("ASSISTANT_NAME", "Lumi")
        self.user_name = os.getenv("USER_NAME", "Senpai")

        # Map tool names to python functions
        self.tools_map = {
            "get_pc_stats": system_server.get_pc_stats,
            "launch_app": system_server.launch_app,
            "get_clipboard": system_server.get_clipboard,
            "set_clipboard": system_server.set_clipboard,
            "organize_downloads": file_server.organize_downloads,
            "read_file": file_server.read_file,
            "write_file": file_server.write_file,
            "list_directory": file_server.list_directory
        }

        self.tools_schema = self._build_tools_schema()

    def _notify_status(self, status: str, message: str = ""):
        if self.on_status_change:
            try:
                self.on_status_change(status, message)
            except Exception:
                pass

    def _build_tools_schema(self) -> List[Dict[str, Any]]:
        """Build OpenAI-compatible tool declaration schema for OpenRouter."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_pc_stats",
                    "description": "Get current computer hardware performance: CPU usage percent, RAM used/available, Disk storage, and Battery percentage/charging status.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "launch_app",
                    "description": "Open or launch a desktop application or browser URL (e.g., chrome, vscode, notepad, calculator, terminal, or https link).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "app_name": {
                                "type": "string",
                                "description": "Name or alias of the application (e.g., 'chrome', 'vscode', 'notepad', 'calc') or full web URL."
                            }
                        },
                        "required": ["app_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_clipboard",
                    "description": "Get current text content from the system clipboard.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "set_clipboard",
                    "description": "Copy text string into the system clipboard.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "The text to copy."
                            }
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "organize_downloads",
                    "description": "Scan and organize files in Downloads (or custom folder) into categories (Images, Documents, Installers, Code, etc.).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "folder_path": {
                                "type": "string",
                                "description": "Optional custom folder path. If not provided, defaults to user Downloads directory."
                            },
                            "dry_run": {
                                "type": "boolean",
                                "description": "If True (default), only preview without moving files. Set False to actually move files."
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read text content of a local file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file to read."
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write text content to a local file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path where the file will be saved."
                            },
                            "content": {
                                "type": "string",
                                "description": "Text content to write."
                            }
                        },
                        "required": ["file_path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_directory",
                    "description": "List files and folders in a specified directory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Directory path to list (defaults to current directory if not provided)."
                            }
                        },
                        "required": []
                    }
                }
            }
        ]

    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute local MCP tool function with given arguments."""
        self._notify_status("tool", f"Đang thực thi: {tool_name}")
        if self.on_tool_call:
            try:
                self.on_tool_call(tool_name, arguments)
            except Exception:
                pass

        tool_fn = self.tools_map.get(tool_name)
        if not tool_fn:
            return {"error": f"Tool '{tool_name}' không tồn tại."}

        try:
            # Handle async and sync tools
            if inspect.iscoroutinefunction(tool_fn):
                result = await tool_fn(**arguments)
            else:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, lambda: tool_fn(**arguments))
            return result
        except Exception as e:
            return {"error": f"Lỗi khi thực thi tool '{tool_name}': {str(e)}"}

    async def generate_response(self, user_prompt: str) -> str:
        """
        Main agent loop:
        1. Format prompt and conversation history
        2. Call OpenRouter / Gemini with tool schemas
        3. If tool calls requested, execute tools and feed results back
        4. Return final friendly response
        """
        self._notify_status("thinking", "Đang suy nghĩ...")

        # Save user message to memory
        self.memory.add_message("user", user_prompt)

        # Build context
        history = self.memory.get_recent_messages(limit=8)
        system_prompt = get_system_prompt(self.assistant_name, self.user_name)

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]

        # Add history
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # Check API key
        if not self.openrouter_key or self.openrouter_key == "your_openrouter_api_key_here":
            # Fallback mock mode if API key not configured yet
            fallback_response = self._handle_offline_fallback(user_prompt)
            self.memory.add_message("assistant", fallback_response)
            self._notify_status("idle", "")
            return fallback_response

        # Execute using AsyncOpenAI client (OpenRouter)
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=self.openrouter_key,
            base_url=self.openrouter_base_url,
            default_headers={
                "HTTP-Referer": "https://github.com/myDeskAssistant",
                "X-Title": "myDeskAssistant Anime Desktop Pet"
            }
        )

        try:
            # Turn 1: Initial call with tools
            response = await client.chat.completions.create(
                model=self.openrouter_model,
                messages=messages,
                tools=self.tools_schema,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=600
            )

            choice = response.choices[0]
            message = choice.message

            # Check if LLM requested tool calling
            if message.tool_calls:
                # Add assistant message containing tool calls
                messages.append(message.model_dump())

                for tool_call in message.tool_calls:
                    fn_name = tool_call.function.name
                    try:
                        fn_args = json.loads(tool_call.function.arguments)
                    except Exception:
                        fn_args = {}

                    # Execute tool
                    tool_output = await self._execute_tool(fn_name, fn_args)

                    # Append tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": fn_name,
                        "content": json.dumps(tool_output, ensure_ascii=False)
                    })

                # Turn 2: Get final friendly response from LLM
                self._notify_status("thinking", "Đang tổng hợp câu trả lời...")
                second_response = await client.chat.completions.create(
                    model=self.openrouter_model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=600
                )
                final_text = second_response.choices[0].message.content or ""
            else:
                final_text = message.content or ""

            # Save assistant response to memory
            self.memory.add_message("assistant", final_text)
            self._notify_status("idle", "")
            return final_text

        except Exception as e:
            err_msg = f"Gặp lỗi khi kết nối OpenRouter: {str(e)}"
            self._notify_status("idle", "")
            return f"Oa... {self.user_name} ơi, Lumi gặp sự cố rồi: {err_msg} (｡•́︿•̀｡)"

    def _handle_offline_fallback(self, user_prompt: str) -> str:
        """Helpful offline fallback response when OPENROUTER_API_KEY is not yet filled."""
        p_lower = user_prompt.lower()
        if any(k in p_lower for k in ["pc", "máy tính", "ram", "cpu", "pin", "phần cứng"]):
            stats = system_server.get_pc_stats()
            cpu = stats['cpu']['usage_percent']
            ram = stats['ram']['usage_percent']
            battery_str = f", pin còn {stats['battery']['percent']}%" if stats['battery']['has_battery'] else ""
            return f"Chào {self.user_name}! Lumi đang chạy chế độ Offline do chưa có OPENROUTER_API_KEY. Nhưng em vẫn kiểm tra được máy: CPU đang ở mức {cpu}%, RAM đã dùng {ram}%{battery_str} nha! (˶ᵔ ᵕ ᵔ˶)"
        
        return (
            f"Chào {self.user_name}! Em là {self.assistant_name} đây! ✨\n"
            f"Để kích hoạt toàn bộ trí thông minh AI của em, {self.user_name} hãy điền 'OPENROUTER_API_KEY' vào file '.env' nhé! (˶ᵔ ᵕ ᵔ˶)"
        )

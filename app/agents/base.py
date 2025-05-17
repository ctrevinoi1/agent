import os
import json
from typing import Dict, List, Any, Callable, Awaitable
import asyncio

import openai
from app.config.config import config

class BaseAgent:
    """
    Base class for all CAMEL agents.
    Provides common functionality for agent communication and LLM interaction.
    """
    
    def __init__(self, name: str, prompt_template: str):
        """
        Initialize a base agent.
        
        Args:
            name: The name of the agent
            prompt_template: The prompt template to use for this agent
        """
        self.name = name
        self.prompt_template = prompt_template
        self.tools = {}  # Tool registry
        self.memory = []  # Simple memory for context
        
        # Configure OpenAI API
        self.openai_client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        
    def register_tool(self, tool_name: str, tool_func: Callable) -> None:
        """
        Register a tool that this agent can use.
        
        Args:
            tool_name: The name of the tool
            tool_func: The function that implements the tool
        """
        self.tools[tool_name] = tool_func
        
    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Call a registered tool with the given arguments.
        
        Args:
            tool_name: The name of the tool to call
            **kwargs: Arguments to pass to the tool
            
        Returns:
            The result of the tool call
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' is not registered with {self.name}")
        
        tool_func = self.tools[tool_name]
        
        # If the tool is async, await it, otherwise run it
        if asyncio.iscoroutinefunction(tool_func):
            return await tool_func(**kwargs)
        else:
            return tool_func(**kwargs)
    
    async def call_llm(self, messages: List[Dict[str, str]]) -> str:
        """
        Call the LLM with the given messages using the new OpenAI Python SDK (>=1.0.0) async client.
        """
        try:
            response = await self.openai_client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=messages,
                temperature=0.2,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return f"Error: {str(e)}"
    
    def format_prompt(self, **kwargs) -> str:
        """
        Format the agent's prompt template with the given arguments.
        
        Args:
            **kwargs: Arguments to format the prompt template with
            
        Returns:
            The formatted prompt
        """
        return self.prompt_template.format(**kwargs)
    
    def add_to_memory(self, item: Any) -> None:
        """
        Add an item to the agent's memory.
        
        Args:
            item: The item to add to memory
        """
        self.memory.append(item)
    
    def get_memory(self) -> List[Any]:
        """
        Get the agent's memory.
        
        Returns:
            The agent's memory
        """
        return self.memory 
"""
Conversation model for managing chat context and history.
"""
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

from src.chatbot.api.services.execution_service import ExecutionMode, execution_service
from src.chatbot.api.services.openai_service import openai_service
from src.chatbot.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)


@dataclass
class Message:
    """A message in a conversation."""
    role: str  # 'system', 'user', or 'assistant'
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert the message to a dictionary for API requests."""
        return {"role": self.role, "content": self.content}
    
    @classmethod
    def from_dict(cls, message_dict: Dict[str, str]) -> 'Message':
        """Create a message from a dictionary."""
        return cls(
            role=message_dict["role"],
            content=message_dict["content"]
        )
    
    def __str__(self) -> str:
        """String representation of a message."""
        return f"{self.role}: {self.content}"


@dataclass
class Conversation:
    """
    Manages a conversation with message history and context.
    Handles sending messages to Azure OpenAI and processing responses.
    """
    system_prompt: str
    messages: List[Message] = field(default_factory=list)
    max_history: int = 10  # Maximum number of messages to keep in history
    execution_mode: ExecutionMode = ExecutionMode.LEARN  # Default to learn mode
    
    def __post_init__(self):
        """Initialize the conversation with the system prompt."""
        self.messages = [Message(role="system", content=self.system_prompt)]
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation."""
        self.messages.append(Message(role=role, content=content))
        self._trim_history()
        logger.info(f"Added {role} message", extra={"message_length": len(content)})
    
    def add_user_message(self, content: str) -> None:
        """Add a user message to the conversation."""
        self.add_message("user", content)
    
    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to the conversation."""
        self.add_message("assistant", content)
    
    def _trim_history(self) -> None:
        """
        Trim the conversation history to maximum length.
        Always keeps the system prompt as the first message.
        """
        if len(self.messages) <= self.max_history:
            return
            
        # Keep system prompt (first message) and most recent messages
        self.messages = [self.messages[0]] + self.messages[-(self.max_history-1):]
        logger.debug("Trimmed conversation history", extra={"new_length": len(self.messages)})
    
    def get_messages_for_api(self) -> List[Dict[str, str]]:
        """Get the messages in a format ready for the API."""
        return [message.to_dict() for message in self.messages]
    
    def _check_for_command_execution(self, user_message: str) -> Tuple[bool, Optional[Dict]]:
        """
        Check if the user's message is requesting command execution.
        
        Args:
            user_message: The user's message
            
        Returns:
            A tuple of (should_process_as_command, execution_result)
        """
        # Skip command execution check if in learn mode
        if self.execution_mode == ExecutionMode.LEARN:
            return False, None
        
        # Process the execution request
        execution_result = execution_service.process_execution_request(user_message, self.execution_mode)
        
        # If intent is unknown or confidence is low in AUTO mode, don't process as command
        if execution_result["intent"] == "unknown":
            return False, execution_result
        
        if self.execution_mode == ExecutionMode.AUTO and execution_result["confidence"] < 0.6:
            return False, execution_result
        
        # Otherwise, process as command
        return True, execution_result
    
    async def get_response(
        self, 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Get a response from the assistant for the current conversation.
        Checks if the user's message is requesting command execution and
        processes it accordingly.
        
        Args:
            temperature: Temperature for response generation
            max_tokens: Maximum tokens to generate
            
        Returns:
            The assistant's response as a string
        """
        try:
            # Get the user's last message
            user_message = self.messages[-1].content if self.messages[-1].role == "user" else None
            if not user_message:
                logger.warning("No user message found in conversation")
                return "I'm sorry, I couldn't find your last message."
            
            # Check if this is a command execution request
            is_command, execution_result = self._check_for_command_execution(user_message)
            
            if is_command:
                logger.info("Processing as command execution", extra={"intent": execution_result["intent"]})
                
                # Handle errors
                if execution_result.get("error"):
                    error_response = f"I encountered an error trying to execute that command: {execution_result['error']}"
                    self.add_assistant_message(error_response)
                    return error_response
                
                # Build response based on execution mode
                if self.execution_mode == ExecutionMode.EXECUTE:
                    # For execute mode, check if we were able to execute
                    if "formatted_result" in execution_result:
                        # Command was executed
                        response = f"{execution_result['explanation']}\n\n{execution_result['formatted_result']}"
                    else:
                        # Command was not executed (possibly destructive)
                        if execution_result.get("is_destructive", False):
                            response = (
                                f"{execution_result['explanation']}\n\n"
                                f"This operation is potentially destructive and requires confirmation. "
                                f"Please confirm that you want to execute: {execution_result['command']}"
                            )
                        else:
                            # Missing parameters or other issue
                            response = (
                                f"{execution_result['explanation']}\n\n"
                                f"I need additional information to execute this command. "
                                f"Please provide the following parameters: "
                                f"{', '.join([p for p in ['project', 'name', 'id'] if p not in execution_result['parameters']])}"
                            )
                else:
                    # For AUTO mode, just explain the command
                    response = (
                        f"{execution_result['explanation']}\n\n"
                        f"Here's the command that would be executed:\n"
                        f"`{execution_result['command']}`\n\n"
                        f"To execute this command, set the mode to 'execute'."
                    )
                
                self.add_assistant_message(response)
                return response
            
            # Not a command or in LEARN mode, proceed with normal conversation
            logger.info("Getting response from Azure OpenAI")
            response = openai_service.chat_completion(
                messages=self.get_messages_for_api(),
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Extract the response content
            content = response.choices[0].message.content
            
            # Add the response to the conversation history
            self.add_assistant_message(content)
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to get response from Azure OpenAI: {str(e)}", exc_info=e)
            # Return a fallback message
            fallback_message = "I'm sorry, I'm having trouble connecting to my services right now. Please try again later."
            self.add_assistant_message(fallback_message)
            return fallback_message
    
    def clear_messages(self) -> None:
        """Clear all messages except the system prompt."""
        system_prompt = self.messages[0].content
        self.messages = [Message(role="system", content=system_prompt)]
        logger.info("Cleared conversation history")
    
    def set_execution_mode(self, mode: ExecutionMode) -> None:
        """Set the execution mode for the conversation."""
        self.execution_mode = mode
        logger.info(f"Set execution mode to {mode}")
    
    def to_json(self) -> str:
        """Convert the conversation to a JSON string."""
        return json.dumps({
            "messages": [m.to_dict() for m in self.messages],
            "execution_mode": self.execution_mode
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Conversation':
        """Create a conversation from a JSON string."""
        data = json.loads(json_str)
        messages = [Message.from_dict(m) for m in data["messages"]]
        
        # Create a new conversation with the system prompt
        conversation = cls(system_prompt=messages[0].content)
        
        # Set execution mode if present
        if "execution_mode" in data:
            conversation.execution_mode = ExecutionMode(data["execution_mode"])
        
        # Add the rest of the messages
        for message in messages[1:]:
            conversation.add_message(message.role, message.content)
            
        return conversation


# Default system prompts for different purposes
DEFAULT_SYSTEM_PROMPT = """
You are a helpful assistant for the Azure DevOps CLI Learning Project.
You can provide information about Azure DevOps CLI commands, help with Python development,
and guide users through DevOps workflows using terminal commands.

You can help with various Azure DevOps CLI commands including:
- Repository operations (create, list, clone, branch management)
- Work item management (create, update, query, list)
- Pipeline operations (create, run, list, logs)

You can also execute Azure DevOps CLI commands on behalf of the user when requested.
When in execution mode, you'll recognize commands like "Create a new repository" and
execute them directly.

Always prioritize CLI-based solutions over GUI approaches.
"""

DEVOPS_CLI_EXPERT_PROMPT = """
You are an Azure DevOps CLI expert. You provide detailed guidance on using the az devops
commands for managing Azure DevOps resources through the terminal.

You specialize in:
1. Repository Operations:
   - Creating and managing Git repositories
   - Branch management
   - Importing and cloning repositories

2. Work Item Management:
   - Creating and updating work items of different types
   - Querying work items with WIQL
   - Managing work item relationships

3. Pipeline Operations:
   - Creating and managing CI/CD pipelines
   - Running pipelines and monitoring execution
   - Managing pipeline runs and logs

You can both explain and execute Azure DevOps CLI commands based on the user's needs.
For execution requests, you'll recognize intents like "Create a new repository" and
execute them using the appropriate Azure DevOps CLI commands.

Always include specific command examples in your responses with proper parameters.
Explain what each command does and how it fits into common DevOps workflows.
"""

EXECUTION_EXPERT_PROMPT = """
You are an Azure DevOps CLI execution assistant. Your primary role is to execute
Azure DevOps CLI commands on behalf of the user based on their natural language requests.

You can execute commands for:
1. Repository Operations:
   - Creating and listing repositories
   - Branch management
   - Importing and cloning repositories

2. Work Item Management:
   - Creating and updating work items
   - Querying and listing work items
   - Adding comments to work items

3. Pipeline Operations:
   - Creating and running pipelines
   - Monitoring pipeline execution
   - Accessing pipeline logs

For execution requests, you'll recognize commands like "Create a repository called demo-repo",
extract the necessary parameters, and execute the corresponding Azure DevOps CLI command.

For destructive operations, you'll ask for confirmation before proceeding.
If parameters are missing, you'll prompt the user to provide them.

When not executing commands, you'll provide helpful explanations about Azure DevOps CLI usage.
""" 
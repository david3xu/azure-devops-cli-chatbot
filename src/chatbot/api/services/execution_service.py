"""
Execution service for handling Azure DevOps CLI command execution.
Bridges between conversation intents and actual command execution.
"""
import json
import re
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from src.chatbot.devops_cli import operations
from src.chatbot.devops_cli.command_runner import CommandError
from src.chatbot.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)


class ExecutionMode(str, Enum):
    """Execution modes for the chatbot."""
    LEARN = "learn"  # Explain commands only
    EXECUTE = "execute"  # Execute commands
    AUTO = "auto"  # Determine based on message content


class OperationType(str, Enum):
    """Types of operations supported by the execution service."""
    REPOSITORY = "repository"
    WORK_ITEM = "work_item"
    PIPELINE = "pipeline"
    UNKNOWN = "unknown"


class ExecutionService:
    """
    Service for executing Azure DevOps CLI commands based on conversation intents.
    Handles parameter extraction, command execution, and result formatting.
    """
    
    def __init__(self):
        """Initialize the execution service."""
        # Mapping of intents to operation functions
        self.operation_map = {
            # Repository operations
            "list_repositories": operations.list_repositories,
            "create_repository": operations.create_repository,
            "get_repository": operations.get_repository,
            "delete_repository": operations.delete_repository,
            "list_branches": operations.list_branches,
            "create_branch": operations.create_branch,
            "import_repository": operations.import_repository,
            "clone_repository": operations.clone_repository,
            
            # Work item operations
            "create_work_item": operations.create_work_item,
            "get_work_item": operations.get_work_item,
            "update_work_item": operations.update_work_item,
            "query_work_items": operations.query_work_items,
            "list_work_items": operations.list_work_items,
            "add_comment": operations.add_comment,
            "get_work_item_types": operations.get_work_item_types,
            
            # Pipeline operations
            "list_pipelines": operations.list_pipelines,
            "get_pipeline": operations.get_pipeline,
            "create_pipeline": operations.create_pipeline,
            "delete_pipeline": operations.delete_pipeline,
            "run_pipeline": operations.run_pipeline,
            "list_runs": operations.list_runs,
            "get_run": operations.get_run,
            "get_logs": operations.get_logs,
            "cancel_run": operations.cancel_run,
        }
        
        # Destructive operations that require confirmation
        self.destructive_operations = {
            "delete_repository",
            "delete_pipeline",
            "update_work_item",  # Only when changing status to completed states
        }
        
        # Command patterns for intent detection
        self.intent_patterns = {
            # Repository patterns
            "list_repositories": [
                r"(list|show|get|view)\s+(all\s+)?(repositories|repos)",
                r"(what|which)\s+(repositories|repos)",
            ],
            "create_repository": [
                r"create\s+(a\s+)?(new\s+)?(repository|repo)",
                r"add\s+(a\s+)?(new\s+)?(repository|repo)",
            ],
            "get_repository": [
                r"(show|get|view|find)\s+(repository|repo)(\s+details)?",
                r"(info|information|details)\s+(about|for|on)\s+(repository|repo)",
            ],
            "delete_repository": [
                r"delete\s+(a\s+)?(repository|repo)",
                r"remove\s+(a\s+)?(repository|repo)",
            ],
            "list_branches": [
                r"(list|show|get|view)\s+(all\s+)?(branches)",
                r"(what|which)\s+branches",
            ],
            "create_branch": [
                r"create\s+(a\s+)?(new\s+)?branch",
                r"add\s+(a\s+)?(new\s+)?branch",
            ],
            "import_repository": [
                r"import\s+(a\s+)?(repository|repo)",
                r"(import|bring)\s+(in|over)",
            ],
            "clone_repository": [
                r"clone\s+(a\s+)?(repository|repo)",
                r"(download|get)\s+(a\s+)?(local\s+)?(copy\s+)?(of\s+)?(repository|repo)",
            ],
            
            # Work item patterns
            "create_work_item": [
                r"create\s+(a\s+)?(new\s+)?(work\s+item|task|bug|user\s+story|issue)",
                r"add\s+(a\s+)?(new\s+)?(work\s+item|task|bug|user\s+story|issue)",
            ],
            "get_work_item": [
                r"(show|get|view|find)\s+(work\s+item|task|bug|user\s+story|issue)(\s+details)?",
                r"(info|information|details)\s+(about|for|on)\s+(work\s+item|task|bug|user\s+story|issue)",
            ],
            "update_work_item": [
                r"update\s+(a\s+)?(work\s+item|task|bug|user\s+story|issue)",
                r"(change|modify|edit)\s+(a\s+)?(work\s+item|task|bug|user\s+story|issue)",
                r"(mark|set)\s+(work\s+item|task|bug|user\s+story|issue)\s+(as|to)",
            ],
            "list_work_items": [
                r"(list|show|get|view)\s+(all\s+)?(work\s+items|tasks|bugs|user\s+stories|issues)",
                r"(what|which)\s+(work\s+items|tasks|bugs|user\s+stories|issues)",
            ],
            "add_comment": [
                r"add\s+(a\s+)?comment\s+to",
                r"comment\s+on",
            ],
            
            # Pipeline patterns
            "list_pipelines": [
                r"(list|show|get|view)\s+(all\s+)?(pipelines)",
                r"(what|which)\s+pipelines",
            ],
            "get_pipeline": [
                r"(show|get|view|find)\s+(pipeline)(\s+details)?",
                r"(info|information|details)\s+(about|for|on)\s+(pipeline)",
            ],
            "create_pipeline": [
                r"create\s+(a\s+)?(new\s+)?pipeline",
                r"add\s+(a\s+)?(new\s+)?pipeline",
            ],
            "delete_pipeline": [
                r"delete\s+(a\s+)?pipeline",
                r"remove\s+(a\s+)?pipeline",
            ],
            "run_pipeline": [
                r"run\s+(a\s+)?pipeline",
                r"(start|execute|trigger)\s+(a\s+)?pipeline",
            ],
            "list_runs": [
                r"(list|show|get|view)\s+(all\s+)?(pipeline\s+)?(runs|executions|builds)",
                r"(what|which)\s+(pipeline\s+)?(runs|executions|builds)",
            ],
            "get_logs": [
                r"(show|get|view|find)\s+(pipeline\s+)?(logs|output)",
                r"logs\s+(from|for)",
            ],
            "cancel_run": [
                r"cancel\s+(a\s+)?(pipeline\s+)?(run|execution|build)",
                r"stop\s+(a\s+)?(pipeline\s+)?(run|execution|build)",
            ],
        }
    
    def detect_intent(self, message: str) -> Tuple[str, float]:
        """
        Detect the user's intent from their message.
        
        Args:
            message: The user's message
            
        Returns:
            A tuple of (intent, confidence) where intent is the detected intent
            and confidence is a float between 0 and 1 indicating confidence level
        """
        # Convert message to lowercase for matching
        message_lower = message.lower()
        
        # Check for explicit intent matches
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    # Simple confidence calculation - more specific patterns get higher confidence
                    return intent, 0.8
        
        # No intent detected
        return "unknown", 0.0
    
    def extract_parameters(self, intent: str, message: str) -> Dict[str, Any]:
        """
        Extract parameters from a message based on the detected intent.
        
        Args:
            intent: The detected intent
            message: The user's message
            
        Returns:
            A dictionary of extracted parameters
        """
        params = {}
        
        # Convert message to lowercase for matching
        message_lower = message.lower()
        
        # Extract project name if present 
        project_match = re.search(r"(in|for)\s+project\s+['\"]?([^'\"]+)['\"]?", message)
        if project_match:
            params["project"] = project_match.group(2)
        
        # Extract repository name if present
        repo_match = re.search(r"(repository|repo)\s+['\"]?([^'\"]+)['\"]?", message)
        if repo_match:
            params["name"] = repo_match.group(2)
        
        # Extract name/title if present
        name_match = re.search(r"(named|called|titled)\s+['\"]?([^'\"]+)['\"]?", message)
        if name_match:
            params["name"] = name_match.group(2)
        
        # Extract ID if present
        id_match = re.search(r"(id|number|#)\s*:?\s*(\d+)", message)
        if id_match:
            params["id"] = id_match.group(2)
        
        # Extract work item specific parameters
        if intent == "create_work_item":
            # Extract type
            type_match = re.search(r"(a|an)\s+([a-zA-Z\s]+)\s+(called|named|titled)", message_lower)
            if type_match:
                params["work_item_type"] = type_match.group(2).strip()
            
            # Extract title if not already extracted
            if "name" in params:
                params["title"] = params.pop("name")
            
            # Extract description if present
            desc_match = re.search(r"description\s+['\"]?([^'\"]+)['\"]?", message_lower)
            if desc_match:
                params["description"] = desc_match.group(1)
        
        # Extract branch specific parameters
        if intent == "create_branch":
            # Extract source branch
            source_match = re.search(r"from\s+(branch\s+)?['\"]?([^'\"]+)['\"]?", message_lower)
            if source_match:
                params["source_branch"] = source_match.group(2)
            
            # Default source branch to main if not specified
            if "source_branch" not in params:
                params["source_branch"] = "main"
        
        # Process pipeline specific parameters
        if intent in ["run_pipeline", "get_pipeline", "get_logs"]:
            # Extract pipeline name
            pipeline_match = re.search(r"(pipeline|build)\s+['\"]?([^'\"]+)['\"]?", message_lower)
            if pipeline_match:
                params["name"] = pipeline_match.group(2)
        
        return params
    
    def get_operation_type(self, intent: str) -> OperationType:
        """
        Get the type of operation from the intent.
        
        Args:
            intent: The detected intent
            
        Returns:
            The operation type (REPOSITORY, WORK_ITEM, PIPELINE, or UNKNOWN)
        """
        if intent.startswith(("list_repositories", "create_repository", "get_repository", 
                            "delete_repository", "list_branches", "create_branch", 
                            "import_repository", "clone_repository")):
            return OperationType.REPOSITORY
        elif intent.startswith(("create_work_item", "get_work_item", "update_work_item", 
                             "query_work_items", "list_work_items", "add_comment")):
            return OperationType.WORK_ITEM
        elif intent.startswith(("list_pipelines", "get_pipeline", "create_pipeline", 
                             "delete_pipeline", "run_pipeline", "list_runs", 
                             "get_run", "get_logs", "cancel_run")):
            return OperationType.PIPELINE
        else:
            return OperationType.UNKNOWN
    
    def is_destructive_operation(self, intent: str, params: Dict[str, Any]) -> bool:
        """
        Check if an operation is destructive and requires confirmation.
        
        Args:
            intent: The detected intent
            params: The extracted parameters
            
        Returns:
            True if the operation is destructive, False otherwise
        """
        if intent in self.destructive_operations:
            return True
        
        # Special case: updating work item to a completed state
        if intent == "update_work_item" and "state" in params:
            completed_states = ["closed", "completed", "done", "resolved"]
            return params["state"].lower() in completed_states
        
        return False
    
    def execute_command(self, intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a command based on intent and parameters.
        
        Args:
            intent: The detected intent
            params: The parameters to pass to the command
            
        Returns:
            The result of the command
            
        Raises:
            ValueError: If the intent is not supported
            CommandError: If the command execution fails
        """
        # Check if the intent is supported
        if intent not in self.operation_map:
            raise ValueError(f"Unsupported intent: {intent}")
        
        # Get the operation function
        operation_func = self.operation_map[intent]
        
        try:
            # Execute the command
            logger.info(f"Executing command: {intent}", extra={"params": params})
            result = operation_func(**params)
            logger.info(f"Command executed successfully", extra={"intent": intent})
            return result
        except CommandError as e:
            logger.error(f"Command execution failed", extra={"intent": intent, "error": str(e)})
            raise
        except Exception as e:
            logger.error(f"Unexpected error in command execution", extra={"intent": intent, "error": str(e)}, exc_info=e)
            raise
    
    def format_result(self, intent: str, result: Any) -> str:
        """
        Format a command result for display to the user.
        
        Args:
            intent: The executed intent
            result: The result of the command
            
        Returns:
            A formatted string representation of the result
        """
        # Handle None result
        if result is None:
            return "The command executed successfully, but returned no output."
        
        # Handle string result
        if isinstance(result, str):
            return result
        
        # Handle dictionary or list result
        if isinstance(result, (dict, list)):
            # Format based on intent
            if intent.startswith("list_"):
                if isinstance(result, list):
                    if len(result) == 0:
                        return "No items found."
                    
                    # Format list results based on type
                    if intent == "list_repositories":
                        items = [f"- {repo.get('name', 'Unnamed')} ({repo.get('id', 'No ID')})" for repo in result]
                        return "Repositories:\n" + "\n".join(items)
                    elif intent == "list_work_items":
                        items = [f"- #{item.get('id', 'No ID')}: {item.get('fields', {}).get('System.Title', 'Untitled')}" for item in result]
                        return "Work Items:\n" + "\n".join(items)
                    elif intent == "list_pipelines":
                        items = [f"- {pipe.get('name', 'Unnamed')} (ID: {pipe.get('id', 'No ID')})" for pipe in result]
                        return "Pipelines:\n" + "\n".join(items)
                    elif intent == "list_branches":
                        items = [f"- {branch.get('name', 'Unnamed')}" for branch in result]
                        return "Branches:\n" + "\n".join(items)
                    elif intent == "list_runs":
                        items = [f"- Run #{run.get('id', 'No ID')}: {run.get('name', 'Unnamed')} ({run.get('status', 'Unknown status')})" for run in result]
                        return "Pipeline Runs:\n" + "\n".join(items)
            
            # Handle create operations with nice formatting
            if intent.startswith("create_"):
                if intent == "create_repository":
                    return f"Repository '{result.get('name', 'Unnamed')}' created successfully.\nID: {result.get('id', 'No ID')}\nURL: {result.get('webUrl', 'No URL')}"
                elif intent == "create_work_item":
                    return f"Work Item #{result.get('id', 'No ID')} created successfully.\nTitle: {result.get('fields', {}).get('System.Title', 'Untitled')}\nURL: {result.get('_links', {}).get('html', {}).get('href', 'No URL')}"
                elif intent == "create_branch":
                    return f"Branch '{result.get('name', 'Unnamed')}' created successfully."
                elif intent == "create_pipeline":
                    return f"Pipeline '{result.get('name', 'Unnamed')}' created successfully.\nID: {result.get('id', 'No ID')}"
            
            # Handle get operations
            if intent.startswith("get_"):
                if intent == "get_repository":
                    return f"Repository: {result.get('name', 'Unnamed')}\nID: {result.get('id', 'No ID')}\nURL: {result.get('webUrl', 'No URL')}\nDefault Branch: {result.get('defaultBranch', 'None')}"
                elif intent == "get_work_item":
                    fields = result.get('fields', {})
                    return f"Work Item #{result.get('id', 'No ID')}\nTitle: {fields.get('System.Title', 'Untitled')}\nState: {fields.get('System.State', 'Unknown')}\nAssigned To: {fields.get('System.AssignedTo', {}).get('displayName', 'Unassigned')}\nCreated: {fields.get('System.CreatedDate', 'Unknown')}"
                elif intent == "get_pipeline":
                    return f"Pipeline: {result.get('name', 'Unnamed')}\nID: {result.get('id', 'No ID')}\nFolder: {result.get('folder', 'Root')}"
                elif intent == "get_logs":
                    return f"Logs:\n{result}"
            
            # Handle run operations
            if intent == "run_pipeline":
                return f"Pipeline run initiated.\nRun ID: {result.get('id', 'No ID')}\nState: {result.get('state', 'Unknown')}\nURL: {result.get('_links', {}).get('web', {}).get('href', 'No URL')}"
            
            # Handle update operations
            if intent == "update_work_item":
                fields = result.get('fields', {})
                return f"Work Item #{result.get('id', 'No ID')} updated.\nTitle: {fields.get('System.Title', 'Untitled')}\nState: {fields.get('System.State', 'Unknown')}\nAssigned To: {fields.get('System.AssignedTo', {}).get('displayName', 'Unassigned')}"
            
            # Default to pretty JSON
            try:
                return json.dumps(result, indent=2)
            except:
                return str(result)
        
        # Default string conversion
        return str(result)
    
    def process_execution_request(
        self, 
        message: str, 
        mode: ExecutionMode = ExecutionMode.LEARN
    ) -> Dict[str, Any]:
        """
        Process an execution request from a message.
        
        Args:
            message: The user's message
            mode: The execution mode (LEARN, EXECUTE, or AUTO)
            
        Returns:
            A dictionary containing:
                - intent: The detected intent
                - confidence: The confidence in the detected intent
                - operation_type: The type of operation
                - parameters: The extracted parameters
                - is_destructive: Whether the operation is destructive
                - command: The formatted command (if in LEARN mode)
                - result: The result of the command (if in EXECUTE mode)
                - explanation: An explanation of the command
                - error: Any error that occurred during execution
        """
        result = {
            "intent": None,
            "confidence": 0.0,
            "operation_type": OperationType.UNKNOWN,
            "parameters": {},
            "is_destructive": False,
            "command": None,
            "result": None,
            "explanation": None,
            "error": None,
        }
        
        try:
            # Detect intent
            intent, confidence = self.detect_intent(message)
            result["intent"] = intent
            result["confidence"] = confidence
            
            # If intent is unknown, return early
            if intent == "unknown":
                result["explanation"] = "I couldn't determine what operation you want to perform. Please try phrasing your request differently."
                return result
            
            # Get operation type
            operation_type = self.get_operation_type(intent)
            result["operation_type"] = operation_type
            
            # Extract parameters
            params = self.extract_parameters(intent, message)
            result["parameters"] = params
            
            # Check if the operation is destructive
            is_destructive = self.is_destructive_operation(intent, params)
            result["is_destructive"] = is_destructive
            
            # Format a command representation for explanation purposes
            if intent in self.operation_map:
                func = self.operation_map[intent]
                param_str = ", ".join([f"{k}='{v}'" if isinstance(v, str) else f"{k}={v}" for k, v in params.items()])
                result["command"] = f"{func.__name__}({param_str})"
            
            # Check if we should execute the command based on mode
            should_execute = False
            if mode == ExecutionMode.EXECUTE:
                should_execute = True
            elif mode == ExecutionMode.AUTO:
                # In AUTO mode, execute if confidence is high and we have parameters
                should_execute = confidence > 0.6 and len(params) > 0
            
            # Generate explanation
            if intent.startswith("list_"):
                result["explanation"] = f"I'll retrieve a list of {intent.replace('list_', '')}."
            elif intent.startswith("create_"):
                entity = intent.replace("create_", "")
                result["explanation"] = f"I'll create a new {entity} with the specified parameters."
            elif intent.startswith("get_"):
                entity = intent.replace("get_", "")
                result["explanation"] = f"I'll retrieve information about the specified {entity}."
            elif intent.startswith("update_"):
                entity = intent.replace("update_", "")
                result["explanation"] = f"I'll update the specified {entity} with the new values."
            elif intent.startswith("delete_"):
                entity = intent.replace("delete_", "")
                result["explanation"] = f"I'll delete the specified {entity}."
            else:
                result["explanation"] = f"I'll execute the {intent} operation."
            
            # Add parameter explanation
            if params:
                param_desc = ", ".join([f"{k} = {v}" for k, v in params.items()])
                result["explanation"] += f" Parameters: {param_desc}"
            
            # Execute the command if in appropriate mode
            if should_execute and not is_destructive:
                command_result = self.execute_command(intent, params)
                result["result"] = command_result
                
                # Format the result for display
                formatted_result = self.format_result(intent, command_result)
                result["formatted_result"] = formatted_result
            
        except Exception as e:
            logger.error("Error processing execution request", exc_info=e)
            result["error"] = str(e)
        
        return result


# Create a global instance
execution_service = ExecutionService() 
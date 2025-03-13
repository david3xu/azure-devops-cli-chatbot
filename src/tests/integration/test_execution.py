"""
Integration tests for command execution functionality.
"""
import pytest
from typing import Dict, Any

from src.chatbot.api.services.execution_service import ExecutionMode, execution_service
from src.chatbot.models.conversation import Conversation, EXECUTION_EXPERT_PROMPT


class TestExecution:
    """Test the execution service functionality."""
    
    def test_detect_intent(self):
        """Test intent detection from natural language."""
        test_cases = [
            # Repository operations
            ("Show me all repositories", "list_repositories", 0.8),
            ("List repositories in project MyProject", "list_repositories", 0.8),
            ("Create a new repository called test-repo", "create_repository", 0.8),
            ("Create a repository", "create_repository", 0.8),
            ("Get repository details for my-repo", "get_repository", 0.8),
            ("Show me all branches in repository my-repo", "list_branches", 0.8),
            
            # Work item operations
            ("Show me all work items", "list_work_items", 0.8),
            ("Create a bug titled 'Login not working'", "create_work_item", 0.8),
            ("Get work item details for ID 123", "get_work_item", 0.8),
            ("Update work item 123 to resolved", "update_work_item", 0.8),
            
            # Pipeline operations
            ("Show me all pipelines", "list_pipelines", 0.8),
            ("Run the build pipeline", "run_pipeline", 0.8),
            ("Show me pipeline logs", "get_logs", 0.8),
            
            # Unknown intent
            ("What's the weather today?", "unknown", 0.0),
            ("Hello there!", "unknown", 0.0),
        ]
        
        for message, expected_intent, expected_confidence in test_cases:
            intent, confidence = execution_service.detect_intent(message)
            assert intent == expected_intent, f"Expected intent '{expected_intent}' for message '{message}', but got '{intent}'"
            assert confidence == expected_confidence, f"Expected confidence {expected_confidence} for message '{message}', but got {confidence}"
    
    def test_parameter_extraction(self):
        """Test parameter extraction from natural language."""
        test_cases = [
            # Repository operations
            (
                "list_repositories", 
                "List repositories in project MyProject", 
                {"project": "MyProject"},
            ),
            (
                "create_repository", 
                "Create a new repository called test-repo in project MyProject", 
                {"name": "test-repo", "project": "MyProject"},
            ),
            (
                "get_repository", 
                "Get details for repository my-repo", 
                {"name": "my-repo"},
            ),
            (
                "list_branches", 
                "Show branches in repository frontend", 
                {"name": "frontend"},
            ),
            (
                "create_branch", 
                "Create a branch named feature/auth from main in repo api", 
                {"name": "feature/auth", "source_branch": "main"},
            ),
            
            # Work item operations
            (
                "create_work_item", 
                "Create a bug titled 'Login not working' in project MyProject", 
                {"title": "Login not working", "project": "MyProject"},
            ),
            (
                "get_work_item", 
                "Get work item #123", 
                {"id": "123"},
            ),
            (
                "update_work_item", 
                "Update work item 123 to resolved", 
                {"id": "123"},
            ),
            
            # Pipeline operations
            (
                "run_pipeline", 
                "Run the build pipeline 'nightly-build'", 
                {"name": "nightly-build"},
            ),
        ]
        
        for intent, message, expected_params in test_cases:
            params = execution_service.extract_parameters(intent, message)
            for key, value in expected_params.items():
                assert key in params, f"Expected parameter '{key}' for message '{message}', but it was not extracted"
                assert params[key] == value, f"Expected parameter '{key}' to have value '{value}' for message '{message}', but got '{params[key]}'"
    
    def test_is_destructive_operation(self):
        """Test destructive operation identification."""
        test_cases = [
            # Destructive operations
            ("delete_repository", {}, True),
            ("delete_pipeline", {}, True),
            ("update_work_item", {"state": "closed"}, True),
            ("update_work_item", {"state": "resolved"}, True),
            
            # Non-destructive operations
            ("list_repositories", {}, False),
            ("create_repository", {}, False),
            ("update_work_item", {"title": "New title"}, False),
            ("update_work_item", {"state": "active"}, False),
        ]
        
        for intent, params, expected_result in test_cases:
            result = execution_service.is_destructive_operation(intent, params)
            assert result == expected_result, f"Expected is_destructive_operation({intent}, {params}) to be {expected_result}, but got {result}"
    
    def test_format_result(self):
        """Test result formatting for display."""
        test_cases = [
            # String result
            ("list_repositories", "No repositories found", "No repositories found"),
            
            # List result
            (
                "list_repositories", 
                [{"name": "repo1", "id": "1"}, {"name": "repo2", "id": "2"}],
                "Repositories:\n- repo1 (1)\n- repo2 (2)",
            ),
            
            # Dictionary result
            (
                "create_repository", 
                {"name": "new-repo", "id": "123", "webUrl": "https://example.com/repo"},
                "Repository 'new-repo' created successfully.\nID: 123\nURL: https://example.com/repo",
            ),
            
            # None result
            ("create_branch", None, "The command executed successfully, but returned no output."),
        ]
        
        for intent, result, expected_output in test_cases:
            output = execution_service.format_result(intent, result)
            assert output == expected_output, f"Expected format_result({intent}, {result}) to be '{expected_output}', but got '{output}'"
    
    def test_process_execution_request_learn_mode(self):
        """Test processing execution requests in LEARN mode."""
        # In LEARN mode, commands should be explained but not executed
        result = execution_service.process_execution_request(
            "Create a repository called test-repo", 
            ExecutionMode.LEARN
        )
        
        assert result["intent"] == "create_repository", "Intent should be detected correctly"
        assert "parameters" in result, "Parameters should be extracted"
        assert result["parameters"].get("name") == "test-repo", "Repository name should be extracted"
        assert "command" in result, "Command representation should be included"
        assert "result" not in result or result["result"] is None, "Command should not be executed in LEARN mode"
    
    def test_process_execution_request_execute_mode(self):
        """Test processing execution requests in EXECUTE mode."""
        # Create a mock function that will be called instead of the actual command
        original_execute_command = execution_service.execute_command
        executed = {"called": False, "intent": None, "params": None}
        
        def mock_execute_command(intent, params):
            executed["called"] = True
            executed["intent"] = intent
            executed["params"] = params
            if intent == "create_repository":
                return {"name": params.get("name", "unnamed"), "id": "mock-id", "webUrl": "https://example.com/repo"}
            return None
        
        try:
            # Replace the execute_command method with our mock
            execution_service.execute_command = mock_execute_command
            
            # Test execute mode
            result = execution_service.process_execution_request(
                "Create a repository called test-repo", 
                ExecutionMode.EXECUTE
            )
            
            # Verify that the mock was called
            assert executed["called"], "execute_command should be called in EXECUTE mode"
            assert executed["intent"] == "create_repository", "Intent should be passed to execute_command"
            assert executed["params"].get("name") == "test-repo", "Parameters should be passed to execute_command"
            
            # Verify the result
            assert "result" in result, "Command result should be included in EXECUTE mode"
            assert "formatted_result" in result, "Formatted result should be included in EXECUTE mode"
            assert "test-repo" in result["formatted_result"], "Repository name should be in the formatted result"
            
        finally:
            # Restore the original method
            execution_service.execute_command = original_execute_command
    
    def test_process_execution_request_auto_mode(self):
        """Test processing execution requests in AUTO mode."""
        # In AUTO mode, commands with high confidence and parameters should be executed
        # Create a mock function that will be called instead of the actual command
        original_execute_command = execution_service.execute_command
        executed = {"called": False}
        
        def mock_execute_command(intent, params):
            executed["called"] = True
            if intent == "create_repository":
                return {"name": params.get("name", "unnamed"), "id": "mock-id", "webUrl": "https://example.com/repo"}
            return None
        
        try:
            # Replace the execute_command method with our mock
            execution_service.execute_command = mock_execute_command
            
            # Test auto mode with a clear command
            result = execution_service.process_execution_request(
                "Create a repository called test-repo", 
                ExecutionMode.AUTO
            )
            
            # Verify that the mock was called
            assert executed["called"], "execute_command should be called in AUTO mode for clear commands"
            
            # Reset the mock
            executed["called"] = False
            
            # Test auto mode with an unclear command
            result = execution_service.process_execution_request(
                "How do I create a repository?", 
                ExecutionMode.AUTO
            )
            
            # Verify that the mock was not called
            assert not executed["called"], "execute_command should not be called in AUTO mode for unclear commands"
            
        finally:
            # Restore the original method
            execution_service.execute_command = original_execute_command
    
    def test_conversation_integration(self):
        """Test integration with the conversation model."""
        # Create a mock function for execute_command
        original_execute_command = execution_service.execute_command
        executed = {"called": False, "intent": None, "params": None}
        
        def mock_execute_command(intent, params):
            executed["called"] = True
            executed["intent"] = intent
            executed["params"] = params
            if intent == "list_repositories":
                return [{"name": "repo1", "id": "1"}, {"name": "repo2", "id": "2"}]
            return None
        
        try:
            # Replace the execute_command method with our mock
            execution_service.execute_command = mock_execute_command
            
            # Create a conversation in EXECUTE mode
            conversation = Conversation(system_prompt=EXECUTION_EXPERT_PROMPT)
            conversation.set_execution_mode(ExecutionMode.EXECUTE)
            
            # Add a user message requesting command execution
            conversation.add_user_message("Show me all repositories")
            
            # Get a response (this would normally be awaited, but we're just testing the execution path)
            # This will raise an error because we're not actually awaiting it, but we just want to verify
            # that the mock was called
            try:
                conversation.get_response()
            except:
                pass
            
            # Verify that the mock was called
            assert executed["called"], "execute_command should be called via conversation in EXECUTE mode"
            assert executed["intent"] == "list_repositories", "Correct intent should be detected and passed to execute_command"
            
        finally:
            # Restore the original method
            execution_service.execute_command = original_execute_command 
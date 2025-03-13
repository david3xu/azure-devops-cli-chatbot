"""
Unit tests for the Conversation model.
"""
import json
import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Fix import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.chatbot.models.conversation import Conversation, Message

# Skip tests if Azure OpenAI API key is not set
import pytest
from src.chatbot.config.settings import settings

# Use pytest.mark.skipif to skip tests if Azure OpenAI API key is not set
needs_azure_openai = pytest.mark.skipif(
    not settings.AZURE_OPENAI_API_KEY,
    reason="Azure OpenAI API key not set, skipping tests that require API access"
)

class TestMessage(unittest.TestCase):
    """Test cases for the Message class."""
    
    def test_message_initialization(self):
        """Test that a message can be initialized with role and content."""
        message = Message(role="user", content="Hello")
        self.assertEqual(message.role, "user")
        self.assertEqual(message.content, "Hello")
        
    def test_message_to_dict(self):
        """Test that a message can be converted to a dictionary."""
        message = Message(role="user", content="Hello")
        message_dict = message.to_dict()
        self.assertEqual(message_dict, {"role": "user", "content": "Hello"})
        
    def test_message_from_dict(self):
        """Test that a message can be created from a dictionary."""
        message_dict = {"role": "assistant", "content": "How can I help?"}
        message = Message.from_dict(message_dict)
        self.assertEqual(message.role, "assistant")
        self.assertEqual(message.content, "How can I help?")
        
    def test_message_str(self):
        """Test the string representation of a message."""
        message = Message(role="user", content="Hello")
        self.assertEqual(str(message), "user: Hello")


class TestConversation(unittest.TestCase):
    """Test cases for the Conversation class."""
    
    def setUp(self):
        """Set up a conversation for testing."""
        self.conversation = Conversation(system_prompt="You are a helpful assistant.")
        
    def test_conversation_initialization(self):
        """Test that a conversation is initialized with a system prompt."""
        self.assertEqual(len(self.conversation.messages), 1)
        self.assertEqual(self.conversation.messages[0].role, "system")
        self.assertEqual(self.conversation.messages[0].content, "You are a helpful assistant.")
        
    def test_add_message(self):
        """Test adding a message to the conversation."""
        self.conversation.add_message("user", "Hello")
        self.assertEqual(len(self.conversation.messages), 2)
        self.assertEqual(self.conversation.messages[1].role, "user")
        self.assertEqual(self.conversation.messages[1].content, "Hello")
        
    def test_get_messages_for_api(self):
        """Test getting messages in the format required by the API."""
        self.conversation.add_message("user", "Hello")
        messages = self.conversation.get_messages_for_api()
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")
        
    @needs_azure_openai
    def test_get_response_real(self):
        """Test getting a response from the API using real Azure OpenAI credentials."""
        # This test will be skipped if Azure OpenAI API key is not set
        self.conversation.add_message("user", "What is Azure DevOps?")
        response = self.conversation.get_response()
        
        # Check that we got a response
        self.assertIsNotNone(response)
        self.assertTrue(isinstance(response, str))
        self.assertTrue(len(response) > 0)
        
        # Check that the response was added to the conversation
        self.assertEqual(len(self.conversation.messages), 3)
        self.assertEqual(self.conversation.messages[2].role, "assistant")
        self.assertEqual(self.conversation.messages[2].content, response)
        
    def test_to_json(self):
        """Test converting a conversation to JSON."""
        self.conversation.add_message("user", "Hello")
        self.conversation.add_message("assistant", "Hi there!")
        json_str = self.conversation.to_json()
        
        # Parse the JSON string back to a dictionary
        conversation_dict = json.loads(json_str)
        
        self.assertEqual(len(conversation_dict["messages"]), 3)
        self.assertEqual(conversation_dict["messages"][0]["role"], "system")
        self.assertEqual(conversation_dict["messages"][1]["role"], "user")
        self.assertEqual(conversation_dict["messages"][2]["role"], "assistant")
        
    def test_from_json(self):
        """Test creating a conversation from JSON."""
        json_str = json.dumps({
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]
        })
        
        conversation = Conversation.from_json(json_str)
        
        self.assertEqual(len(conversation.messages), 3)
        self.assertEqual(conversation.messages[0].role, "system")
        self.assertEqual(conversation.messages[1].role, "user")
        self.assertEqual(conversation.messages[2].role, "assistant")
        
    def test_clear_messages(self):
        """Test clearing all messages except the system prompt."""
        self.conversation.add_message("user", "Hello")
        self.conversation.add_message("assistant", "Hi there!")
        self.conversation.clear_messages()
        
        self.assertEqual(len(self.conversation.messages), 1)
        self.assertEqual(self.conversation.messages[0].role, "system")


if __name__ == "__main__":
    unittest.main() 
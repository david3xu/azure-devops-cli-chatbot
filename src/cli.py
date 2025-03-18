#!/usr/bin/env python
"""
CLI interface for interacting with the Azure DevOps CLI Learning Project Chatbot.
Allows direct conversation with the chatbot from the terminal.
"""
import argparse
import asyncio
import os
import sys

from src.chatbot.api.services.execution_service import ExecutionMode
from src.chatbot.config.settings import settings
from src.chatbot.models.conversation import (
    Conversation, 
    DEFAULT_SYSTEM_PROMPT,
    DEVOPS_CLI_EXPERT_PROMPT,
    EXECUTION_EXPERT_PROMPT
)
from src.chatbot.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)


async def main():
    """Run the CLI interface."""
    parser = argparse.ArgumentParser(
        description="Azure DevOps CLI Learning Project Chatbot CLI"
    )
    parser.add_argument(
        "--mode", 
        choices=["general", "devops-expert", "execution"], 
        default="general",
        help="Conversation mode"
    )
    parser.add_argument(
        "--execution-mode", 
        choices=["learn", "execute", "auto"], 
        default="learn",
        help="Command execution mode: learn (explain only), execute (perform commands), auto (determine based on message)"
    )
    parser.add_argument(
        "--temperature", 
        type=float, 
        default=0.7,
        help="Temperature for response generation (0.0-1.0)"
    )
    args = parser.parse_args()
    
    # Print welcome message
    print("\n======================================================")
    print("  Azure DevOps CLI Learning Project Chatbot")
    print("======================================================")
    print("Type 'exit', 'quit', or Ctrl+C to end the conversation.")
    print("Type 'mode learn|execute|auto' to change execution mode.\n")
    
    # Select prompt based on mode
    if args.mode == "devops-expert":
        system_prompt = DEVOPS_CLI_EXPERT_PROMPT
        print("Mode: Azure DevOps CLI Expert")
    elif args.mode == "execution":
        system_prompt = EXECUTION_EXPERT_PROMPT
        print("Mode: Azure DevOps CLI Execution Assistant")
    else:
        system_prompt = DEFAULT_SYSTEM_PROMPT
        print("Mode: General Assistant")
    
    # Parse execution mode
    try:
        execution_mode = ExecutionMode(args.execution_mode.lower())
        print(f"Execution Mode: {execution_mode.value.capitalize()}")
    except ValueError:
        print(f"Invalid execution mode: {args.execution_mode}, using default (learn)")
        execution_mode = ExecutionMode.LEARN
    
    print()
    
    # Create conversation
    conversation = Conversation(system_prompt=system_prompt)
    conversation.set_execution_mode(execution_mode)
    
    # Interactive loop
    try:
        while True:
            # Get user input
            user_input = input("\nYou: ")
            
            # Check for exit command
            if user_input.lower() in ["exit", "quit"]:
                print("\nGoodbye!")
                break
            
            # Check for mode change command
            if user_input.lower().startswith("mode "):
                mode_arg = user_input.lower().split("mode ")[1].strip()
                try:
                    new_mode = ExecutionMode(mode_arg)
                    conversation.set_execution_mode(new_mode)
                    print(f"\nExecution mode changed to: {new_mode.value.capitalize()}")
                    continue
                except ValueError:
                    print(f"\nInvalid execution mode: {mode_arg}. Valid options: learn, execute, auto")
                    continue
            
            # Add user message and get response
            conversation.add_user_message(user_input)
            
            print("\nChatbot: ", end="", flush=True)
            
            try:
                response = await conversation.get_response(temperature=args.temperature)
                print(response)
            except Exception as e:
                logger.error("Error getting response", exc_info=e)
                print("I encountered an error while processing your request. Please try again.")
    
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    
    except Exception as e:
        logger.error("Unexpected error", exc_info=e)
        print(f"\nAn unexpected error occurred: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 
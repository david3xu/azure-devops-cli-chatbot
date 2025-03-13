"""
Command runner for Azure DevOps CLI operations.
Provides utilities for executing commands and parsing output.
"""
import json
import logging
import subprocess
from typing import Any, Dict, List, Optional, Tuple, Union

from src.chatbot.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)


class CommandError(Exception):
    """Exception raised for errors in the command execution."""
    
    def __init__(self, command: str, return_code: int, stderr: str):
        self.command = command
        self.return_code = return_code
        self.stderr = stderr
        message = f"Command '{command}' failed with exit code {return_code}: {stderr}"
        super().__init__(message)


class CommandRunner:
    """Utility class for running Azure CLI and DevOps CLI commands."""
    
    @staticmethod
    def run_command(
        command: str,
        parse_json: bool = True,
        check: bool = True,
        timeout: int = 60
    ) -> Union[Dict[str, Any], List[Any], str, None]:
        """
        Run a command and return the output.
        
        Args:
            command: The command to run.
            parse_json: Whether to parse the output as JSON.
            check: Whether to check the return code and raise an exception on non-zero exit.
            timeout: Command timeout in seconds.
            
        Returns:
            The command output, parsed as JSON if parse_json is True, otherwise as a string.
            
        Raises:
            CommandError: If the command fails and check is True.
        """
        logger.debug(f"Running command: {command}")
        
        try:
            # Run the command
            completed_process = subprocess.run(
                command,
                shell=True,
                text=True,
                capture_output=True,
                timeout=timeout
            )
            
            # Get output and error
            stdout = completed_process.stdout.strip()
            stderr = completed_process.stderr.strip()
            return_code = completed_process.returncode
            
            # Log the output for debugging
            if stdout:
                logger.debug(f"Command stdout: {stdout[:500]}..." if len(stdout) > 500 else f"Command stdout: {stdout}")
            if stderr:
                logger.debug(f"Command stderr: {stderr[:500]}..." if len(stderr) > 500 else f"Command stderr: {stderr}")
            
            # Check for errors
            if return_code != 0 and check:
                raise CommandError(command, return_code, stderr)
            
            # Parse output as JSON if requested
            if parse_json and stdout:
                try:
                    return json.loads(stdout)
                except json.JSONDecodeError as e:
                    if check:
                        logger.error(f"Failed to parse command output as JSON: {e}")
                        logger.debug(f"Command output: {stdout}")
                        raise CommandError(command, 0, f"Failed to parse output as JSON: {e}")
                    return stdout
            
            # Return raw output if not parsing as JSON
            return stdout if stdout else None
            
        except subprocess.TimeoutExpired:
            if check:
                raise CommandError(command, -1, f"Command timed out after {timeout} seconds")
            return None
        
        except Exception as e:
            if check:
                raise CommandError(command, -1, str(e))
            return None
    
    @staticmethod
    def az_command(
        command: str,
        output_format: str = "json",
        check: bool = True,
        timeout: int = 60
    ) -> Union[Dict[str, Any], List[Any], str, None]:
        """
        Run an Azure CLI command.
        
        Args:
            command: The Azure CLI command to run (without 'az' prefix).
            output_format: Output format (json, table, tsv, yaml).
            check: Whether to check the return code and raise an exception on non-zero exit.
            timeout: Command timeout in seconds.
            
        Returns:
            The command output, parsed as JSON if output_format is 'json', otherwise as a string.
        """
        full_command = f"az {command} -o {output_format}"
        parse_json = output_format == "json"
        
        return CommandRunner.run_command(
            command=full_command,
            parse_json=parse_json,
            check=check,
            timeout=timeout
        )
    
    @staticmethod
    def devops_command(
        command: str,
        output_format: str = "json",
        check: bool = True,
        timeout: int = 60
    ) -> Union[Dict[str, Any], List[Any], str, None]:
        """
        Run an Azure DevOps CLI command.
        
        Args:
            command: The Azure DevOps CLI command to run (without 'az devops' prefix).
            output_format: Output format (json, table, tsv, yaml).
            check: Whether to check the return code and raise an exception on non-zero exit.
            timeout: Command timeout in seconds.
            
        Returns:
            The command output, parsed as JSON if output_format is 'json', otherwise as a string.
        """
        full_command = f"az devops {command} -o {output_format}"
        parse_json = output_format == "json"
        
        return CommandRunner.run_command(
            command=full_command,
            parse_json=parse_json,
            check=check,
            timeout=timeout
        )


# Create a global instance
command_runner = CommandRunner() 
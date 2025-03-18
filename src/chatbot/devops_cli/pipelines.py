"""
Azure DevOps CLI pipeline operations.
Provides functions for managing pipelines through the Azure DevOps CLI.
"""
from typing import Any, Dict, List, Optional, Union

from src.chatbot.devops_cli.command_runner import command_runner
from src.chatbot.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)


def list_pipelines(
    organization: Optional[str] = None,
    project: Optional[str] = None,
    folder_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List pipelines in an Azure DevOps project.
    
    Args:
        organization: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
        project: Azure DevOps project name
        folder_path: Folder path to filter pipelines
        
    Returns:
        List of pipelines
    """
    command = "pipelines list"
    
    if organization:
        command += f" --org {organization}"
    
    if project:
        command += f" --project {project}"
    
    if folder_path:
        command += f" --folder-path \"{folder_path}\""
    
    logger.info(f"Listing pipelines for {project or 'default project'}")
    return command_runner.devops_command(command)


def get_pipeline(
    pipeline_id: int,
    organization: Optional[str] = None,
    project: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get details for a specific pipeline.
    
    Args:
        pipeline_id: Pipeline ID
        organization: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
        project: Azure DevOps project name
        
    Returns:
        Pipeline details
    """
    command = f"pipelines show --id {pipeline_id}"
    
    if organization:
        command += f" --org {organization}"
    
    if project:
        command += f" --project {project}"
    
    logger.info(f"Getting pipeline details for ID {pipeline_id}")
    return command_runner.devops_command(command)


def create_pipeline(
    name: str,
    repository: str,
    branch: str = "main",
    yaml_path: str = "azure-pipelines.yml",
    organization: Optional[str] = None,
    project: Optional[str] = None,
    folder_path: Optional[str] = None,
    skip_first_run: bool = False
) -> Dict[str, Any]:
    """
    Create a new pipeline.
    
    Args:
        name: Pipeline name
        repository: Repository name or ID
        branch: Branch name to build from (default: main)
        yaml_path: Path to pipeline YAML file (default: azure-pipelines.yml)
        organization: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
        project: Azure DevOps project name
        folder_path: Folder path to create pipeline in
        skip_first_run: Skip first pipeline run
        
    Returns:
        Created pipeline details
    """
    command = f"pipelines create --name \"{name}\" --repository \"{repository}\" --branch {branch} --yml-path {yaml_path}"
    
    if organization:
        command += f" --org {organization}"
    
    if project:
        command += f" --project {project}"
    
    if folder_path:
        command += f" --folder-path \"{folder_path}\""
    
    if skip_first_run:
        command += " --skip-first-run"
    
    logger.info(f"Creating pipeline {name} from repository {repository}")
    return command_runner.devops_command(command)


def delete_pipeline(
    pipeline_id: int,
    organization: Optional[str] = None,
    project: Optional[str] = None,
    yes: bool = False
) -> None:
    """
    Delete a pipeline.
    
    Args:
        pipeline_id: Pipeline ID
        organization: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
        project: Azure DevOps project name
        yes: Automatically confirm the delete operation
        
    Returns:
        None
    """
    command = f"pipelines delete --id {pipeline_id}"
    
    if organization:
        command += f" --org {organization}"
    
    if project:
        command += f" --project {project}"
    
    if yes:
        command += " --yes"
    
    logger.info(f"Deleting pipeline {pipeline_id}")
    return command_runner.devops_command(command)


def run_pipeline(
    pipeline_id: int,
    organization: Optional[str] = None,
    project: Optional[str] = None,
    branch: Optional[str] = None,
    variables: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Run a pipeline.
    
    Args:
        pipeline_id: Pipeline ID
        organization: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
        project: Azure DevOps project name
        branch: Branch to run the pipeline on
        variables: Dictionary of variables to pass to the pipeline
        
    Returns:
        Pipeline run details
    """
    command = f"pipelines run --id {pipeline_id}"
    
    if organization:
        command += f" --org {organization}"
    
    if project:
        command += f" --project {project}"
    
    if branch:
        command += f" --branch {branch}"
    
    # Add variables if provided
    if variables and isinstance(variables, dict):
        for var_name, var_value in variables.items():
            command += f" --variables {var_name}={var_value}"
    
    logger.info(f"Running pipeline {pipeline_id}")
    return command_runner.devops_command(command)


def list_runs(
    pipeline_id: int,
    organization: Optional[str] = None,
    project: Optional[str] = None,
    top: Optional[int] = None,
    branch: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List runs for a pipeline.
    
    Args:
        pipeline_id: Pipeline ID
        organization: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
        project: Azure DevOps project name
        top: Number of runs to get
        branch: Filter runs by branch
        
    Returns:
        List of pipeline runs
    """
    command = f"pipelines runs list --pipeline-id {pipeline_id}"
    
    if organization:
        command += f" --org {organization}"
    
    if project:
        command += f" --project {project}"
    
    if top:
        command += f" --top {top}"
    
    if branch:
        command += f" --branch {branch}"
    
    logger.info(f"Listing runs for pipeline {pipeline_id}")
    return command_runner.devops_command(command)


def get_run(
    run_id: int,
    organization: Optional[str] = None,
    project: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get details for a specific pipeline run.
    
    Args:
        run_id: Pipeline run ID
        organization: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
        project: Azure DevOps project name
        
    Returns:
        Pipeline run details
    """
    command = f"pipelines runs show --id {run_id}"
    
    if organization:
        command += f" --org {organization}"
    
    if project:
        command += f" --project {project}"
    
    logger.info(f"Getting details for pipeline run {run_id}")
    return command_runner.devops_command(command)


def get_logs(
    run_id: int,
    organization: Optional[str] = None,
    project: Optional[str] = None
) -> str:
    """
    Get logs for a pipeline run.
    
    Args:
        run_id: Pipeline run ID
        organization: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
        project: Azure DevOps project name
        
    Returns:
        Pipeline run logs
    """
    command = f"pipelines runs logs --id {run_id}"
    
    if organization:
        command += f" --org {organization}"
    
    if project:
        command += f" --project {project}"
    
    logger.info(f"Getting logs for pipeline run {run_id}")
    # Use table format for readability
    return command_runner.devops_command(command, output_format="table")


def cancel_run(
    run_id: int,
    organization: Optional[str] = None,
    project: Optional[str] = None
) -> Dict[str, Any]:
    """
    Cancel a pipeline run.
    
    Args:
        run_id: Pipeline run ID
        organization: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
        project: Azure DevOps project name
        
    Returns:
        Pipeline run details
    """
    command = f"pipelines runs cancel --id {run_id}"
    
    if organization:
        command += f" --org {organization}"
    
    if project:
        command += f" --project {project}"
    
    logger.info(f"Cancelling pipeline run {run_id}")
    return command_runner.devops_command(command) 
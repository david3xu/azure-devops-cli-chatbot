"""
Azure DevOps CLI repository operations.
Provides functions for managing repositories through the Azure DevOps CLI.
"""
from typing import Any, Dict, List, Optional, Union

from src.chatbot.devops_cli.command_runner import command_runner
from src.chatbot.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)


def list_repositories(
    organization: Optional[str] = None,
    project: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List repositories in an Azure DevOps project.
    
    Args:
        organization: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
        project: Azure DevOps project name
        
    Returns:
        List of repositories
    """
    command = "repos list"
    
    if organization:
        command += f" --org {organization}"
    
    if project:
        command += f" --project {project}"
    
    logger.info(f"Listing repositories for {project or 'default project'}")
    return command_runner.devops_command(command)


def get_repository(
    repository: str,
    organization: Optional[str] = None,
    project: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get details for a specific repository.
    
    Args:
        repository: Repository name or ID
        organization: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
        project: Azure DevOps project name
        
    Returns:
        Repository details
    """
    command = f"repos show --repository {repository}"
    
    if organization:
        command += f" --org {organization}"
    
    if project:
        command += f" --project {project}"
    
    logger.info(f"Getting repository details for {repository}")
    return command_runner.devops_command(command)


def create_repository(
    name: str,
    project: Optional[str] = None, 
    organization: Optional[str] = None,
    default_branch: Optional[str] = "main"
) -> Dict[str, Any]:
    """
    Create a new Git repository.
    
    Args:
        name: Repository name
        project: Azure DevOps project name
        organization: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
        default_branch: Default branch name (default: main)
        
    Returns:
        Created repository details
    """
    command = f"repos create --name {name}"
    
    if organization:
        command += f" --org {organization}"
    
    if project:
        command += f" --project {project}"
        
    if default_branch:
        command += f" --default-branch {default_branch}"
    
    logger.info(f"Creating repository {name} in project {project or 'default project'}")
    return command_runner.devops_command(command)


def delete_repository(
    repository: str,
    project: Optional[str] = None,
    organization: Optional[str] = None,
    yes: bool = False
) -> None:
    """
    Delete a Git repository.
    
    Args:
        repository: Repository name or ID
        project: Azure DevOps project name
        organization: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
        yes: Automatically confirm the delete operation
        
    Returns:
        None
    """
    command = f"repos delete --repository {repository}"
    
    if organization:
        command += f" --org {organization}"
    
    if project:
        command += f" --project {project}"
        
    if yes:
        command += " --yes"
    
    logger.info(f"Deleting repository {repository} from project {project or 'default project'}")
    return command_runner.devops_command(command)


def list_branches(
    repository: str,
    project: Optional[str] = None,
    organization: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List branches in a Git repository.
    
    Args:
        repository: Repository name or ID
        project: Azure DevOps project name
        organization: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
        
    Returns:
        List of branches
    """
    command = f"repos ref list --repository {repository}"
    
    if organization:
        command += f" --org {organization}"
    
    if project:
        command += f" --project {project}"
    
    logger.info(f"Listing branches for repository {repository}")
    return command_runner.devops_command(command)


def create_branch(
    name: str,
    repository: str,
    source_branch: str = "main",
    project: Optional[str] = None,
    organization: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new branch in a Git repository.
    
    Args:
        name: Branch name
        repository: Repository name or ID
        source_branch: Source branch to create from (default: main)
        project: Azure DevOps project name
        organization: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
        
    Returns:
        Branch details
    """
    command = f"repos ref create --name {name} --repository {repository} --source-branch {source_branch}"
    
    if organization:
        command += f" --org {organization}"
    
    if project:
        command += f" --project {project}"
    
    logger.info(f"Creating branch {name} in repository {repository} from {source_branch}")
    return command_runner.devops_command(command)


def import_repository(
    git_url: str,
    repository: str,
    project: Optional[str] = None,
    organization: Optional[str] = None
) -> Dict[str, Any]:
    """
    Import a Git repository from a URL.
    
    Args:
        git_url: Git source URL to import from
        repository: Repository name or ID to import into
        project: Azure DevOps project name
        organization: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
        
    Returns:
        Repository details
    """
    command = f"repos import create --git-source-url {git_url} --repository {repository}"
    
    if organization:
        command += f" --org {organization}"
    
    if project:
        command += f" --project {project}"
    
    logger.info(f"Importing repository from {git_url} to {repository}")
    return command_runner.devops_command(command)


def clone_repository(
    repository: str,
    path: Optional[str] = None,
    project: Optional[str] = None,
    organization: Optional[str] = None
) -> str:
    """
    Clone a Git repository locally.
    
    Args:
        repository: Repository name or ID
        path: Local path to clone to
        project: Azure DevOps project name
        organization: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
        
    Returns:
        Command output
    """
    # First get repo URL
    repo_details = get_repository(repository, organization, project)
    repo_url = repo_details.get('remoteUrl')
    
    if not repo_url:
        logger.error(f"Failed to get URL for repository {repository}")
        raise ValueError(f"Failed to get URL for repository {repository}")
    
    # Build git clone command
    command = f"git clone {repo_url}"
    
    if path:
        command += f" {path}"
    
    logger.info(f"Cloning repository {repository} to {path or 'current directory'}")
    return command_runner.run_command(command, parse_json=False)


def get_clone_url(
    repository: str,
    project: Optional[str] = None,
    organization: Optional[str] = None
) -> str:
    """
    Get the clone URL for a Git repository.
    
    Args:
        repository: Repository name or ID
        project: Azure DevOps project name
        organization: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
        
    Returns:
        Repository clone URL
    """
    repo_details = get_repository(repository, organization, project)
    repo_url = repo_details.get('remoteUrl')
    
    if not repo_url:
        logger.error(f"Failed to get URL for repository {repository}")
        raise ValueError(f"Failed to get URL for repository {repository}")
    
    return repo_url 
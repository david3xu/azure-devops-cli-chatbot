"""
Azure DevOps CLI work item operations.
Provides functions for managing work items through the Azure DevOps CLI.
"""
from typing import Any, Dict, List, Optional, Union

from src.chatbot.devops_cli.command_runner import command_runner
from src.chatbot.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)


def create_work_item(
    title: str,
    work_item_type: str,
    project: Optional[str] = None,
    organization: Optional[str] = None,
    description: Optional[str] = None,
    assigned_to: Optional[str] = None,
    area_path: Optional[str] = None,
    iteration_path: Optional[str] = None,
    fields: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create a new work item.
    
    Args:
        title: Work item title
        work_item_type: Work item type (e.g., Bug, Task, User Story)
        project: Azure DevOps project name
        organization: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
        description: Work item description
        assigned_to: User to assign work item to
        area_path: Area path for the work item
        iteration_path: Iteration path for the work item
        fields: Additional fields to set on the work item
        
    Returns:
        Created work item details
    """
    command = f"boards work-item create --title \"{title}\" --type \"{work_item_type}\""
    
    if organization:
        command += f" --org {organization}"
    
    if project:
        command += f" --project {project}"
    
    if description:
        command += f" --description \"{description}\""
    
    if assigned_to:
        command += f" --assigned-to \"{assigned_to}\""
    
    if area_path:
        command += f" --area \"{area_path}\""
    
    if iteration_path:
        command += f" --iteration \"{iteration_path}\""
    
    # Add custom fields if provided
    if fields and isinstance(fields, dict):
        for field_name, field_value in fields.items():
            command += f" --fields \"{field_name}={field_value}\""
    
    logger.info(f"Creating work item of type {work_item_type}: {title}")
    return command_runner.devops_command(command)


def get_work_item(
    work_item_id: int,
    organization: Optional[str] = None,
    project: Optional[str] = None,
    expand: bool = False
) -> Dict[str, Any]:
    """
    Get details for a specific work item.
    
    Args:
        work_item_id: Work item ID
        organization: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
        project: Azure DevOps project name
        expand: Whether to expand relations and fields
        
    Returns:
        Work item details
    """
    command = f"boards work-item show --id {work_item_id}"
    
    if organization:
        command += f" --org {organization}"
    
    if project:
        command += f" --project {project}"
    
    if expand:
        command += " --expand"
    
    logger.info(f"Getting work item details for ID {work_item_id}")
    return command_runner.devops_command(command)


def update_work_item(
    work_item_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    assigned_to: Optional[str] = None,
    state: Optional[str] = None,
    area_path: Optional[str] = None,
    iteration_path: Optional[str] = None,
    fields: Optional[Dict[str, str]] = None,
    organization: Optional[str] = None,
    project: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing work item.
    
    Args:
        work_item_id: Work item ID
        title: Work item title
        description: Work item description
        assigned_to: User to assign work item to
        state: Work item state (e.g., "Active", "Closed")
        area_path: Area path for the work item
        iteration_path: Iteration path for the work item
        fields: Additional fields to set on the work item
        organization: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
        project: Azure DevOps project name
        
    Returns:
        Updated work item details
    """
    command = f"boards work-item update --id {work_item_id}"
    
    if organization:
        command += f" --org {organization}"
    
    if project:
        command += f" --project {project}"
    
    if title:
        command += f" --title \"{title}\""
    
    if description:
        command += f" --description \"{description}\""
    
    if assigned_to:
        command += f" --assigned-to \"{assigned_to}\""
    
    if state:
        command += f" --state \"{state}\""
    
    if area_path:
        command += f" --area \"{area_path}\""
    
    if iteration_path:
        command += f" --iteration \"{iteration_path}\""
    
    # Add custom fields if provided
    if fields and isinstance(fields, dict):
        for field_name, field_value in fields.items():
            command += f" --fields \"{field_name}={field_value}\""
    
    logger.info(f"Updating work item with ID {work_item_id}")
    return command_runner.devops_command(command)


def query_work_items(
    query: str,
    organization: Optional[str] = None,
    project: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Query work items using a WIQL query.
    
    Args:
        query: Work item query language (WIQL) query string
        organization: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
        project: Azure DevOps project name
        
    Returns:
        List of work items matching the query
    """
    # Escape quotes in the query
    escaped_query = query.replace('"', '\\"')
    command = f'boards query --wiql "{escaped_query}"'
    
    if organization:
        command += f" --org {organization}"
    
    if project:
        command += f" --project {project}"
    
    logger.info("Querying work items")
    return command_runner.devops_command(command)


def list_work_items(
    work_item_type: Optional[str] = None,
    assigned_to: Optional[str] = None,
    state: Optional[str] = None,
    organization: Optional[str] = None,
    project: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List work items with optional filtering.
    
    Args:
        work_item_type: Filter by work item type (e.g., Bug, Task, User Story)
        assigned_to: Filter by assigned user
        state: Filter by state (e.g., "Active", "Closed")
        organization: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
        project: Azure DevOps project name
        
    Returns:
        List of work items
    """
    # Construct a WIQL query based on filters
    query_parts = ["SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo], [System.WorkItemType] FROM workitems"]
    where_clauses = []
    
    if work_item_type:
        where_clauses.append(f"[System.WorkItemType] = '{work_item_type}'")
    
    if assigned_to:
        where_clauses.append(f"[System.AssignedTo] = '{assigned_to}'")
    
    if state:
        where_clauses.append(f"[System.State] = '{state}'")
    
    if where_clauses:
        query_parts.append("WHERE " + " AND ".join(where_clauses))
    
    query_parts.append("ORDER BY [System.Id]")
    wiql_query = " ".join(query_parts)
    
    return query_work_items(wiql_query, organization, project)


def add_comment(
    work_item_id: int,
    comment: str,
    organization: Optional[str] = None,
    project: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add a comment to a work item.
    
    Args:
        work_item_id: Work item ID
        comment: Comment text
        organization: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
        project: Azure DevOps project name
        
    Returns:
        Updated work item details
    """
    command = f"boards work-item update --id {work_item_id} --discussion \"{comment}\""
    
    if organization:
        command += f" --org {organization}"
    
    if project:
        command += f" --project {project}"
    
    logger.info(f"Adding comment to work item {work_item_id}")
    return command_runner.devops_command(command)


def get_work_item_types(
    organization: Optional[str] = None,
    project: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get available work item types for a project.
    
    Args:
        organization: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
        project: Azure DevOps project name
        
    Returns:
        List of work item types
    """
    command = "boards work-item type list"
    
    if organization:
        command += f" --org {organization}"
    
    if project:
        command += f" --project {project}"
    
    logger.info(f"Getting work item types for project {project or 'default project'}")
    return command_runner.devops_command(command) 
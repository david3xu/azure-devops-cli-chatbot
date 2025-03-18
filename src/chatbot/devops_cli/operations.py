"""
Azure DevOps CLI operations wrapper.
Provides a single import for all Azure DevOps CLI operations.
"""
# Import command runner
from src.chatbot.devops_cli.command_runner import command_runner, CommandError

# Import repositories operations
from src.chatbot.devops_cli.repositories import (
    list_repositories, 
    get_repository,
    create_repository,
    delete_repository,
    list_branches,
    create_branch,
    import_repository,
    clone_repository,
    get_clone_url
)

# Import work item operations
from src.chatbot.devops_cli.work_items import (
    create_work_item,
    get_work_item,
    update_work_item,
    query_work_items,
    list_work_items,
    add_comment,
    get_work_item_types
)

# Import pipeline operations
from src.chatbot.devops_cli.pipelines import (
    list_pipelines,
    get_pipeline,
    create_pipeline,
    delete_pipeline,
    run_pipeline,
    list_runs,
    get_run,
    get_logs,
    cancel_run
)

# Export all modules
__all__ = [
    # Command runner
    'command_runner',
    'CommandError',
    
    # Repositories
    'list_repositories',
    'get_repository',
    'create_repository',
    'delete_repository',
    'list_branches',
    'create_branch',
    'import_repository',
    'clone_repository',
    'get_clone_url',
    
    # Work Items
    'create_work_item',
    'get_work_item',
    'update_work_item',
    'query_work_items',
    'list_work_items',
    'add_comment',
    'get_work_item_types',
    
    # Pipelines
    'list_pipelines',
    'get_pipeline',
    'create_pipeline',
    'delete_pipeline',
    'run_pipeline',
    'list_runs',
    'get_run',
    'get_logs',
    'cancel_run'
] 
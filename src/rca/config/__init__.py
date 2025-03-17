"""
Settings module for the RCA system.
Manages configuration options and environment variables.
"""
import os
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings from environment variables and defaults."""
    
    # Azure OpenAI settings
    AZURE_OPENAI_API_KEY: str = Field(default="", description="API key for Azure OpenAI")
    AZURE_OPENAI_ENDPOINT: str = Field(default="", description="Endpoint URL for Azure OpenAI")
    AZURE_OPENAI_API_VERSION: str = Field(default="2023-05-15", description="API version for Azure OpenAI")
    AZURE_OPENAI_DEPLOYMENT_NAME: str = Field(default="", description="Deployment name for Azure OpenAI")
    
    # Direct OpenAI settings
    OPENAI_API_KEY: str = Field(default="", description="API key for OpenAI")
    OPENAI_MODEL: str = Field(default="gpt-4", description="Model to use for OpenAI")
    
    # Vector search settings
    VECTOR_SEARCH_ENABLED: bool = Field(default=True, description="Whether vector search is enabled")
    VECTOR_DB_CONNECTION_STRING: str = Field(default="", description="Connection string for vector database")
    VECTOR_DB_INDEX_NAME: str = Field(default="rca-index", description="Index name for vector database")
    
    # Tracking settings
    WORKFLOW_TRACKING_ENABLED: bool = Field(default=True, description="Whether workflow tracking is enabled")
    WORKFLOW_STORAGE_DIR: str = Field(default="./data/workflow_traces", description="Directory for workflow trace storage")
    
    # API settings
    API_HOST: str = Field(default="0.0.0.0", description="Host for API server")
    API_PORT: int = Field(default=8000, description="Port for API server")
    API_DEBUG: bool = Field(default=False, description="Whether to enable debug mode for API server")
    
    # Security settings
    API_KEY_REQUIRED: bool = Field(default=False, description="Whether API key is required for requests")
    API_KEY: str = Field(default="", description="API key for securing endpoints")
    
    # Performance settings
    MAX_WORKERS: int = Field(default=4, description="Maximum number of worker threads")
    REQUEST_TIMEOUT: int = Field(default=60, description="Timeout for requests in seconds")
    
    def __init__(self, **kwargs):
        """Initialize settings, loading from environment variables."""
        # First load environment variables
        env_vars = {}
        for field in self.__annotations__:
            env_value = os.environ.get(field)
            if env_value is not None:
                # Convert to appropriate type
                if field in ["API_PORT", "MAX_WORKERS", "REQUEST_TIMEOUT"]:
                    env_vars[field] = int(env_value)
                elif field in ["VECTOR_SEARCH_ENABLED", "WORKFLOW_TRACKING_ENABLED", "API_DEBUG", "API_KEY_REQUIRED"]:
                    env_vars[field] = env_value.lower() in ["true", "yes", "1", "y"]
                else:
                    env_vars[field] = env_value
        
        # Update with any override kwargs
        env_vars.update(kwargs)
        
        # Initialize the model
        super().__init__(**env_vars)
    
    def validate_llm_settings(self) -> bool:
        """
        Validate that the required LLM settings are provided.
        
        Returns:
            bool: True if valid, False otherwise
        """
        # Check for Azure OpenAI settings
        azure_settings_valid = (
            self.AZURE_OPENAI_API_KEY and
            self.AZURE_OPENAI_ENDPOINT and
            self.AZURE_OPENAI_DEPLOYMENT_NAME
        )
        
        # Check for direct OpenAI settings
        openai_settings_valid = (
            self.OPENAI_API_KEY and
            self.OPENAI_MODEL
        )
        
        # Either Azure or direct OpenAI settings must be valid
        return azure_settings_valid or openai_settings_valid
    
    def validate(self) -> bool:
        """
        Validate that all required settings are provided.
        
        Returns:
            bool: True if valid, False otherwise
        """
        return self.validate_llm_settings()
    
    def to_dict(self, exclude_secrets: bool = True) -> Dict[str, Union[str, int, bool]]:
        """
        Convert settings to a dictionary, optionally excluding secrets.
        
        Args:
            exclude_secrets: Whether to exclude secret values like API keys
            
        Returns:
            Dictionary of settings
        """
        settings_dict = self.dict()
        
        if exclude_secrets:
            # Mask secret values
            secret_fields = [
                "AZURE_OPENAI_API_KEY",
                "OPENAI_API_KEY",
                "VECTOR_DB_CONNECTION_STRING",
                "API_KEY"
            ]
            
            for field in secret_fields:
                if settings_dict.get(field):
                    settings_dict[field] = "********"
        
        return settings_dict


# Create a global settings instance
settings = Settings() 
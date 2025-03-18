"""
Configuration settings for the Azure DevOps CLI Learning Project chatbot.
Uses environment variables with dotenv for local development.
"""
import os
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv

# Load environment variables from .env file if it exists
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings:
    """Application settings loaded from environment variables."""
    
    # Project information
    PROJECT_NAME: str = "Azure DevOps CLI Learning Project Chatbot"
    VERSION: str = "0.1.0"
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
    AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "")
    
    # Azure Key Vault (for production secret management)
    AZURE_KEY_VAULT_NAME: Optional[str] = os.getenv("AZURE_KEY_VAULT_NAME")
    USE_KEY_VAULT: bool = os.getenv("USE_KEY_VAULT", "False").lower() == "true"
    
    # Azure DevOps Configuration
    AZURE_DEVOPS_ORG: str = os.getenv("AZURE_DEVOPS_ORG", "")
    AZURE_DEVOPS_PROJECT: str = os.getenv("AZURE_DEVOPS_PROJECT", "")
    AZURE_DEVOPS_PAT: str = os.getenv("AZURE_DEVOPS_PAT", "")
    
    # Application settings
    PORT: int = int(os.getenv("PORT", "8000"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENABLE_FILE_LOGGING: bool = os.getenv("ENABLE_FILE_LOGGING", "false").lower() == "true"
    LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "logs/app.log")
    
    # Metrics Collection
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "True").lower() == "true"
    
    @property
    def is_production(self) -> bool:
        """Check if the environment is production."""
        return self.ENVIRONMENT.lower() == "production"
    
    def validate(self) -> bool:
        """
        Validate that all required settings are set.
        
        Returns:
            bool: True if all required settings are set, False otherwise
        """
        if not self.AZURE_OPENAI_ENDPOINT:
            return False
        if not self.AZURE_OPENAI_API_KEY:
            return False
        if not self.AZURE_OPENAI_DEPLOYMENT_NAME:
            return False
        return True
    
    def to_dict(self) -> Dict[str, str]:
        """
        Convert settings to a dictionary.
        
        Returns:
            Dict[str, str]: Dictionary of settings
        """
        return {
            "AZURE_OPENAI_ENDPOINT": self.AZURE_OPENAI_ENDPOINT,
            "AZURE_OPENAI_API_VERSION": self.AZURE_OPENAI_API_VERSION,
            "AZURE_OPENAI_DEPLOYMENT_NAME": self.AZURE_OPENAI_DEPLOYMENT_NAME,
            "AZURE_DEVOPS_ORG": self.AZURE_DEVOPS_ORG,
            "AZURE_DEVOPS_PROJECT": self.AZURE_DEVOPS_PROJECT,
            "PORT": str(self.PORT),
            "ENVIRONMENT": self.ENVIRONMENT,
            "LOG_LEVEL": self.LOG_LEVEL,
        }


# Create a global instance
settings = Settings() 
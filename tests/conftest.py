"""
Test configuration and shared fixtures.
"""
import os
import pytest
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
os.environ["PYTHONPATH"] = str(project_root)

# Set environment file path
env_path = project_root / "config" / "env" / ".env.azure"

@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load environment variables for tests."""
    from dotenv import load_dotenv
    if env_path.exists():
        load_dotenv(env_path)
    else:
        pytest.skip(f"Environment file not found: {env_path}")

@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return project_root

@pytest.fixture(scope="session")
def config_dir():
    """Return the config directory."""
    return project_root / "config" 
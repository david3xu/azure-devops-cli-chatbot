# Azure Directory Implementation

## Overview

This document details the `.azure` directory implementation used in the DevOps CLI Learning Project. The implementation provides a structured, CLI-first approach to managing Azure resources through a combination of configuration scripts, Infrastructure as Code (IaC) templates, and deployment automation.

## Directory Structure

```
.azure/
├── config/                     # Configuration files for Azure CLI
│   ├── azure_cli_config.sh     # Script to set up Azure CLI defaults
│   └── current_config.txt      # Current configuration (generated)
├── templates/                  # Infrastructure as Code templates
│   ├── arm/                    # Azure Resource Manager templates (JSON)
│   │   ├── app_service.json    # ARM template for App Service
│   │   └── app_service_parameters.json # Parameters (generated)
│   └── bicep/                  # Bicep templates
│       └── container_registry.bicep # Bicep for Container Registry
├── scripts/                    # Deployment and management scripts
│   ├── build_push_image.sh     # Build and push Docker image to ACR
│   ├── deploy_container_registry.sh # Deploy ACR
│   └── deploy_app_service.sh   # Deploy App Service
├── credentials/                # Securely store credentials (gitignored)
│   └── acr_credentials.txt     # ACR credentials (generated)
└── README.md                   # Azure-specific documentation
```

## Implementation Components

### 1. Configuration Management

The configuration management approach centers around the `azure_cli_config.sh` script that:

- Sets up Azure CLI defaults (output format, location)
- Creates a default resource group
- Installs and configures the Azure DevOps CLI extension
- Prompts for and stores organization and project settings
- Saves configuration to a persistent file for use by other scripts

Key patterns:
- User interaction for required settings
- Persistent configuration storage
- Default value generation for common settings

Example:
```bash
# Set default resource group (create if doesn't exist)
RESOURCE_GROUP="devops-cli-learning-rg"
az group create --name $RESOURCE_GROUP --location eastus

# Set defaults
az devops configure --defaults organization="$DEVOPS_ORG" project="$DEVOPS_PROJECT"
```

### 2. Infrastructure as Code

The implementation uses a hybrid approach to IaC:

#### Bicep Templates

Used for **Container Registry** deployment, leveraging Bicep's more concise syntax for simpler resources.

Key features:
- Parameterization for flexibility
- Resource tagging for governance
- Output variables for integration
- Documentation through parameter descriptions

Example:
```bicep
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2021-09-01' = {
  name: registryName
  location: location
  sku: {
    name: skuName
  }
  properties: {
    adminUserEnabled: adminUserEnabled
  }
  tags: tags
}
```

#### ARM Templates

Used for more complex **App Service** deployment with container configuration.

Key features:
- Nested resources (App Service Plan + App Service)
- Secure parameter handling for credentials
- Resource dependencies
- Output variables for integration

Example:
```json
"properties": {
  "serverFarmId": "[resourceId('Microsoft.Web/serverfarms', parameters('appServicePlanName'))]",
  "siteConfig": {
    "linuxFxVersion": "[concat('DOCKER|', parameters('containerImageReference'))]",
    "appSettings": [
      {
        "name": "DOCKER_REGISTRY_SERVER_URL",
        "value": "[concat('https://', parameters('acrRegistryUrl'))]"
      },
      ...
    ]
  }
}
```

### 3. Deployment Automation

The implementation includes three key deployment scripts:

#### Container Registry Deployment

- Uses Bicep template for deployment
- Generates unique registry name
- Stores credentials securely for other scripts
- Provides usage examples for next steps

#### App Service Deployment

- Uses ARM templates for deployment
- Creates parameter file on-the-fly
- Securely passes ACR credentials from stored credentials
- Generates unique service names
- Provides verbose output and next steps

#### Docker Image Build & Push

- Integrates with ACR credentials
- Supports tagging
- Implements proper ACR authentication
- Validates prerequisites
- Provides clear error messages and next steps

Key patterns:
- Script reuse through configuration sharing
- User confirmation prompts
- Secure handling of credentials
- Automated resource naming
- Clear output and next steps

### 4. Credential Management

The implementation includes a dedicated approach to credential management:

- `.azure/credentials/` directory for storing generated secrets
- Generated credentials stored as environment variables
- Scripts reading credentials from secure storage
- `.gitignore` pattern to prevent credential check-in
- Use of Azure CLI credential commands instead of manual entry

Example:
```bash
# Store ACR info in credentials directory
ACR_LOGIN_SERVER=$(az acr show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query loginServer -o tsv)
ACR_USERNAME=$(az acr credential show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query "passwords[0].value" -o tsv)

# Save credentials to a file
CREDS_FILE=".azure/credentials/acr_credentials.txt"
cat > $CREDS_FILE <<EOL
ACR_NAME=$REGISTRY_NAME
ACR_LOGIN_SERVER=$ACR_LOGIN_SERVER
ACR_USERNAME=$ACR_USERNAME
ACR_PASSWORD=$ACR_PASSWORD
EOL
```

### 5. Azure OpenAI Integration

The project integrates with Azure OpenAI services to power the chatbot's intelligent responses. This integration requires special attention to authentication and configuration settings:

#### Azure OpenAI Resource Configuration

1. **Authentication Methods**: Azure OpenAI supports multiple authentication methods:
   - API Key Authentication: Simplest method, suitable for development
   - Azure AD Authentication: More secure, recommended for production

2. **API Key Authentication Configuration**:
   ```bash
   # Check if API key authentication is enabled (disableLocalAuth)
   az cognitiveservices account show --name <your-openai-resource> --resource-group <your-resource-group>
   
   # Enable API key authentication if needed
   az resource update --ids /subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.CognitiveServices/accounts/<openai-resource> --set properties.disableLocalAuth=false
   
   # Get the API keys
   az cognitiveservices account keys list --name <your-openai-resource> --resource-group <your-resource-group>
   ```

3. **Deployment Management**: Azure OpenAI requires model deployments:
   ```bash
   # List existing deployments
   az cognitiveservices account deployment list --name <your-openai-resource> --resource-group <your-resource-group>
   
   # Create a new deployment (if needed)
   az cognitiveservices account deployment create \
     --name <your-openai-resource> \
     --resource-group <your-resource-group> \
     --deployment-name <deployment-name> \
     --model-name <model-name> \
     --model-version <model-version> \
     --model-format OpenAI \
     --scale-settings-scale-type Standard
   ```

#### Required Environment Variables

The application uses these environment variables for Azure OpenAI connectivity:

- `AZURE_OPENAI_API_KEY`: Authentication key
- `AZURE_OPENAI_ENDPOINT`: Service endpoint URL
- `AZURE_OPENAI_DEPLOYMENT_NAME`: The specific model deployment
- `AZURE_OPENAI_API_VERSION`: API version (default: 2023-05-15)

For production deployments, consider using Azure Key Vault to store these secrets and implementing Azure AD authentication instead of API keys.

## Implementation Benefits

### 1. Separation of Concerns

- Clear distinction between application code and infrastructure
- Dedicated directory for all Azure resource management
- Logical organization of templates, scripts, and configuration

### 2. CLI-First Approach

- Everything automation-ready through scripts
- No manual steps required in Azure Portal
- Full alignment with DevOps CLI Learning Project goals

### 3. Developer Experience

- Guided setup through interactive scripts
- Clear error messages and validation
- Next steps provided after each operation
- Documentation at multiple levels

### 4. Security

- Proper credential management
- Secure parameter handling
- Resource access control patterns

### 5. Flexibility

- Parameterized templates for reuse
- Multiple deployment options
- Easy extension for additional resources

## Usage Workflow

1. **Initial Setup**:
   ```bash
   bash .azure/config/azure_cli_config.sh
   ```

2. **Deploy Container Registry**:
   ```bash
   bash .azure/scripts/deploy_container_registry.sh
   ```

3. **Build and Push Docker Image**:
   ```bash
   bash .azure/scripts/build_push_image.sh [tag]
   ```

4. **Deploy App Service**:
   ```bash
   bash .azure/scripts/deploy_app_service.sh
   ```

## Advanced Patterns

### Resource Dependency Chain

The implementation handles dependencies between resources:

1. **Azure CLI Configuration** establishes baseline settings
2. **Container Registry Deployment** creates image storage
3. **Docker Image Build & Push** populates the registry
4. **App Service Deployment** references the container image

Each script checks for the existence of outputs from previous steps before proceeding.

### Parameter Generation

For resources requiring globally unique names:

```bash
# Set variables with randomization for uniqueness
REGISTRY_NAME="devopsclilearning$RANDOM"
APP_NAME="devopsclilearningapp$RANDOM"
```

### Script Dependencies

Scripts depend on each other through configuration files:

```bash
# Load configuration
CONFIG_FILE=".azure/config/current_config.txt"
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
else
    echo "Configuration file not found. Please run the Azure CLI configuration script first."
    exit 1
fi
```

## Future Enhancements

1. **Key Vault Integration** for more secure credential storage
2. **Managed Identity** implementation for passwordless authentication
3. **GitHub Actions Integration** for CI/CD automation
4. **Azure Monitor** setup for observability
5. **Cost Management** tags and budgets
6. **Additional Resource Types** (SQL, Storage, etc.)

## Conclusion

The `.azure` directory implementation provides a comprehensive, structured approach to Azure resource management that aligns perfectly with the DevOps CLI Learning Project's goals. By separating infrastructure concerns from application code while maintaining a CLI-first approach, it enables efficient, repeatable, and secure deployment of Azure resources. 

## Configuration Strategy: Relationship Between .azure, .env, and config.json

The project implements a multi-layered configuration strategy using three distinct mechanisms to maintain a clear separation of concerns:

### 1. `.azure/` - Infrastructure Configuration

**Purpose**: Manages all Azure infrastructure concerns and deployment automation.

**Characteristics**:
- Contains Infrastructure as Code templates (ARM and Bicep)
- Houses deployment scripts and automation
- Manages Azure CLI configuration
- Stores generated infrastructure credentials securely
- Focuses on cloud resource provisioning and management

**Typical Contents**:
- Resource templates
- Deployment scripts
- CLI configuration
- Infrastructure-specific documentation
- Securely stored service credentials

**Usage Pattern**:
```bash
# Infrastructure deployment through .azure scripts
bash .azure/scripts/deploy_container_registry.sh
```

### 2. `.env` - Environment Variables

**Purpose**: Manages runtime secrets and environment-specific values.

**Characteristics**:
- Contains sensitive information (API keys, connection strings)
- Environment-specific configuration (dev, test, prod)
- Not checked into version control (only template is committed)
- Loaded at application runtime
- Used for values that should not be hardcoded in application code

**Typical Contents**:
```
# Azure OpenAI Configuration
AZURE_OPENAI_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-instance.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=deployment_name

# Logging Configuration
LOG_LEVEL=INFO
ENABLE_FILE_LOGGING=false
```

**Usage Pattern**:
```python
# In Python code, loading from .env
from dotenv import load_dotenv
load_dotenv()

openai_key = os.getenv("AZURE_OPENAI_KEY")
```

### 3. `config.json` - Application Configuration

**Purpose**: Manages non-sensitive application settings and defaults.

**Characteristics**:
- Contains operational configuration for the application
- May be checked into version control
- Can be modified without redeployment
- Default application behavior settings
- Feature flags and toggles

**Typical Contents**:
```json
{
  "conversation": {
    "max_history_messages": 10,
    "default_temperature": 0.7,
    "available_modes": ["general", "devops-expert"]
  },
  "api": {
    "rate_limit": 100,
    "timeout_seconds": 30,
    "retry_attempts": 3
  },
  "ui": {
    "theme": "dark",
    "show_token_usage": true
  }
}
```

**Usage Pattern**:
```python
# In Python code, loading from config.json
with open("config.json") as f:
    config = json.load(f)

max_history = config["conversation"]["max_history_messages"]
```

### Relationship and Boundaries

The three configuration mechanisms interact in a hierarchical manner with clear boundaries:

1. **Infrastructure ▶ Environment ▶ Application**
   - `.azure` scripts provision resources and generate credentials
   - Generated credentials may be stored in `.env` for application use
   - Application loads configuration from both `.env` and `config.json`

2. **Separation by Scope**
   - `.azure`: Infrastructure scope (Azure resources)
   - `.env`: Runtime scope (secrets and environment-specific values)
   - `config.json`: Application scope (operational behavior)

3. **Deployment and Lifecycle**
   - `.azure` changes may require resource (re)deployment
   - `.env` changes may require application restart
   - `config.json` changes can often be picked up dynamically

This multi-layered approach brings several benefits:
- Clear separation of configuration concerns
- Appropriate security for different types of settings
- Flexibility in deployment and operations
- Simplified troubleshooting by isolating configuration domains

By maintaining these clean boundaries, the project achieves a robust configuration strategy that addresses infrastructure, security, and application needs with appropriate tools for each domain. 

### Quick Summary

**Configuration Strategy: .azure vs .env vs config.json**

Each of these components has a specific role in our project's configuration architecture:

1. **`.azure/` - Infrastructure Configuration**
   - **Purpose**: Manages all Azure cloud resources and infrastructure
   - **Contains**: ARM/Bicep templates, deployment scripts, CLI configuration
   - **Example**: deploy_container_registry.sh, app_service.json
   - **Scope**: Cloud infrastructure provisioning and management
   - **Security**: Includes secure credential storage with .gitignore protection

2. **`.env` - Environment Variables & Secrets**
   - **Purpose**: Runtime secrets and environment-specific configuration
   - **Contains**: API keys, connection strings, deployment-specific values
   - **Example**: AZURE_OPENAI_KEY, LOG_LEVEL, ENABLE_FILE_LOGGING
   - **Scope**: Runtime environment configuration
   - **Security**: Never checked into source control (only template is shared)

3. **`config.json` - Application Configuration**
   - **Purpose**: Non-sensitive application settings and defaults
   - **Contains**: Default behaviors, feature flags, operational parameters
   - **Example**: Conversation settings, API timeouts, UI preferences
   - **Scope**: Application behavior and operational settings
   - **Security**: May be checked into source control (no secrets)

**Their Relationship**

These components form a hierarchical configuration strategy:

- **Flow of Configuration**:
  - `.azure` scripts provision infrastructure and generate credentials
  - Credentials may be stored in `.env` for application use
  - Application combines settings from both `.env` and `config.json`

- **Separation of Concerns**:
  - `.azure`: Infrastructure layer (what resources exist)
  - `.env`: Security layer (how to access resources securely)
  - `config.json`: Application layer (how the app behaves)

- **Different Lifecycles**:
  - `.azure` changes → Resource deployment (slow, infrastructure changes)
  - `.env` changes → Application restart (medium, environment changes)
  - `config.json` changes → Runtime reload (fast, behavior changes)

This architecture maintains clean boundaries between infrastructure, security, and application configuration, making the system more maintainable, secure, and flexible. Each configuration mechanism is used for its strengths, resulting in a robust overall approach to configuration management.

## Handling Existing Azure Resources

When working with existing Azure resources, it's important to follow the proper pattern for referencing them in your deployment scripts and templates. Based on Azure Resource Manager best practices:

### Recommended Approach

Instead of storing existing resource information in environment variables like `.azure/existing-resources/.env`, use structured ARM/Bicep files:

```
.azure/
├── existing-resources/
│   ├── resources.json         # JSON file with existing resource references
│   └── import-resources.sh    # Script to import existing resources
├── templates/
│   ├── arm/                   # New resources to deploy
│   └── bicep/
└── ...
```

### Benefits of Structured Files for Existing Resources

1. **Consistent Format**: Uses the same JSON/Bicep format as your template files
2. **Parameter Support**: Resources can be properly parameterized
3. **Reference Support**: ARM template functions can reference these resources
4. **Better Validation**: JSON schema validation ensures correct syntax
5. **Integration**: Seamless integration with ARM template deployments
6. **Documentation**: Self-documenting format with descriptions

### Example Structure for resources.json

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {},
  "variables": {},
  "resources": [],
  "outputs": {
    "existingVNet": {
      "type": "object",
      "value": {
        "id": "/subscriptions/{subscription-id}/resourceGroups/networking-rg/providers/Microsoft.Network/virtualNetworks/main-vnet",
        "name": "main-vnet",
        "resourceGroup": "networking-rg"
      }
    },
    "existingKeyVault": {
      "type": "object",
      "value": {
        "id": "/subscriptions/{subscription-id}/resourceGroups/security-rg/providers/Microsoft.KeyVault/vaults/company-vault",
        "name": "company-vault",
        "resourceGroup": "security-rg"
      }
    }
  }
}
```

### Usage in Deployment Scripts

Scripts can parse these structured JSON files using JQ or similar tools:

```bash
# Extract existing resource information
VNET_ID=$(jq -r '.outputs.existingVNet.value.id' .azure/existing-resources/resources.json)
KEYVAULT_NAME=$(jq -r '.outputs.existingKeyVault.value.name' .azure/existing-resources/resources.json)

# Use in ARM template deployment
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file .azure/templates/arm/app_service.json \
  --parameters existingVNetId=$VNET_ID existingKeyVaultName=$KEYVAULT_NAME
```

This approach maintains our separation of concerns:
- `.azure` directory handles all infrastructure concerns (new and existing) 
- `.env` remains focused on runtime secrets and environment-specific values
- `config.json` manages application configuration

By using structured files for existing resources rather than environment variables, we keep a cleaner boundary between infrastructure configuration and runtime secrets, following ARM template best practices.

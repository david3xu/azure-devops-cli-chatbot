#!/bin/bash
set -e  # Exit on error

# This script sets up GitHub secrets from .env.azure and configures
# federated identity credential in Azure AD for OIDC authentication

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up GitHub Secrets and Azure AD Federation for OIDC...${NC}"

# Check if .env.azure exists
if [ ! -f .env.azure ]; then
    echo -e "${RED}Error: .env.azure file not found!${NC}"
    exit 1
fi

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}GitHub CLI not found. Installing...${NC}"
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt update
    sudo apt install -y gh
fi

# Check if jq is installed (needed for JSON parsing)
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}jq not found. Installing...${NC}"
    sudo apt update
    sudo apt install -y jq
fi

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${YELLOW}Azure CLI not found. Installing...${NC}"
    curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
fi

# Check if azd CLI is installed
AZD_INSTALLED=false
if command -v azd &> /dev/null; then
    AZD_INSTALLED=true
fi

# Login to GitHub
echo -e "${BLUE}Step 1: GitHub Authentication${NC}"
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}Not logged in to GitHub. Please login:${NC}"
    gh auth login
else
    echo -e "${GREEN}Already logged in to GitHub${NC}"
fi

# Azure authentication options
echo -e "\n${BLUE}Step 2: Azure Authentication${NC}"
echo "Please select how you want to authenticate with Azure:"
echo "1. Use az login (standard Azure CLI login)"
if [ "$AZD_INSTALLED" = true ]; then
    echo "2. Use azd auth login (Azure Developer CLI login - may have higher permissions)"
fi
echo "3. Skip authentication (use existing login if available)"
read -p "Enter your choice: " AUTH_CHOICE

# Handle Azure authentication
case $AUTH_CHOICE in
    1)
        echo -e "${YELLOW}Logging in with Azure CLI...${NC}"
        az login
        ;;
    2)
        if [ "$AZD_INSTALLED" = true ]; then
            echo -e "${YELLOW}Logging in with Azure Developer CLI...${NC}"
            azd auth login
        else
            echo -e "${RED}Azure Developer CLI (azd) not installed. Using az login instead.${NC}"
            az login
        fi
        ;;
    3)
        echo -e "${YELLOW}Skipping authentication. Using existing session if available.${NC}"
        ;;
    *)
        echo -e "${RED}Invalid option. Using az login as default.${NC}"
        az login
        ;;
esac

# Verify Azure authentication and collect info
if ! az account show &> /dev/null; then
    echo -e "${RED}Error: Not logged in to Azure. Please run the script again and select a login option.${NC}"
    exit 1
fi

# Get Azure account information
echo -e "${YELLOW}Getting Azure account information...${NC}"
ACCOUNT_JSON=$(az account show --output json)
CLI_SUBSCRIPTION_ID=$(echo $ACCOUNT_JSON | jq -r '.id')
CLI_TENANT_ID=$(echo $ACCOUNT_JSON | jq -r '.tenantId')

echo -e "${GREEN}Found account information:${NC}"
echo "Subscription ID: $CLI_SUBSCRIPTION_ID"
echo "Tenant ID: $CLI_TENANT_ID"

# Check user's permissions
echo -e "${YELLOW}Checking your Azure permissions...${NC}"
USER_INFO=$(az ad signed-in-user show --query '{userPrincipalName:userPrincipalName,objectId:id}' -o json 2>/dev/null || echo '{"userPrincipalName":"Unknown", "objectId":"Unknown"}')
USER_NAME=$(echo $USER_INFO | jq -r '.userPrincipalName')
USER_ID=$(echo $USER_INFO | jq -r '.objectId')

echo "Signed in as: $USER_NAME"

# Check if user has any roles assigned
ROLES=$(az role assignment list --assignee "$USER_ID" --query "[?scope=='/subscriptions/$CLI_SUBSCRIPTION_ID'].roleDefinitionName" -o tsv 2>/dev/null || echo "")

if [ -z "$ROLES" ]; then
    echo -e "${YELLOW}Warning: You don't appear to have any role assignments on this subscription.${NC}"
    echo -e "${YELLOW}Some operations may fail due to insufficient permissions.${NC}"
else
    echo -e "${GREEN}Your roles on this subscription:${NC}"
    echo "$ROLES" | tr '\n' ', ' | sed 's/,$/\n/'
    
    # Check for high-privilege roles
    if echo "$ROLES" | grep -q "Owner\|Contributor\|Application Administrator\|Global Administrator"; then
        echo -e "${GREEN}You have sufficient permissions to perform most operations.${NC}"
    else
        echo -e "${YELLOW}You may not have sufficient permissions for all operations.${NC}"
        echo -e "${YELLOW}Some steps might fail and require manual intervention.${NC}"
    fi
fi

# Load environment variables from .env.azure
echo -e "${YELLOW}Loading environment variables from .env.azure...${NC}"
source .env.azure

# Get current repository
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
if [ -z "$REPO" ]; then
    echo -e "${YELLOW}Could not determine repository automatically.${NC}"
    read -p "Please enter your repository name (format: username/repo): " REPO
fi

echo -e "${YELLOW}Setting GitHub secrets for repository: ${REPO}${NC}"

# Determine AZURE_CLIENT_ID - it could be named differently in .env.azure
# or extract from Azure service principals
if [ -n "$AZURE_CLIENT_ID" ]; then
    CLIENT_ID=$AZURE_CLIENT_ID
elif [ -n "$AZURE_APP_ID" ]; then
    CLIENT_ID=$AZURE_APP_ID
else
    echo -e "${YELLOW}AZURE_CLIENT_ID not found in .env.azure. Looking for available service principals...${NC}"
    
    # List available service principals
    echo -e "${YELLOW}Available service principals:${NC}"
    az ad sp list --all --query "[].{name:displayName, appId:appId}" --output table
    
    echo -e "\n${YELLOW}Options:${NC}"
    echo "1. Select an existing service principal from the list"
    echo "2. Create a new service principal for GitHub Actions (requires Azure AD admin rights)"
    echo "3. Manually enter a client ID"
    read -p "Enter your choice (1, 2, or 3): " SP_CHOICE
    
    if [[ "$SP_CHOICE" == "1" ]]; then
        read -p "Enter the application ID from the list above: " CLIENT_ID
    elif [[ "$SP_CHOICE" == "2" ]]; then
        SP_NAME="github-actions-sp-$(date +%s)"
        echo -e "${YELLOW}Creating new service principal: $SP_NAME${NC}"
        
        # Try to create a new service principal and capture any errors
        echo -e "${YELLOW}Attempting to create service principal with Azure CLI...${NC}"
        SP_RESULT=$(az ad sp create-for-rbac \
            --name "$SP_NAME" \
            --role "Contributor" \
            --scopes "/subscriptions/$CLI_SUBSCRIPTION_ID" \
            --output json 2>&1)
        
        # Check if there was an error
        if echo "$SP_RESULT" | grep -q "Insufficient privileges\|permission\|Authorization"; then
            echo -e "${RED}Error creating service principal using Azure CLI.${NC}"
            
            # Try with azd if installed as it might have different permissions
            if [ "$AZD_INSTALLED" = true ]; then
                echo -e "${YELLOW}Trying with Azure Developer CLI (azd) instead...${NC}"
                AZD_RESULT=$(azd auth app create --subscription "$CLI_SUBSCRIPTION_ID" 2>&1)
                
                if echo "$AZD_RESULT" | grep -q "client_id"; then
                    CLIENT_ID=$(echo "$AZD_RESULT" | grep "client_id" | cut -d ":" -f2 | tr -d " ," | head -1)
                    echo -e "${GREEN}Successfully created service principal with azd: $CLIENT_ID${NC}"
                else
                    echo -e "${RED}Failed to create service principal with azd as well.${NC}"
                    echo -e "${YELLOW}You need Azure AD admin rights to create service principals.${NC}"
                    echo ""
                    echo "To create a service principal manually:"
                    echo "1. Go to Azure Portal → Microsoft Entra ID → App registrations → New registration"
                    echo "2. Name the application and register it"
                    echo "3. Note the Application (client) ID"
                    echo "4. Go to your subscription → Access control (IAM) → Add role assignment"
                    echo "5. Assign the 'Contributor' role to your new app"
                    echo ""
                    read -p "Enter an application (client) ID manually: " CLIENT_ID
                fi
            else
                echo -e "${YELLOW}You need Azure AD admin rights to create service principals.${NC}"
                echo ""
                echo "To create a service principal manually:"
                echo "1. Go to Azure Portal → Microsoft Entra ID → App registrations → New registration"
                echo "2. Name the application and register it"
                echo "3. Note the Application (client) ID"
                echo "4. Go to your subscription → Access control (IAM) → Add role assignment"
                echo "5. Assign the 'Contributor' role to your new app"
                echo ""
                read -p "Enter an application (client) ID manually: " CLIENT_ID
            fi
        else
            # Successfully created a service principal
            CLIENT_ID=$(echo $SP_RESULT | jq -r '.appId')
            echo -e "${GREEN}Created service principal with app ID: $CLIENT_ID${NC}"
        fi
    else
        read -p "Enter an application (client) ID manually: " CLIENT_ID
    fi
fi

# Use Azure CLI values if environment vars not set
if [ -z "$AZURE_SUBSCRIPTION_ID" ]; then
    echo -e "${YELLOW}Using subscription ID from Azure CLI: $CLI_SUBSCRIPTION_ID${NC}"
    AZURE_SUBSCRIPTION_ID=$CLI_SUBSCRIPTION_ID
fi

if [ -z "$AZURE_TENANT_ID" ]; then
    echo -e "${YELLOW}Using tenant ID from Azure CLI: $CLI_TENANT_ID${NC}"
    AZURE_TENANT_ID=$CLI_TENANT_ID
fi

# Check for remaining required variables
declare -a REQUIRED_VARS=(
    "AZURE_OPENAI_ENDPOINT"
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
    "AZURE_SEARCH_ADMIN_KEY"
    "AZURE_SEARCH_ENDPOINT"
    "AZURE_SEARCH_INDEX"
    "AZURE_SEARCH_API_VERSION"
    "AZURE_OPENAI_CHATGPT_DEPLOYMENT"
)

# Validate all required vars are present
for VAR in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!VAR}" ]; then
        echo -e "${RED}Error: ${VAR} is not set in .env.azure${NC}"
        read -p "Please enter the value for ${VAR}: " VALUE
        declare "${VAR}=${VALUE}"
    fi
done

# Set all the secrets
echo -e "${YELLOW}Setting GitHub secrets...${NC}"
gh secret set AZURE_CLIENT_ID --body "$CLIENT_ID" --repo $REPO
gh secret set AZURE_TENANT_ID --body "$AZURE_TENANT_ID" --repo $REPO
gh secret set AZURE_SUBSCRIPTION_ID --body "$AZURE_SUBSCRIPTION_ID" --repo $REPO
gh secret set AZURE_OPENAI_ENDPOINT --body "$AZURE_OPENAI_ENDPOINT" --repo $REPO
gh secret set AZURE_OPENAI_EMBEDDING_DEPLOYMENT --body "$AZURE_OPENAI_EMBEDDING_DEPLOYMENT" --repo $REPO
gh secret set AZURE_SEARCH_ADMIN_KEY --body "$AZURE_SEARCH_ADMIN_KEY" --repo $REPO
gh secret set AZURE_SEARCH_ENDPOINT --body "$AZURE_SEARCH_ENDPOINT" --repo $REPO
gh secret set AZURE_SEARCH_INDEX --body "$AZURE_SEARCH_INDEX" --repo $REPO
gh secret set AZURE_SEARCH_API_VERSION --body "$AZURE_SEARCH_API_VERSION" --repo $REPO
gh secret set AZURE_OPENAI_CHATGPT_DEPLOYMENT --body "$AZURE_OPENAI_CHATGPT_DEPLOYMENT" --repo $REPO

echo -e "${GREEN}GitHub secrets set successfully!${NC}"

# Setup Azure AD Federation for OIDC
echo -e "${YELLOW}Setting up Azure AD Federation for OIDC authentication...${NC}"

# Parse the repository name
IFS='/' read -r OWNER REPO_NAME <<< "$REPO"

# Try to create federated identity credentials but handle permissions gracefully
create_federated_credential() {
    local credential_name=$1
    local subject=$2
    local description=$3
    
    echo -e "${YELLOW}Creating federated identity credential: $credential_name${NC}"
    
    CREDENTIAL_PARAMS=$(cat <<EOF
{
  "name": "$credential_name",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "$subject",
  "audiences": ["api://AzureADTokenExchange"],
  "description": "$description"
}
EOF
    )
    
    echo "Credential parameters:"
    echo "$CREDENTIAL_PARAMS"
    
    # First try with Azure CLI
    echo -e "${YELLOW}Attempting to create federated credential with Azure CLI...${NC}"
    local RESULT=$(az ad app federated-credential create \
      --id "$CLIENT_ID" \
      --parameters "$CREDENTIAL_PARAMS" 2>&1)
    
    # Check if there was an error
    if echo "$RESULT" | grep -q "Insufficient privileges\|Permission\|Authorization"; then
        echo -e "${RED}Error with Azure CLI. Checking for alternative methods...${NC}"
        
        # Try with azd if available
        if [ "$AZD_INSTALLED" = true ]; then
            echo -e "${YELLOW}Trying with Azure Developer CLI (azd)...${NC}"
            azd auth app federated-credential create \
              --client-id "$CLIENT_ID" \
              --issuer "https://token.actions.githubusercontent.com" \
              --subject "$subject" \
              --name "$credential_name" \
              --role "Contributor" \
              --description "$description" 2>/dev/null
              
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}Successfully created federated credential using azd.${NC}"
                return 0
            else
                echo -e "${RED}Failed to create federated credential with azd as well.${NC}"
            fi
        fi
        
        echo -e "${YELLOW}You need Azure AD admin rights to create federated credentials.${NC}"
        echo ""
        echo "To create federated credentials manually:"
        echo "1. Go to Azure Portal → Microsoft Entra ID → App registrations"
        echo "2. Find your application with ID: $CLIENT_ID"
        echo "3. Go to Certificates & secrets → Federated credentials"
        echo "4. Add a credential with:"
        echo "   - Scenario: GitHub Actions"
        echo "   - Organization: $OWNER"
        echo "   - Repository: $REPO_NAME"
        echo "   - Entity type: Branch/Pull request"
        echo "   - GitHub branch: main (for main branch) or Pull request (for PRs)"
        echo "   - Name: $credential_name"
        return 1
    else
        echo -e "${GREEN}Successfully created federated credential.${NC}"
        return 0
    fi
}

# Create federated identity credentials
MAIN_CREDENTIAL_CREATED=false
PR_CREDENTIAL_CREATED=false

# Try to create main branch credential
create_federated_credential "github-actions-$REPO_NAME" "repo:$REPO:ref:refs/heads/main" "GitHub Actions federation for $REPO"
if [ $? -eq 0 ]; then
    MAIN_CREDENTIAL_CREATED=true
fi

# Try to create PR credential
create_federated_credential "github-actions-$REPO_NAME-pr" "repo:$REPO:pull_request" "GitHub Actions federation for PRs in $REPO"
if [ $? -eq 0 ]; then
    PR_CREDENTIAL_CREATED=true
fi

# Update .env.azure with the values we used
echo -e "${YELLOW}Updating .env.azure with the values used...${NC}"

# Update or add values to .env.azure
update_env_var() {
    local var_name=$1
    local var_value=$2
    
    if grep -q "^$var_name=" .env.azure; then
        # Variable exists, update it
        sed -i "s|^$var_name=.*|$var_name=\"$var_value\"|" .env.azure
    else
        # Variable doesn't exist, add it
        echo "$var_name=\"$var_value\"" >> .env.azure
    fi
}

# Update core values
update_env_var "AZURE_CLIENT_ID" "$CLIENT_ID"
update_env_var "AZURE_TENANT_ID" "$AZURE_TENANT_ID"
update_env_var "AZURE_SUBSCRIPTION_ID" "$AZURE_SUBSCRIPTION_ID"

echo -e "${GREEN}Setup complete! Your workflow should now be able to authenticate to Azure using OIDC.${NC}"

# Provide next steps
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Push your workflow changes to GitHub"
echo "2. Verify your workflow runs correctly"

# Additional instructions based on credential creation results
if [ "$MAIN_CREDENTIAL_CREATED" = false ] || [ "$PR_CREDENTIAL_CREATED" = false ]; then
    echo "3. Manually create the federated credentials in Azure portal as described above"
fi

echo "4. If you encounter permission issues, ensure your Azure AD app has the right role assignments" 
# Github action for getting fast (in seconds) all the secrets from an Azure Key Vault

## Why this action

The [Azure official action](https://github.com/Azure/get-keyvault-secrets) is now deprecated, recommending the use of azcli to retrieve secrets. However, the azcli command operates within a bash shell without multithreading. Thus, if numerous secrets need retrieval, it can be time-consuming.

This action is a composite Github action formulated in a Python script. It employs `asyncio`, eliminating the need for third-party Python modules and subsequent pip installations. This method is considerably faster than the sequential azcli command or other docker actions. Although it relies on multithreading under the hood due to the absence of third-party modules (like `requests`, `aiohttp` or `httpx`), **it still completes tasks (typically in seconds)** more rapidly than the azcli command.

This action doesn't offer an input option to specify which secrets to retrieve. Instead, it automatically fetches all secrets from the keyvault. Given its speed advantage over the azcli command, there's no pressing need to filter which secrets to retrieve, simplifying its use.

## Usage

> [!IMPORTANT]
> User must be authenticated to Azure before using this action, please refer to [Azure Login](https://github.com/Azure/login).

> [!WARNING]
> **Secret name prefix by `github-`**: Secrets created in Azure Keyvault should not begin with `github-` (case insensitive). This is because the corresponding environment variable name generated by this action will start with `GITHUB_`, and [GitHub prohibits](https://docs.github.com/en/actions/learn-github-actions/variables#naming-conventions-for-configuration-variables) setting environment variables with names that begin with `GITHUB_`. If such secrets are present, the action will skip them and print a warning message.

**Fetching all secrets from a key vault:**

```yaml
# in the calling workflow, user should first login to Azure
- uses: Azure/login@v1
  with:
    # creds: ${{secrets.AZURE_CREDENTIALS}} is not recommended
    # due to json secrets security concerns.
    creds: >
      {
      "clientId":"${{ secrets.CICD_CLIENT_ID }}",
      "clientSecret":"${{ secrets.CICD_CLIENT_SECRET }}",
      "subscriptionId":"${{ secrets.AZURE_SUBSCRIPTION_ID }}",
      "tenantId":"${{ secrets.AZURE_TENANT_ID }}"
      }

- name: Get Azure KeyVault secrets
  id: get-azure-keyvault-secrets
  uses: copdips/get-azure-keyvault-secrets-action@v1
  with:
    keyvault: {your_azure_keyvault_name}
```

**Using the secrets in two methods:**

```yaml
# Suppose there's a secret named client-secret in the Azure Key Vault,
# so an env var named CLIENT_SECRET should be created by the action.
# You won't see the secret value in the workflow log
# as it's masked by Github automatically.
- name: Method 1 - use secrets from env var
  run: |
    echo $CLIENT_SECRET
    echo ${{ env.CLIENT_SECRET }}

- name: Method 2 - use secrets from output
  run: |
    echo $JSON_SECRETS | jq .CLIENT_SECRET -r
  env:
    JSON_SECRETS: ${{ steps.get-azure-keyvault-secrets.outputs.json }}
```

This action retrieves all secrets from the key vault identified by the input `keyvault` and sets them as **environment variables**, allowing users to access them directly within the same workflow job. The environment variable is named using the upper snake case of the secret name. For example, a key vault secret named `client-secret` will result in an environment variable named `CLIENT_SECRET`. The value of this environment variable remains identical to the original secret value.

Furthermore, the action generates a single **JSON string** containing all the created environment variables. This can be accessed via `${{ steps.get-keyvault-secrets.outputs.json }}` and can be employed in subsequent jobs, eliminating the need to execute the action again. Refer to this [syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idoutputs) guide for details on passing outputs from one job to another.

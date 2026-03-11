// ---------------------------------------------------------------------------
// Role Assignments — Cognitive Services OpenAI User on Foundry account
// Grants each agent Container App's system-assigned managed identity the
// ability to call Azure OpenAI deployments via DefaultAzureCredential().
// ---------------------------------------------------------------------------

@description('Name of the existing Foundry (CognitiveServices) account')
param foundryAccountName string

@description('Principal IDs (object IDs) of the agent Container App managed identities')
param principalIds array

// Cognitive Services OpenAI User — allows calling Azure OpenAI deployments
var cognitiveServicesOpenAIUserRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'

resource foundryAccount 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: foundryAccountName
}

resource roleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for (principalId, i) in principalIds: {
  name: guid(foundryAccount.id, principalId, cognitiveServicesOpenAIUserRoleId)
  scope: foundryAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesOpenAIUserRoleId)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}]

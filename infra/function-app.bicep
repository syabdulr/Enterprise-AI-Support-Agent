param location string = resourceGroup().location
param appName string

@secure()
param dataverseUrl string

@secure()
param dataverseTenantId string

@secure()
param dataverseClientId string

@secure()
param dataverseClientSecret string

param storageAccountName string = toLower(concat('st', uniqueString(resourceGroup().id)))

var runtime = 'python'

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
}

// Consumption (serverless) plan — Y1/Dynamic, scale controlled by the
// Functions runtime, no pre-provisioned instances.
resource hostingPlan 'Microsoft.Web/serverFarms@2023-12-01' = {
  name: '${appName}-plan'
  location: location
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
    size: 'Y1'
    family: 'Y'
    capacity: 0
  }
}

resource functionApp 'Microsoft.Web/sites@2023-12-01' = {
  name: appName
  location: location
  kind: 'functionapp'
  properties: {
    serverFarmId: hostingPlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccountName};AccountKey=${storage.listKeys().keys[0].value}'
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: runtime
        }
        {
          name: 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccountName};AccountKey=${storage.listKeys().keys[0].value}'
        }
        {
          name: 'WEBSITE_CONTENTSHARE'
          value: toLower(concat(appName, 'content'))
        }
        {
          name: 'DATAVERSE_URL'
          value: dataverseUrl
        }
        {
          name: 'DATAVERSE_TENANT_ID'
          value: dataverseTenantId
        }
        {
          name: 'DATAVERSE_CLIENT_ID'
          value: dataverseClientId
        }
        {
          name: 'DATAVERSE_CLIENT_SECRET'
          value: dataverseClientSecret
        }
      ]
    }
  }
}

output functionAppName string = functionApp.name
output functionAppDefaultHostname string = functionApp.properties.defaultHostName

param location string = resourceGroup().location
param apimName string
param functionAppUrl string
param publisherName string = 'Site Safety Incidents'
param publisherEmail string = 'safety@example.com'

resource apim 'Microsoft.ApiManagement/service@2023-05-01-preview' = {
  name: apimName
  location: location
  sku: {
    name: 'Consumption'
    capacity: 0
  }
  properties: {
    publisherEmail: publisherEmail
    publisherName: publisherName
  }
}

// One API surface: the incident-write operation backed by the Function.
resource api 'Microsoft.ApiManagement/service/apis@2023-05-01-preview' = {
  parent: apim
  name: 'incident-api'
  properties: {
    displayName: 'Site Safety Incident API'
    path: 'incidents'
    protocols: [
      'https'
    ]
    subscriptionRequired: true
  }
}

resource operation 'Microsoft.ApiManagement/service/apis/operations@2023-05-01-preview' = {
  parent: api
  name: 'post-incident'
  properties: {
    displayName: 'POST /incidents'
    method: 'POST'
    urlTemplate: '/'
    templateParameters: []
  }
}

// Subscription-key product: callers must subscribe to reach the API.
resource product 'Microsoft.ApiManagement/service/products@2023-05-01-preview' = {
  parent: apim
  name: 'incident-product'
  properties: {
    displayName: 'Site Safety Incident Product'
    subscriptionRequired: true
    approvalRequired: true
  }
}

resource productApi 'Microsoft.ApiManagement/service/products/apis@2023-05-01-preview' = {
  parent: product
  name: 'incident-api'
  properties: {}
}

// Rate limit: 100 calls/min keyed on subscription key, then forward to
// the Function App backend.
resource operationPolicy 'Microsoft.ApiManagement/service/apis/operations/policies@2023-05-01-preview' = {
  parent: operation
  name: 'policy'
  properties: {
    value: '''
    <policies>
      <inbound>
        <rate-limit-by-key calls="100" renewal-period="60" counter-key="@(context.Subscription?.Id ?? context.Request.IpAddress)" />
        <set-backend-service base-url="${functionAppUrl}" />
        <rewrite-uri template="/" />
      </inbound>
      <backend>
        <forward-request />
      </backend>
      <outbound>
        <set-header name="X-Powered-By" exists-action="delete" />
      </outbound>
    </policies>
    '''
  }
}

output apimBaseUrl string = 'https://${apim.name}.azure-api.net/incidents'

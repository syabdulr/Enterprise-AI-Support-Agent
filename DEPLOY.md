# Deployment Guide — Azure Functions + API Management

This stack turns the incident-write + severity-classification logic into a
governed API surface:

```
client → APIM (subscription key, rate limit) → Function App → Dataverse
```

## Prerequisites

- Azure CLI (`az`) and Azure Functions Core Tools (`func`) installed
- An Azure subscription (free tier is sufficient: Functions Consumption
  gives 1M executions/month free; APIM Consumption is pay-per-call)
- Dataverse environment credentials (Power Apps Developer Plan) — the same
  `DATAVERSE_*` values used by the rest of this repo
- Python 3.11

## 1. Provision infrastructure (Bicep)

```bash
az login

az group create --name aecon-demo-rg --location canadacentral

az deployment group create \
  --resource-group aecon-demo-rg \
  --template-file infra/function-app.bicep \
  --parameters appName=incident-write-func \
    dataverseUrl=https://<org>.crm.dynamics.com \
    dataverseTenantId=<tenant-id> \
    dataverseClientId=<client-id> \
    dataverseClientSecret=<client-secret>

az deployment group create \
  --resource-group aecon-demo-rg \
  --template-file infra/apim.bicep \
  --parameters apimName=incident-apim \
    functionAppUrl=https://incident-write-func.azurewebsites.net
```

Secure parameters are passed at deploy time and never committed.

## 2. Local development and testing

```bash
pip install -r requirements.txt -r requirements-dev.txt

# unit tests (network mocked at the HTTP boundary)
python -m pytest tests/unit/ tests/test_self_reflection.py --no-cov

# local function runtime
func start
```

The function imports `src.dataverse` from the repo root, so run `func start`
from the repo root (see `host.json`).

## 3. Publish the function code

```bash
func azure functionapp publish incident-write-func
```

## 4. End-to-end verification

Create a subscription in APIM, get its key, then:

```bash
curl -X POST https://incident-apim.azure-api.net/incidents \
  -H "Ocp-Apim-Subscription-Key: <key>" \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Site A - North Tower",
    "description": "Worker reported unstable scaffolding on level 3",
    "reporter": "jsmith@aecon.com",
    "severity": "high"
  }'
```

Expected: `201` with the Dataverse record ID in the response body.

## 5. Teardown (avoid ongoing costs)

```bash
az group delete --name aecon-demo-rg --yes
```

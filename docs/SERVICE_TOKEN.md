# Service Token Authentication

## Overview

Service tokens allow service-to-service authentication using JWT tokens with the special `SERVICE` role.

## Generating a Service Token

Use the provided script to generate a service token:

```bash
1. First activate venw
# For example using conda
conda activate bioscopeai-core

2. Generate service token
# Generate token valid for 365 days (default)
python scripts/generate_service_token.py my-service

# Generate token valid for specific number of days
python scripts/generate_service_token.py classification-service --days 730
```

Output example:
```
================================================================================
Service Token Generated Successfully
================================================================================

Service Name: classification-service
Role: service
Valid for: 365 days

Token:
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...

================================================================================
Usage in HTTP requests:
  Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
================================================================================
```

## Using Service Tokens

### In HTTP Requests

```bash
curl -H "Authorization: Bearer <service_token>" \
     http://localhost:8000/api/images/{image_id}/download
```

## Endpoints that Accept Service Tokens

Service tokens work with any endpoint that requires authentication.

## Adding Service Token Support to Endpoints

Service tokens automatically work with the existing `require_role()` dependency:

```python
from bioscopeai_core.app.auth.permissions import require_role
from bioscopeai_core.app.models import UserRole

@router.get("/internal/data")
async def get_data(
    user: Annotated[User, Depends(require_role(UserRole.SERVICE.value))],
):
    # This endpoint only accepts SERVICE role tokens
    service_name = user.id  # Service name is stored in user.id
    ...
```

## Security Notes

- Service tokens are long-lived (default 365 days) - store them securely
- Treat service tokens like passwords - never commit them to version control
- Use environment variables or secret management systems to store tokens
- Rotate tokens periodically
- Each service should have its own unique token
- Monitor service token usage in logs

## Environment Variables

Store service tokens in environment variables:

```bash
# .yaml
SERVICE_TOKEN=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

```python
import os

service_token = os.getenv("SERVICE_TOKEN")
```

## Token Structure

Service tokens are standard JWT tokens with:
- `sub`: Service name (identifier)
- `roles`: "service"
- `exp`: Expiration timestamp
- `iat`: Issued at timestamp

Example decoded payload:
```json
{
  "sub": "classification-service",
  "roles": "service",
  "exp": 1736208000,
  "iat": 1704672000
}
```

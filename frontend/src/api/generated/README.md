# Auto-Generated API Types

**⚠️ DO NOT EDIT FILES IN THIS DIRECTORY MANUALLY**

This directory contains auto-generated TypeScript types and API clients created from the OpenAPI specification.

## How to Regenerate

```bash
npm run generate-api
```

**Requirements:**
- Backend Flask server must be running on port 5000
- Run from project root directory

## What Gets Generated

- **`data-contracts.ts`** - All TypeScript type definitions
- **`Api.ts`** - Main API client class  
- **`http-client.ts`** - HTTP client utilities
- Other route-specific API client files

## Generator Tool

Generated using [swagger-typescript-api](https://github.com/acacode/swagger-typescript-api)

## Import Types

Don't import directly from this directory. Use the convenience exports:

```typescript
// ✅ Good
import type { Repair, RepairUpdate } from '@/api/types'

// ❌ Avoid
import type { RepairResponse } from '@/api/generated/data-contracts'
```

## When to Regenerate

Regenerate whenever you modify backend Pydantic schemas in `/app/schemas.py`:

1. Make changes to Pydantic schemas
2. Start backend: `FLASK_ENV=dev python -m flask run`
3. Run: `npm run generate-api`
4. Commit the generated files

## Troubleshooting

**Error: Cannot connect to server**
- Ensure Flask is running: `FLASK_ENV=dev python -m flask run`
- Check server is on port 5000

**Error: Spec parsing failed**
- Check backend OpenAPI spec is valid: visit `http://localhost:5000/apispec_1.json`
- Ensure all Pydantic schemas are properly defined

**Types don't match backend**
- Regenerate types: `npm run generate-api`
- Make sure backend server is running latest code

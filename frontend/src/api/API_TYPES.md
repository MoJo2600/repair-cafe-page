# API Types - Auto-Generated

This document explains how frontend types are automatically generated from the backend API.

## Overview

The frontend uses **auto-generated TypeScript types** from the OpenAPI specification using **`swagger-typescript-api`**. Types are generated directly from the backend's Pydantic schemas, ensuring perfect consistency.

## Type Generation

### Command

```bash
npm run generate-api
```

This runs:
```bash
swagger-typescript-api generate -p http://localhost:5000/apispec_1.json -o ./frontend/src/api/generated --modular --extract-request-params --extract-request-body
```

### Requirements

- Backend Flask server must be running on port 5000
- OpenAPI spec available at `http://localhost:5000/apispec_1.json`

### Generated Files

All generated files are in `/frontend/src/api/generated/`:
- **`data-contracts.ts`** - All type definitions (RepairCreate, RepairUpdate, RepairResponse, etc.)
- **`Api.ts`** - Main API client class
- **`http-client.ts`** - HTTP client utilities
- Other route-specific files

## Type Location

Generated types are exported from `/frontend/src/api/types.ts` for convenient importing:

```typescript
import type { Repair, RepairUpdate, RepairCreate } from '@/api/types'
// or
import type { Repair } from '@/api'
```

## Available Types

All types match the backend Pydantic schemas:

### Repair Types
- `Repair` / `RepairResponse` - Full repair object
- `RepairCreate` - For creating new repairs
- `RepairUpdate` - For updating existing repairs (all fields optional)
- `RepairCreateResponse` - API response for repair creation

### Repair Log Types
- `RepairLogCreate` - Create repair log
- `RepairLogResponse` - Full repair log object
- `RepairLogListResponse` - List response

### VDE Test Types
- `VdeTestCreate` - Create VDE test
- `VdeTestResponse` - Full VDE test object  
- `VdeTestListResponse` - List response

### Generic Types
- `APIResponse` - Standard API response format

## When to Regenerate

Regenerate types whenever you modify Pydantic schemas in `app/schemas.py`:

1. Start the backend: `FLASK_ENV=dev python -m flask run`
2. Generate types: `npm run generate-api`
3. Commit the generated files

## Type Mapping

Python (Pydantic) → TypeScript mapping:

- `str` → `string`
- `int` → `number`
- `float` → `number`
- `bool` → `boolean`
- `date` → `string` (with `@format date` comment)
- `datetime` → `string` (with `@format date-time` comment)
- `Optional[T]` → `T | null` or `T?`
- `Literal["A", "B"]` → `string` (with `@pattern` comment)
- `List[T]` → `T[]`

## Benefits

✅ **Zero Maintenance** - Types auto-generated from backend  
✅ **Always in Sync** - Types match backend schemas exactly  
✅ **Type Safety** - Full TypeScript compile-time checking  
✅ **IntelliSense** - Complete autocomplete in IDE  
✅ **Documentation** - JSDoc comments from Pydantic Field descriptions  
✅ **Validation Hints** - Min/max constraints in comments

## Importing Types

```typescript
// Import from API index (recommended)
import type { Repair, RepairUpdate } from '@/api/models/Repair'
// or
import type { Repair } from '@/api'

// Use in components
const repair = ref<Repair | null>(null)

// Use in stores
const repairs = ref<Repair[]>([])

// Use in functions
function updateRepair(id: number, updates: RepairUpdate) {
  // ...
}
```

## Type Safety Benefits

1. **Compile-time errors** - Catch mismatched types before runtime
2. **IntelliSense** - Get autocomplete and documentation in your IDE
3. **Refactoring** - Safely rename fields across the codebase
4. **Documentation** - Types serve as inline documentation
5. **Consistency** - Frontend and backend speak the same language

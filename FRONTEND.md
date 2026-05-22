# Frontend — Vue 3 + TypeScript + Vuetify

> For setup, commands, project structure, and troubleshooting see [QUICK_REFERENCE.md](QUICK_REFERENCE.md).

---

## Technology Stack

- **Vue 3** — Composition API with `<script setup lang="ts">`
- **TypeScript** — strict mode, full type safety
- **Vuetify 3** — Material Design component library
- **Vite** — dev server with HMR and production build
- **Pinia** — state management
- **vue-router** — client-side routing
- **@mdi/font** — Material Design Icons

---

## Vuetify Component Cheat Sheet

| Category | Components |
|----------|-----------|
| Layout | `v-app`, `v-main`, `v-container`, `v-row`, `v-col` |
| Navigation | `v-app-bar`, `v-navigation-drawer`, `v-bottom-navigation` |
| Forms | `v-text-field`, `v-select`, `v-checkbox`, `v-radio`, `v-switch`, `v-autocomplete` |
| Buttons | `v-btn`, `v-btn-group`, `v-fab` |
| Cards | `v-card`, `v-card-title`, `v-card-text`, `v-card-actions` |
| Lists | `v-list`, `v-list-item`, `v-list-group` |
| Tables | `v-data-table` |
| Dialogs | `v-dialog`, `v-menu`, `v-overlay` |
| Feedback | `v-alert`, `v-snackbar`, `v-banner`, `v-progress-circular` |

Full docs: https://vuetifyjs.com/components/

---

## Theme Customization

Edit `frontend/src/plugins/vuetify.ts`:

```typescript
theme: {
  themes: {
    light: {
      colors: {
        primary: '#1976D2',
        secondary: '#424242',
        // add / override colors here
      },
    },
  },
},
```

---

## Adding New Components

1. Create `frontend/src/components/MyComponent.vue`
2. Use `<script setup lang="ts">`
3. Import and use Vuetify components directly (globally registered)
4. Import the component in a view or parent component

---

## Auto-Generated API Client

The TypeScript API client in `frontend/src/api/` is generated from the Flask OpenAPI spec.

### Regenerate

1. Start the Flask backend (`cd app && flask run --port 5000`)
2. Run the generator:

```bash
cd frontend && pnpm generate-api
```

This fetches the spec from `http://localhost:5000/apispec_1.json` and writes typed client code to `frontend/src/api/generated/`.

### When to regenerate

- After adding or changing Flask API endpoints
- After modifying request/response schemas
- After updating Swagger documentation

### Usage

```typescript
import { RepairsService } from '@/api/services/RepairsService'

const repairs = await RepairsService.listRepairs()
```

All service methods are fully typed — parameter and return types come from the generated client.

---

## Production Notes

- `pnpm build` outputs to `app/static/dist/` — Flask serves these as static files
- The Vite dev server proxies `/api/*` requests to Flask (configured in `vite.config.ts`)
- In production only Flask needs to run; the built assets are self-contained


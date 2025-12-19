# Vue 3 + TypeScript + Vite + Ant Design Vue + Axios

This project is set up with Vue 3, TypeScript, Vite, Ant Design Vue, and Axios.

## Tech Stack

- **Vue 3** - Progressive JavaScript framework
- **TypeScript** - Typed superset of JavaScript
- **Vite** - Next generation frontend tooling
- **Ant Design Vue** - Enterprise-class UI design language and Vue UI library
- **Axios** - Promise-based HTTP client

## Project Setup

### Install Dependencies

```bash
npm install
```

### Development

```bash
npm run dev
```

### Build

```bash
npm run build
```

### Preview

```bash
npm run preview
```

## Configuration

### Ant Design Vue

Ant Design Vue is already configured in `src/main.ts`. You can import components directly:

```vue
<script setup lang="ts">
import { Button, Card } from 'ant-design-vue'
</script>
```

### Axios

Axios is configured in `src/api/axios.ts` with:
- Base URL configuration (can be set via `VITE_API_BASE_URL` environment variable)
- Request/Response interceptors
- Default headers

Example usage:

```typescript
import apiClient from './api/axios'

const response = await apiClient.get('/endpoint')
```

## Learn More

- [Vue 3 Documentation](https://vuejs.org/)
- [TypeScript Guide](https://vuejs.org/guide/typescript/overview.html#project-setup)
- [Ant Design Vue](https://antdv.com/)
- [Axios Documentation](https://axios-http.com/)

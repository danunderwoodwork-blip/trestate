---
name: API client extra headers
description: How to inject static per-session headers (e.g. X-Device-Id) into all API calls
---

`lib/api-client-react/src/custom-fetch.ts` was extended with `setExtraHeaders(headers: Record<string, string>)`.

It is re-exported from `lib/api-client-react/src/index.ts`.

**Usage in main.tsx:**
```ts
import { setExtraHeaders } from '@workspace/api-client-react';
setExtraHeaders({ 'X-Device-Id': getDeviceId() });
```

**Why:** The TREstate backend identifies anonymous users by `X-Device-Id` header. The generated API client had no hook for static headers before this change.

**How to apply:** Call `setExtraHeaders` once at app startup (before first render) in `src/main.tsx`. The headers are merged into every `customFetch` call for that session.

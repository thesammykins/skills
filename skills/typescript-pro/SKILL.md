---
name: typescript-pro
description: Enforces 2025 strict TypeScript standards. Focuses on type safety at runtime (Zod), strict compiler options, and advanced type gymnastics only when necessary to prevent bugs.
license: MIT
---

## What I do
- Audit and generate `tsconfig.json` with maximum strictness (`noUncheckedIndexedAccess`).
- Implement runtime validation using `zod` for all IO boundaries (API responses, form inputs).
- Refactor `any` and loose types to strict, narrowed types.
- Apply "Branded Types" for primitives (e.g., `UserId` vs `string`) to prevent logic errors.

## When to use me
- When setting up a new TypeScript project.
- When asked to "fix type errors" or "improve type safety".
- When writing API clients or data processing logic.
- Triggers: "strict mode", "zod validation", "type safety", "refactor types".

## Instructions

### 1. The Holy Configuration
- A Senior Engineer's `tsconfig.json` in 2025 MUST include:
  ```json
  {
    "compilerOptions": {
      "strict": true,
      "noUncheckedIndexedAccess": true,
      "exactOptionalPropertyTypes": true,
      "noImplicitOverride": true,
      "forceConsistentCasingInFileNames": true,
      "skipLibCheck": true
    }
  }
  ```
- **Why**: `noUncheckedIndexedAccess` prevents the billion-dollar mistake of assuming array access always returns a value.

### 2. Runtime Validation (Zod)
- **Rule**: NEVER trust external data (API, DB, User Input). Casts (`as User`) are forbidden at boundaries.
- **Pattern**:
  ```ts
  import { z } from 'zod';

  const UserSchema = z.object({
    id: z.string().uuid(),
    email: z.string().email(),
    role: z.enum(['ADMIN', 'USER']),
  });

  type User = z.infer<typeof UserSchema>;

  function parseUser(input: unknown): User {
    return UserSchema.parse(input); // Throws if invalid
  }
  ```

### 3. Anti-Patterns to Annihilate
- **The `any` Plague**: If you must escape, use `unknown` and narrow it.
- **Ghost Types**: Don't define types that don't match runtime reality.
- **Enum Abuse**: Prefer `const` assertions or Zod enums over TypeScript `enum` (which emits runtime code).
  - *Good*: `const Roles = { Admin: 'admin' } as const; type Role = typeof Roles[keyof typeof Roles];`

### 4. Advanced Patterns
- **Branded Types**: Use for IDs to prevent mixing `UserId` and `OrderId`.
  ```ts
  declare const brand: unique symbol;
  type Brand<T, TBrand> = T & { [brand]: TBrand };
  type UserId = Brand<string, 'UserId'>;
  ```

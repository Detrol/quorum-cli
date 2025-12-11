# ADR-0003: Zustand for Frontend State Management

## Status

Accepted

## Context

The Quorum frontend (built with Ink/React for terminal UI) needs to manage:
- View mode (input, discussion, models, command palette)
- Selected models and validation state
- Discussion state (messages, phase, paused, thinking)
- UI modal visibility (8+ modals)
- Input history and navigation

State is accessed across many components:
- `App.tsx` - Main orchestrator
- `InputView.tsx` - Question input
- `DiscussionView.tsx` - Message display
- Various modals and overlays

Requirements:
- Reactive updates when state changes
- Accessible from any component without prop drilling
- Supports complex nested updates (arrays, objects)
- Works with React concurrent features

## Decision

Use **Zustand** with **Immer middleware** for global state management.

```typescript
import { create } from "zustand";
import { immer } from "zustand/middleware/immer";

export const useStore = create<StoreState>()(
  immer((set) => ({
    // State
    viewMode: "input",
    messages: [],

    // Actions mutate draft directly (Immer handles immutability)
    addMessage: (message) =>
      set((state) => {
        state.messages.push(message);
      }),
  }))
);
```

Components subscribe to specific slices:
```typescript
const messages = useStore((state) => state.messages);
const addMessage = useStore((state) => state.addMessage);
```

## Consequences

### Positive

- **Minimal boilerplate**: No reducers, action types, or dispatch
- **Direct mutation syntax**: Immer allows `state.foo = bar` instead of spreading
- **Selective subscriptions**: Components only re-render when their slice changes
- **No provider wrapper**: Works without React Context provider
- **TypeScript native**: Full type inference out of the box
- **Small bundle**: ~2KB minified

### Negative

- **Less structure**: No enforced patterns like Redux
- **Immer overhead**: Slight performance cost for deep objects
- **Debugging**: No Redux DevTools time-travel (though Zustand has middleware)
- **Less ecosystem**: Fewer middleware/tools than Redux

### Neutral

- Single store pattern (all state in one place)
- Actions colocated with state (not separate files)
- No middleware for async (actions can be async directly)

## Alternatives Considered

### Redux Toolkit

Industry standard for React state. Rejected because:
- Significant boilerplate (slices, reducers, selectors)
- Overkill for CLI application
- Provider wrapper required
- Larger bundle size

### React Context + useReducer

Built-in React solution. Rejected because:
- Re-renders all consumers on any state change
- Requires manual memoization
- Boilerplate for complex state
- No middleware ecosystem

### Jotai

Atomic state management. Rejected because:
- Better for fine-grained atoms, not single large store
- Less intuitive for application state
- Learning curve for atom patterns

### MobX

Observable-based state. Rejected because:
- Heavier runtime
- Class-based patterns don't fit functional style
- Proxy-based reactivity can be surprising

## References

- [Zustand Documentation](https://zustand-demo.pmnd.rs/)
- [Zustand GitHub](https://github.com/pmndrs/zustand)
- [Immer Documentation](https://immerjs.github.io/immer/)
- `frontend/src/store/index.ts` - Store implementation

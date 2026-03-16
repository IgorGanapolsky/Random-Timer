<!-- tech-stack: universal -->
# Testing

## General Principles

- Co-locate test files next to the source file they test.
- Name test files to match source: `Xxx.test.tsx` or `xxx.test.ts`.
- Use `describe` → `it` / `test` blocks for structure.
- Name test cases descriptively: `it('should display error when API fails')`.

## API Mocking

- Use a mock server or interceptor (e.g., MSW) for API mocking in tests.
- Avoid mocking implementation details — mock at the network layer.

## Component Testing

- Use a testing library (e.g., `@testing-library/react`) for rendering and assertions.
- Test behavior, not implementation details.
- Prefer user-event simulations over programmatic state changes.

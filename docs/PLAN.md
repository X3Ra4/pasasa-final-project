# Smak Implementation Plan

> Execute inline with test-driven-development; independent review before publication.

**Spec:** [SPEC.md](SPEC.md)
**Architecture:** Expo Router screens, reusable UI, typed API boundary, transactional persisted Context.

- [ ] 1. Tests first for normalization, API failure/empty/query, storage corruption, serialized writes,
  offline snapshots, shopping import deduplication and form validation; implement `src/core/`.
- [ ] 2. Context, theme and animations; implement Router tabs, detail, shopping form and onboarding.
- [ ] 3. Integration tests for persistence/navigation/error states; real public API checks and browser QA.
- [ ] 4. Native bundles/build configuration, docs, screenshots, independent review, GitHub CI/push.

Review focus: stale API response after search change; storage writes on hydration; removal of saved
meal while detail open; malformed API/storage data; duplicate ingredient imports; rapid edits.

Initial: generated with create-expo-app, isolated orphan branch. Android SDK absent locally.

# PASASA submission plan

Goal: turn the existing Django map catalog into a reproducible final project and publish a new public GitHub repository, as requested.

Architecture: preserve existing interactive maps and models. Add a separate catalog module with ModelForms and server-rendered CRUD for Map, Spot and Place. Visitors read; registered users create and manage their own locations; staff manage maps and all locations. Supporting dictionaries, media and ratings remain manageable through Django Admin.

Constraints: no personal database or user uploads in Git; Python 3.12-compatible Django 5.2 LTS; Ukrainian submission documentation; screenshots of the actual application.

- [x] Add failing integration tests for CRUD, ownership, coordinate validation, protected deletion, registration, search/filter/sort and demo seeding.
- [x] Implement catalog forms, views, routes and templates; add authentication and navigation.
- [x] Add repeatable demo seed command, configuration and dependencies.
- [x] Run all tests, migration checks and a fresh database startup; inspect the UI and capture screenshots.
- [x] Write README, theme description, requirement mapping and defense walkthrough.
- [ ] Review changes, create the new GitHub repository, push and verify remote contents.

Review focus: another user's object; nonstaff map mutations; deleting a map with locations; invalid coordinates/filter values; repeat demo seeding without overwriting edits.

Verification: 17 Django tests pass; check reports no issues; makemigrations --check reports no changes; all migrations applied to an empty database. Browser registration/login/logout and location CRUD passed on desktop and mobile, with no JS errors or mobile horizontal overflow. Six actual screenshots captured.

Independent review: identified optional PvE fields causing invisible markers and mixed-null resource sorting failures. Both reproduced by failing tests, then fixed; full suite passed. No unresolved important review findings.

Implementation decisions: preserve optional nullable fields in existing schema for compatibility; require complete data in new public forms and handle legacy null resources in the interactive view. Use Django 5.2 LTS for Python 3.12 compatibility. No private source database, credentials or user uploads are included in publication.

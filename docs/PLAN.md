# TaskFlow Implementation Plan

> Implement inline using executing-plans; final independent review.

**Goal:** Complete the approved TaskFlow website and publish its dedicated Git branch.
**Architecture:** Django monolith, shared policy/query helpers for HTML and REST, PostgreSQL Compose.
**Spec:** [SPEC.md](SPEC.md).

## Constraints and review focus
Private projects never leak through lists, IDs, API or statistics. Members cannot escalate rights.
Reject assigning outsiders or moving tasks across projects. Member removal revokes assignment/access.
Archived tasks cannot be modified by an assignee. Escape comments; enforce CSRF and POST changes.

## 1. Domain and access
- [x] Write failing HTTP/API tests for owner CRUD, member status, outsider isolation, invalid assignee,
  membership removal, archive/restore, statistics and filters in `board/tests.py`.
- [x] Run tests and record missing behavior; implement `models.py`, `policies.py`, `forms.py`,
  `views.py`, `api.py`, `urls.py` and migrations. Run complete Django suite.
## 2. Website
- [x] Implement responsive Ukrainian templates, local Bootstrap, styles and progressive JavaScript.
- [x] Add signup/login/logout, dashboard, board, detail/comments, settings and confirmation pages.
- [x] Run browser workflow signup→project→task→edit→comment→archive→restore→delete;
  check mobile overflow and capture screenshots.
## 3. Delivery
- [x] Add seed_demo, Dockerfile, Compose, Nginx, CI, deployment/user/API documentation and tracker templates.
- [x] Run suite against PostgreSQL, actual HTTP through Nginx/Gunicorn, static assets, migrations, pip check.
- [x] Independent review; fix important findings with regression tests; commit/push dedicated branch.

## Progress
Initial: empty orphan branch, clean baseline; previous PASASA branches preserved.

Verification: SQLite 29 passed / 4 PostgreSQL-only skipped; PostgreSQL 33 passed. Browser and real container HTTP passed. Independent review findings TF-B01..03 fixed with regression tests. Publication is the remaining delivery action.

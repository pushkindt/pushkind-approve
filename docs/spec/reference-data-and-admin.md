# Reference Data and Admin Specification

## Purpose

The admin area manages hub-specific reference data and application settings that drive order numbering, exports, category metadata, and project/site availability.

## Entry Points

- `/admin/`: consolidated admin page.
- `/admin/app/save`
- `/admin/category/edit/`, `/admin/category/add/`, `/admin/category/remove/<id>`
- `/admin/project/add`, `/admin/project/edit/`, `/admin/project/remove/<id>`
- `/admin/site/add`, `/admin/site/edit/`, `/admin/site/remove/<id>`
- `/admin/income/add`, `/admin/income/edit/`, `/admin/income/remove/<id>`
- `/admin/cashflow/add`, `/admin/cashflow/edit/`, `/admin/cashflow/remove/<id>`

All admin endpoints are `admin`-only.

## App Settings

`AppSettings` is unique per hub and stores:

- whether 1C email sending is enabled
- 1C recipient email
- numeric order ID bias
- whether multi-category cart orders are allowed
- a free-text alert shown on the inbox

The app settings form also allows uploading a PNG logo, saved under `app/static/upload/` as `logo<hub_id>.<ext>`.

## Categories

Categories are hub-scoped and can be created or removed by name. The edit flow enriches a category with:

- responsible person text
- functional budget text
- income statement and cashflow statement references
- code
- optional JPG/PNG image stored in `app/static/upload/category-<id>.<ext>`

Category rows are also used to derive order categories, catalog membership, validator assignments, and 1C export fields.

## Projects and Sites

- Projects are hub-scoped, named, optionally keyed by `uid`, and can be enabled or disabled.
- Sites belong to a project and can also store an optional `uid`.
- Non-admin pages usually filter projects to `enabled=True`; admin pages can edit disabled projects.
- Duplicate names within the current hub are rejected during create or edit.

## Budget Statements

Income statements (`БДР`) and cashflow statements (`БДДС`) are simple named reference tables scoped to the hub. They are selected in order review, category metadata, and limit records.

## Operational Notes

- Deletes are immediate and depend on SQLAlchemy relationship cleanup and database FK behavior.
- Some admin endpoints query only by object ID without re-checking `hub_id`, so the intended rule is hub-scoped but the implementation is worth reviewing for cross-hub hardening.

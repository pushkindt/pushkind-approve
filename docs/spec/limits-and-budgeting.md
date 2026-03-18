# Limits and Budgeting Specification

## Purpose

Budget limits track approved spend by project, cashflow statement, and time interval. The system also exposes a small authenticated API to refresh current limit usage.

## Core Model

`OrderLimit` contains:

- `hub_id`
- limit `value`
- computed `current`
- manual `external_expenses`
- `cashflow_id`
- `project_id`
- `interval` in `daily`, `weekly`, `monthly`, `quarterly`, `annually`, `all_time`

## UI Routes

- `/limits/`, `/limits/show`
- `/limits/add`
- `/limits/edit`
- `/limits/remove/<id>`

`default`, `vendor`, and `supervisor` are blocked from the limits page. Add, edit, and remove additionally block `supervisor`, leaving `admin`, `purchaser`, `validator`, and `initiative` able to mutate limits.

## Recalculation Logic

`OrderLimit.update_current()` recalculates current spend per matching limit:

- filters orders by the interval start timestamp from `get_filter_timestamps()`
- joins through `Site` to match the limit’s project
- filters by matching order cashflow statement
- sums `order.total` only for `approved` orders
- sets `limit.current`

If `current + external_expenses` exceeds 95% of the configured limit, each matching non-approved order is marked `over_limit=True`.

## Recalculation Triggers

Recalculation is called after:

- adding or editing a limit
- order approval state changes that include site and cashflow
- some order structure or parameter changes such as split, duplicate, quantity change, statement change, or site/category change
- `/api/daily/limits`

Removing a limit deletes the row but does not itself clear any previously set `order.over_limit` flags on related orders.

## API Endpoint

`GET /api/daily/limits` uses HTTP Basic Auth. Only authenticated users with role `admin` are allowed. On success it recalculates all current limits for the admin’s hub and returns empty body with status `200`. Non-admin authenticated users receive `403`; failed auth receives `401`.

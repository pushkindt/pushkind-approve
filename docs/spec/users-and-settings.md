# Users and Settings Specification

## Purpose

The settings subsystem handles both self-service profile editing and admin-driven user administration, including role assignment and the project/category bindings that determine order review responsibility.

## Entry Points

- `/settings/`
- `/users/remove/<id>`
- `/users/download`
- `/dashboard/`
- `/dashboard/<user_id>`

## Self-Service vs Admin Behavior

- `admin` gets `UserRolesForm` and can edit any user in the current hub, plus unassigned `default` users.
- `purchaser`, `validator`, and `initiative` can edit only their own profile via `UserSettingsForm`.
- `vendor` and `default` cannot access `/settings/`.

See `access-and-auth.md` for the cross-application permissions matrix.

## User Fields

Editable fields include:

- full name, phone, location
- position name
- notification preferences for new/modified/disapproved/approved/comment emails
- for admins only: role, note, birthday, dashboard URL, and hub assignment
- for validator and purchaser roles only: assigned categories and projects

If a user is not a validator or purchaser, their category and project assignments are cleared. Position names are normalized to lowercase and reused when possible through the `Position` table.

## Review Assignment Effects

Changing a user’s role or position can affect order approval routing:

- orphaned positions are cleaned up by `RemoveExcessivePosition()`
- if the user becomes or stops being a validator, all non-approved hub orders call `update_positions()`
- validator and purchaser assignments determine who appears in `order.reviewers`, inbox filters, and comment notification options

## User Removal and Export

- Removing a user reassigns their initiated orders to the current admin before deletion.
- After deletion, positions are cleaned and non-approved orders may refresh validator positions.
- `/users/download` returns XLSX with profile data, activity timestamps, birthday, dashboard hyperlink, and order statistics such as approved-order count and pending approvals.

## Dashboard Views

- `/dashboard/` shows the current user by default; admins also receive a list of hub users to switch context.
- `/dashboard/<user_id>` is admin-only and renders the selected user’s dashboard URL in the shared dashboard template.

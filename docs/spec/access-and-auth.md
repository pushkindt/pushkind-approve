# Access and Authentication Specification

## Purpose

Authentication is form-based with optional token login via JWT. Authorization is role-driven and enforced primarily by route decorators plus per-query filtering.

## Auth Routes

- `/auth/login/`: email/password login.
- `/auth/login/<token>/`: token login, typically linked from notification emails.
- `/auth/signup/`: public signup for new users; admins can also create users from an authenticated session.
- `/auth/logout/`: logout.
- `/auth/request/`: request password reset mail.
- `/auth/reset/<token>`: set a new password from reset token.

## Authentication Behavior

- Passwords are hashed with Werkzeug helpers.
- Login lowercases email before lookup.
- Successful login redirects to the inbox.
- Failed login returns the login form with flash message `Некорректный логин или пароль.`
- Signup creates a user with no operational role (`default`) unless later edited by an admin.
- Signup sends a “user registered” email after persistence.
- Reset request sends mail only when the email exists; otherwise it flashes that the user was not found.
- JWT tokens are signed with `SECRET_KEY` and encode `user_id` plus expiration timestamp.

## Session and Activity Tracking

- `before_app_request` updates `current_user.last_seen` on most authenticated requests.
- Token login sets `session["skip_last_seen_once"] = True` so the redirect target request does not immediately overwrite `last_seen`.
- The `auth.login_token` endpoint is excluded from the automatic `last_seen` update hook.

## Authorization Model

Roles are defined in `UserRoles`: `default`, `admin`, `initiative`, `validator`, `purchaser`, `supervisor`, `vendor`.

- `role_required()` renders `errors/403.html` when the current role is not allowed.
- `role_forbidden()` renders `errors/403.html` when the current role is forbidden.
- API basic auth uses the same password check and returns JSON error payloads through `error_response()`.

## Effective Permissions

- `default`: can authenticate but is blocked from operational pages.
- `admin`: full access within current hub, including user and reference data administration.
- `initiative`: own-order creation and lifecycle edits, but not user administration or catalog administration.
- `validator`: review-assigned orders and maintain own settings.
- `purchaser`: review-assigned orders, create orders, mark processed/dealdone, maintain own settings.
- `supervisor`: read-only supporting access to enabled-project data.
- `vendor`: sees vendor-relevant orders and manages own product catalog.

## Permissions Matrix

The table below summarizes intended access by route group. Query-level filters still apply inside several allowed areas, especially for orders, products, and settings.

| Route group | default | admin | initiative | validator | purchaser | supervisor | vendor |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/auth/*` | self-service auth only | yes | yes | yes | yes | yes | yes |
| Inbox `/`, `/index/` | no | yes | own orders | assigned orders | assigned orders | enabled-project read | vendor-linked orders |
| Shop `/shop/*` | no | yes | yes | no | yes | no | no |
| Order detail `/orders/<id>` | no | yes | own orders | assigned orders | assigned orders | no direct detail route | vendor-linked orders |
| Order workflow mutations | no | broad access | own-order edits | approval only | processing and selected edits | no | no |
| Admin `/admin/*` | no | yes | no | no | no | no | no |
| Products `/products/*` | no | yes | no | yes | yes | no | own vendor only |
| Stores `/stores/*` | no | yes | read only | read only | read only | no | no |
| Settings `/settings/` | no | all hub users | self only | self only | self only | self only | no |
| User admin `/users/*` | no | yes | no | no | no | no | no |
| Limits `/limits/*` | no | yes | yes | yes | yes | no | no |
| History `/history/` | no | yes | yes | yes | yes | yes | no |
| Help `/help/` | no | yes | yes | yes | yes | yes | no |
| Dashboard `/dashboard/*` | yes for self after auth | yes | self only | self only | self only | self only | self only |
| API `/api/*` | no | basic-auth admin only | no | no | no | no | no |

## Order Workflow Permission Breakdown

For `/orders/*` mutations, current implementation splits access as follows:

| Action | admin | initiative | validator | purchaser | supervisor | vendor |
| --- | --- | --- | --- | --- | --- | --- |
| comment | yes | yes | yes | yes | no | no |
| edit parameters or statements | yes | yes | yes | yes | no | no |
| approve or disapprove | no | no | yes | no | no | no |
| change quantity | yes | yes | no | yes | no | no |
| duplicate | yes | yes | no | yes | no | no |
| split | yes | yes | no | yes | no | no |
| merge from inbox | yes | yes | no | yes | no | no |
| mark purchased | yes | no | no | yes | no | no |
| mark dealdone | yes | no | no | yes | no | no |
| cancel | yes | yes | no | no | no | no |
| export XLSX | yes | yes | yes | yes | no | yes if order visible |

## Important Constraints

- Many routes rely on both decorator checks and query filtering. The spec for each subsystem should describe both layers.
- New users created by signup are not automatically attached to a hub and require admin configuration before meaningful access.

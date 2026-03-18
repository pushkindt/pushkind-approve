# Order Lifecycle Specification

## Purpose

Orders are the central business object. They can be created from the shopping catalog, viewed in the inbox, edited while open, approved by validators, processed by purchasers, exported, commented on, merged, split, duplicated, and cancelled.

## Entry Points

- `/shop/`, `/shop/<cat_id>`, `/shop/order`: browse catalog and create orders.
- `/`, `/index/`: inbox listing with role-specific filtering.
- `/orders/<order_id>`: single-order detail page.
- Workflow actions: `/orders/merge/`, `/orders/save/`, `/orders/split/<id>`, `/orders/duplicate/<id>`, `/orders/quantity/<id>`, `/orders/approval/<id>`, `/orders/statements/<id>`, `/orders/parameters/<id>`, `/orders/comment/<id>`, `/orders/process/<id>`, `/orders/cancel/<id>`, `/orders/dealdone/<id>`, `/orders/excel1/<id>`, `/orders/excel2/<id>`, `/orders/excel1C/<id>`.

## Order Creation

`initiative`, `purchaser`, and `admin` can create orders from the shop cart. The cart stores product ID, quantity, free-text comment, and optional product option selections. Creation validates that the target site exists under the chosen project, ignores unknown cart items, derives vendors and categories from the selected products, and computes total price from quantity × unit price.

If `AppSettings.single_category_orders` is enabled, a cart spanning multiple categories is rejected. New orders start with status `new`, use a string order number derived from total order count plus `order_id_bias`, and immediately call `update_positions()` to derive validator positions. A `new` email notification is sent after creation.

## Visibility Rules

Order access is filtered by `GetOrder()` and the inbox query:

- `initiative`: only own orders.
- `validator` and `purchaser`: orders matching at least one assigned category and one assigned project.
- `vendor`: only orders assigned to the vendor with matching email.
- `supervisor`: enabled-project orders only in the inbox; no single-order write access.
- `admin`: hub-wide access.

The inbox also supports date filtering, optional inclusion of disapproved and cancelled orders, and a role-specific "focus" mode for validators and purchasers.

The shared route-group and action-level permission tables live in `access-and-auth.md`.

## Status Model

Statuses are `new`, `not_approved`, `partly_approved`, `approved`, `modified`, and `cancelled`.

- `update_positions()` derives required validator positions from project/category assignments.
- `update_status()` sets `approved` if all `OrderPosition.approved` values are true.
- Any `OrderApproval` with non-null `product_id` forces `not_approved`.
- Otherwise the order becomes `partly_approved`.
- Orders without site, with disabled project, or already cancelled are not auto-transitioned.
- Quantity changes set status to `modified` and wipe prior approvals.
- Cancellation sets status to `cancelled` and total to `0`.

## State Machine

### State meanings

- `new`: newly created order before validator approval has been computed into an approved or disapproved result.
- `partly_approved`: order has active approval positions, is not fully approved, and has no disapproval rows.
- `not_approved`: at least one order-level or product-level disapproval row exists.
- `approved`: every required `OrderPosition` is marked approved.
- `modified`: an existing order was edited through quantity change and prior approvals were cleared.
- `cancelled`: the order was explicitly cancelled and should not be edited further.

### Transition table

| From | Trigger | To | Notes |
| --- | --- | --- | --- |
| none | Shop cart creation | `new` | New order, derived positions, `new` notification email |
| `new` or `modified` or `partly_approved` | Validator approves all required positions via `SaveApproval` | `approved` | May trigger `approved` email and optional 1C email |
| `new` or `modified` or `partly_approved` | Validator disapproves order or product via `SaveApproval` | `not_approved` | Triggered by any `OrderApproval.product_id != None` |
| `new` or `modified` or `not_approved` | Validator approval removes all disapprovals but not all positions are approved | `partly_approved` | Computed by `update_status()` |
| any non-cancelled status | Quantity edit via `SaveQuantity` | `modified` | Total recalculated and all approvals deleted |
| any non-cancelled status | Parameter edit via `SaveParameters` | recomputed | User approvals deleted, positions rebuilt, status may change |
| any non-cancelled status | Explicit cancel via `CancelOrder` | `cancelled` | Total set to `0`, cancellation event recorded |

### Status-adjacent flags

- `purchased=True` is set by `ProcessHubOrder` and does not change `status`.
- `dealdone=True` is set by `SetDealDone` and does not change `status`.
- `exported=True` is set when 1C export is emailed and does not change `status`.
- `over_limit=True` is set during limit recalculation and does not change `status`.

## Review and Editing Flows

- `SaveApproval` is validator-only. A null `product_id` means full approval; `0` means full disapproval; any positive `product_id` is a position-level remark against a specific product.
- Approving removes the same user’s previous approval rows. Disapproving a product or whole order updates the matching `OrderPosition` to `approved=False`.
- A duplicate action by the same validator with the same remark is rejected.
- On status change to `approved`, the system sends `approved` emails and may auto-send 1C export mail if admin settings enable it.
- On status change to `not_approved`, the system sends `disapproved` emails.
- `SaveStatements` updates income and cashflow references and records audit events.
- `SaveParameters` updates project/site/categories, deletes user approvals, recalculates approval positions, and may change status.
- `LeaveComment` records an `OrderEvent` and can notify selected reviewers only.
- `SetDealDone` marks `dealdone=True`, logs an event, and can notify reviewers.
- `ProcessHubOrder` marks `purchased=True` and logs the vendor list but does not send vendor mail itself.

## Structural Mutations

- `DuplicateOrder` copies products, totals, references, categories, and vendors into a new `new` order owned by the current user.
- `SplitOrder` is allowed for `admin`, `initiative`, and `purchaser` when the order has no children and is neither approved nor cancelled. It creates two child orders, zeroes the original total, logs split events, recalculates positions, and sends `new` emails for each child.
- `MergeOrders` creates a new order from at least two source orders. Site, income statement, and cashflow statement must match across all sources. Products with the same SKU plus selected-option signature are combined by quantity. Source orders remain but totals are zeroed and linked as parents.
- `SaveQuantity` changes a single product quantity, logs a quantity event, clears existing approvals, and recalculates totals.

## Exports and Side Effects

- `/orders/save/` exports selected inbox rows to XLSX summary format.
- `/orders/excel1/<id>` and `/orders/excel2/<id>` generate document-style XLSX files from bundled templates.
- `/orders/excel1C/<id>` generates a 1C-oriented XLSX file. With `?send=true`, it emails the file to `AppSettings.email_1C`, logs an `exported` event, and sets `order.exported=True`.
- Comments, status changes, dealdone, and creation can generate email notifications.
- Several order mutations call `OrderLimit.update_current()` when both site and cashflow are present.

## Failure Modes and Quirks

- Approved and cancelled orders reject most edits.
- Split, merge, and quantity operations rely on client-supplied JSON lists or IDs; invalid lists are rejected with flash messages.
- Vendor matching during some merge and split paths uses vendor names from product payloads, so bad product data can affect vendor linkage.
- Limit recalculation is conditional and may not run after every conceivable state change.

# Application Specification

This directory documents the current behavior of the Pushkind Approve application as implemented in the Flask codebase. The goal is to describe what the system does today, including role restrictions, side effects, and known quirks, not to propose a redesign.

## System Summary

Pushkind Approve is a hub-scoped procurement workflow application. Users create purchase orders from a product catalog, route them through validator and purchaser review, export approved orders, track budget limits, and manage reference data such as projects, sites, categories, and vendors.

## Primary Actors

- `admin`: full hub administration, reference data, users, vendors, orders, limits.
- `initiative`: creates and edits own orders, comments, cancels, duplicates, merges, splits.
- `validator`: approves or disapproves orders assigned by project and category.
- `purchaser`: participates in review, sends orders to vendors, marks contracts done.
- `supervisor`: read-oriented access to enabled-project orders and supporting pages.
- `vendor`: sees assigned vendor orders and vendor catalog management for own vendor only.
- `default`: registered but not yet granted operational access.

## Document Map

- [order-lifecycle.md](order-lifecycle.md): core order workflow, state changes, notifications, exports.
- [access-and-auth.md](access-and-auth.md): login, signup, password reset, token login, session behavior, permission model.
- [reference-data-and-admin.md](reference-data-and-admin.md): app settings, categories, projects, sites, budget statements.
- [catalog-and-vendors.md](catalog-and-vendors.md): vendor accounts, product catalog upload/download, image handling.
- [users-and-settings.md](users-and-settings.md): user profile editing, role assignment, dashboard links, exports.
- [limits-and-budgeting.md](limits-and-budgeting.md): order limits, current usage recalculation, over-limit flags, API refresh.
- [supporting-pages-and-integrations.md](supporting-pages-and-integrations.md): dashboard, history, help, support mail, email and 1C integration.

## Route Coverage

- `app/auth/routes.py`: authentication and recovery endpoints.
- `app/main/routes_index.py`: inbox, merge, export, support.
- `app/main/routes_approve.py`: single-order view and workflow actions.
- `app/main/routes_shop.py`: catalog browsing and cart-based order creation.
- `app/main/routes_admin.py`: reference data and app settings.
- `app/main/routes_products.py`: vendor catalog operations.
- `app/main/routes_settings.py`: user administration and personal settings.
- `app/main/routes_limits.py`: budget limits.
- `app/main/routes_stores.py`: vendor/store management.
- `app/main/routes_history.py`, `routes_dashboard.py`, `routes_help.py`: supporting views.
- `app/api/routes.py`: authenticated maintenance API.

## Core Data Areas

- Identity and access: `User`, `Position`, `UserCategory`, `UserProject`.
- Procurement: `Order`, `OrderApproval`, `OrderPosition`, `OrderEvent`, `OrderCategory`, `OrderVendor`.
- Reference data: `Vendor`, `Project`, `Site`, `Category`, `IncomeStatement`, `CashflowStatement`, `Product`, `AppSettings`.
- Budgeting: `OrderLimit`, `OrderLimitsIntervals`.

## Cross-Cutting Rules

- Most data is scoped by `hub_id`; admin operations are intended to stay within the current user hub.
- Order reviewers are derived from the initiative user plus project/category-matched validators and purchasers.
- Order status is driven by `OrderPosition` approvals and `OrderApproval` disapprovals.
- Many write actions create `OrderEvent` rows and may send email notifications.
- Limit recalculation is triggered opportunistically after key order and limit mutations rather than through a centralized domain service.

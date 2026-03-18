# Catalog and Vendors Specification

## Purpose

Vendor and catalog management covers supplier account creation plus the upload, download, and maintenance of vendor product catalogs used by the shopping flow.

## Stores / Vendors

Routes:

- `/stores/`
- `/stores/add/`
- `/stores/remove/<id>`
- `/stores/activate/<id>`

`admin` manages vendor records under the current hub. Creating a store creates both:

- a `Vendor` row for procurement linkage
- a `User` row with role `vendor`, matching email, and supplied password

Creation is blocked if the email is already used by any user. Removing a store deletes the vendor and its associated vendor admin if present. Activation toggles `Vendor.enabled`.

## Product Catalog Access

Routes:

- `/products/`, `/products/show`
- `/products/upload`
- `/products/upload/images`
- `/products/remove`
- `/products/download`
- `/products/<product_id>/upload/image`

Allowed roles are `admin`, `purchaser`, `validator`, and `vendor`. `initiative`, `supervisor`, and `default` are blocked. Vendors are restricted to the vendor whose email matches the logged-in user.

See `access-and-auth.md` for the shared permissions matrix.

## XLSX Catalog Upload

The product upload expects an `.xlsx` file with mandatory columns:

- `name`
- `sku`
- `price`
- `measurement`
- `category`
- `description`
- `input_required`

Extra columns become product option lists after normalization. Column names are lowercased and non-word characters are replaced with underscores. Category names are resolved case-insensitively against hub categories. Existing products for the same vendor and uploaded SKUs are deleted before bulk insert.

## Image Handling

- ZIP image upload extracts only files for known product SKUs and skips directories or entries larger than `MAX_ZIP_FILE_SIZE`.
- Images are stored under `app/static/upload/vendor<vendor_id>/`.
- Single-product image upload uses JPG or PNG and updates the product image path.
- Download exports current vendor products back to XLSX, flattening option arrays into comma-separated values.

## Shopping Dependency

Products provide the source catalog for `/shop/`. The order payload copies product name, SKU, price, measurement, category, vendor, optional free-text comment, and validated option selections into the order JSON snapshot, so later catalog changes do not retroactively rewrite existing orders.

#include <json.h>
#include <stdint.h>
#include <stdbool.h>
#include <math.h>

#include "rest.h"
#include "model.h"
#include "http.h"
#include "util.h"
#include "dbg.h"

static const char *_ALLOWED_PRODUCTS_FIELDS[] = {"name", "price", "enabled", "options", "description", "imageUrl"};

static void ProcessCategoryProducts(TEcwid hub, TEcwid store, uint64_t hub_category, uint64_t store_category, struct json_object *hub_products);
static void ProcessCategories(TEcwid hub, TEcwid store, uint64_t hub_category, uint64_t store_category, struct json_object *hub_products);

static bool SetHubProductImage(TEcwid store, uint64_t product_id, char *img_url)
{
	uint8_t *response = NULL;
	bool result = false;
	struct json_object *json = NULL, *params = NULL;
	size_t response_len = 0;

	check(img_url != NULL, "Invalid function inputs");

	check(HTTPcall(HTTP_GET, img_url, NULL, 0, &response, &response_len) == 0, "Invalid HTTP response");

	params = json_object_new_object();
	check_mem(params);
	json_object_object_add(params, "token", json_object_new_string(store.token));
	json_object_object_add(params, "productId", json_object_new_int64(product_id));

	json = RESTcall(store.id, POST_IMAGE, params, response, response_len);
	check(json != NULL, "Cannot create hub product.");

	result = true;
error:
	if (params != NULL)
		json_object_put(params);
	if (json != NULL)
		json_object_put(json);
	if (response != NULL)
		free(response);
	return result;
}

static int64_t CreateCategory(TEcwid store, uint64_t parent_id, char *name)
{
	struct json_object *payload = NULL, *json = NULL, *tmp = NULL, *params = NULL;
	int64_t result = -1;

	check(name != NULL && strlen(name) > 0, "Invalid function inputs.");

	params = json_object_new_object();
	check_mem(params);
	json_object_object_add(params, "parent", json_object_new_int64(parent_id));
	json_object_object_add(params, "token", json_object_new_string(store.token));
	json_object_object_add(params, "hidden_categories", json_object_new_boolean(true));
	json = RESTcall(store.id, GET_CATEGORIES, params, NULL, 0);
	check_mem(json);
	json_object_object_get_ex(json, "items", &tmp);
	if (tmp != NULL && json_object_get_type(tmp) == json_type_array && json_object_array_length(tmp) > 0)
	{
		for (size_t i = 0; i < json_object_array_length(tmp); i++)
		{
			struct json_object *category_id = NULL, *category = json_object_array_get_idx(tmp, i);
			json_object_object_get_ex(category, "name", &category_id);
			if (category_id != NULL && strcmp(name, (char *)json_object_get_string(category_id)) == 0)
			{
				json_object_object_get_ex(category, "id", &category_id);
				if (category_id != NULL)
					result = (int64_t)json_object_get_int64(category_id);
				break;
			}
		}
	}
	if (result == -1)
	{

		payload = json_object_new_object();
		check_mem(payload);
		json_object_object_add(payload, "parentId", json_object_new_int64(parent_id));
		json_object_object_add(payload, "name", json_object_new_string(name));
		const char *buffer = json_object_to_json_string(payload);
		if (json != NULL)
			json_object_put(json);
		json = RESTcall(store.id, POST_CATEGORY, params, (uint8_t *)buffer, strlen(buffer));
		check_mem(json);
		struct json_object *category_id = NULL;
		json_object_object_get_ex(json, "id", &category_id);
		if (category_id != NULL)
			result = (int64_t)json_object_get_int64(category_id);
	}
error:
	if (params != NULL)
		json_object_put(params);
	if (payload != NULL)
		json_object_put(payload);
	if (json != NULL)
		json_object_put(json);
	return result;
}

static void ProcessCategories(TEcwid hub, TEcwid store, uint64_t hub_category, uint64_t store_category, struct json_object *hub_products)
{
	struct json_object *store_json = NULL, *params = NULL;
	struct json_object *store_categories = NULL;

	check(hub_products != NULL, "Invalid function inputs.");

	/*****************************************************************************/
	//	Get nested store categories for given parent category
	/*****************************************************************************/

	params = json_object_new_object();
	check_mem(params);

	json_object_object_add(params, "token", json_object_new_string(store.token));
	json_object_object_add(params, "parent", json_object_new_int64(store_category));
	store_json = RESTcall(store.id, GET_CATEGORIES, params, NULL, 0);
	check(store_json != NULL, "JSON is invalid.");
	json_object_object_get_ex(store_json, "items", &store_categories);
	check(store_categories != NULL && json_object_get_type(store_categories) == json_type_array, "JSON is invalid.");
	json_object_put(params);
	params = NULL;

	for (size_t i = 0; i < json_object_array_length(store_categories); i++)
	{
		struct json_object *category_id = NULL, *category_name = NULL, *category = json_object_array_get_idx(store_categories, i);

		if (category == NULL)
			continue;

		json_object_object_get_ex(category, "name", &category_name);
		json_object_object_get_ex(category, "id", &category_id);
		if (category_id == NULL || category_name == NULL)
			continue;
		int64_t next_store_category = (int64_t)json_object_get_int64(category_id);
		int64_t next_hub_category = CreateCategory(hub, hub_category, TrimWhiteSpaces((char *)json_object_get_string(category_name)));
		if (next_hub_category < 0)
		{
			log_err("Cannot create hub category.");
			continue;
		}
		ProcessCategoryProducts(hub, store, next_hub_category, next_store_category, hub_products);
	}

error:
	if (params != NULL)
		json_object_put(params);
	if (store_json != NULL)
		json_object_put(store_json);
}

static bool CreateHubProduct(TEcwid hub, struct json_object *product)
{
	bool result = false;
	struct json_object *params = NULL, *response = NULL;
	struct json_object *sku = NULL, *product_id = NULL, *image_url = NULL;

	check(product != NULL, "Invalid function inputs.");

	json_object_object_get_ex(product, "sku", &sku);

	check(sku != NULL, "Invalid function inputs.");

	/*****************************************************************************/
	//	Create non-existent product
	/*****************************************************************************/

	params = json_object_new_object();
	check_mem(params);
	json_object_object_add(params, "token", json_object_new_string(hub.token));

	const char *buffer = json_object_to_json_string(product);
	response = RESTcall(hub.id, POST_PRODUCT, params, (uint8_t *)buffer, strlen(buffer));
	check(response != NULL, "Cannot create hub product %s.", (char *)json_object_get_string(sku));

	json_object_object_get_ex(response, "id", &product_id);

	check(product_id != NULL, "Cannot create hub product %s.", (char *)json_object_get_string(sku));

	json_object_object_get_ex(product, "imageUrl", &image_url);
	if (image_url != NULL)
	{
		check(SetHubProductImage(hub, (int64_t)json_object_get_int64(product_id), (char *)json_object_get_string(image_url)) == true, "Setting product %s image failed", (char *)json_object_get_string(sku));
	}
	result = true;
error:
	if (response != NULL)
		json_object_put(response);
	if (params != NULL)
		json_object_put(params);
	return result;
}

static bool UpdateHubProduct(TEcwid hub, struct json_object *hub_product, struct json_object *store_product)
{

	bool result = false;
	struct json_object *params = NULL, *response = NULL;
	struct json_object *sku = NULL, *product_id = NULL;
	struct json_object *hub_image_url = NULL, *store_image_url = NULL;

	check(hub_product != NULL && store_product != NULL, "Invalid function inputs.");

	params = json_object_new_object();
	check_mem(params);
	json_object_object_add(params, "token", json_object_new_string(hub.token));

	/*****************************************************************************/
	//	Update existing product
	/*****************************************************************************/
	json_object_object_get_ex(hub_product, "id", &product_id);
	json_object_object_get_ex(hub_product, "imageURL", &hub_image_url);
	json_object_object_get_ex(store_product, "imageUrl", &store_image_url);
	json_object_object_get_ex(hub_product, "sku", &sku);

	check(product_id != NULL && sku != NULL, "Invalid function inputs.");

	if (hub_image_url == NULL && store_image_url != NULL)
	{
		if (SetHubProductImage(hub, (int64_t)json_object_get_int64(product_id), (char *)json_object_get_string(store_image_url)) != true)
		{
			log_err("Setting product %s image failed", (char *)json_object_get_string(sku));
		}
	}
	json_object_object_add(params, "productId", json_object_get(product_id));
	const char *buffer = json_object_to_json_string(store_product);
	response = RESTcall(hub.id, PUT_PRODUCT, params, (uint8_t *)buffer, strlen(buffer));
	check(response != NULL, "Cannot create hub product %s.", (char *)json_object_get_string(sku));
	json_object_object_add(hub_product, "processed", json_object_new_boolean(true));
	result = true;
error:
	if (response != NULL)
		json_object_put(response);
	if (params != NULL)
		json_object_put(params);
	return result;
}

static void ProcessCategoryProducts(TEcwid hub, TEcwid store, uint64_t hub_category, uint64_t store_category, struct json_object *hub_products)
{

	struct json_object *store_json = NULL, *params = NULL;
	struct json_object *store_products = NULL;
	char *hub_sku = NULL;
	uint64_t hub_vendor_category = 0;

	check(hub_products != NULL, "Invalid function inputs.");

	/*****************************************************************************/
	//	Get store's products for given category
	/*****************************************************************************/
	params = json_object_new_object();
	check_mem(params);
	json_object_object_add(params, "token", json_object_new_string(store.token));
	json_object_object_add(params, "category", json_object_new_int64(store_category));
	store_json = RESTcall(store.id, GET_PRODUCTS, params, NULL, 0);
	check(store_json != NULL, "JSON is invalid.");
	json_object_object_get_ex(store_json, "items", &store_products);
	check(store_products != NULL && json_object_get_type(store_products) == json_type_array, "JSON is invalid.");
	json_object_put(params);
	params = NULL;

	/*****************************************************************************/
	//	Create a vendor name category in the hub store
	/*****************************************************************************/

	if (json_object_array_length(store_products) > 0)
	{
		hub_vendor_category = CreateCategory(hub, hub_category, store.name);
		check(hub_vendor_category > 0, "Cannot create vendor category.");
	}

	/*****************************************************************************/
	//	Compare hub and store products
	/*****************************************************************************/

	for (size_t i = 0; i < json_object_array_length(store_products); i++)
	{

		struct json_object *store_product_sku = NULL, *store_product = json_object_array_get_idx(store_products, i);

		if (store_product == NULL)
			continue;

		json_object_object_get_ex(store_product, "sku", &store_product_sku);

		if (store_product_sku == NULL)
			continue;

		/*****************************************************************************/
		//	Prepare hub sku string ("store_id"-"store_sku")
		/*****************************************************************************/

		hub_sku = calloc(strlen((char *)json_object_get_string(store_product_sku)) + ceil(log10(store.id + 1)) + 2, 1);
		check_mem(hub_sku);
		sprintf(hub_sku, "%ld-%s", store.id, (char *)json_object_get_string(store_product_sku));

		/*****************************************************************************/
		//	Remove unnecessary product's fields
		/*****************************************************************************/

		FilterJSONFields(store_product, _ALLOWED_PRODUCTS_FIELDS, ARRAY_SIZE(_ALLOWED_PRODUCTS_FIELDS));

		struct json_object *tmp = json_object_new_array();
		json_object_array_add(tmp, json_object_new_int64(hub_vendor_category));
		json_object_object_add(store_product, "categoryIds", tmp);
		json_object_object_add(store_product, "defaultCategoryId", json_object_new_int64(hub_vendor_category));
		json_object_object_add(store_product, "sku", json_object_new_string(hub_sku));

		bool found = false;
		for (size_t j = 0; j < json_object_array_length(hub_products); j++)
		{

			struct json_object *hub_product_sku = NULL, *hub_product = json_object_array_get_idx(hub_products, j);

			if (hub_product == NULL)
				continue;

			json_object_object_get_ex(hub_product, "sku", &hub_product_sku);

			if (hub_product_sku == NULL)
				continue;

			if (strcmp((char *)json_object_get_string(hub_product_sku), hub_sku) == 0)
			{
				if (UpdateHubProduct(hub, hub_product, store_product) != true)
				{
					log_err("There was problems while updating %s", hub_sku);
				}
				found = true;
				break;
			}
		}
		if (found == false)
		{
			if (CreateHubProduct(hub, store_product) != true)
			{
				log_err("There was problems while creating %s", hub_sku);
			}
		}
		free(hub_sku);
		hub_sku = NULL;
	}

	/*****************************************************************************/
	//	Process nested categories
	/*****************************************************************************/

	ProcessCategories(hub, store, hub_category, store_category, hub_products);

error:
	if (store_json != NULL)
		json_object_put(store_json);
	if (params != NULL)
		json_object_put(params);
	if (hub_sku != NULL)
		free(hub_sku);
	return;
}

static bool ProcessStoreProducts(TEcwid hub, TEcwid store)
{
	bool result = false;
	struct json_object *json = NULL, *params = NULL;
	struct json_object *hub_products = NULL;
	char *search_sku = NULL;

	/*****************************************************************************/
	//	Get the hub products, which sku is related to the current store's id
	/*****************************************************************************/
	search_sku = calloc(ceil(log10(store.id + 1)) + 3, 1);
	check_mem(search_sku);
	sprintf(search_sku, "%ld-", store.id);

	params = json_object_new_object();
	check_mem(params);
	json_object_object_add(params, "token", json_object_new_string(hub.token));
	json_object_object_add(params, "keyword", json_object_new_string(search_sku));
	json = RESTcall(hub.id, GET_PRODUCTS, params, NULL, 0);
	check(json != NULL, "JSON is invalid.");
	json_object_object_get_ex(json, "items", &hub_products);
	check(hub_products != NULL && json_object_get_type(hub_products) == json_type_array, "JSON is invalid.");
	json_object_object_del(params, "keyword");

	/*****************************************************************************/
	//	Process store category products
	/*****************************************************************************/
	//ProcessCategoryProducts(hub, store, 0, 0, hub_products, vendor);
	ProcessCategories(hub, store, 0, 0, hub_products);

	/*****************************************************************************/
	//	Remove excess hub products
	/*****************************************************************************/
	for (size_t j = 0; j < json_object_array_length(hub_products); j++)
	{

		struct json_object *hub_product_processed = NULL, *hub_product = json_object_array_get_idx(hub_products, j);
		struct json_object *hub_product_id = NULL;

		if (hub_product == NULL)
			continue;

		json_object_object_get_ex(hub_product, "processed", &hub_product_processed);
		json_object_object_get_ex(hub_product, "id", &hub_product_id);
		if (hub_product_id == NULL)
			continue;
		if (hub_product_processed == NULL)
		{
			json_object_object_add(params, "productId", json_object_get(hub_product_id));
			struct json_object *tmp = NULL;
			tmp = RESTcall(hub.id, DELETE_PRODUCT, params, NULL, 0);
			if (tmp != NULL)
			{
				json_object_put(tmp);
				tmp = NULL;
			}
			else
			{
				log_err("Removing product %ld failed", (int64_t)json_object_get_int64(hub_product_id));
			}
			json_object_object_del(params, "productId");
		}
	}

	result = true;
error:
	if (json != NULL)
		json_object_put(json);
	if (params != NULL)
		json_object_put(params);
	if (search_sku != NULL)
		free(search_sku);
	return result;
}

bool ProcessProducts(uint64_t hub_id, uint64_t store_id)
{

	bool result = false;
	TDatabase *pDB = NULL;
	TEcwid *hub = NULL;
	TEcwid *stores = NULL;
	size_t stores_count = 0;
	size_t hub_count = 0;

	/*****************************************************************************/
	//	Open database, get hub and stores
	/*****************************************************************************/

	check(OpenDatabaseConnection(&pDB) == true, "Error while opening DB.");
	hub = GetStores(pDB, 0, &hub_count, hub_id);
	check(hub != NULL && hub_count == 1, "There is no such ecwid settings.");
	check(hub[0].token != NULL, "Hub token is NULL.");

	stores = GetStores(pDB, hub_id, &stores_count, store_id);
	check(stores != NULL && stores_count > 0, "There are no registered stores.");

	/*****************************************************************************/
	//	Process stores' products
	/*****************************************************************************/
	for (size_t i = 0; i < stores_count; i++)
	{
		if (stores[i].token == NULL || stores[i].name == NULL)
		{
			log_err("Token is NULL or name is NULL for store %lu.", stores[i].id);
			continue;
		}
		if (ProcessStoreProducts(hub[0], stores[i]) != true)
		{
			log_err("Failed to process store %lu", stores[i].id);
		}
	}
	result = true;
error:
	/*****************************************************************************/
	//	Clean everything up
	/*****************************************************************************/
	if (stores != NULL)
		FreeStores(stores, stores_count);
	if (hub != NULL)
		FreeStores(hub, hub_count);
	if (pDB != NULL)
		CloseDatabaseConnection(pDB);
	return result;
}

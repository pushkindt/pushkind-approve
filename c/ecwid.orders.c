#include <json.h>

#include "rest.h"
#include "model.h"
#include "http.h"
#include "util.h"

static const char *_ALLOWED_PRODUCTS_FIELDS[] = {"id", "categoryId", "price", "sku", "quantity", "name", "imageUrl", "selectedOptions"};	

#define ARRAY_SIZE(arr)     (sizeof(arr) / sizeof((arr)[0]))

static void FilterProductFields(struct json_object *product){
	if (product == NULL)
		return;
	
	/*****************************************************************************/
	//	Loop through products and remove excessive product fields.
	/*****************************************************************************/
	
	{
		json_object_object_foreach(product, key, val){
			
			bool found = false;
			for (size_t i = 0; i < ARRAY_SIZE(_ALLOWED_PRODUCTS_FIELDS); i++){
				if (strcmp(key, _ALLOWED_PRODUCTS_FIELDS[i]) == 0){
					found = true;
					break;
				}
			}
			if (found == false)
				json_object_object_del(product, key);
		}
	}
}

static bool GetStoreOrders(TDatabase *pDB, TEcwid store, uint64_t start_from, char *order_id){
	
	bool result = false;
	struct json_object *json = NULL, *params = NULL, *tmp = NULL;
	
	check(pDB != NULL, "Invalid function inputs.");
	
	params = json_object_new_object();
	check_mem(params);
	json_object_object_add(params, "token", json_object_new_string(store.token));
	if (order_id != NULL)
		json_object_object_add(params, "ids", json_object_new_string(order_id));
	else if (start_from != 0)
		json_object_object_add(params, "createdFrom", json_object_new_int64(start_from));
	
	json = RESTcall(store.id, GET_ORDERS, params, NULL, 0);
	check_mem(json);
	json_object_object_get_ex(json, "items", &tmp);
	
	if (tmp != NULL && json_object_get_type(tmp) == json_type_array && json_object_array_length(tmp) > 0){
		
		for (size_t i = 0; i < json_object_array_length(tmp); i++){
			
			struct json_object *template = json_object_array_get_idx(tmp, i);
			
			if (template != NULL){

				TOrder order = {0};

				struct json_object * parsed_comment = NULL;

				struct json_object *id = NULL, *total = NULL, *create_timestamp = NULL, \
				*products = NULL, *comments = NULL, *email = NULL, \
				*external_fulfillment = NULL;

				json_object_object_get_ex(template,"id", &id);
				json_object_object_get_ex(template,"total", &total);
				json_object_object_get_ex(template,"createTimestamp", &create_timestamp);
				json_object_object_get_ex(template,"items", &products);
				json_object_object_get_ex(template,"orderComments", &comments);
				json_object_object_get_ex(template,"email", &email);
				json_object_object_get_ex(template,"externalFulfillment", &external_fulfillment);

				if (id == NULL || total == NULL || create_timestamp == NULL || products == NULL || email == NULL)
					continue;

				if (json_object_get_type(products) != json_type_array)
					continue;

				size_t products_count = json_object_array_length(products);
				if (products_count == 0)
					continue;

				order.initiative_id = GetInitiativeIdByEmail(pDB, store.id, (char *)json_object_get_string(email));
				if (order.initiative_id == 0)
					continue;

				order.id = (char *)json_object_get_string(id);
				if (order.id == NULL)
					continue;

				order.total = json_object_get_double(total);
				order.create_timestamp = json_object_get_int64(create_timestamp);
				
				if (external_fulfillment != NULL){
					order.purchased = json_object_get_boolean(external_fulfillment);
				}

				if (comments != NULL){
					parsed_comment = json_tokener_parse((char *)json_object_get_string(comments));
					if (parsed_comment != NULL){
						struct json_object *object = NULL, *income_statement = NULL, *cash_flow_statement = NULL;
						
						json_object_object_get_ex(parsed_comment,"object", &object);
						json_object_object_get_ex(parsed_comment,"budget", &income_statement);
						json_object_object_get_ex(parsed_comment,"cashflow", &cash_flow_statement);
						
						if (object != NULL)
							order.site_id = GetSiteIdByName(pDB, store.id, (char *)json_object_get_string(object));
						if (cash_flow_statement != NULL){
							order.cash_flow_statement = (char *)json_object_get_string(cash_flow_statement);
							if (strlen(order.cash_flow_statement) == 0)
								order.cash_flow_statement = NULL;
						}
						if (income_statement != NULL){
							order.income_statement = (char *)json_object_get_string(income_statement);
							if (strlen(order.income_statement) == 0)
								order.income_statement = NULL;
						}
					}
				}

				for (size_t j = 0; j < products_count; j++){
					struct json_object *product = json_object_array_get_idx(products, j);
					FilterProductFields(product);
					struct json_object *sku = NULL;
					json_object_object_get_ex(product,"sku", &sku);
					if (sku != NULL){
						char *sku_value = (char *)json_object_get_string(sku);
						
						if (sku_value != NULL){
							char *dash = strchr(sku_value, '-');
							if (dash != NULL){
								*dash = '\0';
								char *vendor = GetStoreNameById(pDB, sku_value);
								if (vendor != NULL){
									json_object_object_add(product, "vendor", json_object_new_string(vendor));
									free(vendor);
								}
								*dash = '-';
							}
						}
					}
					
				}
				
				order.hub_id = store.id;
				
				for (size_t j = 0; j < products_count; j++){
					struct json_object *product = json_object_array_get_idx(products, j);
					
					if (product == NULL)
						continue;
					struct json_object *category_id = NULL;
					json_object_object_get_ex(product,"categoryId", &category_id);
					if (category_id != NULL){
						char *cat_name = NULL;
						uint64_t root_category = GetCategoryIdByChildId(pDB, store.id, json_object_get_int64(category_id), &cat_name);
						if (root_category != 0){
							if (StoreOrderCategory(pDB, order.id, root_category) != 0){
								log_err("Cannot save order category %s %lu.", order.id, root_category);
							}
							json_object_object_add(product, "categoryId", json_object_new_int64(root_category));
						}
						if (cat_name != NULL){
							json_object_object_add(product, "category", json_object_new_string(cat_name));
							free(cat_name);
						}
					}
				}
				
				order.products = (char *)json_object_to_json_string(products);
				if (StoreOrders(pDB, order) != 0)
					log_err("Cannot save order %s.", order.id);
					   
				if (parsed_comment != NULL)
					json_object_put(parsed_comment);
				
				if (UpdateOrderPositions(pDB, order.id) != 0)
					log_err("Cannot save order %s positions.", order.id);
				
			}
		}
	} 
	else {
		log_info("No orders have been found.");
	}
	result = true;
error:
	if (json != NULL)
		json_object_put(json);
	if (params != NULL)
		json_object_put(params);
	return result;
}

bool ProcessOrders(uint64_t hub_id, char *order_id){
	
	bool result = false;
	TDatabase *pDB = NULL;
	TEcwid *hub = NULL;
	size_t hub_count = 0;
	uint64_t start_from = 0;

	/*****************************************************************************/
	//	Open database, get hub
	/*****************************************************************************/

	check(OpenDatabaseConnection(&pDB) == true, "Error while opening DB.");
	hub = GetStores(pDB, 0, &hub_count, hub_id);
	check(hub != NULL && hub_count == 1, "There is no such ecwid settings.");
	
	/*****************************************************************************/
	//	if we don't need a particular order, get the date of the most recent one,
	//	to query only new orders.
	/*****************************************************************************/
	
	if (order_id == NULL){
		start_from = GetRecentOrderTimestamp(pDB, hub_id);
		if (start_from > 0)
			start_from += 1;
	}
	
	/*****************************************************************************/
	//	Process orders and store them in the database.
	/*****************************************************************************/	
	
	check(GetStoreOrders(pDB, hub[0], start_from, order_id) == true, "Cannot process store orders.");	

	result = true;
error:
	/*****************************************************************************/
	//	Clean everything up
	/*****************************************************************************/
	if (hub != NULL)
		FreeStores(hub, hub_count);
	if (pDB != NULL)
		CloseDatabaseConnection(pDB);
	return result;	
}
#include <json.h>

#include "rest.h"
#include "model.h"
#include "http.h"
#include "util.h"


static bool ProcessCategoriesTree(TEcwid hub, uint64_t root_id, struct json_object *children){
	
	struct json_object *json = NULL, *params = NULL;
	struct json_object *categories = NULL;
	bool result = false;
	check(children != NULL && root_id != 0, "Invalid function inputs.");
	
	params = json_object_new_object();
	check_mem(params);
	json_object_object_add(params, "token", json_object_new_string(hub.token));
	json_object_object_add(params, "parent", json_object_new_int64(root_id));
	json_object_object_add(params, "hidden_categories", json_object_new_boolean(true));	
	json = RESTcall(hub.id, GET_CATEGORIES, params, NULL, 0);
	check(json != NULL, "JSON is invalid.");
	json_object_object_get_ex(json, "items", &categories);
	check(categories != NULL && json_object_get_type(categories) == json_type_array, "JSON is invalid.");
	
	for (size_t i = 0; i < json_object_array_length(categories); i++) {
		struct json_object *category = json_object_array_get_idx(categories, i);
		struct json_object *cat_id = NULL;
		check_mem(category);
		json_object_object_get_ex(category, "id", &cat_id);
		check_mem(cat_id);
		json_object_array_add(children, json_object_get(cat_id));
		check(ProcessCategoriesTree(hub, (int64_t)json_object_get_int64(cat_id), children) == true, "Error while processing categories tree.");
	}
	result = true;
error:
	if (json != NULL)
		json_object_put(json);
	if (params != NULL)
		json_object_put(params);
	return result;
}


bool ProcessCategories(uint64_t hub_id){
	
	bool result = false;

	TDatabase *pDB = NULL;
	TEcwid *hub = NULL;
	struct json_object *json = NULL, *params = NULL;
	struct json_object *categories = NULL;
	struct json_object *children = NULL;
	TCategory *cache = NULL;
	size_t hub_count = 0;

	check(OpenDatabaseConnection(&pDB) == true, "Error while opening DB.");
	hub = GetStores(pDB, 0, &hub_count, hub_id);
	check(hub != NULL && hub_count == 1, "There is no such ecwid settings.");


	/*****************************************************************************/
	//	Starting database transaction
	/*****************************************************************************/

	check(BeginTransaction(pDB) == 0, "Failed to start database transaction.");	

	/*****************************************************************************/
	//	Delete obsolete cache
	/*****************************************************************************/

	check(DeleteCategories(pDB, hub_id) == 0, "Error while deleting cache.");
	
	/*****************************************************************************/
	//	Get root categories
	/*****************************************************************************/
	
	params = json_object_new_object();
	check_mem(params);
	json_object_object_add(params, "token", json_object_new_string(hub[0].token));
	json_object_object_add(params, "parent", json_object_new_int64(0));	
	json_object_object_add(params, "hidden_categories", json_object_new_boolean(true));
	json = RESTcall(hub[0].id, GET_CATEGORIES, params, NULL, 0);
	check(json != NULL, "JSON is invalid.");
	json_object_object_get_ex(json, "items", &categories);
	check(categories != NULL && json_object_get_type(categories) == json_type_array, "JSON is invalid.");
	
	/*****************************************************************************/
	//	Process categories tree
	/*****************************************************************************/
	
	for (size_t i = 0; i < json_object_array_length(categories); i++) {
		struct json_object *category = json_object_array_get_idx(categories, i);
		struct json_object *cat_id = NULL, *cat_name = NULL;
		children = json_object_new_array();
		check_mem(children);
		check_mem(category);
		json_object_object_get_ex(category,"id", &cat_id);
		check_mem(cat_id);
		json_object_object_get_ex(category,"name", &cat_name);
		check_mem(cat_name);
		cache = calloc(sizeof(TCategory), 1);
		check_mem(cache);
		cache->name = strdup((char *)json_object_get_string(cat_name));
		cache->hub_id = hub_id;
		cache->id = (int64_t)json_object_get_int64(cat_id);
		
		json_object_array_add(children, json_object_get(cat_id));
		ProcessCategoriesTree(hub[0], (int64_t)json_object_get_int64(cat_id), children);		
		
		cache->children = strdup((char *)json_object_to_json_string(children));
		check(StoreCategories(pDB, cache) == 0, "Error while saving cache.");
		
		json_object_put(children);
		children = NULL;
		FreeCategories(cache);
		cache = NULL;
	}
	
	check(CleanCategoriesRelationships(pDB) == 0, "Error while cleaning categories relationships.");
	
	/*****************************************************************************/
	//	Commiting database transaction
	/*****************************************************************************/

	CommitTransaction(pDB);	
	
	result = true;
error:

	/*****************************************************************************/
	//	Rolling back database transaction
	/*****************************************************************************/
	if (result != true)
		RollbackTransaction(pDB);	

	/*****************************************************************************/
	//	Clean everything up
	/*****************************************************************************/
	if (children != NULL)
		json_object_put(children);
	if (cache != NULL)
		FreeCategories(cache);
	if (json != NULL)
		json_object_put(json);
	if (params != NULL)
		json_object_put(params);
	if (hub != NULL)
		FreeStores(hub, hub_count);
	if (pDB != NULL)
		CloseDatabaseConnection(pDB);
	return result;
}
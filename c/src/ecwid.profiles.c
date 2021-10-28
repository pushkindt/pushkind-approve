#include <json.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>

#include "rest.h"
#include "model.h"
#include "http.h"
#include "util.h"
#include "dbg.h"

/*
 * Function:  GetStoreProfile 
 * --------------------
 * retrieves a store's profile from ECWID
 *
 *  store: a pointer to a TEcwid structure, which should have id and token filled.
 *
 *  returns: a boolean to indicate the status of the query
 */
static bool GetStoreProfile(TEcwid *store)
{

	bool result = false;
	struct json_object *json = NULL, *params = NULL;

	/*****************************************************************************/
	//	Prepare REST query parameters JSON
	/*****************************************************************************/
	params = json_object_new_object();
	check_mem(params);
	json_object_object_add(params, "token", json_object_new_string(store->token));

	/*****************************************************************************/
	//	Make a REST query to Ecwid to retrieve the store's profile
	/*****************************************************************************/
	json = RESTcall(store->id, GET_PROFILE, params, NULL, 0);
	check(json != NULL, "Cannot retrieve store profile.");

	/*****************************************************************************/
	//	Get the "account" section from the profile JSON
	/*****************************************************************************/
	struct json_object *settings = NULL, *tmp = NULL;
	json_object_object_get_ex(json, "account", &settings);
	check(settings != NULL, "Cannot retrieve store profile");

	/*****************************************************************************/
	//	Get the "accountEmail" key from the "account" section
	/*****************************************************************************/
	json_object_object_get_ex(settings, "accountEmail", &tmp);
	check(tmp != NULL, "Cannot retrieve store email");
	if (store->email != NULL)
		free(store->email);
	store->email = strdup(TrimWhiteSpaces((char *)json_object_get_string(tmp)));
	check(store->email != NULL, "Cannot retrieve store email");

	/*****************************************************************************/
	//	Get the "settings" section from the profile JSON
	/*****************************************************************************/
	json_object_object_get_ex(json, "settings", &settings);
	check(settings != NULL, "Cannot retrieve store profile");

	/*****************************************************************************/
	//	Get the "storeName" key from the "settings" section
	/*****************************************************************************/
	json_object_object_get_ex(settings, "storeName", &tmp);
	check(tmp != NULL, "Cannot retrieve store name");
	if (store->name != NULL)
		free(store->name);
	store->name = strdup(TrimWhiteSpaces((char *)json_object_get_string(tmp)));
	check(store->name != NULL, "Cannot retrieve store name");

	/*****************************************************************************/
	//	Get the "generalInfo" section from the profile JSON
	/*****************************************************************************/
	json_object_object_get_ex(json, "generalInfo", &settings);
	check(settings != NULL, "Cannot retrieve store profile");

	/*****************************************************************************/
	//	Get the "storeUrl" key from the "generalInfo" section
	/*****************************************************************************/
	json_object_object_get_ex(settings, "storeUrl", &tmp);
	check(tmp != NULL, "Cannot retrieve store url");
	if (store->url != NULL)
		free(store->url);
	store->url = strdup(TrimWhiteSpaces((char *)json_object_get_string(tmp)));
	check(store->name != NULL, "Cannot retrieve store url");

	result = true;

error:
	/*****************************************************************************/
	//	Clean everything up
	/*****************************************************************************/
	if (params != NULL)
		json_object_put(params);
	if (json != NULL)
		json_object_put(json);

	return result;
}

/*
 * Function:  ProcessProfiles 
 * --------------------
 * updates local stores' profile information from Ecwid
 *
 *  hub_id: id of the hub store
 *  store_id: id of a particular store you want to update or zero to update all stores
 *
 *  returns: a boolean to indicate the status of the processing
 */
bool ProcessProfiles(uint64_t hub_id, uint64_t store_id)
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

	stores = GetStores(pDB, hub_id, &stores_count, store_id);
	check(stores != NULL && stores_count > 0, "There are no registered stores.");

	/*****************************************************************************/
	//	Get store profile information from Ecwid and store it locally
	/*****************************************************************************/
	for (size_t i = 0; i < stores_count; i++)
	{
		if ((GetStoreProfile(&stores[i]) != true) || (UpdateEcwidProfile(pDB, stores[i]) != 0))
		{
			log_err("Cannot process store %lu", stores[i].id);
			continue;
		}
	}

	/*****************************************************************************/
	//	Get hub profile information from Ecwid and store it locally
	/*****************************************************************************/
	if ((GetStoreProfile(&hub[0]) != true) || (UpdateEcwidProfile(pDB, hub[0]) != 0))
	{
		log_err("Cannot process hub %lu", hub[0].id);
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
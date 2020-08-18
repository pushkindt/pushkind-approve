#include "model.h"

void FreeHub(TEcwid *hub){
	if (hub == NULL)
		return;
	if (hub->token != NULL)
		free(hub->token);
	if (hub->client_id != NULL)
		free(hub->client_id);
	if (hub->client_secret != NULL)
		free(hub->client_secret);
	if (hub->partners_key != NULL)
		free(hub->partners_key);
	free(hub);
}

void FreeStores(TEcwid *stores, size_t stores_count){
	if (stores == NULL)
		return;
	for(size_t i = 0; i < stores_count; i++){
		if (stores[i].token != NULL)
			free(stores[i].token);
		if (stores[i].client_id != NULL)
			free(stores[i].client_id);
		if (stores[i].client_secret != NULL)
			free(stores[i].client_secret);
		if (stores[i].partners_key != NULL)
			free(stores[i].partners_key);
	}
	free(stores);
}

TEcwid *GetHub(sqlite3 *pDB, uint64_t ecwid_id){
	
	int result = -1;
	sqlite3_stmt *stmt = NULL;
	TEcwid *hub = NULL;
	check(pDB != NULL, "Invalid function inputs.");
	result = sqlite3_prepare_v2(pDB, "select partners_key,client_id,client_secret,token,store_id from ecwid where id = ? limit 1", -1, &stmt, NULL);
	check(result == SQLITE_OK, "Error while preparing SQLite statement.");
	result = sqlite3_bind_int64(stmt, 1, ecwid_id);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");	
	result = sqlite3_step(stmt);
	check(result == SQLITE_ROW, "No data available.");
	hub = calloc(sizeof(TEcwid), 1);
	hub->partners_key = strdup((const char *)sqlite3_column_text(stmt, 0));
	hub->client_id = strdup((const char *)sqlite3_column_text(stmt, 1));
	hub->client_secret = strdup((const char *)sqlite3_column_text(stmt, 2));
	hub->token = strdup((const char *)sqlite3_column_text(stmt, 3));
	hub->id = sqlite3_column_int64(stmt, 4);
	check_mem(hub);
	result = 0;
error:
	sqlite3_finalize(stmt);
	if (result != 0){
		if (hub != NULL){
			FreeHub(hub);
			hub = NULL;
		}
	}
	return hub;
}

TEcwid *GetStores(sqlite3 *pDB, uint64_t ecwid_id, size_t *stores_count){
	
	int result = -1;
	sqlite3_stmt *stmt = NULL;
	TEcwid *stores = NULL;
	check(pDB != NULL && stores_count != NULL, "Invalid function inputs.");
	result = sqlite3_prepare_v2(pDB, "select partners_key,client_id,client_secret,token,store_id from ecwid where ecwid_id = ?", -1, &stmt, NULL);
	check(result == SQLITE_OK, "Error while preparing SQLite statement.");
	result = sqlite3_bind_int64(stmt, 1, ecwid_id);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	while (sqlite3_step(stmt) == SQLITE_ROW){
		if (stores == NULL){
			stores = calloc(sizeof(TEcwid), 1);
			check_mem(stores);
			*stores_count = 1;
		}else{
			stores = realloc(stores, (*stores_count + 1) * sizeof(TEcwid));
			check_mem(stores);
			*stores_count += 1;
		}
		stores[*stores_count - 1].partners_key = strdup((const char *)sqlite3_column_text(stmt, 0));
		stores[*stores_count - 1].client_id = strdup((const char *)sqlite3_column_text(stmt, 1));
		stores[*stores_count - 1].client_secret = strdup((const char *)sqlite3_column_text(stmt, 2));
		stores[*stores_count - 1].token = strdup((const char *)sqlite3_column_text(stmt, 3));
		stores[*stores_count - 1].id = sqlite3_column_int64(stmt, 4);
	}
	result = 0;
error:
	sqlite3_finalize(stmt);
	if (result != 0){
		if (stores != NULL){
			FreeStores(stores, *stores_count);
			stores = NULL;
		}
	}
	return stores;
}
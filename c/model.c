#include "model.h"


bool OpenDatabaseConnection(TDatabase **pDB){
	
	bool result = false;
	check(pDB != NULL, "Invalid function inputs.")
	check(sqlite3_open_v2(DATABASE_URL, pDB, SQLITE_OPEN_READWRITE | SQLITE_OPEN_WAL, NULL) == SQLITE_OK, "Error while opening DB.");
	result = true;
error:
	return result;
}
	
bool CloseDatabaseConnection(TDatabase *pDB){
	
	bool result = false;
	check(pDB != NULL, "Invalid function inputs.");
	check(sqlite3_close_v2(pDB) == SQLITE_OK, "Error while closing DB.");
	result = true;
error:
	return result;
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
		if (stores[i].name != NULL)
			free(stores[i].name);
		if (stores[i].email != NULL)
			free(stores[i].email);
		if (stores[i].url != NULL)
			free(stores[i].url);
	}
	free(stores);
}

void FreeCategories(TCategory *cache){
	if (cache == NULL)
		return;
	if (cache->name != NULL)
		free(cache->name);
	if (cache->children != NULL)
		free(cache->children);
	free(cache);
}

int BeginTransaction(TDatabase *pDB){
	int result = -1;
	result = sqlite3_exec(pDB, "BEGIN", 0, 0, 0);
	check(result == SQLITE_OK, "Failed to start transaction.");
	result = 0;
error:
	return result;
}

int CommitTransaction(TDatabase *pDB){
	int result = -1;
	result = sqlite3_exec(pDB, "COMMIT", 0, 0, 0);
	check(result == SQLITE_OK, "Failed to commit transaction.");
	result = 0;
error:
	return result;
}

int RollbackTransaction(TDatabase *pDB){
	int result = -1;
	result = sqlite3_exec(pDB, "ROLLBACK", 0, 0, 0);
	check(result == SQLITE_OK, "Failed to rollback transaction.");
	result = 0;
error:
	return result;
}


int DeleteCategories(TDatabase *pDB, uint64_t hub_id){
	int result = -1;
	sqlite3_stmt *stmt = NULL;
	check(pDB != NULL, "Invalid function inputs.");
	
	/*****************************************************************************/
	//	Prepare SQL query
	/*****************************************************************************/	
	result = sqlite3_prepare_v2(pDB, "delete from `category` where `hub_id` = ?", -1, &stmt, NULL);
	check(result == SQLITE_OK, "Error while preparing SQLite statement.");
	result = sqlite3_bind_int64(stmt, 1, hub_id);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");	
	result = sqlite3_step(stmt);
	check(result == SQLITE_DONE, "Error while deleting cache.");
	result = 0;
error:
	if (stmt != NULL)
		sqlite3_finalize(stmt);
	return result;
}

int StoreCategories(TDatabase *pDB, TCategory *cache){
	int result = -1;
	sqlite3_stmt *stmt = NULL;
	check(pDB != NULL && cache != NULL, "Invalid function inputs.");
	
	/*****************************************************************************/
	//	Prepare SQL query
	/*****************************************************************************/	
	result = sqlite3_prepare_v2(pDB, "insert into `category`(`id`, `name`, `children`, `hub_id`) values (?,?,?,?)", -1, &stmt, NULL);
	check(result == SQLITE_OK, "Error while preparing SQLite statement.");
	result = sqlite3_bind_int64(stmt, 1, cache->id);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	result = sqlite3_bind_text(stmt, 2, cache->name, -1, SQLITE_STATIC);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	result = sqlite3_bind_text(stmt, 3, cache->children, -1, SQLITE_STATIC);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	result = sqlite3_bind_int64(stmt, 4, cache->hub_id);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	result = sqlite3_step(stmt);
	check(result == SQLITE_DONE, "Error while saving cache. %d", result);
	result = 0;
error:
	if (stmt != NULL)
		sqlite3_finalize(stmt);
	return result;
}

TEcwid *GetStores(TDatabase *pDB, uint64_t hub_id, size_t *stores_count, uint64_t store_id){
	
	int result = -1;
	sqlite3_stmt *stmt = NULL;
	TEcwid *stores = NULL;
	check(pDB != NULL && stores_count != NULL, "Invalid function inputs.");
	
	/*****************************************************************************/
	//	Prepare SQL query
	/*****************************************************************************/
	const char *sql = NULL;
	if (hub_id != 0){
		if (store_id == 0)
			sql = "select `id`,`token`,`name` from `ecwid` where `hub_id` = ?";
		else
			sql = "select `id`,`token`,`name` from `ecwid` where `hub_id` = ? and `id` = ?";
	}
	else
		sql = "select `id`, `token` from `ecwid` where `id` = ?";
	result = sqlite3_prepare_v2(pDB, sql, -1, &stmt, NULL);
	check(result == SQLITE_OK, "Error while preparing SQLite statement.");
	if (hub_id == 0){
		result = sqlite3_bind_int64(stmt, 1, store_id);
		check(result == SQLITE_OK, "Error while binding SQLite statement.");
	}
	else{
		result = sqlite3_bind_int64(stmt, 1, hub_id);
		check(result == SQLITE_OK, "Error while binding SQLite statement.");
		if (store_id != 0){
			result = sqlite3_bind_int64(stmt, 2, store_id);
			check(result == SQLITE_OK, "Error while binding SQLite statement.");
		}
	}
	/*****************************************************************************/
	//	Get SQL query result
	/*****************************************************************************/	
	while (sqlite3_step(stmt) == SQLITE_ROW){
		if (stores == NULL){
			stores = calloc(sizeof(TEcwid), 1);
			check_mem(stores);
			*stores_count = 1;
		}else{
			stores = realloc(stores, (*stores_count + 1) * sizeof(TEcwid));
			check_mem(stores);
			*stores_count += 1;
			memset(&stores[*stores_count - 1], 0, sizeof(TEcwid));
		}

		stores[*stores_count - 1].id = sqlite3_column_int64(stmt, 0);
		const char *value = (const char *)sqlite3_column_text(stmt, 1);
		if (value != NULL)
			stores[*stores_count - 1].token = strdup(value);
		value = (const char *)sqlite3_column_text(stmt, 2);
		if (value != NULL)
			stores[*stores_count - 1].name = strdup(value);
	}
	result = 0;
	
error:
	/*****************************************************************************/
	//	Clean everything up
	/*****************************************************************************/
	if (stmt != NULL)
		sqlite3_finalize(stmt);
	if (result != 0){
		if (stores != NULL){
			FreeStores(stores, *stores_count);
			stores = NULL;
		}
	}
	return stores;
}

int StoreEcwidProfile(TDatabase *pDB, TEcwid store){
	int result = -1;
	sqlite3_stmt *stmt = NULL;
	check(pDB != NULL, "Invalid function inputs.");
	
	/*****************************************************************************/
	//	Prepare SQL query
	/*****************************************************************************/	
	result = sqlite3_prepare_v2(pDB, "update `ecwid` set `email` = ?, `name` = ?, `url` = ? where `id` = ?", -1, &stmt, NULL);
	check(result == SQLITE_OK, "Error while preparing SQLite statement.");
	result = sqlite3_bind_text(stmt, 1, store.email, -1, SQLITE_STATIC);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	result = sqlite3_bind_text(stmt, 2, store.name, -1, SQLITE_STATIC);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	result = sqlite3_bind_text(stmt, 3, store.url, -1, SQLITE_STATIC);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	result = sqlite3_bind_int64(stmt, 4, store.id);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	result = sqlite3_step(stmt);
	check(result == SQLITE_DONE, "Error while saving store profile.");
	result = 0;
error:
	if (stmt != NULL)
		sqlite3_finalize(stmt);
	return result;
}

uint64_t GetRecentOrderTimestamp(TDatabase *pDB, uint64_t hub_id){
	
	uint64_t timestamp = 0;
	int result = -1;
	sqlite3_stmt *stmt = NULL;
	check(pDB != NULL, "Invalid function inputs.");
	
	
	/*****************************************************************************/
	//	Prepare SQL query
	/*****************************************************************************/
	result = sqlite3_prepare_v2(pDB, "select `create_timestamp` from `order` where `hub_id` = ? order by `create_timestamp` desc limit 1", -1, &stmt, NULL);
	check(result == SQLITE_OK, "Error while preparing SQLite statement.");
	result = sqlite3_bind_int64(stmt, 1, hub_id);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	result = sqlite3_step(stmt);
	if (result == SQLITE_ROW){
		timestamp = (uint64_t) sqlite3_column_int64(stmt, 0);
	}
error:
	if (stmt != NULL)
		sqlite3_finalize(stmt);
	return timestamp;
}

int StoreOrders(TDatabase *pDB, TOrder order){
	int result = -1;
	sqlite3_stmt *stmt = NULL;
	check(pDB != NULL && order.id != NULL, "Invalid function inputs.");
	
	result = sqlite3_prepare_v2(pDB, "insert or replace into `order`(`id`, `initiative_id`, `create_timestamp`, \
	`products`, `total`, `hub_id`, `purchased`) values (?,?,?,?,?,?,?)", -1, &stmt, NULL);
	check(result == SQLITE_OK, "Error while preparing SQLite statement. %d", result);
	result = sqlite3_bind_text(stmt, 1, order.id, -1, SQLITE_STATIC);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	result = sqlite3_bind_int64(stmt, 2, order.initiative_id);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	result = sqlite3_bind_int64(stmt, 3, order.create_timestamp);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	result = sqlite3_bind_text(stmt, 4, order.products, -1, SQLITE_STATIC);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	result = sqlite3_bind_double(stmt, 5, order.total);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	result = sqlite3_bind_int64(stmt, 6, order.hub_id);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	result = sqlite3_bind_int(stmt, 7, order.purchased);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	result = sqlite3_step(stmt);
	check(result == SQLITE_DONE, "Error while saving order %s.", order.id);
	
	sqlite3_finalize(stmt);
	stmt = NULL;
	
	if (order.cash_flow_statement != NULL){
		
		result = sqlite3_prepare_v2(pDB, "update `order` set `cash_flow_statement` = ? where `order`.`id` = ? and `hub_id` = ?", -1, &stmt, NULL);
		check(result == SQLITE_OK, "Error while preparing SQLite statement. %d", result);
		result = sqlite3_bind_text(stmt, 1, order.cash_flow_statement, -1, SQLITE_STATIC);
		check(result == SQLITE_OK, "Error while binding SQLite statement.");
		result = sqlite3_bind_text(stmt, 2, order.id, -1, SQLITE_STATIC);
		check(result == SQLITE_OK, "Error while binding SQLite statement.");
		result = sqlite3_bind_int64(stmt, 3, order.hub_id);
		check(result == SQLITE_OK, "Error while binding SQLite statement.");
		result = sqlite3_step(stmt);
		check(result == SQLITE_DONE, "Error while saving order %s.", order.id);
		sqlite3_finalize(stmt);
		stmt = NULL;
	}	
	
	if (order.income_statement != NULL){
		result = sqlite3_prepare_v2(pDB, "update `order` set `income_statement` = ? where `order`.`id` = ? and `hub_id` = ?", -1, &stmt, NULL);
		check(result == SQLITE_OK, "Error while preparing SQLite statement. %d", result);
		result = sqlite3_bind_text(stmt, 1, order.income_statement, -1, SQLITE_STATIC);
		check(result == SQLITE_OK, "Error while binding SQLite statement.");
		result = sqlite3_bind_text(stmt, 2, order.id, -1, SQLITE_STATIC);
		check(result == SQLITE_OK, "Error while binding SQLite statement.");
		result = sqlite3_bind_int64(stmt, 3, order.hub_id);
		check(result == SQLITE_OK, "Error while binding SQLite statement.");
		result = sqlite3_step(stmt);
		check(result == SQLITE_DONE, "Error while saving order %s.", order.id);
		sqlite3_finalize(stmt);
		stmt = NULL;
	}
	
	if (order.site_id != 0){
		result = sqlite3_prepare_v2(pDB, "update `order` set `site_id` = ? where `order`.`id` = ? and `hub_id` = ?", -1, &stmt, NULL);
		check(result == SQLITE_OK, "Error while preparing SQLite statement. %d", result);
		result = sqlite3_bind_int64(stmt, 1, order.site_id);
		check(result == SQLITE_OK, "Error while binding SQLite statement.");
		result = sqlite3_bind_text(stmt, 2, order.id, -1, SQLITE_STATIC);
		check(result == SQLITE_OK, "Error while binding SQLite statement.");
		result = sqlite3_bind_int64(stmt, 3, order.hub_id);
		check(result == SQLITE_OK, "Error while binding SQLite statement.");
		result = sqlite3_step(stmt);
		check(result == SQLITE_DONE, "Error while saving order %s.", order.id);
		sqlite3_finalize(stmt);
		stmt = NULL;
	}
	
	result = 0;
error:
	if (stmt != NULL)
		sqlite3_finalize(stmt);
	return result;
}

uint64_t GetCategoryIdByChildId(TDatabase *pDB, uint64_t hub_id, uint64_t cat_id, char **cat_name){
	
	uint64_t root_id = 0;
	int result = -1;
	sqlite3_stmt *stmt = NULL;
	check(pDB != NULL, "Invalid function inputs.");
	
	
	/*****************************************************************************/
	//	Prepare SQL query
	/*****************************************************************************/
	result = sqlite3_prepare_v2(pDB, "SELECT `category`.`id`, `category`.`name` FROM `category`, json_each(`category`.`children`) WHERE json_each.value = ? and `hub_id` = ? LIMIT 1", -1, &stmt, NULL);
	check(result == SQLITE_OK, "Error while preparing SQLite statement.");
	result = sqlite3_bind_int64(stmt, 1, cat_id);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	result = sqlite3_bind_int64(stmt, 2, hub_id);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	result = sqlite3_step(stmt);
	if (result == SQLITE_ROW){
		root_id = (uint64_t) sqlite3_column_int64(stmt, 0);
		if (cat_name != NULL){
			*cat_name = (char *)sqlite3_column_text(stmt, 1);
			if (*cat_name != NULL)
				*cat_name = strdup(*cat_name);
		}
	}
error:
	if (stmt != NULL)
		sqlite3_finalize(stmt);
	return root_id;
}

char *GetStoreNameById(TDatabase *pDB, char *store_id){
	int result = -1;
	char *store_name = NULL;
	sqlite3_stmt *stmt = NULL;
	
	check(pDB != NULL, "Invalid function inputs.");
	result = sqlite3_prepare_v2(pDB, "SELECT `name` FROM `ecwid` WHERE `id` = ? LIMIT 1", -1, &stmt, NULL);
	check(result == SQLITE_OK, "Error while preparing SQLite statement.");
	result = sqlite3_bind_text(stmt, 1, store_id, -1, SQLITE_STATIC);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");	
	result = sqlite3_step(stmt);
	if (result == SQLITE_ROW){
		const char *value = (const char *)sqlite3_column_text(stmt, 0);
		if (value != NULL)
			store_name = strdup(value);
	}
error:
	if (stmt != NULL)
		sqlite3_finalize(stmt);
	return store_name;
}

uint64_t GetInitiativeIdByEmail(TDatabase *pDB, uint64_t hub_id, char *email){
	
	uint64_t user_id = 0;
	int result = -1;
	sqlite3_stmt *stmt = NULL;
	check(pDB != NULL, "Invalid function inputs.");
	
	
	/*****************************************************************************/
	//	Prepare SQL query
	/*****************************************************************************/
	result = sqlite3_prepare_v2(pDB, "select `user`.`id` from `user` where `email` = lower(?) and `hub_id` = ? LIMIT 1", -1, &stmt, NULL);
	check(result == SQLITE_OK, "Error while preparing SQLite statement.");
	result = sqlite3_bind_text(stmt, 1, email, -1, SQLITE_STATIC);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	result = sqlite3_bind_int64(stmt, 2, hub_id);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	result = sqlite3_step(stmt);
	if (result == SQLITE_ROW){
		user_id = (uint64_t) sqlite3_column_int64(stmt, 0);
	}
error:
	if (stmt != NULL)
		sqlite3_finalize(stmt);
	return user_id;
}

uint64_t GetSiteIdByName(TDatabase *pDB, uint64_t hub_id, char *name){
	
	uint64_t site_id = 0;
	int result = -1;
	sqlite3_stmt *stmt = NULL;
	check(pDB != NULL, "Invalid function inputs.");
	
	
	/*****************************************************************************/
	//	Prepare SQL query
	/*****************************************************************************/
	result = sqlite3_prepare_v2(pDB, "select `site`.`id` from `site` inner join `project` on `site`.`project_id` = `project`.`id` where `site`.`name` == ? and `project`.`hub_id` = ? LIMIT 1", -1, &stmt, NULL);
	check(result == SQLITE_OK, "Error while preparing SQLite statement.");
	result = sqlite3_bind_text(stmt, 1, name, -1, SQLITE_STATIC);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	result = sqlite3_bind_int64(stmt, 2, hub_id);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	result = sqlite3_step(stmt);
	if (result == SQLITE_ROW){
		site_id = (uint64_t) sqlite3_column_int64(stmt, 0);
	}
error:
	if (stmt != NULL)
		sqlite3_finalize(stmt);
	return site_id;
}

int StoreOrderCategory(TDatabase *pDB, char *order_id, uint64_t cat_id){
	
	int result = -1;
	sqlite3_stmt *stmt = NULL;
	check(pDB != NULL && order_id != NULL, "Invalid function inputs.");
	
	
	/*****************************************************************************/
	//	Prepare SQL query
	/*****************************************************************************/
	result = sqlite3_prepare_v2(pDB, "insert or ignore into `order_category`(`order_id`, `category_id`) values (?,?)", -1, &stmt, NULL);
	check(result == SQLITE_OK, "Error while preparing SQLite statement.");
	result = sqlite3_bind_text(stmt, 1, order_id, -1, SQLITE_STATIC);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	result = sqlite3_bind_int64(stmt, 2, cat_id);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	result = sqlite3_step(stmt);
	check(result == SQLITE_DONE, "Error while saving order category %s %lu.", order_id, cat_id);
	result = 0;
error:
	if (stmt != NULL)
		sqlite3_finalize(stmt);
	return result;
}

int CleanCategoriesRelationships(TDatabase *pDB){
	
	int result = -1;
	check(pDB != NULL, "Invalid function inputs.");

	/*****************************************************************************/
	//	Execute SQL queries
	/*****************************************************************************/
	result = sqlite3_exec(pDB, "delete from `order_category` where `category_id` not in (select `id` from `category`)", 0, NULL, NULL);
	check(result == SQLITE_OK, "Error while cleaning categories relationships.");
	result = sqlite3_exec(pDB, "delete from `user_category` where `category_id` not in (select `id` from `category`)", 0, NULL, NULL);
	check(result == SQLITE_OK, "Error while cleaning categories relationships.");
	result = 0;
error:
	return result;
}

int UpdateOrderPositions(TDatabase *pDB, char *order_id){
	int result = -1;

	sqlite3_stmt *stmt1 = NULL, *stmt2 = NULL, *stmt3 = NULL;
	check(pDB != NULL && order_id != NULL, "Invalid function inputs.");

	/*****************************************************************************/
	//	Prepare SQL query
	/*****************************************************************************/
	result = sqlite3_prepare_v2(pDB, "SELECT `order`.`hub_id`, `site`.`project_id` FROM `order` JOIN `site` ON `order`.`site_id` == `site`.`id` where `order`.`id` = ?", -1, &stmt1, NULL);
	check(result == SQLITE_OK, "Error while preparing SQLite statement.");
	result = sqlite3_bind_text(stmt1, 1, order_id, -1, SQLITE_STATIC);
	check(result == SQLITE_OK, "Error while binding SQLite statement.");
	
	/*****************************************************************************/
	//	Get SQL query result
	/*****************************************************************************/	
	if (sqlite3_step(stmt1) == SQLITE_ROW){
		uint64_t hub_id = sqlite3_column_int64(stmt1, 0);
		uint64_t project_id = sqlite3_column_int64(stmt1, 1);
		
		result = sqlite3_prepare_v2(pDB, "SELECT position.id AS position_id \
										  FROM position JOIN user ON position.id = user.position_id JOIN user_category ON user.id = user_category.user_id JOIN user_project ON user.id = user_project.user_id \
                                          WHERE position.hub_id = ? AND user.role = \"validator\" AND user_category.category_id IN (select `category_id` from `order_category` where order_id = ?) AND user_project.project_id = ?", -1, &stmt2, NULL);
		check(result == SQLITE_OK, "Error while preparing SQLite statement.");
		result = sqlite3_bind_int64(stmt2, 1, hub_id);
		check(result == SQLITE_OK, "Error while binding SQLite statement.");
		result = sqlite3_bind_text(stmt2, 2, order_id, -1, SQLITE_STATIC);
		check(result == SQLITE_OK, "Error while binding SQLite statement.");
		result = sqlite3_bind_int64(stmt2, 3, project_id);
		check(result == SQLITE_OK, "Error while binding SQLite statement.");
		while (sqlite3_step(stmt2) == SQLITE_ROW){
			uint64_t position_id = sqlite3_column_int64(stmt2, 0);
			result = sqlite3_prepare_v2(pDB, "INSERT OR IGNORE INTO `order_position`(`order_id`, `position_id`) VALUES (?,?)", -1, &stmt3, NULL);
			if (result != SQLITE_OK){
				log_err("Error while saving order positions (%s %lu).", order_id, position_id);
				if (stmt3 != NULL){
					sqlite3_finalize(stmt3);
					stmt3 = NULL;
				}
				continue;
			}
			result = sqlite3_bind_text(stmt3, 1, order_id, -1, SQLITE_STATIC);
			if (result != SQLITE_OK){
				log_err("Error while saving order positions (%s %lu).", order_id, position_id);
				if (stmt3 != NULL){
					sqlite3_finalize(stmt3);
					stmt3 = NULL;
				}
				continue;
			}
			result = sqlite3_bind_int64(stmt3, 2, position_id);
			if (result != SQLITE_OK){
				log_err("Error while saving order positions (%s %lu).", order_id, position_id);
				if (stmt3 != NULL){
					sqlite3_finalize(stmt3);
					stmt3 = NULL;
				}
				continue;
			}
			result = sqlite3_step(stmt3);
			if (result != SQLITE_DONE){
				log_err("Error while saving order positions (%s %lu).", order_id, position_id);
			}
			if (stmt3 != NULL){
				sqlite3_finalize(stmt3);
				stmt3 = NULL;
			}
		}
	}
	result = 0;
error:
	if (stmt1 != NULL)
		sqlite3_finalize(stmt1);
	if (stmt2 != NULL)
		sqlite3_finalize(stmt2);
	if (stmt3 != NULL)
		sqlite3_finalize(stmt3);
	return result;
}
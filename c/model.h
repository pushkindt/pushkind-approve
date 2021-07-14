#include <sqlite3.h>

#define DATABASE_URL "app.db"
#define DATABASE_OK SQLITE_OK

typedef struct
{
	uint64_t id;
	char *token;
	char *client_id;
	char *client_secret;
	char *partners_key;
	char *name;
	char *email;
	char *url;
} TEcwid;

typedef struct
{
	uint64_t id;
	uint64_t hub_id;
	char *name;
	char *children;
} TCategory;

typedef struct
{
	char *id;
	uint64_t initiative_id;
	uint64_t hub_id;
	uint64_t create_timestamp;
	char *products;
	double total;
	uint64_t site_id;
	char *cash_flow_statement;
	char *income_statement;
	bool purchased;
} TOrder;

typedef sqlite3 TDatabase;

extern bool OpenDatabaseConnection(TDatabase **pDB);
extern bool CloseDatabaseConnection(TDatabase *pDB);

extern void FreeStores(TEcwid *stores, size_t stores_count);
extern void FreeCategories(TCategory *cache);

extern TEcwid *GetStores(TDatabase *pDB, uint64_t hub_id, size_t *stores_count, uint64_t store_id);
extern int StoreEcwidProfile(TDatabase *pDB, TEcwid store);

extern int DeleteCategories(TDatabase *pDB, uint64_t hub_id);
extern int StoreCategories(TDatabase *pDB, TCategory *cache);

extern int BeginTransaction(TDatabase *pDB);
extern int CommitTransaction(TDatabase *pDB);
extern int RollbackTransaction(TDatabase *pDB);

extern uint64_t GetRecentOrderTimestamp(TDatabase *pDB, uint64_t hub_id);
extern uint64_t GetCategoryIdByChildId(TDatabase *pDB, uint64_t hub_id, uint64_t cat_id, char **cat_name);
extern uint64_t GetInitiativeIdByEmail(TDatabase *pDB, uint64_t hub_id, char *email);
extern uint64_t GetSiteIdByName(TDatabase *pDB, uint64_t hub_id, char *name);
extern int StoreOrders(TDatabase *pDB, TOrder order);
extern int StoreOrderCategory(TDatabase *pDB, char *order_id, uint64_t cat_id);
extern int CleanCategoriesRelationships(TDatabase *pDB);
extern int UpdateOrderPositions(TDatabase *pDB, char *order_id);
extern char *GetStoreNameById(TDatabase *pDB, char *store_id);
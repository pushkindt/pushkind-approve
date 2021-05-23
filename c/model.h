#include <sqlite3.h>

typedef struct {
	uint64_t id;
	char *token;
	char *client_id;
	char *client_secret;
	char *partners_key;
	char *store_name;
	char *store_email;
} TEcwid;

typedef struct {
	uint64_t id;
	uint64_t ecwid_id;
	char *name;
	char *children;
} TCacheCategories;

typedef struct {
	uint64_t id;
	uint64_t ecwid_id;
	char *name;
} TLocation;

extern void FreeStores(TEcwid *stores, size_t stores_count);
extern void FreeHub(TEcwid *hub);
extern void FreeCacheCategories(TCacheCategories *cache);
extern void FreeLocation(TLocation *location);

extern TEcwid *GetHub(sqlite3 *pDB, uint64_t ecwid_id);
extern TEcwid *GetStores(sqlite3 *pDB, uint64_t ecwid_id, size_t *stores_count);
extern TEcwid *GetStore(sqlite3 *pDB, uint64_t ecwid_id, uint64_t store_id);

extern int DeleteCacheCategories(sqlite3 *pDB, uint64_t ecwid_id);
extern int StoreCacheCategories(sqlite3 *pDB, TCacheCategories *cache);

extern int DeleteLocations(sqlite3 *pDB, uint64_t ecwid_id);
extern int StoreLocation(sqlite3 *pDB, TLocation *location);

extern int BeginTransaction(sqlite3 *pDB);
extern int CommitTransaction(sqlite3 *pDB);
extern int RollbackTransaction(sqlite3 *pDB);
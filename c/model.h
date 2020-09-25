#include <sqlite3.h>

typedef struct {
	uint64_t id;
	char *token;
	char *client_id;
	char *client_secret;
	char *partners_key;
} TEcwid;

typedef struct {
	uint64_t id;
	uint64_t ecwid_id;
	char *name;
	char *children;
} TCacheCategories;

extern void FreeStores(TEcwid *stores, size_t stores_count);
extern void FreeHub(TEcwid *hub);
extern void FreeCacheCategories(TCacheCategories *cache);

extern TEcwid *GetHub(sqlite3 *pDB, uint64_t ecwid_id);
extern TEcwid *GetStores(sqlite3 *pDB, uint64_t ecwid_id, size_t *stores_count);
extern TEcwid *GetStore(sqlite3 *pDB, uint64_t ecwid_id, uint64_t store_id);

extern int DeleteCacheCategories(sqlite3 *pDB, uint64_t ecwid_id);
extern int StoreCacheCategories(sqlite3 *pDB, TCacheCategories *cache);
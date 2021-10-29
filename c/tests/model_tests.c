#include <stdint.h>
#include <stdbool.h>
#include <curl/curl.h>
#include <sqlite3.h>
#include <json.h>

#include "minunit.h"
#include "model.h"

char *DATABASE_URL = NULL;
char *REST_URL = NULL;

TDatabase *pDB = NULL;

char *test_OpenDatabaseConnection()
{
    mu_assert(DATABASE_URL != NULL, "DATABASE_URL is not present in the environment.");

    mu_assert(OpenDatabaseConnection(NULL) == false, "The result doesn't match the expected false.");

    mu_assert(OpenDatabaseConnection(&pDB) == true, "The result doesn't match the expected true.");

    mu_assert(pDB != NULL, "The result must not be NULL.");

    return NULL;
}

char *test_CategoryFunctions()
{
    TCategory category1 = {
        .children = "[1]",
        .hub_id = 1,
        .id = 1,
        .name = "name"};

    mu_assert(StoreCategory(pDB, &category1) == 0, "The result doesn't match the expected 0.");

    TCategory *category2 = NULL;

    category2 = GetCategoryByChildId(pDB, 1, 1);

    mu_assert(category2 != NULL, "The result doesn't match the expected non-NULL value.");

    mu_assert(strcmp(category2->name, "name") == 0, "The name of the category must be \"name\".");

    FreeCategory(category2);

    category2 = NULL;

    mu_assert(DeleteCategories(pDB, 1) == 0, "The result doesn't match the expected 0.");

    category2 = GetCategoryByChildId(pDB, 1, 1);

    mu_assert(category2 == NULL, "The result doesn't match the expected NULL.");

    FreeCategory(category2);

    return NULL;
}

char *test_StoreFunctions()
{
    TEcwid ecwid1 = {
        .id = 1,
        .hub_id = 0,
        .name = "hub",
        .email = "email@email.email",
        .client_id = "client_id",
        .client_secret = "client_secret",
        .partners_key = "partners_key",
        .token = "token",
        .url = "http://url.url"};

    DeleteEcwidProfile(pDB, ecwid1.id);

    mu_assert(StoreEcwidProfile(pDB, ecwid1) == 0, "The result doesn't match the expected 0.");

    TEcwid *ecwid2 = NULL;
    size_t store_count = 0;

    ecwid2 = GetStores(pDB, 1, &store_count, 0);

    mu_assert(store_count == 1 && ecwid2 != NULL, "The result doesn't match the expected ecwid data.");
    mu_assert(ecwid2[0].id == 2, "The result doesn't match the expected ecwid data.");

    if (ecwid2 != NULL)
    {
        FreeStores(ecwid2, store_count);
        ecwid2 = NULL;
        store_count = 0;
    }

    ecwid1.name = "test";

    mu_assert(UpdateEcwidProfile(pDB, ecwid1) == 0, "The result doesn't match the expected 0.");

    char *store_name = GetStoreNameById(pDB, ecwid1.id);

    mu_assert(store_name != NULL, "The result doesn't match the expected non-NULL value.");

    mu_assert(strcmp(store_name, "test") == 0, "The result doesn't match the expected \"test\".");

    if (store_name != NULL)
        free(store_name);

    return NULL;
}

char *test_OrderFunctions()
{
    TOrder order = {
        .id = "1",
        .hub_id = 1,
        .income_id = 1,
        .initiative_id = 1,
        .create_timestamp = 0,
        .cashflow_id = 1,
        .products = "[]",
        .purchased = true,
        .site_id = 1,
        .total = 1.0};

    mu_assert(StoreOrders(pDB, order) == 0, "The result doesn't match the expected 0.");

    mu_assert(GetRecentOrderTimestamp(pDB, 1) == 0, "The result doesn't match the expected 123.");

    mu_assert(StoreOrderCategory(pDB, "1", 1) == 0, "The result doesn't match the expected 0.");

    mu_assert(CleanCategoriesRelationships(pDB) == 0, "The result doesn't match the expected 0.");

    mu_assert(GetInitiativeIdByEmail(pDB, 1, "email@email.email") == 1, "The result doesn't match the expected 1.");

    mu_assert(GetSiteIdByName(pDB, 1, "name") == 1, "The result doesn't match the expected 1.");

    mu_assert(UpdateOrderPositions(pDB, "1") == 0, "The result doesn't match the expected 0.");

    return NULL;
}

char *all_tests()
{
    REST_URL = getenv("REST_URL");
    DATABASE_URL = getenv("DATABASE_URL");
    sqlite3_initialize();
    curl_global_init(CURL_GLOBAL_ALL);

    mu_suite_start();

    mu_run_test(test_OpenDatabaseConnection);

    mu_run_test(test_CategoryFunctions);

    mu_run_test(test_StoreFunctions);

    mu_run_test(test_OrderFunctions);

    if (pDB != NULL)
    {
        CloseDatabaseConnection(pDB);
    }

    curl_global_cleanup();
    sqlite3_shutdown();
    return NULL;
}

RUN_TESTS(all_tests);
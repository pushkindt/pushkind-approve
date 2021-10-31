#include <stdint.h>
#include <stdbool.h>
#include <curl/curl.h>
#include <sqlite3.h>

#include "minunit.h"
#include "ecwid.h"
#include "model.h"

char *DATABASE_URL = NULL;
char *REST_URL = NULL;

char *test_ProcessProfiles()
{
    mu_assert(DATABASE_URL != NULL, "DATABASE_URL is not present in the environment.");

    mu_assert(REST_URL != NULL, "REST_URL is not present in the environment.");

    mu_assert(ProcessProfiles(1, 0) == true, "The result doesn't match the expected true.");

    TDatabase *pDB = NULL;

    mu_assert(OpenDatabaseConnection(&pDB) == true, "The result doesn't match the expected true.");

    mu_assert(pDB != NULL, "The result must not be NULL.");

    TEcwid *ecwid = NULL;
    size_t store_count = 0;

    ecwid = GetStores(pDB, 1, &store_count, 0);

    mu_assert(store_count == 1 && ecwid != NULL, "The result doesn't match the expected ecwid data.");
    mu_assert(ecwid[0].id == 2, "The result doesn't match the expected ecwid data.");
    mu_assert(strcmp(ecwid[0].name, "vendor") == 0, "The result doesn't match the expected \"vendor\".");

    if (ecwid != NULL)
    {
        FreeStores(ecwid, store_count);
        ecwid = NULL;
        store_count = 0;
    }

    ecwid = GetStores(pDB, 0, &store_count, 1);

    mu_assert(store_count == 1 && ecwid != NULL, "The result doesn't match the expected ecwid data.");
    mu_assert(ecwid[0].id == 1, "The result doesn't match the expected ecwid data.");
    mu_assert(strcmp(ecwid[0].name, "hub") == 0, "The result doesn't match the expected \"hub\".");

    if (ecwid != NULL)
    {
        FreeStores(ecwid, store_count);
        ecwid = NULL;
        store_count = 0;
    }

    if (pDB != NULL)
    {
        CloseDatabaseConnection(pDB);
    }

    return NULL;
}

char *all_tests()
{
    REST_URL = getenv("REST_URL");
    DATABASE_URL = getenv("DATABASE_URL");
    sqlite3_initialize();
    curl_global_init(CURL_GLOBAL_ALL);

    mu_suite_start();

    mu_run_test(test_ProcessProfiles);

    curl_global_cleanup();
    sqlite3_shutdown();
    return NULL;
}

RUN_TESTS(all_tests);
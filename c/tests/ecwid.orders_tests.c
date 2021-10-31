#include <stdint.h>
#include <stdbool.h>
#include <curl/curl.h>
#include <sqlite3.h>

#include "minunit.h"
#include "ecwid.h"
#include "model.h"

char *DATABASE_URL = NULL;
char *REST_URL = NULL;

char *test_ProcessOrders()
{
    mu_assert(DATABASE_URL != NULL, "DATABASE_URL is not present in the environment.");

    mu_assert(REST_URL != NULL, "REST_URL is not present in the environment.");

    mu_assert(ProcessOrders(1, NULL) == true, "The result doesn't match the expected true.");

    TDatabase *pDB = NULL;

    mu_assert(OpenDatabaseConnection(&pDB) == true, "The result doesn't match the expected true.");

    mu_assert(pDB != NULL, "The result must not be NULL.");

    mu_assert(GetRecentOrderTimestamp(pDB, 1) == 1527779316, "The result doesn't match the expected 1527779316.");

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

    mu_run_test(test_ProcessOrders);

    curl_global_cleanup();
    sqlite3_shutdown();
    return NULL;
}

RUN_TESTS(all_tests);
#include <stdint.h>
#include <stdbool.h>
#include <curl/curl.h>
#include <sqlite3.h>
#include <json.h>

#include "minunit.h"
#include "rest.h"

char *DATABASE_URL = NULL;
char *REST_URL = NULL;

#define cleanup_test_data(result_json) \
    if (result_json != NULL)           \
    {                                  \
        json_object_put(result_json);  \
        result_json = NULL;            \
    }

char *test_RESTcall()
{

    struct json_object *param_json = NULL;
    struct json_object *result_json = NULL;

    param_json = json_object_new_object();
    check_mem(param_json);
    json_object_object_add(param_json, "productId", json_object_new_int64(10));

    mu_assert(REST_URL != NULL, "REST_URL is not present in the environment.");

    mu_assert(RESTcall(1, -1, NULL, NULL, 0) == NULL, "The result doesn't match the expected NULL.");

    result_json = RESTcall(1, GET_PRODUCTS, NULL, NULL, 0);
    mu_assert(result_json != NULL, "The result doesn't match the expected JSON object.");
    cleanup_test_data(result_json);

    result_json = RESTcall(1, GET_PRODUCTS, param_json, NULL, 0);
    mu_assert(result_json != NULL, "The result doesn't match the expected JSON object.");
    cleanup_test_data(result_json);

    result_json = RESTcall(1, DELETE_PRODUCT, param_json, NULL, 0);
    mu_assert(result_json != NULL, "The result doesn't match the expected JSON object.");
    cleanup_test_data(result_json);

    result_json = RESTcall(1, PUT_PRODUCT, param_json, NULL, 0);
    mu_assert(result_json != NULL, "The result doesn't match the expected JSON object.");
    cleanup_test_data(result_json);

    result_json = RESTcall(1, POST_IMAGE, param_json, NULL, 0);
    mu_assert(result_json != NULL, "The result doesn't match the expected JSON object.");
    cleanup_test_data(result_json);

error:
    if (param_json != NULL)
    {
        json_object_put(param_json);
        param_json = NULL;
    }
    cleanup_test_data(result_json);
    return NULL;
}

char *all_tests()
{
    REST_URL = getenv("REST_URL");
    DATABASE_URL = getenv("DATABASE_URL");
    sqlite3_initialize();
    curl_global_init(CURL_GLOBAL_ALL);

    mu_suite_start();

    mu_run_test(test_RESTcall);

    curl_global_cleanup();
    sqlite3_shutdown();
    return NULL;
}

RUN_TESTS(all_tests);
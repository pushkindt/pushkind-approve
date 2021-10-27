#include <stdint.h>
#include <stdbool.h>
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

    REST_URL = getenv("REST_URL");

    mu_assert(REST_URL != NULL, "REST_URL is not present in the environment.");

    mu_assert(RESTcall(0, -1, NULL, NULL, 0) == NULL, "The result doesn't match the expected NULL.");

    result_json = RESTcall(0, GET_PRODUCTS, NULL, NULL, 0);
    mu_assert(result_json != NULL, "The result doesn't match the expected JSON object.");
    cleanup_test_data(result_json);

    result_json = RESTcall(0, GET_PRODUCTS, param_json, NULL, 0);
    mu_assert(result_json != NULL, "The result doesn't match the expected JSON object.");
    cleanup_test_data(result_json);

    result_json = RESTcall(0, DELETE_PRODUCT, param_json, NULL, 0);
    mu_assert(result_json != NULL, "The result doesn't match the expected JSON object.");
    cleanup_test_data(result_json);

    result_json = RESTcall(0, PUT_PRODUCT, param_json, NULL, 0);
    mu_assert(result_json != NULL, "The result doesn't match the expected JSON object.");
    cleanup_test_data(result_json);

    result_json = RESTcall(0, POST_IMAGE, param_json, NULL, 0);
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
    mu_suite_start();

    mu_run_test(test_RESTcall);

    return NULL;
}

RUN_TESTS(all_tests);
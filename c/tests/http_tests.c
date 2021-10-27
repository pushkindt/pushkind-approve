#include <stdint.h>
#include <json.h>

#include "minunit.h"
#include "http.h"

#define cleanup_test_data(json, buffer) \
    if (json != NULL)                   \
    {                                   \
        json_object_put(json);          \
        json = NULL;                    \
    }                                   \
    if (buffer != NULL)                 \
    {                                   \
        free(buffer);                   \
        buffer = NULL;                  \
        buffer_size = 0;                \
    }

char *test_HTTPcall()
{

    char *REST_URL = getenv("REST_URL");

    mu_assert(REST_URL != NULL, "REST_URL is not present in the environment.");

    mu_assert(HTTPcall(HTTP_GET, NULL, NULL, 0, NULL, NULL) == -1, "The result doesn't match the expected -1.");

    uint8_t *buffer = NULL;
    size_t buffer_size = 0;
    mu_assert(HTTPcall(HTTP_GET, REST_URL, NULL, 0, &buffer, &buffer_size) == 0, "The result doesn't match the expected 0.");
    mu_assert(buffer_size > 0, "The response buffer size have to be greater than 0.");
    mu_assert(buffer != NULL, "The response buffer can't be NULL.");
    struct json_object *json = json_tokener_parse((char *)buffer);
    mu_assert(json != NULL, "The response must be a valid JSON.");
    cleanup_test_data(json, buffer);

    const char *test_str = "{\"key\":\"value\"}";
    mu_assert(HTTPcall(HTTP_POST, REST_URL, (uint8_t *)test_str, strlen(test_str), &buffer, &buffer_size) == 0, "The result doesn't match the expected 0.");
    mu_assert(buffer_size > 0, "The response buffer size have to be greater than 0.");
    mu_assert(buffer != NULL, "The response buffer can't be NULL.");
    json = json_tokener_parse((char *)buffer);
    mu_assert(json != NULL, "The response must be a valid JSON.");
    cleanup_test_data(json, buffer);

    mu_assert(HTTPcall(HTTP_PUT, REST_URL, (uint8_t *)test_str, strlen(test_str), &buffer, &buffer_size) == 0, "The result doesn't match the expected 0.");
    mu_assert(buffer_size > 0, "The response buffer size have to be greater than 0.");
    mu_assert(buffer != NULL, "The response buffer can't be NULL.");
    json = json_tokener_parse((char *)buffer);
    mu_assert(json != NULL, "The response must be a valid JSON.");
    cleanup_test_data(json, buffer);

    mu_assert(HTTPcall(HTTP_DELETE, REST_URL, (uint8_t *)test_str, strlen(test_str), &buffer, &buffer_size) == 0, "The result doesn't match the expected 0.");
    mu_assert(buffer_size > 0, "The response buffer size have to be greater than 0.");
    mu_assert(buffer != NULL, "The response buffer can't be NULL.");
    json = json_tokener_parse((char *)buffer);
    mu_assert(json != NULL, "The response must be a valid JSON.");
    cleanup_test_data(json, buffer);

    mu_assert(HTTPcall(4, REST_URL, (uint8_t *)test_str, strlen(test_str), &buffer, &buffer_size) == -1, "The result doesn't match the expected -1.");
    mu_assert(buffer_size == 0, "The response buffer size have to be 0 but was.");
    mu_assert(buffer == NULL, "The response buffer must be NULL but was.");
    cleanup_test_data(json, buffer);

    return NULL;
}

char *all_tests()
{
    mu_suite_start();

    curl_global_init(CURL_GLOBAL_ALL);

    mu_run_test(test_HTTPcall);

    curl_global_cleanup();

    return NULL;
}

RUN_TESTS(all_tests);
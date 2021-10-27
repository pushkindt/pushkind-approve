#include <stdint.h>
#include <stdbool.h>
#include <json.h>
#include <string.h>

#include "minunit.h"
#include "util.h"

char *DATABASE_URL = NULL;
char *REST_URL = NULL;

char *test_FilterJSONFields()
{
	const char *ALLOWED_FIELDS[] = {"key1"};

	struct json_object *json = json_object_new_object();
	check_mem(json);
	json_object_object_add(json, "key1", json_object_new_string("value1"));
	json_object_object_add(json, "key2", json_object_new_string("value2"));

	FilterJSONFields(NULL, NULL, 0);

	FilterJSONFields(json, ALLOWED_FIELDS, ARRAY_SIZE(ALLOWED_FIELDS));

	mu_assert(strcmp(json_object_to_json_string(json), "{ \"key1\": \"value1\" }") == 0, "The result JSON doesn't match the expected one.");

error:
	if (json != NULL)
	{
		json_object_put(json);
	}
	return NULL;
}

char *test_TrimWhiteSpaces()
{
	char *test_string1 = NULL;
	mu_assert(TrimWhiteSpaces(test_string1) == NULL, "The result of trimming NULL should be NULL.");

	char *test_string2 = strdup("test");
	mu_assert(strcmp(TrimWhiteSpaces(test_string2), "test") == 0, "The result doesn't match the expected string.");
	free(test_string2);

	char *test_string3 = strdup(" test");
	mu_assert(strcmp(TrimWhiteSpaces(test_string3), "test") == 0, "The result doesn't match the expected string.");
	free(test_string3);

	char *test_string4 = strdup(" test ");
	mu_assert(strcmp(TrimWhiteSpaces(test_string4), "test") == 0, "The result doesn't match the expected string.");
	free(test_string4);

	char *test_string5 = strdup("   test   ");
	mu_assert(strcmp(TrimWhiteSpaces(test_string5), "test") == 0, "The result doesn't match the expected string.");
	free(test_string5);

	char *test_string6 = strdup("");
	mu_assert(TrimWhiteSpaces(test_string6) == NULL, "The result doesn't match the expected string.");
	free(test_string6);

	return NULL;
}

char *all_tests()
{
	mu_suite_start();

	mu_run_test(test_FilterJSONFields);
	mu_run_test(test_TrimWhiteSpaces);

	return NULL;
}

RUN_TESTS(all_tests);
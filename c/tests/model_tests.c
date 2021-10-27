#include <stdint.h>
#include <stdbool.h>
#include <json.h>

#include "minunit.h"
#include "model.h"

char *DATABASE_URL = NULL;
char *REST_URL = NULL;

char *test_MyCoolFunction()
{
    return NULL;
}

char *all_tests()
{
    mu_suite_start();

    mu_run_test(test_MyCoolFunction);

    return NULL;
}

RUN_TESTS(all_tests);
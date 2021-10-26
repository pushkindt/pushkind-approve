#include "minunit.h"

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
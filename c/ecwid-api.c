#include <curl/curl.h>
#include <sqlite3.h>
#include <sys/file.h>
#include <argp.h>

#include "model.h"
#include "ecwid.h"

const char *argp_program_version =  "ecwid-api 1.0";
const char *argp_program_bug_address =  "<matrizaev@gmail.com>";
static char doc[] =  "ecwid-api -- a program to sync approvals database with ecwid";
static char args_doc[] = "(products | categories | orders | profiles) HUB_ID";
static struct argp_option options[] = {
  {"store",   's', "STORE_ID", 0,
   "store_id to sync only that store, use it with products or profiles", 0},
  {"order",   'o', "ORDER_ID", 0,
   "order_id to sync only that order, use it with orders", 0},
  { 0 }
};


struct arguments
{
	char *operation;
	uint64_t hub_id;
	uint64_t store_id;
	char *order_id;
};

static error_t parse_opt (int key, char *arg, struct argp_state *state)
{
	struct arguments *arguments = state->input;
	
	switch (key){
		case 's':
			/* STORE_ID is an unsigned integer. */
			arguments->store_id = atoi(arg);
			if (arguments->store_id == 0)
				argp_usage (state);
			break;
		case 'o':
			/* ORDER_ID is a string. */
			arguments->order_id = arg;
			break;
		case ARGP_KEY_NO_ARGS:
			argp_usage (state);
			break;
		case ARGP_KEY_ARG:
			if (state->arg_num >= 2)
				/* Too many arguments. */
				argp_usage (state);
			if (state->arg_num == 0){
				/* Arguments should be either of the following */
				if (((strcmp(arg, "products") == 0 || strcmp(arg, "profiles") == 0) && arguments->order_id == NULL) ||
					(strcmp(arg, "orders") == 0 && arguments->store_id == 0) ||
					(strcmp(arg, "categories") == 0 && arguments->store_id == 0 && arguments->order_id == NULL))
					arguments->operation = arg;
				else	
					argp_usage (state);
			}
			if (state->arg_num == 1){
				/* HUB_ID is unsigned integer. */
				arguments->hub_id = atoi(arg);
				if (arguments->hub_id == 0)
					argp_usage (state);
			}
			break;

		case ARGP_KEY_END:
			if (state->arg_num < 2)
				/* Not enough arguments. */
				argp_usage (state);
			break;

		default:
			return ARGP_ERR_UNKNOWN;
	}
	return 0;
}


static struct argp argp = { options, parse_opt, args_doc, doc, 0, 0, 0 };


int main(int argc, char* argv[]){
	
	int result = -1;
	int pid_file = -1;
	struct arguments arguments = {0};
	
	
	/*****************************************************************************/
	//	Parse arguments
	/*****************************************************************************/
	
	check(argp_parse (&argp, argc, argv, 0, 0, &arguments) == 0, "Cannot parse the arguments.");
	
	
	/*****************************************************************************/
	//	Initialize libraries
	/*****************************************************************************/
	
	sqlite3_initialize();
	curl_global_init(CURL_GLOBAL_ALL);
	
	/*****************************************************************************/
	//	Lock the pid file to prevent multiple copies
	/*****************************************************************************/
	
	pid_file = open("ecwid-api-products.pid", O_RDWR | O_CREAT, 0666);
	check(pid_file > 0, "You are not allowed to run multiple instances of the program.");
	int rc = flock(pid_file, LOCK_EX | LOCK_NB);
	check(rc != -1, "You are not allowed to run multiple instances of the program.");

	if (strcmp(arguments.operation, "products") == 0){
		check(ProcessProducts(arguments.hub_id, arguments.store_id) == true, "Cannot process products.");
	}
	else if (strcmp(arguments.operation, "categories") == 0){
		check(ProcessCategories(arguments.hub_id) == true, "Cannot process categories.");
	}
	else if (strcmp(arguments.operation, "orders") == 0){
		check(ProcessOrders(arguments.hub_id, arguments.order_id) == true, "Cannot process orders.");
	}
	else if (strcmp(arguments.operation, "profiles") == 0){
		check(ProcessProfiles(arguments.hub_id, arguments.store_id) == true, "Cannot process profiles.");
	}
	else {
		log_warn("The operations is not implemented");
	}
	result = 0;
error:

	/*****************************************************************************/
	//	Clean everything up
	/*****************************************************************************/
	close(pid_file);
	sqlite3_shutdown();
	curl_global_cleanup();
	return result;
}

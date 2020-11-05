#include <curl/curl.h>
#include <sqlite3.h>
#include <sys/file.h>

#include "model.h"
#include "ecwid.h"

#define USAGE_STRING "ecwid-api ecwid_id {store_id}"

int main(int argc, char* argv[]){
	int result = -1;
	uint64_t ecwid_id = 0;
	uint64_t store_id = 0;
	
	/*****************************************************************************/
	//	Initialize libraries
	/*****************************************************************************/
	
	sqlite3_initialize();
	curl_global_init(CURL_GLOBAL_ALL);
	int pid_file = -1;
	
	/*****************************************************************************/
	//	Check the usage
	/*****************************************************************************/
	check(argc == 2 || argc == 3, USAGE_STRING);
	ecwid_id = atoi(argv[1]);
	check(ecwid_id != 0, USAGE_STRING);
	
	/*****************************************************************************/
	//	Lock the pid file to prevent multiple copies
	/*****************************************************************************/
	
	pid_file = open("ecwid-api-products.pid", O_RDWR | O_CREAT, 0666);
	check(pid_file > 0, "You are not allowed to run multiple instances of the program.");
	int rc = flock(pid_file, LOCK_EX | LOCK_NB);
	check(rc != -1, "You are not allowed to run multiple instances of the program.");

	if (argc == 2){
		/*****************************************************************************/
		//	Synchronize stores with the hub store
		/*****************************************************************************/
		
		check(ProcessHub(ecwid_id, 0) == true, "Cannot process hub products.");
	}
	else if (argc == 3){
		/*****************************************************************************/
		//	Synchronize the store with the hub store
		/*****************************************************************************/
		store_id = atoi(argv[2]);
		check(store_id != 0, USAGE_STRING);
		check(ProcessHub(ecwid_id, store_id) == true, "Cannot process hub products.");
	}
	
	check(ProcessCache(ecwid_id) == true, "Cannot process cache.");
	//check(ProcessLocations(ecwid_id) == true, "Cannot process locations.");
	
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

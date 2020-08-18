#include "http.h"

static size_t WriteMemoryCallback(void *contents, size_t size, size_t nmemb, void *userp){
	char *tempBuffer = NULL;
	size_t realSize = size * nmemb;

	if(contents != NULL && userp != NULL){
		TMemoryStruct *mem =(TMemoryStruct *)userp;
		tempBuffer = realloc(mem->memory, mem->size + realSize + 1);
		if(tempBuffer != NULL){
			mem->memory = tempBuffer;
			memcpy(&(((unsigned char *)mem->memory)[mem->size]), contents, realSize);
			mem->size += realSize;
			return realSize;
		}
	}
	return 0;
}

int HTTPcall(THTTPMethod method, const char *url, uint8_t *payload, size_t payload_size, uint8_t **output, size_t *output_size){

	int result = -1;
	TMemoryStruct buffer = {.memory = NULL, .size = 0};
	CURL *handle = NULL;
	CURLcode curl_result = 0;
	struct curl_slist *curl_headers = NULL;
	char *encoded_url = NULL;
	
	check(method >= HTTP_GET && method <= HTTP_DELETE && url != NULL, "Invalid functions inputs.");
	
	/*************************************************************************
	* Init CURL handle                                                       *
	*************************************************************************/
	handle = curl_easy_init();
	check(handle != NULL, "Error while initializing CURL.");
	
	/*************************************************************************
	* Set CURL options                                                       *
	*************************************************************************/
	curl_result = curl_easy_setopt(handle, CURLOPT_URL, url);
	check(curl_result == CURLE_OK, "CURL error: %s", curl_easy_strerror(curl_result));
	curl_result = curl_easy_setopt(handle, CURLOPT_FOLLOWLOCATION, 1L);
	check(curl_result == CURLE_OK, "CURL error: %s", curl_easy_strerror(curl_result));
	curl_result = curl_easy_setopt(handle, CURLOPT_WRITEFUNCTION, WriteMemoryCallback);
	check(curl_result == CURLE_OK, "CURL error: %s", curl_easy_strerror(curl_result));
	curl_result = curl_easy_setopt(handle, CURLOPT_WRITEDATA,(void *)&buffer);
	check(curl_result == CURLE_OK, "CURL error: %s", curl_easy_strerror(curl_result));
	curl_result = curl_easy_setopt(handle, CURLOPT_USERAGENT, "libcurl-agent/1.0");
	check(curl_result == CURLE_OK, "CURL error: %s", curl_easy_strerror(curl_result));
	
	switch(method){
		case HTTP_GET:
			curl_result = curl_easy_setopt(handle, CURLOPT_HTTPGET, 1L);
			check(curl_result == CURLE_OK, "CURL error: %s", curl_easy_strerror(curl_result));
			break;
		case HTTP_POST:
			curl_result = curl_easy_setopt(handle, CURLOPT_POST, 1L);
			check(curl_result == CURLE_OK, "CURL error: %s", curl_easy_strerror(curl_result));
			curl_result = curl_easy_setopt(handle, CURLOPT_POSTFIELDS, payload);
			check(curl_result == CURLE_OK, "CURL error: %s", curl_easy_strerror(curl_result));
			curl_result = curl_easy_setopt(handle, CURLOPT_POSTFIELDSIZE, payload_size);
			check(curl_result == CURLE_OK, "CURL error: %s", curl_easy_strerror(curl_result));
			break;
		case HTTP_PUT:
			curl_result = curl_easy_setopt(handle, CURLOPT_CUSTOMREQUEST, "PUT");
			check(curl_result == CURLE_OK, "CURL error: %s", curl_easy_strerror(curl_result));
			curl_result = curl_easy_setopt(handle, CURLOPT_POSTFIELDS, payload);
			check(curl_result == CURLE_OK, "CURL error: %s", curl_easy_strerror(curl_result));
			curl_result = curl_easy_setopt(handle, CURLOPT_POSTFIELDSIZE, payload_size);
			check(curl_result == CURLE_OK, "CURL error: %s", curl_easy_strerror(curl_result));
			break;
		case HTTP_DELETE:
			curl_result = curl_easy_setopt(handle, CURLOPT_CUSTOMREQUEST, "DELETE");
			check(curl_result == CURLE_OK, "CURL error: %s", curl_easy_strerror(curl_result));
			break;
		default:
			log_err("Invalid HTTP method.");
			goto error;
	}
	/*************************************************************************
	* Set HTTP headers                                                       *
	*************************************************************************/
	curl_headers = curl_slist_append(curl_headers, "Accept: application/json");
	check(curl_headers != NULL, "Error while constructing CURL headers.");
	curl_headers = curl_slist_append(curl_headers, "Content-Type: application/json; charset=utf-8");
	check(curl_headers != NULL, "Error while constructing CURL headers.");	
	curl_headers = curl_slist_append(curl_headers, "Connection: close");
	check(curl_headers != NULL, "Error while constructing CURL headers.");	
	curl_result = curl_easy_setopt(handle, CURLOPT_HTTPHEADER, curl_headers);
	check(curl_result == CURLE_OK, "CURL error: %s", curl_easy_strerror(curl_result));
	
	/*************************************************************************
	* Make HTTP request                                                      *
	*************************************************************************/
	curl_result = curl_easy_perform(handle);
	check(curl_result == CURLE_OK, "CURL error: %s", curl_easy_strerror(curl_result));
	
	long http_code = 0;
	curl_result = curl_easy_getinfo(handle, CURLINFO_RESPONSE_CODE, &http_code);
	check(curl_result == CURLE_OK, "CURL error: %s", curl_easy_strerror(curl_result));
	check((http_code == 200), "HTTP error: %ld", http_code);
	*output = buffer.memory;
	*output_size = buffer.size;
	result = 0;
error:
	if(result != 0){
		if(buffer.memory != NULL){
			free(buffer.memory);
			buffer.memory = NULL;
			*output = NULL;
			*output_size = 0;
		}
	}
	if(curl_headers != NULL)
		curl_slist_free_all(curl_headers);
	if(encoded_url != NULL)
		free(encoded_url);
	if(handle != NULL)
			curl_easy_cleanup(handle);
	return result;
}
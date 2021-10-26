#include <json.h>
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <math.h>

#include "http.h"
#include "rest.h"
#include "dbg.h"

#define REST_URL "https://app.ecwid.com/api/v3/%lu/%s?"
#define REST_URL2 "https://app.ecwid.com/api/v3/%lu/%s/%lu?"
#define REST_URL3 "https://app.ecwid.com/api/v3/%lu/%s/%lu/%s?"

static const char *ENDPOINTS[] = {"profile", "products", "categories", "orders", "products", "products", "products", "categories", "orders", "products"};

struct json_object *RESTcall(uint64_t store_id, TRESTEndpoint endpoint, struct json_object *params, uint8_t *payload, size_t payload_size)
{

	char *url = NULL;
	uint8_t *response = NULL;
	size_t response_len = 0;
	struct json_object *json = NULL;
	int result = -1;
	size_t param_str_len = 1;

	check(endpoint >= GET_PROFILE && endpoint <= DELETE_PRODUCT && params != NULL && json_object_get_type(params) == json_type_object, "Invalid functions inputs.");
	{
		json_object_object_foreach(params, key, val)
		{
			param_str_len += strlen(key) + strlen((char *)json_object_get_string(val)) + 2;
		}
	}

	/*************************************************************************
	* Make URL string                                                        *
	*************************************************************************/
	switch (endpoint)
	{
	case GET_PROFILE:
	case GET_PRODUCTS:
	case GET_CATEGORIES:
	case GET_ORDERS:
	case POST_CATEGORY:
	case POST_PRODUCT:
	case POST_ORDER:
		url = calloc(strlen(REST_URL) + strlen(ENDPOINTS[endpoint]) + ceil(log10(store_id + 1)) + param_str_len + 2, 1);
		check_mem(url);
		result = sprintf(url, REST_URL, store_id, ENDPOINTS[endpoint]);
		check(result > 0, "Error while constructing url.");
		break;
	case DELETE_PRODUCT:
	case PUT_PRODUCT:
	{
		json_object *product_id_json = NULL;
		json_object_object_get_ex(params, "productId", &product_id_json);
		check(product_id_json != NULL && json_object_get_type(product_id_json) == json_type_int, "Invalid function inputs.");
		uint64_t product_id = (uint64_t)json_object_get_int64(product_id_json);
		url = calloc(strlen(REST_URL2) + strlen(ENDPOINTS[endpoint]) + ceil(log10(store_id + 1)) + ceil(log10(product_id + 1)) + param_str_len + 2, 1);
		check_mem(url);
		result = sprintf(url, REST_URL2, store_id, ENDPOINTS[endpoint], product_id);
		check(result > 0, "Error while constructing url.");
	}
	break;
	case POST_IMAGE:
	{
		json_object *product_id_json = NULL;
		json_object_object_get_ex(params, "productId", &product_id_json);
		check(product_id_json != NULL && json_object_get_type(product_id_json) == json_type_int, "Invalid function inputs.");
		uint64_t product_id = (uint64_t)json_object_get_int64(product_id_json);
		url = calloc(strlen(REST_URL3) + strlen(ENDPOINTS[endpoint]) + ceil(log10(store_id + 1)) + ceil(log10(product_id + 1)) + param_str_len + 2, 1);
		check_mem(url);
		result = sprintf(url, REST_URL3, store_id, ENDPOINTS[endpoint], product_id, "image");
		check(result > 0, "Error while constructing url.");
	}
	break;
	default:
		sentinel("Endpoint is not implemented yet.");
	}
	{
		char *dest = &url[result - 1];
		json_object_object_foreach(params, key, val)
		{
			dest++;
			result = sprintf(dest, "%s=%s", key, (char *)json_object_get_string(val));
			dest = &dest[result];
			*dest = '&';
		}
		*dest = '\0';
	}
	/*************************************************************************
	* Make HTTP call                                                         *
	*************************************************************************/
	switch (endpoint)
	{
	case GET_PROFILE:
	case GET_PRODUCTS:
	case GET_CATEGORIES:
	case GET_ORDERS:
		check(HTTPcall(HTTP_GET, url, payload, payload_size, &response, &response_len) == 0, "Invalid HTTP response");
		check(response != NULL && response_len > 0, "Invalid HTTP response.");
		response[response_len] = 0;
		json = json_tokener_parse((char *)response);
		check(json != NULL, "Invalid JSON response");
		struct json_object *json_total = NULL, *json_count = NULL, *json_offset = NULL, *json_items = NULL;
		json_object_object_get_ex(json, "total", &json_total);
		json_object_object_get_ex(json, "count", &json_count);
		json_object_object_get_ex(params, "offset", &json_offset);
		json_object_object_get_ex(json, "items", &json_items);
		if (json_total != NULL && json_count != NULL && json_items != NULL)
		{
			int offset = 0;
			if (json_offset != NULL)
				offset = (int)json_object_get_int(json_offset);
			int total = (int)json_object_get_int(json_total), count = (int)json_object_get_int(json_count);
			if ((offset + count) < total && count > 0)
			{
				struct json_object *tmp = NULL;
				tmp = json_object_new_int(offset + count);
				check_mem(tmp);
				json_object_object_add(params, "offset", tmp);
				struct json_object *next_json = RESTcall(store_id, endpoint, params, payload, payload_size);
				if (next_json != NULL)
				{
					json_object_object_get_ex(next_json, "items", &tmp);
					if (tmp != NULL)
					{
						for (size_t i = 0; i < json_object_array_length(tmp); i++)
						{
							json_object *src_item = json_object_array_get_idx(tmp, i);
							json_object_get(src_item);
							json_object_array_add(json_items, src_item);
						}
					}
					json_object_put(next_json);
				}
			}
		}
		break;
	case PUT_PRODUCT:
		check(HTTPcall(HTTP_PUT, url, payload, payload_size, &response, &response_len) == 0, "Invalid HTTP response.");
		check(response != NULL && response_len > 0, "Invalid HTTP response.");
		response[response_len] = 0;
		json = json_tokener_parse((char *)response);
		check(json != NULL, "Invalid JSON response");
		break;
	case DELETE_PRODUCT:
		check(HTTPcall(HTTP_DELETE, url, payload, payload_size, &response, &response_len) == 0, "Invalid HTTP response.");
		check(response != NULL && response_len > 0, "Invalid HTTP response.");
		response[response_len] = 0;
		json = json_tokener_parse((char *)response);
		check(json != NULL, "Invalid JSON response");
		break;
	case POST_IMAGE:
	case POST_CATEGORY:
	case POST_PRODUCT:
	case POST_ORDER:
		check(HTTPcall(HTTP_POST, url, payload, payload_size, &response, &response_len) == 0, "Invalid HTTP response.");
		check(response != NULL && response_len > 0, "Invalid HTTP response.");
		response[response_len] = 0;
		json = json_tokener_parse((char *)response);
		check(json != NULL, "Invalid JSON response");
		break;
	default:
		sentinel("Endpoint is not implemented yet.");
	}
error:
	if (response != NULL)
		free(response);
	if (url != NULL)
		free(url);
	return json;
}

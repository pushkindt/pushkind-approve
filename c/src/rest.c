#include <json.h>
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <math.h>

#include "ecwid-api.h"
#include "http.h"
#include "rest.h"
#include "dbg.h"

#define REST_URL1 "%s/%lu/%s"
#define REST_URL2 "%s/%lu/%s/%lu"
#define REST_URL3 "%s/%lu/products/%lu/image"

static const char *ENDPOINTS[] = {"profile", "products", "categories", "orders", "products", "products", "products", "categories", "orders", "products"};
static THTTPMethod HTTP_METHODS[] = {HTTP_GET, HTTP_GET, HTTP_GET, HTTP_GET, HTTP_PUT, HTTP_POST, HTTP_POST, HTTP_POST, HTTP_POST, HTTP_DELETE};

/*
 * Function:  RESTcall 
 * --------------------
 * performs a request to the ECWID endpoint
 *
 *  store_id: id of the store to be queried
 *  endpoint: on of [GET_PROFILE,GET_PRODUCTS,GET_CATEGORIES,GET_ORDERS,PUT_PRODUCT,POST_PRODUCT,POST_IMAGE,POST_CATEGORY,POST_ORDER,DELETE_PRODUCT]
 *  params: parameters to be sent via URL
 *  payload: optional payload for POST and PUT
 *  payload_size: size of the payload
 *
 *  returns: JSON object or NULL
 */
struct json_object *RESTcall(uint64_t store_id, TRESTEndpoint endpoint, struct json_object *params, uint8_t *payload, size_t payload_size)
{

	char *url = NULL;
	uint8_t *response = NULL;
	size_t response_len = 0;
	struct json_object *json = NULL;
	int result = -1;
	size_t param_str_len = 0;

	check(endpoint >= GET_PROFILE && endpoint <= DELETE_PRODUCT, "Invalid functions inputs.");

	/*************************************************************************
	* Calculate the length of the URL                                        *
	*************************************************************************/

	if (params != NULL)
	{

		check(json_object_get_type(params) == json_type_object, "Invalid functions inputs.");

		json_object_object_foreach(params, key, val)
		{
			// We add two extra bytes for "=" and "&"
			param_str_len += strlen(key) + strlen((char *)json_object_get_string(val)) + 2;
		}
	}

	param_str_len += strlen(REST_URL) + strlen(ENDPOINTS[endpoint]) + ceil(log10(store_id + 1)) + 1;

	/*************************************************************************
	* Make the URL string                                                    *
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
		param_str_len += strlen(REST_URL1);
		url = calloc(param_str_len, 1);
		check_mem(url);
		result = sprintf(url, REST_URL1, REST_URL, store_id, ENDPOINTS[endpoint]);
		check(result > 0, "Error while constructing url.");
		break;
	case DELETE_PRODUCT:
	case PUT_PRODUCT:
	{
		check(params != NULL, "Invalid functions inputs.");
		json_object *product_id_json = NULL;
		json_object_object_get_ex(params, "productId", &product_id_json);
		check(product_id_json != NULL && json_object_get_type(product_id_json) == json_type_int, "Invalid function inputs.");
		uint64_t product_id = (uint64_t)json_object_get_int64(product_id_json);
		param_str_len += strlen(REST_URL2) + ceil(log10(product_id + 1));
		url = calloc(param_str_len, 1);
		check_mem(url);
		result = sprintf(url, REST_URL2, REST_URL, store_id, ENDPOINTS[endpoint], product_id);
		check(result > 0, "Error while constructing url.");
	}
	break;
	case POST_IMAGE:
	{
		check(params != NULL, "Invalid functions inputs.");
		json_object *product_id_json = NULL;
		json_object_object_get_ex(params, "productId", &product_id_json);
		check(product_id_json != NULL && json_object_get_type(product_id_json) == json_type_int, "Invalid function inputs.");
		uint64_t product_id = (uint64_t)json_object_get_int64(product_id_json);
		param_str_len += strlen(REST_URL3) + ceil(log10(product_id + 1));
		url = calloc(param_str_len, 1);
		check_mem(url);
		result = sprintf(url, REST_URL3, REST_URL, store_id, product_id);
		check(result > 0, "Error while constructing url.");
	}
	break;
	default:
		sentinel("Endpoint is not implemented yet.");
	}

	debug("Predicted length of url and parameters is %zu", param_str_len);

	/*************************************************************************
	* Applying URL parameters                                                *
	*************************************************************************/
	if (params != NULL)
	{
		char *dest = &url[result];
		*dest = '?';
		json_object_object_foreach(params, key, val)
		{
			dest++;
			result = sprintf(dest, "%s=%s", key, (char *)json_object_get_string(val));
			dest = &dest[result];
			*dest = '&';
		}
		*dest = '\0';
	}

	debug("The url after the parameters are applied: %s", url);

	/*************************************************************************
	* Make HTTP call                                                         *
	*************************************************************************/
	THTTPMethod http_method = HTTP_METHODS[endpoint];
	if (http_method == HTTP_GET)
	{
		check(HTTPcall(http_method, url, payload, payload_size, &response, &response_len) == 0, "Invalid HTTP response");
		check(response != NULL && response_len > 0, "Invalid HTTP response.");
		response[response_len] = 0;
		json = json_tokener_parse((char *)response);
		check(json != NULL, "Invalid JSON response");
		struct json_object *json_total = NULL, *json_count = NULL, *json_offset = NULL, *json_items = NULL;
		json_object_object_get_ex(json, "total", &json_total);
		json_object_object_get_ex(json, "count", &json_count);
		json_object_object_get_ex(json, "offset", &json_offset);
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
				bool params_created = false;
				if (params == NULL)
				{
					params = json_object_new_object();
					params_created = true;
				}
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
				if (params_created == true)
				{
					json_object_put(params);
					params = NULL;
				}
			}
		}
	}
	else
	{
		check(HTTPcall(http_method, url, payload, payload_size, &response, &response_len) == 0, "Invalid HTTP response.");
		check(response != NULL && response_len > 0, "Invalid HTTP response.");
		response[response_len] = 0;
		json = json_tokener_parse((char *)response);
		check(json != NULL, "Invalid JSON response");
	}

	debug("The response of size %zu: %s", response_len, response);

error:
	/*************************************************************************
	* Clean everything up                                                    *
	*************************************************************************/
	if (response != NULL)
		free(response);
	if (url != NULL)
		free(url);
	return json;
}

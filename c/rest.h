typedef enum
{
	GET_PROFILE,
	GET_PRODUCTS,
	GET_CATEGORIES,
	GET_ORDERS,
	PUT_PRODUCT,
	POST_PRODUCT,
	POST_IMAGE,
	POST_CATEGORY,
	POST_ORDER,
	DELETE_PRODUCT
} TRESTEndpoint;

extern struct json_object *RESTcall(uint64_t store_id, TRESTEndpoint endpoint, struct json_object *params, uint8_t *payload, size_t payload_size);
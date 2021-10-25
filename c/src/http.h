#include <curl/curl.h>

typedef enum
{
	HTTP_GET,
	HTTP_POST,
	HTTP_PUT,
	HTTP_DELETE
} THTTPMethod;

typedef struct
{
	void *memory;
	size_t size;
} TMemoryStruct;

extern int HTTPcall(THTTPMethod method, const char *url, uint8_t *payload, size_t payload_size, uint8_t **output, size_t *output_size);
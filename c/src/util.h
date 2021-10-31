#define ARRAY_SIZE(arr) (sizeof(arr) / sizeof((arr)[0]))

extern void FilterJSONFields(struct json_object *json, const char *allowed_fields[], size_t allowed_fields_count);

extern char *TrimWhiteSpaces(char *str);
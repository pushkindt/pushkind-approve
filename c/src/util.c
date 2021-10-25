#include <json.h>
#include <stdbool.h>

/*
 * Function:  FilterJSONFields 
 * --------------------
 * removes all keys from the json except for the allowed ones
 *
 *  json: json to work on
 *  allowed_fields: list of allowed keys
 *  allowed_fields_count: size of the list of allowed keys
 *
 *  returns: nothing
 */
void FilterJSONFields(struct json_object *json, const char *allowed_fields[], size_t allowed_fields_count)
{
	/*****************************************************************************/
	//	Loop through json and remove excessive json fields.
	/*****************************************************************************/

	if (json != NULL && allowed_fields != NULL && allowed_fields_count != 0)
	{
		json_object_object_foreach(json, key, val)
		{

			bool found = false;
			for (size_t i = 0; i < allowed_fields_count; i++)
			{
				if (strcmp(key, allowed_fields[i]) == 0)
				{
					found = true;
					break;
				}
			}
			if (found == false)
			{
				if (val != NULL)
				{
					debug("Dropping key %s with value %s", key, json_object_to_json_string(val));
				}
				json_object_object_del(json, key);
			}
		}
	}
}

/*
 * Function:  TrimWhiteSpaces 
 * --------------------
 * trims whitespaces in the beginning and in the end of a string
 * to do so it shifts the string pointer and the zero terminator
 *
 *  str: string to be trimmed
 *
 *  returns: pointer inside the input string or NULL
 */
char *TrimWhiteSpaces(char *str)
{
	char *end = NULL;

	if (str == NULL)
		return NULL;
	while (isspace(*str))
		str++;
	if (*str == 0)
		return NULL;
	end = str + strlen(str) - 1;
	while (end > str && isspace(*end))
		end--;
	*(end + 1) = 0;
	return str;
}
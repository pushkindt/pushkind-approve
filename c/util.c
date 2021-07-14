
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
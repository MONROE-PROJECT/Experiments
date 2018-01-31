/*******************************************************************************
 * Copyright 2017 Leonhard Wimmer
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *  http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *******************************************************************************/

#include "rmbt_json.h"

#include <errno.h>

#include "rmbt_compress.h"

#ifdef HAVE_JSONC

#define IS_JSON_NULL(x)	(json_object_get_type(x) == json_type_null)

rmbt_json rmbt_json_new(void) {
	return json_object_new_object();
}

rmbt_json rmbt_json_new_array(void) {
	return json_object_new_array();
}

void rmbt_json_add_to_array(rmbt_json_array array, rmbt_json object) {
	json_object_array_add(array, object);
}

void rmbt_json_add_object(rmbt_json obj, const char *key, rmbt_json val) {
	json_object_object_add(obj, key, val);
}

void rmbt_json_add_int64(rmbt_json obj, const char *key, int64_t val) {
	json_object_object_add(obj, key, json_object_new_int64(val));
}

void rmbt_json_add_null(rmbt_json obj, const char *key) {
	json_object_object_add(obj, key, NULL);
}

void rmbt_json_add_string(rmbt_json obj, const char *key, const char *val) {
	json_object_object_add(obj, key, json_object_new_string(val));
}

void rmbt_json_add_double(rmbt_json obj, const char *key, double val) {
	json_object_object_add(obj, key, json_object_new_double(val));
}

void rmbt_json_add_bool(rmbt_json obj, const char *key, bool val) {
	json_object_object_add(obj, key, json_object_new_boolean(val));
}

void rmbt_json_add_array(rmbt_json obj, const char *key, rmbt_json_array val) {
	json_object_object_add(obj, key, val);
}

void rmbt_json_get_string_alloc(char **dst, rmbt_json json, const char *key) {
	rmbt_json value;
	if (json_object_object_get_ex(json, key, &value) && !IS_JSON_NULL(value)) {
		*dst = strdup(json_object_get_string(value));
	}
}

void rmbt_json_get_bool(bool *dst, rmbt_json json, const char *key) {
	rmbt_json value;
	if (json_object_object_get_ex(json, key, &value) && !IS_JSON_NULL(value))
		*dst = json_object_get_boolean(value);
}

bool rmbt_json_get_object(rmbt_json *dst, rmbt_json json, const char *key) {
	rmbt_json value;
	if (json_object_object_get_ex(json, key, &value)) {
		*dst = value;
		return true;
	}
	return false;
}

void rmbt_json_get_int_fast16_t(int_fast16_t *dst, rmbt_json json, const char *key) {
	rmbt_json value;
	if (json_object_object_get_ex(json, key, &value) && !IS_JSON_NULL(value))
		*dst = json_object_get_int(value);
}

void rmbt_json_get_int_fast32_t(int_fast32_t *dst, rmbt_json json, const char *key) {
	rmbt_json value;
	if (json_object_object_get_ex(json, key, &value) && !IS_JSON_NULL(value))
		*dst = json_object_get_int(value);
}

uint32_t rmbt_json_array_length(rmbt_json_array array) {
	return (uint32_t)json_object_array_length(array);
}

rmbt_json rmbt_parse_json(const char *str) {
	return json_tokener_parse(str);
}

const char *rmbt_json_to_string(rmbt_json json, bool beautify) {
	return json_object_to_json_string_ext(json, beautify ? JSON_C_TO_STRING_PRETTY : JSON_C_TO_STRING_PLAIN);
}

const char *rmbt_json_array_to_string(rmbt_json_array array, bool beautify) {
	return rmbt_json_to_string(array, beautify);
}

rmbt_json rmbt_json_read_from_file(const char *filename) {
	return json_object_from_file(filename);
}

void rmbt_json_free(rmbt_json json) {
	json_object_put(json);
}

void rmbt_json_free_array(rmbt_json_array array) {
	json_object_put(array);
}

#pragma GCC diagnostic push  // require GCC 4.6
#pragma GCC diagnostic ignored "-Wcast-qual" // json_object_object_foreachC otherwise leads to warnings
void flatten_json(rmbt_json dst, rmbt_json src) {
	if (src == NULL || dst == NULL)
		return;
	struct json_object_iter iter;
	json_object_object_foreachC(src, iter)
	{
		json_object_get(iter.val);
		json_object_object_add(dst, iter.key, iter.val);
	}
}
#pragma GCC diagnostic pop   // require GCC 4.6

#endif /* HAVE_JSONC */

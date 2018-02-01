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

#ifndef SRC_RMBT_JSON_H_
#define SRC_RMBT_JSON_H_

#include "rmbt_common.h"

#ifdef HAVE_JSONC

#include <json.h>
typedef struct json_object *rmbt_json;
typedef struct json_object *rmbt_json_array;

#else

#error need a JSON library

#endif /* HAVE_JSONC */

rmbt_json rmbt_json_new(void);
rmbt_json_array rmbt_json_new_array(void);

void rmbt_json_add_to_array(rmbt_json_array array, rmbt_json object);

void rmbt_json_add_object(rmbt_json obj, const char *key, rmbt_json val);
void rmbt_json_add_int64(rmbt_json obj, const char *key, int64_t val);
void rmbt_json_add_null(rmbt_json obj, const char *key);
void rmbt_json_add_string(rmbt_json obj, const char *key, const char *val);
void rmbt_json_add_double(rmbt_json obj, const char *key, double val);
void rmbt_json_add_bool(rmbt_json obj, const char *key, bool val);
void rmbt_json_add_array(rmbt_json obj, const char *key, rmbt_json_array val);

void rmbt_json_get_string_alloc(char **dst, rmbt_json json, const char *key);

void rmbt_json_get_bool(bool *dst, rmbt_json json, const char *key);

bool rmbt_json_get_object(rmbt_json *dst, rmbt_json json, const char *key);

void rmbt_json_get_int_fast16_t(int_fast16_t *dst, rmbt_json json, const char *key);
void rmbt_json_get_int_fast32_t(int_fast32_t *dst, rmbt_json json, const char *key);

uint32_t rmbt_json_array_length(rmbt_json_array array);

void flatten_json(rmbt_json dst, rmbt_json src);

rmbt_json rmbt_parse_json(const char *str);

const char *rmbt_json_array_to_string(rmbt_json_array array, bool beautify);
const char *rmbt_json_to_string(rmbt_json json, bool beautify);

rmbt_json rmbt_json_read_from_file(const char *filename);

void rmbt_json_free(rmbt_json json);
void rmbt_json_free_array(rmbt_json_array array);

#endif /* SRC_RMBT_JSON_H_ */

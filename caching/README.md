# CacheBase Class

The `CacheBase` class serves as a base class for caching operations. It provides methods for key formatting, getting, setting, deleting, and manipulating cached values. The class also allows for setting a default key prefix.

## Methods

- **\_\_init\_\_(self, cache_alias, key_prefix=None):** Initializes the cache object with the provided cache alias and sets the default key prefix if not already set.

- **\_format_key(self, key):** Formats the cache key based on the key prefix and the provided key.

- **cache_get(self, key):** Retrieves the value associated with the given key from the cache.

- **cache_get_many(self, keys):** Retrieves the values associated with the given keys from the cache.

- **cache_set(self, key, value):** Sets the value associated with the given key in the cache.

- **delete(self, key):** Deletes the value associated with the given key from the cache.

- **delete_many(self, keys):** Deletes the values associated with the given keys from the cache.

- **add(self, key, value):** Adds the value associated with the given key to the cache if it does not already exist.

- **delete_pattern(self, pattern):** Deletes all cache keys matching the given pattern.

- **delete_all(self):** Deletes all cache keys.

- **incr(self, key, delta=1):** Increments the value associated with the given key in the cache by the specified delta.

- **decr(self, key, delta=1):** Decrements the value associated with the given key in the cache by the specified delta.

# NewBadgeCache Subclass

The `NewBadgeCache` subclass extends `CacheBase` and is specifically designed for caching new badges. It sets a longer expiration duration for caching new badges and provides methods for getting and setting new badge data.

## Additional Methods

- **get_new_badge_data(self, user_uuid):** Retrieves new badge data associated with the given user UUID.

- **set_new_badge_data(self, user_uuid, data):** Sets new badge data in the cache associated with the given user UUID.

# SimpleGetCache Subclass

The `SimpleGetCache` subclass extends `CacheBase` and provides a simplified interface for retrieving and caching data. It includes a method for retrieving data from the cache or the database if not found in the cache.

## Additional Methods

- **get_or_set(self, key, data_retrieval_function):** Retrieves data associated with the given key from the cache. If not found, it calls the provided data retrieval function, stores the data in the cache, and returns the data.

# Usage Example

```python
# Create an instance of the NewBadgeCache class
new_badge_cache = NewBadgeCache()

# Get the value associated with a user UUID from the cache
user_uuid = "12345"
data = new_badge_cache.get(user_uuid)

# If the value is not found in the cache, retrieve it from the database and store it in the cache
if data is None:
    data = get_data_from_database(user_uuid)
    new_badge_cache.set(user_uuid, data)

# Delete the value associated with a user UUID from the cache
new_badge_cache.delete(user_uuid)
```

## ModelCacheBase Class

The `ModelCacheBase` class provides a method called 'get' for retrieving model data. It checks the cache first and, if not found, retrieves the data from the database, serializes it, and caches it.

### Method

- **get(self, key, force_db=False, *args, **kwargs):** Retrieves model data from the cache or the database based on the provided key. If 'force_db' is True, the data is retrieved from the database even if it is available in the cache. Additional arguments can be passed to the 'get_from_db' method.

### Flow

1. **Check Cache:** The method first checks if the data is available in the cache by calling the 'cache_get' method.

2. **Retrieve from Database:** If the data is not found in the cache and 'force_db' is False, it calls the 'get_from_db' method to retrieve the data from the database.

3. **Serialize Data:** If the data is found in the database, it serializes the data using the 'serialize' method.

4. **Cache Data:** The serialized data is then cached using the 'cache_set' method.

5. **Return Cached Data:** Finally, the method returns the cached data after converting it to a representation suitable for caching using the 'to_cache_representation' method.

### Outputs

The model data, either retrieved from the cache or the database.

### Usage Example

```python
# Create an instance of the ModelCacheBase class
model_cache = ModelCacheBase()

# Retrieve model data with the key 'my_key'
data = model_cache.get('my_key')
```

# PaginationCache Class

The `PaginationCache` class extends the functionality of the `CacheBase` class by incorporating pagination support. It allows users to retrieve paginated results from the cache based on a given key, page number, page size, and additional arguments. If the paginated results are not found in the cache, it retrieves them from the database using the 'get_from_db' method and stores them in the cache using the 'cache_set' method. The class calculates start and end indices based on the page number and page size to fetch the corresponding subset of results from the 'uuid_list'. For each UUID in the subset, it calls the 'get_item' method to retrieve the actual items and appends them to the result list, which is returned as the final output.

## Inputs

- **key (str):** The key used to retrieve the paginated results from the cache.
- **page_num (int):** The page number of the results to retrieve.
- **page_size (int, optional):** The number of items per page. Defaults to 50.
- **\*args:** Additional positional arguments to be passed to the 'get_from_db' method.
- **\*\*kwargs:** Additional keyword arguments to be passed to the 'get_from_db' method.

## Flow

1. **Validate Parameters:** Validate the 'page_num' and 'page_size' parameters to ensure they are integers greater than or equal to 1.

2. **Check Cache:** Check if the paginated results are already stored in the cache by calling the 'cache_get' method with the given key.

3. **Retrieve from Database if not in Cache:** If the results are not found in the cache, call the 'get_from_db' method with the given key and additional arguments to retrieve them from the database.

4. **Store in Cache:** Store the retrieved results in the cache using the 'cache_set' method.

5. **Calculate Indices:** Calculate the start and end indices based on the page number and page size.

6. **Retrieve Items:** Iterate over the subset of 'uuid_list' from the start to end indices. For each UUID in the subset, call the 'get_item' method to retrieve the actual items.

7. **Build Result List:** Append the retrieved items to the 'result' list.

8. **Return Output:** Return the 'result' list as the final output.

## Outputs

- **list:** A list of paginated results.

## Usage Example

```python
# Create an instance of the PaginationCache class
cache = PaginationCache()

# Retrieve paginated results with the key "my_key", page number 2, page size 10, and additional arguments
results = cache.get("my_key", 2, page_size=10, arg1="value1", arg2="value2")

# Print the retrieved results
print(results)
```
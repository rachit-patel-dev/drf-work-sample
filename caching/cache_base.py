from django.conf import settings
from django.core.cache import cache, caches

DEFAULT_CACHE_ALIAS = "default"


def _get_cache(cache_alias):
    """
    Return the cache object based on the given cache alias.

    Parameters:
    - cache_alias (str): The alias of the cache to retrieve.

    Returns:
    - cache object: The cache object corresponding to the given alias.

    """
    # did this because debug toolbar does not track caches when not using just cache.
    # So, caches["default"] is not tracked
    if cache_alias == DEFAULT_CACHE_ALIAS:
        return cache
    else:
        return caches[cache_alias]


class CacheBase:
    """
    A base class for caching operations.

    Attributes:
    - key_prefix (str): The prefix to be added to cache keys. Defaults to an empty string.
    - cache_alias (str): The alias of the cache to be used. Defaults to the value of DEFAULT_CACHE_ALIAS.
    - single_key (bool): Indicates whether a single key is used for caching. Defaults to False.
    - expire_duration (int): The duration in seconds for which the cache should be valid. Defaults to the value of settings.CACHE_EXPIRATION_DURATION.

    Methods:
    - _set_default_key_prefix(): Sets the default key prefix if not already set.
    - __init__(): Initializes the CacheBase object.
    - _format_key(key): Formats the cache key based on the key prefix and the provided key.
    - _args_format_key_list(*args): Formats a list of cache keys based on the key prefix and the provided keys.
    - cache_get(key): Retrieves the value associated with the given key from the cache.
    - cache_get_many(*args): Retrieves the values associated with the given keys from the cache.
    - cache_set(key, value, expire_duration): Sets the value associated with the given key in the cache.
    - delete(key): Deletes the value associated with the given key from the cache.
    - delete_many(*args): Deletes the values associated with the given keys from the cache.
    - add(key, value): Adds the value associated with the given key to the cache if it does not already exist.
    - delete_pattern(pattern): Deletes all cache keys matching the given pattern.
    - delete_all(): Deletes all cache keys.
    - incr(key, delta): Increments the value associated with the given key in the cache by the specified delta.
    - decr(key, delta): Decrements the value associated with the given key in the cache by the specified delta.
    """

    key_prefix = ""
    cache_alias = DEFAULT_CACHE_ALIAS
    single_key = False
    expire_duration = settings.CACHE_EXPIRATION_DURATION

    @classmethod
    def _set_default_key_prefix(cls):
        if cls.key_prefix == "":
            cls.key_prefix = cls.__name__

    def __init__(self):
        self.cache = _get_cache(self.cache_alias)

        self._set_default_key_prefix()

    def _format_key(self, key):
        if self.single_key:
            return self.key_prefix
        elif isinstance(key, tuple) or isinstance(key, list):
            return f'{self.key_prefix}:{"-".join(str(k) for k in key)}'
        else:
            return f"{self.key_prefix}:{key}"

    def _args_format_key_list(self, *args):
        return [self._format_key(key) for key in args]

    def cache_get(self, key):
        key = self._format_key(key)
        data = self.cache.get(key)
        return data

    def cache_get_many(self, *args):
        if self.single_key:
            return self.get(*args)
        else:
            key_list = self._args_format_key_list(*args)
            result = self.cache.get_many(key_list)
            missing = [key for key in args if self._format_key(key) not in result]
            return result, missing

    def cache_set(self, key, value, expire_duration=None):
        key = self._format_key(key)

        # implicit delete
        if value is None:
            self.delete(key)
        else:
            self.cache.set(key, value, expire_duration or self.expire_duration)

    def delete(self, key):
        key = self._format_key(key)
        self.cache.delete(key)

    def delete_many(self, *args):
        key_list = self._args_format_key_list(*args)
        self.cache.delete_many(key_list)

    def add(self, key, value):
        key = self._format_key(key)
        if not self.get(key):
            self.set(key, value)

    def delete_pattern(self, pattern):
        self.cache.delete_pattern(pattern)

    def delete_all(self):
        pattern = self._format_key("*")
        return self.delete_pattern(pattern)

    def incr(self, key, delta):
        key = self._format_key(key)
        self.cache.incr(key, delta)

    def decr(self, key, delta):
        key = self._format_key(key)
        self.cache.incr(key, -delta)


class NewBadgeCache(CacheBase):
    """
    A class for caching operations related to new badges.

    Inherits from CacheBase.

    Attributes:
    - expire_duration (int): The duration in seconds for which the cache should be valid. Defaults to 60 * 60 * 24 * 30 * 6.

    Methods:
    - get(user_uuid): Retrieves the value associated with the given user UUID from the cache.
    - set(user_uuid, data): Sets the value associated with the given user UUID in the cache.

    """

    expire_duration = 60 * 60 * 24 * 30 * 6

    def get(self, user_uuid):
        return self.cache_get(user_uuid)

    def set(self, user_uuid, data):
        self.cache_set(user_uuid, data)


class SimpleGetCache(CacheBase):
    """
    A class that extends the CacheBase class and provides a simplified interface for retrieving and caching data.

    Attributes:
    - key_prefix (str): The prefix to be added to cache keys. Defaults to an empty string.
    - cache_alias (str): The alias of the cache to be used. Defaults to the value of DEFAULT_CACHE_ALIAS.
    - single_key (bool): Indicates whether a single key is used for caching. Defaults to False.
    - expire_duration (int): The duration in seconds for which the cache should be valid. Defaults to the value of settings.CACHE_EXPIRATION_DURATION.

    Methods:
    - get(key=None, force_db=False, *args, **kwargs): Retrieves the value associated with the given key from the cache. If the value is not found in the cache, it is retrieved from the database and then stored in the cache.
    - delete(key=None): Deletes the value associated with the given key from the cache.

    Inherits from:
    - CacheBase
    """

    def get(self, key=None, force_db=False, *args, **kwargs):
        """
        Retrieves the value associated with the given key from the cache. If the value is not found in the cache, it is retrieved from the database and then stored in the cache.

        Parameters:
        - key (optional): The key to retrieve the value from the cache. If not provided, the default key will be used.
        - force_db (optional): A boolean indicating whether to force retrieving the value from the database instead of the cache. Defaults to False.
        - *args (optional): Additional positional arguments to be passed to the get_from_db method if the value is not found in the cache.
        - **kwargs (optional): Additional keyword arguments to be passed to the get_from_db method if the value is not found in the cache.

        Returns:
        - The value associated with the given key, either from the cache or from the database.

        """
        data = None

        if force_db:
            data = None
        else:
            data = self.cache_get(key)

        if data is None:
            data = self.get_from_db(key, *args, **kwargs)
            self.cache_set(key, data)
        return data

    def delete(self, key=None):
        """
        Deletes the value associated with the given key from the cache.

        Parameters:
        - key (optional): The key to delete the value from the cache. If not provided, the default key will be used.

        Returns:
        - None

        """
        key = self._format_key(key)
        self.cache.delete(key)

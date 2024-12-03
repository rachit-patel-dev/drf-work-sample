from .cache_base import CacheBase


class PaginationCache(CacheBase):
    """
    A class for caching paginated results.

    Inherits from CacheBase.

    Attributes:
    - expire_duration (int): The duration in seconds for which the cache should be valid. Defaults to 60.

    Methods:
    - __init__(): Initializes the PaginationCache object.
    - get_from_db(key, *args, **kwargs): Retrieves paginated results from the database based on the given key and additional arguments.
    - get_item(key): Retrieves a single item from the cache based on the given key.
    - get(key, page_num, page_size=50, *args, **kwargs): Retrieves paginated results from the cache based on the given key, page number, page size, and additional arguments.

    Note:
    - The PaginationCache class extends the functionality of the CacheBase class by adding pagination support.
    - The get_from_db() and get_item() methods need to be implemented in subclasses of PaginationCache.
    """

    expire_duration = 60

    def __init__(self):
        super().__init__()

    def get_from_db(self, key, *args, **kwargs):
        raise NotImplementedError("get_from_db is not implemented.")

    def get_item(self, key):
        raise NotImplementedError("get_item is not implemented.")

    def get(self, key, page_num, page_size=50, *args, **kwargs):
        """
        Retrieves paginated results from the cache based on the given key, page number, page size, and additional arguments.

        Parameters:
        - key (str): The key used to retrieve the paginated results from the cache.
        - page_num (int): The page number of the results to retrieve.
        - page_size (int, optional): The number of items per page. Defaults to 50.
        - *args: Additional positional arguments to be passed to the get_from_db method.
        - **kwargs: Additional keyword arguments to be passed to the get_from_db method.

        Returns:
        - list: A list of paginated results.

        Note:
        - The page_num and page_size parameters are validated to ensure they are integers greater than or equal to 1.
        - If the paginated results are not found in the cache, the get_from_db method is called to retrieve them from the database.
        - The retrieved results are then stored in the cache using the cache_set method.
        - The start and end indices are calculated based on the page number and page size to retrieve the corresponding subset of results from the uuid_list.
        - The get_item method is called for each uuid in the subset to retrieve the actual items.
        - The retrieved items are appended to the result list.
        - The result list is returned as the final output.
        """
        page_num = max(int(page_num), 1)
        page_size = max(int(page_size), 1)

        result = []

        uuid_list = self.cache_get(key)
        if uuid_list is None:
            uuid_list = self.get_from_db(key, *args, **kwargs)
            self.cache_set(key, uuid_list)

        start = page_size * (page_num - 1)
        end = start + page_size
        for uuid in uuid_list[start:end]:
            result.append(self.get_item(uuid))

        return result

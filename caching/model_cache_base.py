from django.db.models.query import QuerySet

from .cache_base import CacheBase


class ModelCacheBase(CacheBase):
    """
    A base class for caching operations on model data.

    Attributes:
    - serializer_class (class): The serializer class to be used for serializing model data.

    Methods:
    - __init__(): Initializes the ModelCacheBase object.
    - get_from_db(key, *args, **kwargs): Retrieves model data from the database based on the given key.
    - get_serializer_class(): Returns the serializer class to be used for serializing model data.
    - get_serializer(data): Returns an instance of the serializer class for the given data.
    - to_cache_representation(obj): Converts the model data to a representation suitable for caching.
    - serialize(data): Serializes the model data using the serializer class.
    - get(key, force_db=False, *args, **kwargs): Retrieves model data from the cache if available, otherwise retrieves it from the database, serializes it, and caches it.
    """

    serializer_class = None

    def __init__(self):
        super(ModelCacheBase, self).__init__()

    def get_from_db(self, key, *args, **kwargs):
        raise NotImplementedError("get_from_db is not implemented.")

    def get_serializer_class(self):
        return self.serializer_class

    def get_serializer(self, data):
        """
        Returns an instance of the serializer class for the given data.

        Parameters:
        - data: The data to be serialized.

        Returns:
        - An instance of the serializer class for the given data.

        Raises:
        - TypeError: If the 'serializer_class' attribute is not defined in the class or the 'get_serializer_class()' method is not overridden.

        Note:
        - If the given data is a QuerySet or a list, the serializer class will be instantiated with the 'many=True' argument.
        - If the given data is not a QuerySet or a list, the serializer class will be instantiated without any additional arguments.
        """
        serializer_class = self.get_serializer_class()
        if serializer_class is None:
            raise TypeError(
                f"{self.__class__.__name__} should either include a 'serializer_class' attribute,"
                "or override the 'get_serializer_class()' method"
            )

        if isinstance(data, QuerySet) or isinstance(data, list):
            return serializer_class(data, many=True)
        else:
            return serializer_class(data)

    def to_cache_representation(self, obj):
        return obj

    def serialize(self, data):
        serializer = self.get_serializer(data)
        serialized_data = serializer.data
        return serialized_data

    def get(self, key, force_db=False, *args, **kwargs):
        """
        Retrieves model data from the cache if available, otherwise retrieves it from the database, serializes it, and caches it.

        Parameters:
        - key: The key used to retrieve the data from the cache or the database.
        - force_db (optional): If True, the data will be retrieved from the database even if it is available in the cache. Default is False.
        - *args, **kwargs (optional): Additional arguments that can be passed to the 'get_from_db' method.

        Returns:
        - The model data, either retrieved from the cache or the database.

        Note:
        - If the data is retrieved from the database, it will be serialized using the 'serialize' method before being cached.
        - If the data is not found in the database, None will be returned.

        Example usage:
        data = model_cache.get('my_key')

        """
        if force_db:
            data = None
        else:
            data = self.cache_get(key)

        if data is None:
            data = self.get_from_db(key, *args, **kwargs)
            if data is None:
                return None
            data = self.serialize(data)
            self.cache_set(key, data)

        return self.to_cache_representation(data)

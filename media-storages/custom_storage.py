from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """
    Custom storage class for managing media files on Amazon S3.

    This class extends the S3Boto3Storage class to provide customized behavior
    for storing and retrieving media files (such as images, videos, etc.) in an
    Amazon S3 bucket. It utilizes the specified AWS storage bucket name and
    designates the 'media' directory as the location for storing the files.

    Attributes:
        bucket_name (str): The name of the AWS S3 bucket where media files are stored.
                        This value is obtained from the `AWS_STORAGE_BUCKET_NAME` setting.

        location (str): The subdirectory within the S3 bucket where media files are stored.
                        By default, this is set to 'media'.

        file_overwrite (bool): A flag indicating whether to allow overwriting existing files
                            with the same name. When set to True, existing files will be
                            overwritten. When set to False, a new unique filename will be
                            generated for each uploaded file to avoid overwrites.

    Note:
        This class assumes that appropriate AWS credentials and settings are configured
        for the application to interact with the specified S3 bucket.

    Example:
        # Create an instance of the MediaStorage class
        media_storage = MediaStorage()

        # Save a media file to the specified location in the S3 bucket
        media_storage.save('path/to/my_image.jpg', ContentFile(image_data))

        # Retrieve the URL for accessing the saved media file
        file_url = media_storage.url('path/to/my_image.jpg')
    """

    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    location = "media"
    file_overwrite = True


class FileAppServices(BaseAppServiceWithAttributeLogger):
    """
    A class that provides file-related services for a file management application.

    This class extends the BaseAppServiceWithAttributeLogger class and is responsible for handling file upload and creation/update operations. It utilizes the FileServices class for additional file-related functionality.

    Attributes:
        file_services (FileServices): An instance of the FileServices class for accessing file-related functionality.
        user_app_service (UserAppServices): An instance of the UserAppServices class for accessing user-related functionality.

    Methods:
        file_upload_s3(file_obj, file_path_within_bucket): Uploads a file to Amazon S3 storage and returns the file URL.
        create_or_update_file_from_file_obj(file_obj, user, file_instance): Creates or updates a file object based on the provided file object, user, and optional file instance.

    Example:
        # Create an instance of the FileAppServices class
        file_app_service = FileAppServices(user_app_service)

        # Upload a file to Amazon S3 storage and get the file URL
        file_url = file_app_service.file_upload_s3(file_obj, file_path_within_bucket)

        # Create or update a file object based on the provided file object and user
        file_obj = file_app_service.create_or_update_file_from_file_obj(file_obj, user, file_instance)
    """

    def __init__(self, user_app_service: UserAppServices) -> None:
        self.file_services = FileServices()
        self.user_app_service = user_app_service

    def file_upload_s3(self, file_obj, file_path_within_bucket: str):
        """
        Uploads a file to Amazon S3 storage and returns the file URL.

        Parameters:
            file_obj: The file object to be uploaded.
            file_path_within_bucket (str): The path of the file within the S3 bucket.

        Returns:
            str: The URL of the uploaded file.

        Example:
            # Create an instance of the FileAppServices class
            file_app_service = FileAppServices(user_app_service)

            # Upload a file to Amazon S3 storage and get the file URL
            file_url = file_app_service.file_upload_s3(file_obj, file_path_within_bucket)
        """
        file_obj_copy = file_obj
        media_storage = MediaStorage()
        media_storage.save(file_path_within_bucket, file_obj_copy)
        file_url = media_storage.url(file_path_within_bucket)
        return file_url

    def create_or_update_file_from_file_obj(
        self, file_obj, user: User, file_instance: File = None
    ) -> File:
        """
        Creates or updates a file object based on the provided file object, user, and optional file instance.

        Parameters:
            file_obj: The file object to be uploaded.
            user (User): The user object associated with the file.
            file_instance (File, optional): An optional existing file instance to be updated. If provided, the file URL will be updated and the instance will be saved.

        Returns:
            File: The created or updated file object.

        Raises:
            FileObjectCreateException: If there is an error creating or updating the file object.

        Example:
            # Create an instance of the FileAppServices class
            file_app_service = FileAppServices(user_app_service)

            # Upload a file to Amazon S3 storage and get the file URL
            file_url = file_app_service.file_upload_s3(file_obj, file_path_within_bucket)

            # Create or update a file object based on the provided file object and user
            file_obj = file_app_service.create_or_update_file_from_file_obj(file_obj, user, file_instance)
        """
        try:
            with transaction.atomic():
                file_path_within_bucket = os.path.join(
                    user.username, f"{get_random_string(15)}_{file_obj.name}"
                )
                file_url = self.file_upload_s3(
                    file_obj=file_obj, file_path_within_bucket=file_path_within_bucket
                )
                if file_instance:
                    file_instance.url = file_url
                    file_instance.save()
                    return file_instance
                file_factory = self.file_services.get_file_factory()
                file_obj = file_factory.build_entity_with_id(
                    uploader=str(user.id), url=file_url
                )
                file_obj.save()

                return file_obj
        except Exception as e:
            raise FileObjectCreateException(
                "file-object-exception", "File is not saved try again.", self.log
            )

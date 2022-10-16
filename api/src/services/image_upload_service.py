from models.image_upload import ImageUpload

class ImageUploadService:
    @staticmethod
    def is_valid_extension(content_type: str) -> bool:
        '''Checks if content_type parameter is a valid file type for image upload

        :param content_type: File type to validate

        :return: True if validation passes, otherwise False
        '''
        return content_type in ImageUpload.ACCEPTED_FORMATS

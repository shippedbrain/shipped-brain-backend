import libs.utilities as utilities
import os

class UserPhotoService:
    @staticmethod
    def get_user_photo_path(username: str) -> str:
        '''Returns the full path for user's photo directory \n
        Photo path should look like "/files/users/<username>/photo/"

        :param username: Username to use for path

        :return: Full user's photo directory path
        '''
        user_photo_path: str = os.path.join('files', 'users', username, 'photo')
        full_user_photo_path = os.path.abspath(path=user_photo_path)

        return full_user_photo_path

    @staticmethod
    def get_user_photo(username: str) -> str:
        '''Returns user's photo in base64 format

        :param username: Username to use for getting content

        :return: Base64 string if photo's directory contains file, else None is returned
        '''
        photo_path = UserPhotoService.get_user_photo_path(username)
        files = os.listdir(photo_path)

        if len(files) > 0:
            return utilities.convert_to_base_64(os.path.join(photo_path, files[0]))
        
        return None
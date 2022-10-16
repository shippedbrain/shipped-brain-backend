import libs.utilities as utilities
import os

class ModelCoverUploadService:
    @staticmethod
    def get_model_cover_photo_path(model_name: str) -> str:
        '''Returns the full path for model's cover photo directory \n
        Cover photo should look like "/files/models/<model_name>/cover/"

        :param model_name: Model name to use for path

        :return: Full model's cover photo directory path
        '''
        model_cover_photo_path: str = os.path.join('files', 'models', model_name, 'cover')
        full_cover_photo_path = os.path.abspath(path=model_cover_photo_path)

        return full_cover_photo_path

    @staticmethod
    def get_model_cover_photo(model_name: str) -> str:
        '''Returns model's cover photo in base64 format

        :param model_name: Model name to use for getting content

        :return: Base64 string if cover photo's directory contains file, else None is returned
        '''
        cover_photo_path = ModelCoverUploadService.get_model_cover_photo_path(model_name)
        files = os.listdir(cover_photo_path)

        if len(files) > 0:
            return utilities.convert_to_base_64(os.path.join(cover_photo_path, files[0]))
        
        return None
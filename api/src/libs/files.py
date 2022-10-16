import os
from zipfile import ZipFile, ZIP_DEFLATED
import logging

class Zipper:

    def __init__(self):
        pass

    @staticmethod
    def zip_dir(path: str = './', zip_file_name: str = 'shipped_brain_project.zip') -> None:
        ''' Zip a whole directory

        :param path: path to directory
        :param zip_file_name: the name of the generated zip file

        :return: void 
        '''
        zipf = ZipFile(zip_file_name, 'w', ZIP_DEFLATED)

        for root, dirs, files in os.walk(path):
            for file in files:
                zipf.write(os.path.join(root, file))

        zipf.close()


    @staticmethod
    def unzip(file_name: str, target_dir: str) -> None:
        '''Unzip file to a target directory

        :param file_name: the name of the zipped file to unzip
        :param target_dir: the target directory to extract the files to

        :return: void
        '''
        with ZipFile(file_name, 'r') as zip: 
             # extracting all the files 
            logging.info(f'Extracting all the files from {file_name}...')
            # zip.printdir()
            zip.extractall(target_dir) 
from fastapi import UploadFile
import os, shutil, glob, base64

def create_dir(dir: str) -> None:
    '''Create directory path recursively

    :param dir: directory path to create

    :return void
    '''
    if os.path.isdir(dir) is False:
        os.makedirs(dir)

def clear_dir(dir: str) -> None:
    '''Clear all files in directory

    :param dir: directory to search files in

    :return void
    '''
    if os.path.isdir(dir):
        files = glob.glob(dir + '/*')

        for file in files:
            os.remove(file)

def save_uploaded_file(dir: str, file: UploadFile) -> None:
    '''Save file upload in specified path

    :param dir: directory to save file to
    :param file: file to save

    :return void
    '''
    with open(os.path.join(dir, file.filename), 'wb') as buffer:
        shutil.copyfileobj(file.file, buffer)

def convert_to_base_64(file_path: str) -> str:
    '''Reads file path and converts its content to base64

    :param file_path: File path to convert

    :return: File in base64 string
    '''
    base64_str = ''

    with open(file_path, 'rb') as file:
        file_name, file_extension = os.path.splitext(file.name)
        base64_str = f'data:{get_mime_type(file_extension)}; base64,' + base64.b64encode(file.read()).decode('utf-8')

    return base64_str

def get_mime_type(file_extension: str) -> str:
    '''Returns MIME type from file extension. \n
    E.g.: When file extension is a .jpg file, "image/jpeg" will be returned

    :param file_extension: File extension to check
    :return: File's MIME type
    '''
    file_extension = file_extension.replace('.', '')
    
    if file_extension in ['jpg', 'jpeg']: return f'image/jpeg'
    if file_extension == 'png': return f'image/png'
    if file_extension == 'gif': return f'image/gif'

    return 'text/html'
import json
import re

USER_PASSWORD_MIN_LENGTH: int = 6

def has_whitespaces(text: str) -> bool:
    ''' Checks if text contains whitespaces

    :param text: Text to validate

    :return: True if text contains whitespaces, otherwise False
    '''

    return text.find(' ') > -1

def trim_whitespaces(text: str) -> str:
    ''' Trims whitespaces from string

    :param text: Text to trim

    :return: Text without whitespaces
    '''

    return f'{text}'.strip()

def strip_html_tags(text: str) -> str:
    ''' Removes HTML tags from string

    :param text: Text to format

    :return: Plain text without HTML tags
    '''

    return re.sub(re.compile('<.*?>'), '', text)

def is_github_repo_valid(url: str) -> bool:
    ''' Validates if GitHub repository's URL is valid

    :param url: URL to validate

    :return: True if URL is valid, otherwise False
    '''
    return re.match(r"(?:(https:\/\/)?github.com\/\w+\/\w+)", url) is not None

def get_friendly_github_url(raw_url: str) -> str:
    ''' Removes "https://" from GitHub URL

    :param raw_url: URL to parse

    :return: URL without "https://"
    '''
    return raw_url.replace('https://', '')

def get_github_raw_files_url(url: str) -> str:
    ''' Returns GitHub's repository file URL.
    E.g.: github.com/<repo_name> is converted to raw.githubusercontent.com/<repo_name>/master

    :param url: GitHub repository's URL

    :return: GitHub repository's file's URL
    '''
    return get_friendly_github_url(url).replace('github.com', 'raw.githubusercontent.com') + '/master'

def get_github_readme_url(url: str) -> str:
    ''' Returns GitHub's repository README.md URL.

    :param url: GitHub repository's URL

    :return: GitHub repository's file's URL
    '''
    return f'{get_github_raw_files_url(url)}/README.md'
    
def is_valid_json(data: str) -> bool:
    ''' Validates if string data can be successfully parsed to JSON

    :param data: String data to validate

    :return: True if validation passes, otherwise False
    '''
    try:
        json.loads(data)
    except:
        return False

    return True

def is_email_valid(email: str) -> bool:
    ''' Checks if email address is valid

    :param email: Email to validate

    :return: True if email is valid, otherwise False
    '''
    return re.match(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", email) is not None

def is_password_valid(password: str) -> bool:
    f''' Checks if password length has at least {USER_PASSWORD_MIN_LENGTH} characters

    :param password: Password to validate

    :return: True if validation passes, otherwise False
    '''
    return len(password) >= USER_PASSWORD_MIN_LENGTH

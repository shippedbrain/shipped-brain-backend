from models.model_request import ModelRequest
from models.registered_model import RegisteredModel
from models.model_version import ModelVersion
from models.user import User
from models.hashtag import Hashtag
from typing import Dict, List


def format_model_list(model_list_raw):
    '''Takes in raw model list from sqlalchemy and returns list with properly formatted dictionaries

    :param model_list_raw: raw model list from sqlalchemy

    :return formatted list of models
    '''

    results = []

    if model_list_raw is not None:
        for result in model_list_raw:
            model = format_registered_model(result)
            results.append(model)

    return results


def format_registered_model(model_raw: RegisteredModel):
    '''Takes in raw registered model from sqlalchemy and returns formatted dictionary

    :param model_raw: raw model from sqlalchemy

    :return formatted model
    '''

    registered_model = {
        'name': model_raw.name,
        'creation_time': model_raw.creation_timestamp,
        'last_updated_time': model_raw.last_updated_timestamp,
        'description': model_raw.description,
        'latest_versions': model_raw.latest_versions,
        'tags': model_raw.tags
    }

    registered_model['versions'] = []

    if len(registered_model['latest_versions']) > 0:
        for model_version in registered_model['latest_versions']:
            version = format_model_version(model_version)

            registered_model['versions'].append(version)

    registered_model.pop('latest_versions')

    return registered_model


def format_model_version(model_version_full: ModelVersion):
    '''Takes in raw model version from sqlalchemy and returns formatted dictionary, including user

    :param model_version_full:

    :return formatted model version
    '''

    model_version = {
        'description': model_version_full.description,
        'name': model_version_full.name,
        'user_id': model_version_full.user_id,
        'version': model_version_full.version
    }

    try:
        if model_version_full.creation_time is not None:
            model_version['creation_time'] = model_version_full.creation_time
    except:
        model_version['creation_time'] = model_version_full.creation_timestamp

    try:
        if model_version_full.last_updated_time is not None:
            model_version['last_updated_time'] = model_version_full.last_updated_time
    except:
        model_version['last_updated_time'] = model_version_full.last_updated_timestamp

    return model_version


def format_user(user_raw: User):
    return {
        'name': user_raw.name,
        'username': user_raw.username,
        'email': user_raw.email,
        'description': user_raw.description,
        'created_at': user_raw.created_at,
        'updated_at': user_raw.updated_at,
        'models_count': user_raw.models_count if user_raw.models_count is not None else None,
        'model_versions_count': user_raw.model_versions_count if user_raw.model_versions_count is not None else None,
        'photo': ''
    }


def format_model_request(model_request_raw: ModelRequest):
    return {
        'id': model_request_raw.id,
        'title': model_request_raw.title,
        'description': model_request_raw.description,
        'status': model_request_raw.status,
        'prize': model_request_raw.prize,
        'input_data': model_request_raw.input_data,
        'output_data': model_request_raw.output_data,
        'requested_by': model_request_raw.requested_by,
        'fulfilled_by': model_request_raw.fulfilled_by,
        'fulfilled_at': model_request_raw.fulfilled_at,
        'created_at': model_request_raw.created_at,
        'updated_at': model_request_raw.updated_at,
        'user_requested_by': dict(),
        'user_fulfilled_by': dict(),
        'is_recent': False
    }


def format_hashtag_list(hashtag_list: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    ''' Format hashtag list - group by key

    :param hashtag_list: a list of Hashtag dicts (Hashtag.to_json())

    :return: a dict grouped by Hashtag keys
    '''
    hashtags_format = {
        'categories': [],
        'hashtags': []
    }

    for hashtag in hashtag_list:
        # key: category
        if hashtag['key'] == Hashtag.CATEGORY:
            hashtags_format['categories'].append(hashtag)
        # key: hashtag
        elif hashtag['key'] == Hashtag.HASHTAG:
            hashtags_format['hashtags'].append(hashtag)

    return hashtags_format

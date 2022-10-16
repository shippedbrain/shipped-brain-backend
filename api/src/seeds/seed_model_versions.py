from os import name
from models.model_version import ModelVersion
from services.model_version_service import ModelVersionService
from datetime import datetime

def seed_model_versions():
    try:
        elastic_net = ModelVersion(name = 'ElasticNet', version = 1, creation_time = datetime.timestamp(datetime.now()), last_updated_time = datetime.timestamp(datetime.now()), description = 'ElasticNet description', user_id = 'atlas', current_stage = '', source = '', run_id = '', status = '', status_message = '', run_link = '')
        
        gpt_3 = ModelVersion(name = 'GPT-3', version = 1, creation_time = datetime.timestamp(datetime.now()), last_updated_time = datetime.timestamp(datetime.now()), description = 'GPT-3 description', user_id = 'atlas', current_stage = '', source = '', run_id = '', status = '', status_message = '', run_link = '')

        gpt_3_v2 = ModelVersion(name = 'GPT-3', version = 2, creation_time = datetime.timestamp(datetime.now()), last_updated_time = datetime.timestamp(datetime.now()), description = 'GPT-3 description v2', user_id = 'atlas', current_stage = '', source = '', run_id = '', status = '', status_message = '', run_link = '')

        print('-' * 20 + '\n')
        print('MODEL VERSIONS SEED')
        print('-' * 20 + '\n')

        print('*' * 20 + '\n')
        print('ELASTICNET v1: ', ModelVersionService.create_model_version(model_version = elastic_net).to_dict())
        print('*' * 20 + '\n')
        print('GPT-3 v1: ', ModelVersionService.create_model_version(model_version = gpt_3).to_dict())
        print('*' * 20 + '\n')
        print('GPT-3 v2: ', ModelVersionService.create_model_version(model_version = gpt_3_v2).to_dict())
        print('*' * 20 + '\n')

        return True
    except:
        return False
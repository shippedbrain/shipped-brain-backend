from db.db_config import session
from models.hashtag import Hashtag
from models.user_hashtag import UserHashtag
from models.model_hashtag import ModelHashtag
from models.result import Result
from models.user import User
from models.registered_model import RegisteredModel
from models.registered_model_tag import RegisteredModelTag


class HashtagService:

    @staticmethod
    def create_hashtag(key: str, value: str) -> Result:
        ''' Create a hashtag record

        :param value: a hashtag key
        :param key: a hashtag value

        :return: a Result object
                 on success Result.data is Hashtag; otherwise None
        '''
        try:
            hashtag = Hashtag(key=key, value=value)
            session.add(hashtag)
            session.commit()

            return Result(
                Result.SUCCESS,
                f'Successfully created hashtag with key {key} and value {value}',
                {
                    'id': hashtag.id,
                    'key': key,
                    'value': value
                }
            )
        except Exception:
            return Result(
                Result.FAIL,
                f'Failed to create hashtag with key {key} and value {value}',
                Result.EXCEPTION
            )

    @staticmethod
    def get_or_create_hashtag(key: str, value: str) -> Result:
        ''' Get or creates hashtag with given key and value

        :param value: a hashtag key
        :param key: a hashtag value

        :return: a Result object
                 on success Result.data is Hashtag; otherwise None
        '''
        try:
            hashtag = session.query(Hashtag).filter_by(key=key, value=value).first()
            # create if not exists
            if hashtag is None:
                create_hashtag_result = HashtagService.create_hashtag(key, value)
                if create_hashtag_result.is_fail():
                    return create_hashtag_result

                return Result(
                    Result.SUCCESS,
                    create_hashtag_result.message,
                    create_hashtag_result.data
                )

            return Result(
                Result.SUCCESS,
                f'Successfully fetched hashtag with key {key} and value {value}',
                {
                    'id': hashtag.id,
                    'key': hashtag.key,
                    'value': hashtag.value
                }
            )
        except Exception:
            return Result(
                Result.FAIL,
                f'Failed to get or create hashtag with key {key} and value {value}',
                Result.EXCEPTION
            )

    @staticmethod
    def add_user_hashtag(user_id: int, value: str, key: str = Hashtag.HASHTAG) -> Result:
        ''' Adds hashtag to existing user

        :param user_id: a user id
        :param value: a hashtag key
        :param key: a hashtag value

        :return: a Result object
                 on success Result.data is UserHashtag; otherwise None
        '''
        fail_message = f'Failed to create user hashtag with key {key} and value {value}'
        fail_result = Result(
            Result.FAIL,
            fail_message,
            Result.EXCEPTION
        )

        try:
            hashtag_result = HashtagService.get_or_create_hashtag(key, value)
            if hashtag_result.is_fail():
                return fail_result

            hashtag = hashtag_result.data

            # Check if user already has hashtag
            user_hashtags = HashtagService.get_user_hashtags(user_id)
            if hashtag not in user_hashtags.data:
                user_hashtag = UserHashtag(user_id=user_id, hashtag_id=hashtag['id'])
                session.add(user_hashtag)
                session.commit()

            return Result(
                Result.SUCCESS,
                f'Successfully created user hashtag with key hashtag and value {value}',
                {
                    'key': key,
                    'value': value
                }
            )
        except Exception:
            return Result(
                Result.FAIL,
                fail_message,
                Result.EXCEPTION
            )

    @staticmethod
    def add_model_hashtag(model_name: str,
                          value: str,
                          key: str = Hashtag.HASHTAG) -> Result:
        ''' Adds hashtag to existing model

        :param model_name: a model name
        :param value: a hashtag key
        :param key: a hashtag value

        :return: a Result object
                 on success Result.data is ModelHashtag; otherwise None
        '''
        fail_message = f'Failed to create model hashtag with key {key} and value {value}'
        fail_result = Result(
            Result.FAIL,
            fail_message,
            Result.EXCEPTION
        )

        try:
            hashtag_result = HashtagService.get_or_create_hashtag(key, value)
            if hashtag_result.is_fail():
                return fail_result

            hashtag = hashtag_result.data

            # Check if model already has hashtag
            model_hashtags = HashtagService.get_model_hashtags(model_name)
            if hashtag not in model_hashtags.data:
                model_hashtag = ModelHashtag(model_name=model_name, hashtag_id=hashtag['id'])
                session.add(model_hashtag)
                session.commit()

            return Result(
                Result.SUCCESS,
                f'Successfully created model hashtag with key hashtag and value {value}',
                {
                    'key': key,
                    'value': value
                }
            )
        except Exception:
            return fail_result

    @staticmethod
    def get_hashtags(key: str,
                     value: str = None,
                     offset: int = 0, limit: int = 100) -> Result:
        ''' Get hashtags with given key and value, paginated

        :param key: the hashtag key
        :param value: the hashtag value, if None gets all
        :param offset: the query offset
        :param limit: the query limit

        :return: a Result object, on success Result.data is a collection of Hashtag dicts
        '''
        try:
            query_params = {'key': key} if value is None else {'key': key, 'value': value}
            hashtags = session.query(Hashtag).filter_by(**query_params).offset(offset).limit(limit)
            hashtags_as_dicts = [h.to_dict() for h in hashtags]

            return Result(
                Result.SUCCESS,
                f'Successfully fetched hashtags.',
                hashtags_as_dicts
            )
        except Exception:
            return Result(
                Result.FAIL,
                f'Failed to get hashtags with key {key} and value {value}',
                Result.EXCEPTION
            )

    @staticmethod
    def get_user_hashtags(user_id: int,
                          hashtag_id: str = None) -> Result:

        ''' Get user hashtags with given key and value

        :param user_id: the user_id
        :param hashtag_id: the hashtag id

        :return: a Result object, on success Result.data is a collection of Hashtag dicts
        '''
        try:
            query_params = {'user_id': user_id} if hashtag_id is None else {'user_id': user_id,
                                                                            'hashtag_id': hashtag_id}
            user_hashtags = session.query(UserHashtag).filter_by(**query_params).all()
            hashtags = []
            for user_hashtag in user_hashtags:
                hashtag = session.query(Hashtag).get(user_hashtag.hashtag_id)
                hashtags.append(hashtag.to_dict())

            return Result(
                Result.SUCCESS,
                f'Successfully fetched user hashtags.',
                hashtags
            )
        except Exception:
            return Result(
                Result.FAIL,
                f'Failed to get hashtags',
                Result.EXCEPTION
            )

    @staticmethod
    def get_model_hashtags(model_name: str) -> Result:
        ''' Get model hashtags with given key and value

        :param model_name: the name of the model

        :return: a Result object, on success Result.data is a collection of Hashtag dicts
        '''
        try:
            query_params = {'model_name': model_name}
            model_hashtags = session.query(ModelHashtag).filter_by(**query_params).all()
            hashtags = []
            for model_hashtag in model_hashtags:
                hashtag = session.query(Hashtag).get(model_hashtag.hashtag_id)
                hashtags.append(hashtag.to_dict())

            return Result(
                Result.SUCCESS,
                f"Successfully fetched hashtags for model with name '{model_name}'.",
                hashtags
            )
        except Exception:
            return Result(
                Result.FAIL,
                f"Failed to get hashtags for model with name '{model_name}'.",
                Result.EXCEPTION
            )

    @staticmethod
    def get_models_with_hashtag(hashtag_id: int) -> Result:
        ''' Get models with query hashtag

        :param hashtag_id: Hashtag id
        :return: a Result object
                 on success Result.data is List[RegisteredModel]; None otherwise
        '''

        try:
            hashtag = session.query(Hashtag).filter_by(id=hashtag_id).first()
            model_hashtags = session.query(ModelHashtag).filter_by(hashtag_id=hashtag_id).all()

            model_list = []
            for model_h in model_hashtags:
                model = session.query(RegisteredModel) \
                    .filter_by(name=model_h.model_name) \
                    .order_by(RegisteredModel.name).first()

                model_list.append(model)

            return Result(
                Result.SUCCESS,
                f'Successfully fetched models with hashtag key {hashtag.key} and value {hashtag.value}',
                model_list
            )
        except Exception:
            return Result(
                Result.FAIL,
                f'Failed to get models with hashtag key or value',
                Result.EXCEPTION
            )

    @staticmethod
    def get_users_with_hashtag(key: str, value: str) -> Result:
        ''' Get models with query hashtag
        
        :param key: a Hashtag key
        :param value: a Hashtag value
        :return: a Result object
                 on success Result.data is List[User]; None otherwise
        '''

        try:
            hashtag = session.query(Hashtag).filter_by(key=key, value=value).first()
            user_hashtags = session.query(UserHashtag).filter_by(hashtag_id=hashtag.id).all()
            users = []
            for user_h in user_hashtags:
                user = session.query(User).get(user_h.user_id)
                users.append(user)

            return Result(
                Result.SUCCESS,
                'Successfully fetched users with key {key} and value {value}',
                users
            )

        except Exception:
            return Result(
                Result.FAIL,
                f'Failed to get users with hashtag key {key} and value {value}',
                Result.EXCEPTION
            )

    @staticmethod
    def get_hashtags_from_user_models(username: str) -> Result:
        ''' Get hashtags from models owned by a specific user

        :param username: model owner's username

        :return: Result object
        '''

        hashtags = []
        try:
            query_result = session.query(RegisteredModelTag, Hashtag) \
                .filter(RegisteredModelTag.key == "user_id", RegisteredModelTag.value == username) \
                .join(ModelHashtag, (ModelHashtag.model_name == RegisteredModelTag.name))\
                .join(Hashtag, (Hashtag.id == ModelHashtag.hashtag_id)) \
                .all()

            # Extract hashtags
            for qr in query_result:
                hashtags.append(qr[1])

            return Result(
                Result.SUCCESS,
                'Successfully fetched hashtags',
                hashtags
            )
        except Exception as e:
            print(f"[EXCEPTION] Failed to get hashtags from user's models. Error {e}")
            return Result(
                Result.FAIL,
                "Failed to get hashtags from user's models.",
                Result.EXCEPTION
            )

    @staticmethod
    def delete_hashtag(hashtag_id: int) -> Result:
        ''' Delete a hashtag from the system

        :param hashtag_id: the hashtag's id

        :retrun: Result with message, Result.data i None
        '''
        try:
            session.query(Hashtag).filter_by(id=hashtag_id).delete()
            session.commit()

            return Result(
                Result.SUCCESS,
                f'Successfully deleteted hashtag with id {hashtag_id}'
            )
        except Exception:
            return Result(
                Result.FAIL,
                f'Failed to delete hashtag with id {hashtag_id}',
                Result.EXCEPTION
            )

    @staticmethod
    def delete_user_hashtag(user_id: int, hashtag_id: int) -> Result:
        ''' Delete user hashtag

        :param user_id: the user's id
        :param hashtag_id: the hashtag's id

        :retrun: Result with message, Result.data i None
        '''
        try:
            session.query(UserHashtag).filter_by(user_id=user_id, hashtag_id=hashtag_id).delete()
            session.commit()

            return Result(
                Result.SUCCESS,
                f'Successfully deleteted user hashtag with id {hashtag_id}'
            )
        except Exception:
            return Result(
                Result.FAIL,
                f'Failed to delete user hashtag with id {hashtag_id}',
                Result.EXCEPTION
            )

    @staticmethod
    def delete_model_hashtag(model_name: str, hashtag_id: int) -> Result:
        ''' Delete model hashtag

        :param model_name: the name of the model
        :param hashtag_id: the hashtag's id

        :return: Result with message, Result.data i None
        '''
        try:
            session.query(ModelHashtag).filter_by(hashtag_id=hashtag_id, model_name=model_name).delete()
            session.commit()

            return Result(
                Result.SUCCESS,
                f'Successfully deleteted model hashtag with id {hashtag_id}'
            )
        except Exception:
            return Result(
                Result.FAIL,
                f'Failed to delete model hashtag with id {hashtag_id}',
                Result.EXCEPTION
            )

    @staticmethod
    def search_models_with_hashtag(hashtag_value: str) -> Result:
        ''' Searches for model with hashtag matching at least partially the given value

        :param hashtag_value: hashtag value to search for

        :return: Result 'success' with message & data if successful, else Result 'fail' with message
        '''
        try:
            query_results = session.query(Hashtag, ModelHashtag, RegisteredModelTag) \
                .join(ModelHashtag, ModelHashtag.hashtag_id == Hashtag.id) \
                .join(RegisteredModelTag, (RegisteredModelTag.name == ModelHashtag.model_name)) \
                .filter(Hashtag.value.ilike(f'%{hashtag_value}%')) \
                .all()

            results = []
            for index, result in enumerate(query_results):
                # Check if hashtag already exists in results list
                found_hashtag_index = next((i for i, item in enumerate(results) if item.id == result[0].id), None)

                # If hashtag was found, append model to it
                if found_hashtag_index is not None:
                    results[found_hashtag_index].hashtag_models.append(result[2])
                else:
                    # If hashtag was not found, create new hashtag and append model to it
                    hashtag = result[0]
                    hashtag.hashtag_models = []
                    hashtag.hashtag_models.append(result[2])

                    results.append(hashtag)

            return Result(
                Result.SUCCESS,
                f'Successfully retrieved models matching category {hashtag_value}',
                results
            )
        except Exception:
            return Result(
                Result.FAIL,
                f'Failed to retrieve models with category matching {hashtag_value}',
                Result.EXCEPTION
            )

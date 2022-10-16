from db.db_config import session
from models.user_social_network import UserSocialNetwork
from models.result import Result
import logging

class SocialNetworkService:
    
    @staticmethod
    def get_user_social_network_by_id(user_id: int, social_network_id: int) -> Result:
        try:
            query_result = session.query(UserSocialNetwork).filter_by(user_id=user_id, social_network=social_network_id).all()
            return Result(
                Result.SUCCESS, 
                'Successfully collect social network for user.', 
                query_result
            )
        except Exception:
            return Result(
                Result.FAIL,
                'Failed to get social network for user.',
                Result.EXCEPTION
            )

    @staticmethod
    def add_social_network_by_user(user_id: int, social_network: str, link: str) -> Result:
        ''' Adds social_network to existing user

        :param user_id: a user id
        :param social_network: a social_network key
        :param link: the link to the social network

        :return: a Result object
                 on success Result.data is UserSocialNetwork; otherwise None
        '''
        fail_message = f'Failed to create user social_network with key {social_network} and link {link}'
        try:
            if social_network not in UserSocialNetwork.SOCIAL_NETWORKS:
                return Result(
                    Result.FAIL,
                    'Social network name is not valid',
                    Result.NOT_ACCEPTABLE
                )

            # Get social network id
            social_network_id = UserSocialNetwork.get_social_network_id(social_network)
            
            # Check if user already has social_network
            get_social_network_result = SocialNetworkService.get_user_social_network_by_id(user_id, social_network_id)
            if get_social_network_result.is_fail():
                return get_social_network_result
            elif len(get_social_network_result.data) == 0:
                user_social_network = UserSocialNetwork(user_id=user_id, social_network=social_network_id, link=link)
                session.add(user_social_network)
                session.commit()
            else:
                user_social_network = get_social_network_result.data[0]

            return Result(
                Result.SUCCESS,
                f'Successfully created user social network {social_network} with link {link}', 
                user_social_network.to_dict()
            )
        except Exception:
            return Result(
                Result.FAIL, 
                fail_message,
                Result.EXCEPTION
            )

    @staticmethod
    def update_social_network_by_user(user_id: int, social_network: str, link: str) -> Result:
        ''' Update social network's link for user

        :param user_id: a user id
        :param social_network: a social_network key
        :param link: the link to the social network

        :return: a Result object
                 on success Result.data is UserSocialNetwork; otherwise None
        '''
        try:
            if social_network not in UserSocialNetwork.SOCIAL_NETWORKS:
                return Result(
                    Result.FAIL, 
                    'Social network name is not valid',
                    Result.NOT_ACCEPTABLE
                )

            # Get social network id
            social_network_id = UserSocialNetwork.get_social_network_id(social_network)
            
            # Check if user already has social_network
            get_social_network_result = SocialNetworkService.get_user_social_network_by_id(user_id, social_network_id)
            if get_social_network_result.is_fail():
                return get_social_network_result
            elif len(get_social_network_result.data) == 1:
                user_social_network = get_social_network_result.data[0]
                user_social_network.link = link
                session.commit()
            else:
                return Result(
                    Result.FAIL, 
                    f'Failed to update link for user social network {social_network}. User does not have social network reference.',
                    Result.NOT_FOUND
                )

            return Result(
                Result.SUCCESS,
                f'Successfully updated user social network {social_network} with link {link}', 
                user_social_network.to_dict()
            )
        except Exception:
            return Result(
                Result.FAIL, 
                f'Failed to update link for user social network {social_network}'
            )              

    @staticmethod
    def get_social_networks_by_user_id(user_id: int) -> Result:
        ''' Get user social networks with given key and value

        :param user_id: the user_id
        :param social_network_id: the social_network id

        :return: a Result object, on success Result.data is a collection of SocialNetwork dicts
        '''

        try:
            user_social_networks_result = session.query(UserSocialNetwork).filter_by(user_id=user_id).all()
            social_networks = []
            for record in user_social_networks_result:
                social_networks.append(record.to_dict())
            return Result(
                Result.SUCCESS,
                f'Successfully fetched user social networks.',
                social_networks
            )
        except Exception:
            return Result(Result.FAIL, 
            f'Failed to get social networks',
            Result.EXCEPTION
        )
    
    @staticmethod
    def delete_social_network_by_user_id(user_id:int, social_network: str) -> Result:
        ''' Delete user's social network

        :param user_id: the user's id
        :param social_network: the social_network to delete

        :retrun: Result with message, Result.data i None
        '''
        try:
            if social_network not in UserSocialNetwork.SOCIAL_NETWORKS:
                return Result(
                    Result.FAIL, 
                    'Social network name is not valid',
                    Result.NOT_ACCEPTABLE
                )

            # Get social network id
            social_network_id = UserSocialNetwork.get_social_network_id(social_network)
            
            # Check if user already has social_network
            get_social_network_result = SocialNetworkService.get_user_social_network_by_id(user_id, social_network_id)
            if get_social_network_result.is_fail():
                return get_social_network_result
            elif len(get_social_network_result.data) == 1:
                session.delete(get_social_network_result.data[0])
                session.commit()
            else:
                return Result(
                    Result.FAIL, 
                    f'Failed to delete user social network {social_network}. User does not have social network reference.',
                    Result.NOT_FOUND
            )

            return Result(
                Result.SUCCESS, 
                f'Successfully deleteted user social network {social_network}'
            )
        except Exception:
            return Result(
                Result.FAIL, 
                f'Failed to delete user social network {social_network}'
            )

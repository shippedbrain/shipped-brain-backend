from sqlalchemy import Column, Integer, String, ForeignKey
from db.db_config import Base
from models.user import User
from typing import Optional, Dict, Any

class UserSocialNetwork(Base):
    __tablename__ = 'user_social_networks'
    
    FACEBOOK = 'facebook'
    TWITTER = 'twitter'
    LINKEDIN = 'linkedin'
    GITHUB = 'github'
    GITLAB = 'gitlab'

    SOCIAL_NETWORKS = [FACEBOOK, TWITTER, LINKEDIN, GITHUB, GITLAB]
    SOCIAL_NETWORKS_ID = {i: sn for i, sn in enumerate(SOCIAL_NETWORKS)}
    SOCIAL_NETWORKS_STR = {sn: i for i, sn in enumerate(SOCIAL_NETWORKS)}
    
    # Columns
    user_id = Column(Integer, ForeignKey(User.id, ondelete='CASCADE'), primary_key=True, nullable=False)
    social_network = Column(Integer, primary_key=True, nullable=True)
    link = Column(String(256), nullable=True)

    @staticmethod
    def get_social_network_id(social_network: str) -> Optional[int]:
        return UserSocialNetwork.SOCIAL_NETWORKS_STR.get(social_network)

    @staticmethod
    def get_social_network_name(social_network: int) -> Optional[str]:
        return UserSocialNetwork.SOCIAL_NETWORKS_ID.get(social_network)

    def to_dict(self, social_network_name: bool=True) -> Dict[str, Any]:
        ''' Return object as dict

        :param social_network_name: if True returns name of social network, id otherwise

        :return: a dict. 
        '''
        social_network = UserSocialNetwork.get_social_network_name(self.social_network) if social_network_name else self.social_network
        return {'social_network': social_network,
                'link': self.link,
                'user_id': self.user_id
        }
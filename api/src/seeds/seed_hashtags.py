from services.hashtag_service import HashtagService
from models.hashtag import Hashtag

def seed_hashtags():
    try:
        HashtagService.create_hashtag(Hashtag.CATEGORY, 'Computer Vision')
        HashtagService.create_hashtag(Hashtag.CATEGORY, 'Natural Language Processing')
        HashtagService.create_hashtag(Hashtag.CATEGORY, 'Generative Models')
        HashtagService.create_hashtag(Hashtag.CATEGORY, 'Reinforcement Learning')
        HashtagService.create_hashtag(Hashtag.CATEGORY, 'Unsupervised Learning')
        HashtagService.create_hashtag(Hashtag.CATEGORY, 'Audio and Speech')
        HashtagService.create_hashtag(Hashtag.CATEGORY, 'Text Generation')

        return True
    except:
        return False
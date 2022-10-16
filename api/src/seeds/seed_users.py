import schemas.user as UserSchema
from services.user_service import UserService

def create_seed_users():
    try:
        users = list()

        users.append(UserSchema.UserCreate(
            name = 'Diogo Pinto',
            username = 'diogo',
            email = 'diogo@shippedbrain.com',
            description = '<p>Far far away, behind the word mountains, far from the countries Vokalia and Consonantia, there live the blind texts. <br>Separated they live in Bookmarksgrove right at the coast of the Semantics, a large.</p>',
            password = '123456'))

        users.append(UserSchema.UserCreate(
            name = 'Bernardo Lemos Costa',
            username = 'blc',
            email = 'bernardo@shippedbrain.com',
            description = '<p>A wonderful serenity has taken possession of my entire soul, like these sweet mornings of spring which I enjoy with my whole heart. <br>I am alone, and feel the charm of existence in this spot, which was.</p>',
            password = '123456'))

        users.append(UserSchema.UserCreate(
            name = 'José Medeiros',
            username = 'joseprsm',
            email = 'jose@shippedbrain.com',
            description = '<p>One morning, when Gregor Samsa woke from troubled dreams, he found himself transformed in his bed into a horrible vermin. <br>He lay on his armour-like back, and if he lifted his head a little he could se</p>',
            password = '123456'))

        for user in users:
            UserService.create_user(user)

        return True
    except:
        return False
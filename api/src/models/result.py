from typing import Union, Optional
from fastapi import status

# TODO move to schemas
class Result:
    BAD_REQUEST: str = 'bad_request'
    UNAUTHORIZED: str = 'unauthorized'
    FORBIDDEN: str = 'forbidden'
    NOT_FOUND: str = 'not_found'
    NOT_ACCEPTABLE: str = 'not_acceptable'
    EXCEPTION: str = 'exception'
    SUCCESS: str = 'success'
    FAIL: str = 'fail'

    class Success:
        def __init__(self):
            pass
    
    class Fail:
        def __init__(self):
            pass
    
    @staticmethod
    def __create_status(status: Union[Success, Fail, str]) -> Optional[Union[Success, Fail]]:
        ''' Create a status object of class Fail or Success

        :param status: a valid status string, case insensitive, or status object
                        value must be: 'success' or 'fail'

        :return: a status object Fail or Result, None if exception is raised 
        '''
        if type(status) is Result.Success or type(status) is Result.Fail:
            return status

        status_cleaned = status.strip().lower()
        if status_cleaned == 'fail':
            return Result.Fail()
        elif status_cleaned == 'success':
            return Result.Success()
        else:
            raise ValueError(f"Bad status value '{status}'. Valid values are: 'success' and 'fail', case insensitive.")
        
    def __init__(self, status: Union[Success, Fail, str], message: str, data: Optional[Union[dict, str]] = None):
        self.status = Result.__create_status(status)
        self.message = message
        self.data = data

    def is_success(self) -> bool:
        return type(self.status) is Result.Success

    def is_fail(self) -> bool:
        return type(self.status) is Result.Fail

    def get_status_code(self) -> status:
        ''' Returns FastAPI's status code based on Result's status
        '''
        
        if self.data == Result.BAD_REQUEST: return status.HTTP_400_BAD_REQUEST
        if self.data == Result.UNAUTHORIZED: return status.HTTP_401_UNAUTHORIZED
        if self.data == Result.FORBIDDEN: return status.HTTP_403_FORBIDDEN
        if self.data == Result.NOT_FOUND: return status.HTTP_404_NOT_FOUND
        if self.data == Result.NOT_ACCEPTABLE: return status.HTTP_406_NOT_ACCEPTABLE
        if self.data == Result.EXCEPTION: return status.HTTP_500_INTERNAL_SERVER_ERROR

    def to_dict(self):
        status = 'success' if self.is_success() else 'fail'
        prop_type = 'results' if self.is_success() else 'error'

        return {
            'data': {
                prop_type: self.data
            },
            'status': status,
            'message': self.message
        }
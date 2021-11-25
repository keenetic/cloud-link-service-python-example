"""
Interface of storage for device records
"""

from typing import *
from datetime import datetime


class RecordStore(object):

    service_id: str = ''

    def __init__(self, service_id):
        self.service_id = service_id

    @staticmethod
    def name():
        return 'not implemented'

    @staticmethod
    def prepare_ec_record(
            token_alias: str,
            service_ec_private: str,
            service_ec_public: str,
            device_ec_public: str
    ) -> Dict[str, str]:
        """
        Formats record from given parameters as dict
        """
        content = {
            'tokenAlias': token_alias,
            'serviceEcPrivate': service_ec_private,
            'serviceEcPublic': service_ec_public,
            'deviceEcPublic': device_ec_public,
            'timestampCreated': int(datetime.now().timestamp())
        }
        return content

    @staticmethod
    def prepare_bearer_record(
            token_alias: str,
            access_role: str,
            user_data: str,
            bearer_value: str,
            timestamp_expires: int
    ) -> Dict[str, str]:
        """
        Formats bearer record from given parameters as dict
        """
        content = {
            'tokenAlias': token_alias,
            'accessRole': access_role,
            'userData': user_data,
            'bearerValue': bearer_value,
            'timestampExpires': timestamp_expires
        }
        return content

    def ensure_infra(self) -> bool:
        """
        Checks, if storage environment is ready to operate
        """
        raise NotImplementedError

    def save_pending_ec_record(
            self,
            token_alias: str,
            content: Union[str, Dict]
    ) -> None:
        """
        Saves record to storage as pending
        """
        raise NotImplementedError

    def save_active_ec_record(
            self,
            token_alias: str,
            content: Union[str, Dict]
    ) -> None:
        """
        Saves record to storage as active
        """
        raise NotImplementedError

    def load_ec_record(
            self,
            token_alias: str
    ) -> Optional[Dict]:
        """
        Loads active record from storage by token alias
        """
        raise NotImplementedError

    def save_bearer_record(
            self,
            content: Dict[str, str]
    ) -> None:
        raise NotImplementedError

    def load_bearer_record(
            self,
            token_alias: str,
            access_role: str,
            user_data: str
    ) -> Optional[Dict]:
        raise NotImplementedError

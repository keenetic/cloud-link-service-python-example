"""
Sample RecordStore: saving device records to files
(not for production!)
"""

import json
import os
from typing import *
from record_store import RecordStore


class RecordStoreFiles(RecordStore):

    _directory_prefix = ''

    def __init__(self, service_id: str, directory_prexix: str):
        super().__init__(service_id)
        self._directory_prefix = directory_prexix

    @staticmethod
    def name():
        return 'file'

    def ensure_infra(self) -> bool:
        """
        Checks local directories before starting server, creates if neccessary
        """
        if not isinstance(self.service_id, str) or not self.service_id:
            return False

        def check_or_create(dirname: str) -> bool:
            if not os.path.isdir(dirname):
                try:
                    os.mkdir(dirname)
                except:  # doesn't care why
                    return False
            return True

        list_to_check = []
        if self._directory_prefix:
            list_to_check.append(self._directory_prefix)
        list_to_check.extend([
            os.path.join(self._directory_prefix, 'devices'),
            os.path.join(self._directory_prefix, 'devices', self.service_id),
            os.path.join(self._directory_prefix, 'devices', self.service_id, 'pending'),
            os.path.join(self._directory_prefix, 'devices', self.service_id, 'active'),
            os.path.join(self._directory_prefix, 'bearers'),
            os.path.join(self._directory_prefix, 'bearers', self.service_id)
        ])

        all_checked = True
        for dirname in list_to_check:
            all_checked = all_checked and check_or_create(dirname)
            if not all_checked:
                break
        return all_checked

    def _get_filename_records(self, token_alias: str, for_type: str) -> str:
        return os.path.join(self._directory_prefix, 'devices', self.service_id, for_type, f'{token_alias}.json')

    def _get_filename_bearers(self, token_alias: str, access_role: str, user_data: str) -> str:
        # not adding user_data part to filename for now
        filename = f'{token_alias}|{access_role}.json'
        return os.path.join(self._directory_prefix, 'bearers', self.service_id, filename)

    @staticmethod
    def _ensure_string_before_save(content) -> str:
        if isinstance(content, dict):
            return json.dumps(content, indent=4)
        return str(content)

    @staticmethod
    def _get_json_from_filename(filename: str) -> Optional[Dict]:
        if os.path.isfile(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return None

    def save_pending_ec_record(
            self,
            token_alias: str,
            content: Union[str, Dict]
    ) -> None:
        with open(self._get_filename_records(token_alias, 'pending'), 'w') as f:
            f.write(RecordStoreFiles._ensure_string_before_save(content))

    def save_active_ec_record(
            self,
            token_alias: str,
            content: Union[str, Dict]
    ) -> None:
        with open(self._get_filename_records(token_alias, 'active'), 'w') as f:
            f.write(RecordStoreFiles._ensure_string_before_save(content))
        os.remove(self._get_filename_records(token_alias, 'pending'))

    def load_ec_record(
            self,
            token_alias: str
    ) -> Optional[Dict]:
        filename = self._get_filename_records(token_alias, 'active')
        return self._get_json_from_filename(filename)

    def load_bearer_record(
            self,
            token_alias: str,
            access_role: str,
            user_data: str
    ) -> Optional[Dict]:
        filename = self._get_filename_bearers(token_alias, access_role, user_data)
        return self._get_json_from_filename(filename)

    def save_bearer_record(
            self,
            content: Dict[str, str]
    ) -> None:
        if isinstance(content, dict):
            token_alias, access_role, user_data = [content.get(x) for x in ['tokenAlias', 'accessRole', 'userData']]
            if token_alias and access_role:
                with open(self._get_filename_bearers(token_alias, access_role, user_data), 'w') as f:
                    f.write(RecordStoreFiles._ensure_string_before_save(content))

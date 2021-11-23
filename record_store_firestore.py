"""
Sample RecordStore: saving device records to Google Cloud Firestore
"""

from typing import Optional, Union
from record_store import RecordStore
from google.cloud import firestore


class RecordFirestore(RecordStore):

    _firestore_db = None
    _firestore_collection_records = None
    _firestore_collection_bearers = None

    def __init__(self, service_id: str, firestore_project: str):
        super().__init__(service_id)
        self._firestore_db = firestore.Client(firestore_project)
        self._firestore_collection_records = self._firestore_db.collection(service_id)
        self._firestore_collection_bearers = self._firestore_db.collection('bearers')

    @staticmethod
    def name():
        return 'firestore'

    def ensure_infra(self) -> bool:
        """
        Checks Google Cloud Firestore
        """
        if not isinstance(self.service_id, str) or not self.service_id:
            return False

        # Trying to yield something from collection. If fails, there is some kind of error
        try:
            for _ in self._firestore_collection_records.stream():
                break
        except:
            return False
        return True

    @staticmethod
    def _ensure_dict_before_save(content) -> dict[str]:
        if not isinstance(content, dict):
            return {'content': content}
        return content

    def save_pending_ec_record(
            self,
            token_alias: str,
            content: Union[str, dict]
    ) -> None:
        content_dict: dict = RecordFirestore._ensure_dict_before_save(content)
        content_dict['isActive'] = False
        doc_ref = self._firestore_collection_records.document(token_alias)
        doc_ref.set(content_dict)

    def save_active_ec_record(
            self,
            token_alias: str,
            content: Union[str, dict]
    ) -> None:
        content_dict: dict = RecordFirestore._ensure_dict_before_save(content)
        content_dict['isActive'] = True
        doc_ref = self._firestore_collection_records.document(token_alias)
        doc_ref.set(RecordFirestore._ensure_dict_before_save(content))

    def load_ec_record(
            self,
            token_alias: str
    ) -> Optional[dict]:
        doc_ref = self._firestore_collection_records.document(token_alias)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            if data.get('isActive'):
                return data
        return None

    @staticmethod
    def _get_bearer_key(token_alias: str, access_role: str, user_data: str) -> str:
        return f'{token_alias};{access_role};{user_data}'

    def save_bearer_record(
            self,
            content: dict[str]
    ) -> None:
        content_dict: dict = RecordFirestore._ensure_dict_before_save(content)
        token_alias, access_role, user_data = [content_dict.get(x) for x in ['tokenAlias', 'accessRole', 'userData']]
        document_key = RecordFirestore._get_bearer_key(token_alias, access_role, user_data)
        doc_ref = self._firestore_collection_bearers.document(document_key)
        doc_ref.set(content_dict)

    def load_bearer_record(
            self,
            token_alias: str,
            access_role: str,
            user_data: str
    ) -> Optional[dict]:
        document_key = RecordFirestore._get_bearer_key(token_alias, access_role, user_data)
        doc_ref = self._firestore_collection_bearers.document(document_key)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None

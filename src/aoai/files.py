from typing import Optional, List, Dict, Any
from openai import AzureOpenAI
from .utils import clean_params, validate_vector_store_id, validate_files
from .constants import (
    DEFAULT_VECTOR_STORE_NAME,
    DEFAULT_EXPIRES_AFTER,
    DEFAULT_VECTOR_STORE_LIST_PARAMS,
    PARAM_LIMIT,
    PARAM_ORDER,
    PARAM_AFTER,
    PARAM_BEFORE,
    LIST_LIMIT_RANGE,
    ERROR_INVALID_LIMIT,
)


class VectorStores:
    """Vector store operations"""

    def __init__(self, client: AzureOpenAI):
        self._client = client
        self.file_batches = self.FileBatches(client)

    def create(
        self,
        name: Optional[str] = DEFAULT_VECTOR_STORE_NAME,
        expires_after: Optional[dict] = DEFAULT_EXPIRES_AFTER,
        **kwargs
    ) -> Any:
        """Creates a vector store"""
        params = {"name": name, "expires_after": expires_after, **kwargs}
        return self._client.beta.vector_stores.create(**clean_params(params))

    def retrieve(self, vector_store_id: str) -> Any:
        """Retrieves a vector store by ID"""
        validate_vector_store_id(vector_store_id)
        return self._client.beta.vector_stores.retrieve(vector_store_id)

    def list(
        self,
        limit: Optional[int] = DEFAULT_VECTOR_STORE_LIST_PARAMS[PARAM_LIMIT],
        order: Optional[str] = DEFAULT_VECTOR_STORE_LIST_PARAMS[PARAM_ORDER],
        after: Optional[str] = DEFAULT_VECTOR_STORE_LIST_PARAMS[PARAM_AFTER],
        before: Optional[str] = DEFAULT_VECTOR_STORE_LIST_PARAMS[PARAM_BEFORE],
    ) -> Any:
        """Lists vector stores"""
        if limit and limit not in LIST_LIMIT_RANGE:
            raise ValueError(ERROR_INVALID_LIMIT)

        params = {
            PARAM_LIMIT: limit,
            PARAM_ORDER: order,
            PARAM_AFTER: after,
            PARAM_BEFORE: before,
        }
        return self._client.beta.vector_stores.list(**clean_params(params))

    def delete(self, vector_store_id: str) -> Any:
        """Deletes a vector store"""
        validate_vector_store_id(vector_store_id)
        return self._client.beta.vector_stores.delete(vector_store_id)

    class FileBatches:
        """File batch operations for vector stores"""

        def __init__(self, client: AzureOpenAI):
            self._client = client

        def upload_and_poll(self, vector_store_id: str, files: list) -> Any:
            """Uploads files to a vector store"""
            validate_vector_store_id(vector_store_id)
            validate_files(files)
            return self._client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store_id, files=files
            )

    # Compatibility methods
    def create_vector_store(self, *args, **kwargs) -> Any:
        """Compatibility method for create()"""
        return self.create(*args, **kwargs)

    def retrieve_vector_store(self, vector_store_id: str) -> Any:
        """Compatibility method for retrieve()"""
        return self.retrieve(vector_store_id)

    def list_vector_stores(self, *args, **kwargs) -> Any:
        """Compatibility method for list()"""
        return self.list(*args, **kwargs)

    def delete_vector_store(self, vector_store_id: str) -> Any:
        """Compatibility method for delete()"""
        return self.delete(vector_store_id)

    def upload_files_to_vector_store(self, vector_store_id: str, files: list) -> Any:
        """Compatibility method for file_batches.upload_and_poll()"""
        return self.file_batches.upload_and_poll(vector_store_id, files)

"""Azure OpenAI Vector Store operations.

This module provides functionality for managing vector stores and file operations
within Azure OpenAI, including creation, retrieval, listing, and deletion of
vector stores, as well as file batch uploads.

Typical usage example:
    client = AOAIClient.create(...)
    vector_stores = VectorStores(client)
    store = vector_stores.create(name="my-store")
    vector_stores.file_batches.upload_and_poll(store.id, files=[...])
"""

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
    """Manages vector store operations in Azure OpenAI.

    This class provides methods for creating, retrieving, listing, and deleting
    vector stores, as well as managing file batch operations.

    Attributes:
        _client: An instance of AzureOpenAI client.
        file_batches: An instance of FileBatches for managing file operations.
    """

    def __init__(self, client: AzureOpenAI):
        """Initialize the VectorStores manager.

        Args:
            client: An instance of AzureOpenAI client.
        """
        self._client = client
        self.file_batches = self.FileBatches(client)

    def create(
        self,
        name: Optional[str] = DEFAULT_VECTOR_STORE_NAME,
        expires_after: Optional[dict] = DEFAULT_EXPIRES_AFTER,
        **kwargs
    ) -> Any:
        """Creates a new vector store.

        Args:
            name: The name of the vector store (default: DEFAULT_VECTOR_STORE_NAME).
            expires_after: Expiration configuration for the store (default: DEFAULT_EXPIRES_AFTER).
            **kwargs: Additional parameters to pass to the API.

        Returns:
            The created vector store object.
        """
        params = {"name": name, "expires_after": expires_after, **kwargs}
        return self._client.beta.vector_stores.create(**clean_params(params))

    def retrieve(self, vector_store_id: str) -> Any:
        """Retrieves a vector store by ID.

        Args:
            vector_store_id: The ID of the vector store to retrieve.

        Returns:
            The vector store object.

        Raises:
            ValueError: If the vector store ID is invalid.
        """
        validate_vector_store_id(vector_store_id)
        return self._client.beta.vector_stores.retrieve(vector_store_id)

    def list(
        self,
        limit: Optional[int] = DEFAULT_VECTOR_STORE_LIST_PARAMS[PARAM_LIMIT],
        order: Optional[str] = DEFAULT_VECTOR_STORE_LIST_PARAMS[PARAM_ORDER],
        after: Optional[str] = DEFAULT_VECTOR_STORE_LIST_PARAMS[PARAM_AFTER],
        before: Optional[str] = DEFAULT_VECTOR_STORE_LIST_PARAMS[PARAM_BEFORE],
    ) -> Any:
        """Lists vector stores with pagination support.

        Args:
            limit: Maximum number of stores to return (default: from DEFAULT_VECTOR_STORE_LIST_PARAMS).
            order: Sort order for results (default: from DEFAULT_VECTOR_STORE_LIST_PARAMS).
            after: Return results after this ID (default: from DEFAULT_VECTOR_STORE_LIST_PARAMS).
            before: Return results before this ID (default: from DEFAULT_VECTOR_STORE_LIST_PARAMS).

        Returns:
            A list of vector store objects.

        Raises:
            ValueError: If the limit is outside the valid range.
        """
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
        """Deletes a vector store.

        Args:
            vector_store_id: The ID of the vector store to delete.

        Returns:
            A deletion status object.

        Raises:
            ValueError: If the vector store ID is invalid.
        """
        validate_vector_store_id(vector_store_id)
        return self._client.beta.vector_stores.delete(vector_store_id)

    class FileBatches:
        """Manages file batch operations for vector stores.

        This nested class handles file upload operations to vector stores.

        Attributes:
            _client: An instance of AzureOpenAI client.
        """

        def __init__(self, client: AzureOpenAI):
            """Initialize the FileBatches manager.

            Args:
                client: An instance of AzureOpenAI client.
            """
            self._client = client

        def upload_and_poll(self, vector_store_id: str, files: list) -> Any:
            """Uploads files to a vector store and polls for completion.

            Args:
                vector_store_id: The ID of the target vector store.
                files: List of files to upload (can be paths, bytes, or file objects).

            Returns:
                The upload operation result.

            Raises:
                ValueError: If the vector store ID is invalid or files list is invalid.
            """
            validate_vector_store_id(vector_store_id)
            validate_files(files)
            return self._client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store_id, files=files
            )

    # Compatibility methods
    def create_vector_store(self, *args, **kwargs) -> Any:
        """Compatibility method for create().

        See create() for full documentation.

        Returns:
            The created vector store object.
        """
        return self.create(*args, **kwargs)

    def retrieve_vector_store(self, vector_store_id: str) -> Any:
        """Compatibility method for retrieve().

        See retrieve() for full documentation.

        Args:
            vector_store_id: The ID of the vector store to retrieve.

        Returns:
            The vector store object.
        """
        return self.retrieve(vector_store_id)

    def list_vector_stores(self, *args, **kwargs) -> Any:
        """Compatibility method for list().

        See list() for full documentation.

        Returns:
            A list of vector store objects.
        """
        return self.list(*args, **kwargs)

    def delete_vector_store(self, vector_store_id: str) -> Any:
        """Compatibility method for delete().

        See delete() for full documentation.

        Args:
            vector_store_id: The ID of the vector store to delete.

        Returns:
            A deletion status object.
        """
        return self.delete(vector_store_id)

    def upload_files_to_vector_store(self, vector_store_id: str, files: list) -> Any:
        """Compatibility method for file_batches.upload_and_poll().

        See FileBatches.upload_and_poll() for full documentation.

        Args:
            vector_store_id: The ID of the target vector store.
            files: List of files to upload.

        Returns:
            The upload operation result.
        """
        return self.file_batches.upload_and_poll(vector_store_id, files)

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.vector_db_column_request_embedding_config import (
        VectorDBColumnRequestEmbeddingConfig,
    )


T = TypeVar("T", bound="VectorDBColumnRequest")


@_attrs_define
class VectorDBColumnRequest:
    """
    Attributes:
        column_id (UUID):
        sub_type (str):
        api_key (str):
        new_column_name (str | Unset):
        collection_name (str | Unset):
        url (str | Unset):
        search_type (str | Unset):
        key (str | Unset):
        limit (int | Unset):
        index_name (str | Unset):
        top_k (int | Unset):
        namespace (str | Unset):
        embedding_config (VectorDBColumnRequestEmbeddingConfig | Unset):
        concurrency (int | Unset):  Default: 5.
        query_key (str | Unset):
        vector_length (int | Unset):
    """

    column_id: UUID
    sub_type: str
    api_key: str
    new_column_name: str | Unset = UNSET
    collection_name: str | Unset = UNSET
    url: str | Unset = UNSET
    search_type: str | Unset = UNSET
    key: str | Unset = UNSET
    limit: int | Unset = UNSET
    index_name: str | Unset = UNSET
    top_k: int | Unset = UNSET
    namespace: str | Unset = UNSET
    embedding_config: VectorDBColumnRequestEmbeddingConfig | Unset = UNSET
    concurrency: int | Unset = 5
    query_key: str | Unset = UNSET
    vector_length: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        column_id = str(self.column_id)

        sub_type = self.sub_type

        api_key = self.api_key

        new_column_name = self.new_column_name

        collection_name = self.collection_name

        url = self.url

        search_type = self.search_type

        key = self.key

        limit = self.limit

        index_name = self.index_name

        top_k = self.top_k

        namespace = self.namespace

        embedding_config: dict[str, Any] | Unset = UNSET
        if not isinstance(self.embedding_config, Unset):
            embedding_config = self.embedding_config.to_dict()

        concurrency = self.concurrency

        query_key = self.query_key

        vector_length = self.vector_length

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "column_id": column_id,
                "sub_type": sub_type,
                "api_key": api_key,
            }
        )
        if new_column_name is not UNSET:
            field_dict["new_column_name"] = new_column_name
        if collection_name is not UNSET:
            field_dict["collection_name"] = collection_name
        if url is not UNSET:
            field_dict["url"] = url
        if search_type is not UNSET:
            field_dict["search_type"] = search_type
        if key is not UNSET:
            field_dict["key"] = key
        if limit is not UNSET:
            field_dict["limit"] = limit
        if index_name is not UNSET:
            field_dict["index_name"] = index_name
        if top_k is not UNSET:
            field_dict["top_k"] = top_k
        if namespace is not UNSET:
            field_dict["namespace"] = namespace
        if embedding_config is not UNSET:
            field_dict["embedding_config"] = embedding_config
        if concurrency is not UNSET:
            field_dict["concurrency"] = concurrency
        if query_key is not UNSET:
            field_dict["query_key"] = query_key
        if vector_length is not UNSET:
            field_dict["vector_length"] = vector_length

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.vector_db_column_request_embedding_config import (
            VectorDBColumnRequestEmbeddingConfig,
        )

        d = dict(src_dict)
        column_id = UUID(d.pop("column_id"))

        sub_type = d.pop("sub_type")

        api_key = d.pop("api_key")

        new_column_name = d.pop("new_column_name", UNSET)

        collection_name = d.pop("collection_name", UNSET)

        url = d.pop("url", UNSET)

        search_type = d.pop("search_type", UNSET)

        key = d.pop("key", UNSET)

        limit = d.pop("limit", UNSET)

        index_name = d.pop("index_name", UNSET)

        top_k = d.pop("top_k", UNSET)

        namespace = d.pop("namespace", UNSET)

        _embedding_config = d.pop("embedding_config", UNSET)
        embedding_config: VectorDBColumnRequestEmbeddingConfig | Unset
        if isinstance(_embedding_config, Unset):
            embedding_config = UNSET
        else:
            embedding_config = VectorDBColumnRequestEmbeddingConfig.from_dict(
                _embedding_config
            )

        concurrency = d.pop("concurrency", UNSET)

        query_key = d.pop("query_key", UNSET)

        vector_length = d.pop("vector_length", UNSET)

        vector_db_column_request = cls(
            column_id=column_id,
            sub_type=sub_type,
            api_key=api_key,
            new_column_name=new_column_name,
            collection_name=collection_name,
            url=url,
            search_type=search_type,
            key=key,
            limit=limit,
            index_name=index_name,
            top_k=top_k,
            namespace=namespace,
            embedding_config=embedding_config,
            concurrency=concurrency,
            query_key=query_key,
            vector_length=vector_length,
        )

        vector_db_column_request.additional_properties = d
        return vector_db_column_request

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties

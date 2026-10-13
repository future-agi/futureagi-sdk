from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.preview_run_eval_request_config import PreviewRunEvalRequestConfig


T = TypeVar("T", bound="PreviewRunEvalRequest")


@_attrs_define
class PreviewRunEvalRequest:
    """
    Attributes:
        config (PreviewRunEvalRequestConfig):
        template_id (UUID):
        model (str | Unset):
        sdk_uuid (str | Unset):
        source (str | Unset):
        protect_flash (bool | Unset):  Default: False.
    """

    config: PreviewRunEvalRequestConfig
    template_id: UUID
    model: str | Unset = UNSET
    sdk_uuid: str | Unset = UNSET
    source: str | Unset = UNSET
    protect_flash: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        config = self.config.to_dict()

        template_id = str(self.template_id)

        model = self.model

        sdk_uuid = self.sdk_uuid

        source = self.source

        protect_flash = self.protect_flash

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "config": config,
                "template_id": template_id,
            }
        )
        if model is not UNSET:
            field_dict["model"] = model
        if sdk_uuid is not UNSET:
            field_dict["sdk_uuid"] = sdk_uuid
        if source is not UNSET:
            field_dict["source"] = source
        if protect_flash is not UNSET:
            field_dict["protect_flash"] = protect_flash

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.preview_run_eval_request_config import PreviewRunEvalRequestConfig

        d = dict(src_dict)
        config = PreviewRunEvalRequestConfig.from_dict(d.pop("config"))

        template_id = UUID(d.pop("template_id"))

        model = d.pop("model", UNSET)

        sdk_uuid = d.pop("sdk_uuid", UNSET)

        source = d.pop("source", UNSET)

        protect_flash = d.pop("protect_flash", UNSET)

        preview_run_eval_request = cls(
            config=config,
            template_id=template_id,
            model=model,
            sdk_uuid=sdk_uuid,
            source=source,
            protect_flash=protect_flash,
        )

        preview_run_eval_request.additional_properties = d
        return preview_run_eval_request

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

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.output_diff_side_output_state import OutputDiffSideOutputState

if TYPE_CHECKING:
    from ..models.output_diff_side_output_preview_type_4_type_0 import (
        OutputDiffSideOutputPreviewType4Type0,
    )


T = TypeVar("T", bound="OutputDiffSide")


@_attrs_define
class OutputDiffSide:
    """
    Attributes:
        item_id (None | UUID):
        status (None | str):
        output_state (OutputDiffSideOutputState):
        output_digest (None | str):
        output_bytes (int | None):
        output_preview (bool | float | list[Any] | None | OutputDiffSideOutputPreviewType4Type0 | str): Any valid JSON
            value.
        preview_omitted (bool):
    """

    item_id: None | UUID
    status: None | str
    output_state: OutputDiffSideOutputState
    output_digest: None | str
    output_bytes: int | None
    output_preview: (
        bool | float | list[Any] | None | OutputDiffSideOutputPreviewType4Type0 | str
    )
    preview_omitted: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.output_diff_side_output_preview_type_4_type_0 import (
            OutputDiffSideOutputPreviewType4Type0,
        )

        item_id: None | str
        if isinstance(self.item_id, UUID):
            item_id = str(self.item_id)
        else:
            item_id = self.item_id

        status: None | str
        status = self.status

        output_state = self.output_state.value

        output_digest: None | str
        output_digest = self.output_digest

        output_bytes: int | None
        output_bytes = self.output_bytes

        output_preview: bool | dict[str, Any] | float | list[Any] | None | str
        if isinstance(self.output_preview, list):
            output_preview = self.output_preview

        elif isinstance(self.output_preview, OutputDiffSideOutputPreviewType4Type0):
            output_preview = self.output_preview.to_dict()
        else:
            output_preview = self.output_preview

        preview_omitted = self.preview_omitted

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "item_id": item_id,
                "status": status,
                "output_state": output_state,
                "output_digest": output_digest,
                "output_bytes": output_bytes,
                "output_preview": output_preview,
                "preview_omitted": preview_omitted,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.output_diff_side_output_preview_type_4_type_0 import (
            OutputDiffSideOutputPreviewType4Type0,
        )

        d = dict(src_dict)

        def _parse_item_id(data: object) -> None | UUID:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                item_id_type_0 = UUID(data)

                return item_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | UUID, data)

        item_id = _parse_item_id(d.pop("item_id"))

        def _parse_status(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        status = _parse_status(d.pop("status"))

        output_state = OutputDiffSideOutputState(d.pop("output_state"))

        def _parse_output_digest(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        output_digest = _parse_output_digest(d.pop("output_digest"))

        def _parse_output_bytes(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        output_bytes = _parse_output_bytes(d.pop("output_bytes"))

        def _parse_output_preview(
            data: object,
        ) -> (
            bool
            | float
            | list[Any]
            | None
            | OutputDiffSideOutputPreviewType4Type0
            | str
        ):
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                output_preview_type_3 = cast(list[Any], data)

                return output_preview_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                output_preview_type_4_type_0 = (
                    OutputDiffSideOutputPreviewType4Type0.from_dict(data)
                )

                return output_preview_type_4_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool
                | float
                | list[Any]
                | None
                | OutputDiffSideOutputPreviewType4Type0
                | str,
                data,
            )

        output_preview = _parse_output_preview(d.pop("output_preview"))

        preview_omitted = d.pop("preview_omitted")

        output_diff_side = cls(
            item_id=item_id,
            status=status,
            output_state=output_state,
            output_digest=output_digest,
            output_bytes=output_bytes,
            output_preview=output_preview,
            preview_omitted=preview_omitted,
        )

        output_diff_side.additional_properties = d
        return output_diff_side

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

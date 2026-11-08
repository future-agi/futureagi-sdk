from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.trace_observe_column_config_target_type import (
    TraceObserveColumnConfigTargetType,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.trace_observe_column_config_annotators_type_4_type_0 import (
        TraceObserveColumnConfigAnnotatorsType4Type0,
    )
    from ..models.trace_observe_column_config_choices_map_type_4_type_0 import (
        TraceObserveColumnConfigChoicesMapType4Type0,
    )
    from ..models.trace_observe_column_config_settings_type_4_type_0 import (
        TraceObserveColumnConfigSettingsType4Type0,
    )


T = TypeVar("T", bound="TraceObserveColumnConfig")


@_attrs_define
class TraceObserveColumnConfig:
    """
    Attributes:
        id (str):
        name (str):
        is_visible (bool):
        group_by (None | str | Unset):
        output_type (None | str | Unset):
        reverse_output (bool | None | Unset):
        annotation_label_type (None | str | Unset):
        choices (list[None | str] | None | Unset):
        settings (bool | float | list[Any] | None | str | TraceObserveColumnConfigSettingsType4Type0 | Unset): Any valid
            JSON value.
        choices_map (bool | float | list[Any] | None | str | TraceObserveColumnConfigChoicesMapType4Type0 | Unset): Any
            valid JSON value.
        eval_template_id (None | str | Unset):
        target_type (None | TraceObserveColumnConfigTargetType | Unset):
        annotators (bool | float | list[Any] | None | str | TraceObserveColumnConfigAnnotatorsType4Type0 | Unset): Any
            valid JSON value.
        source_field (None | str | Unset):
        parent_eval_id (None | str | Unset):
        property_id (None | str | Unset):
        property_kind (None | str | Unset):
        property_source (None | str | Unset):
    """

    id: str
    name: str
    is_visible: bool
    group_by: None | str | Unset = UNSET
    output_type: None | str | Unset = UNSET
    reverse_output: bool | None | Unset = UNSET
    annotation_label_type: None | str | Unset = UNSET
    choices: list[None | str] | None | Unset = UNSET
    settings: (
        bool
        | float
        | list[Any]
        | None
        | str
        | TraceObserveColumnConfigSettingsType4Type0
        | Unset
    ) = UNSET
    choices_map: (
        bool
        | float
        | list[Any]
        | None
        | str
        | TraceObserveColumnConfigChoicesMapType4Type0
        | Unset
    ) = UNSET
    eval_template_id: None | str | Unset = UNSET
    target_type: None | TraceObserveColumnConfigTargetType | Unset = UNSET
    annotators: (
        bool
        | float
        | list[Any]
        | None
        | str
        | TraceObserveColumnConfigAnnotatorsType4Type0
        | Unset
    ) = UNSET
    source_field: None | str | Unset = UNSET
    parent_eval_id: None | str | Unset = UNSET
    property_id: None | str | Unset = UNSET
    property_kind: None | str | Unset = UNSET
    property_source: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.trace_observe_column_config_annotators_type_4_type_0 import (
            TraceObserveColumnConfigAnnotatorsType4Type0,
        )
        from ..models.trace_observe_column_config_choices_map_type_4_type_0 import (
            TraceObserveColumnConfigChoicesMapType4Type0,
        )
        from ..models.trace_observe_column_config_settings_type_4_type_0 import (
            TraceObserveColumnConfigSettingsType4Type0,
        )

        id = self.id

        name = self.name

        is_visible = self.is_visible

        group_by: None | str | Unset
        if isinstance(self.group_by, Unset):
            group_by = UNSET
        else:
            group_by = self.group_by

        output_type: None | str | Unset
        if isinstance(self.output_type, Unset):
            output_type = UNSET
        else:
            output_type = self.output_type

        reverse_output: bool | None | Unset
        if isinstance(self.reverse_output, Unset):
            reverse_output = UNSET
        else:
            reverse_output = self.reverse_output

        annotation_label_type: None | str | Unset
        if isinstance(self.annotation_label_type, Unset):
            annotation_label_type = UNSET
        else:
            annotation_label_type = self.annotation_label_type

        choices: list[None | str] | None | Unset
        if isinstance(self.choices, Unset):
            choices = UNSET
        elif isinstance(self.choices, list):
            choices = []
            for choices_type_0_item_data in self.choices:
                choices_type_0_item: None | str
                choices_type_0_item = choices_type_0_item_data
                choices.append(choices_type_0_item)

        else:
            choices = self.choices

        settings: bool | dict[str, Any] | float | list[Any] | None | str | Unset
        if isinstance(self.settings, Unset):
            settings = UNSET
        elif isinstance(self.settings, list):
            settings = self.settings

        elif isinstance(self.settings, TraceObserveColumnConfigSettingsType4Type0):
            settings = self.settings.to_dict()
        else:
            settings = self.settings

        choices_map: bool | dict[str, Any] | float | list[Any] | None | str | Unset
        if isinstance(self.choices_map, Unset):
            choices_map = UNSET
        elif isinstance(self.choices_map, list):
            choices_map = self.choices_map

        elif isinstance(self.choices_map, TraceObserveColumnConfigChoicesMapType4Type0):
            choices_map = self.choices_map.to_dict()
        else:
            choices_map = self.choices_map

        eval_template_id: None | str | Unset
        if isinstance(self.eval_template_id, Unset):
            eval_template_id = UNSET
        else:
            eval_template_id = self.eval_template_id

        target_type: None | str | Unset
        if isinstance(self.target_type, Unset):
            target_type = UNSET
        elif isinstance(self.target_type, TraceObserveColumnConfigTargetType):
            target_type = self.target_type.value
        else:
            target_type = self.target_type

        annotators: bool | dict[str, Any] | float | list[Any] | None | str | Unset
        if isinstance(self.annotators, Unset):
            annotators = UNSET
        elif isinstance(self.annotators, list):
            annotators = self.annotators

        elif isinstance(self.annotators, TraceObserveColumnConfigAnnotatorsType4Type0):
            annotators = self.annotators.to_dict()
        else:
            annotators = self.annotators

        source_field: None | str | Unset
        if isinstance(self.source_field, Unset):
            source_field = UNSET
        else:
            source_field = self.source_field

        parent_eval_id: None | str | Unset
        if isinstance(self.parent_eval_id, Unset):
            parent_eval_id = UNSET
        else:
            parent_eval_id = self.parent_eval_id

        property_id: None | str | Unset
        if isinstance(self.property_id, Unset):
            property_id = UNSET
        else:
            property_id = self.property_id

        property_kind: None | str | Unset
        if isinstance(self.property_kind, Unset):
            property_kind = UNSET
        else:
            property_kind = self.property_kind

        property_source: None | str | Unset
        if isinstance(self.property_source, Unset):
            property_source = UNSET
        else:
            property_source = self.property_source

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "is_visible": is_visible,
            }
        )
        if group_by is not UNSET:
            field_dict["group_by"] = group_by
        if output_type is not UNSET:
            field_dict["output_type"] = output_type
        if reverse_output is not UNSET:
            field_dict["reverse_output"] = reverse_output
        if annotation_label_type is not UNSET:
            field_dict["annotation_label_type"] = annotation_label_type
        if choices is not UNSET:
            field_dict["choices"] = choices
        if settings is not UNSET:
            field_dict["settings"] = settings
        if choices_map is not UNSET:
            field_dict["choices_map"] = choices_map
        if eval_template_id is not UNSET:
            field_dict["eval_template_id"] = eval_template_id
        if target_type is not UNSET:
            field_dict["target_type"] = target_type
        if annotators is not UNSET:
            field_dict["annotators"] = annotators
        if source_field is not UNSET:
            field_dict["source_field"] = source_field
        if parent_eval_id is not UNSET:
            field_dict["parent_eval_id"] = parent_eval_id
        if property_id is not UNSET:
            field_dict["property_id"] = property_id
        if property_kind is not UNSET:
            field_dict["property_kind"] = property_kind
        if property_source is not UNSET:
            field_dict["property_source"] = property_source

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.trace_observe_column_config_annotators_type_4_type_0 import (
            TraceObserveColumnConfigAnnotatorsType4Type0,
        )
        from ..models.trace_observe_column_config_choices_map_type_4_type_0 import (
            TraceObserveColumnConfigChoicesMapType4Type0,
        )
        from ..models.trace_observe_column_config_settings_type_4_type_0 import (
            TraceObserveColumnConfigSettingsType4Type0,
        )

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        is_visible = d.pop("is_visible")

        def _parse_group_by(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        group_by = _parse_group_by(d.pop("group_by", UNSET))

        def _parse_output_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        output_type = _parse_output_type(d.pop("output_type", UNSET))

        def _parse_reverse_output(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        reverse_output = _parse_reverse_output(d.pop("reverse_output", UNSET))

        def _parse_annotation_label_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        annotation_label_type = _parse_annotation_label_type(
            d.pop("annotation_label_type", UNSET)
        )

        def _parse_choices(data: object) -> list[None | str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                choices_type_0 = []
                _choices_type_0 = data
                for choices_type_0_item_data in _choices_type_0:

                    def _parse_choices_type_0_item(data: object) -> None | str:
                        if data is None:
                            return data
                        return cast(None | str, data)

                    choices_type_0_item = _parse_choices_type_0_item(
                        choices_type_0_item_data
                    )

                    choices_type_0.append(choices_type_0_item)

                return choices_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[None | str] | None | Unset, data)

        choices = _parse_choices(d.pop("choices", UNSET))

        def _parse_settings(
            data: object,
        ) -> (
            bool
            | float
            | list[Any]
            | None
            | str
            | TraceObserveColumnConfigSettingsType4Type0
            | Unset
        ):
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                settings_type_3 = cast(list[Any], data)

                return settings_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                settings_type_4_type_0 = (
                    TraceObserveColumnConfigSettingsType4Type0.from_dict(data)
                )

                return settings_type_4_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool
                | float
                | list[Any]
                | None
                | str
                | TraceObserveColumnConfigSettingsType4Type0
                | Unset,
                data,
            )

        settings = _parse_settings(d.pop("settings", UNSET))

        def _parse_choices_map(
            data: object,
        ) -> (
            bool
            | float
            | list[Any]
            | None
            | str
            | TraceObserveColumnConfigChoicesMapType4Type0
            | Unset
        ):
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                choices_map_type_3 = cast(list[Any], data)

                return choices_map_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                choices_map_type_4_type_0 = (
                    TraceObserveColumnConfigChoicesMapType4Type0.from_dict(data)
                )

                return choices_map_type_4_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool
                | float
                | list[Any]
                | None
                | str
                | TraceObserveColumnConfigChoicesMapType4Type0
                | Unset,
                data,
            )

        choices_map = _parse_choices_map(d.pop("choices_map", UNSET))

        def _parse_eval_template_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        eval_template_id = _parse_eval_template_id(d.pop("eval_template_id", UNSET))

        def _parse_target_type(
            data: object,
        ) -> None | TraceObserveColumnConfigTargetType | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                target_type_type_1 = TraceObserveColumnConfigTargetType(data)

                return target_type_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | TraceObserveColumnConfigTargetType | Unset, data)

        target_type = _parse_target_type(d.pop("target_type", UNSET))

        def _parse_annotators(
            data: object,
        ) -> (
            bool
            | float
            | list[Any]
            | None
            | str
            | TraceObserveColumnConfigAnnotatorsType4Type0
            | Unset
        ):
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                annotators_type_3 = cast(list[Any], data)

                return annotators_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                annotators_type_4_type_0 = (
                    TraceObserveColumnConfigAnnotatorsType4Type0.from_dict(data)
                )

                return annotators_type_4_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool
                | float
                | list[Any]
                | None
                | str
                | TraceObserveColumnConfigAnnotatorsType4Type0
                | Unset,
                data,
            )

        annotators = _parse_annotators(d.pop("annotators", UNSET))

        def _parse_source_field(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        source_field = _parse_source_field(d.pop("source_field", UNSET))

        def _parse_parent_eval_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        parent_eval_id = _parse_parent_eval_id(d.pop("parent_eval_id", UNSET))

        def _parse_property_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        property_id = _parse_property_id(d.pop("property_id", UNSET))

        def _parse_property_kind(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        property_kind = _parse_property_kind(d.pop("property_kind", UNSET))

        def _parse_property_source(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        property_source = _parse_property_source(d.pop("property_source", UNSET))

        trace_observe_column_config = cls(
            id=id,
            name=name,
            is_visible=is_visible,
            group_by=group_by,
            output_type=output_type,
            reverse_output=reverse_output,
            annotation_label_type=annotation_label_type,
            choices=choices,
            settings=settings,
            choices_map=choices_map,
            eval_template_id=eval_template_id,
            target_type=target_type,
            annotators=annotators,
            source_field=source_field,
            parent_eval_id=parent_eval_id,
            property_id=property_id,
            property_kind=property_kind,
            property_source=property_source,
        )

        trace_observe_column_config.additional_properties = d
        return trace_observe_column_config

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

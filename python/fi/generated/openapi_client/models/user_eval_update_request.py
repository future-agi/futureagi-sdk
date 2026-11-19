from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.user_eval_update_request_composite_weight_overrides import (
        UserEvalUpdateRequestCompositeWeightOverrides,
    )
    from ..models.user_eval_update_request_config import UserEvalUpdateRequestConfig


T = TypeVar("T", bound="UserEvalUpdateRequest")


@_attrs_define
class UserEvalUpdateRequest:
    """
    Attributes:
        config (UserEvalUpdateRequestConfig):
        name (str | Unset):
        template_id (str | Unset):
        kb_id (UUID | Unset):
        error_localizer (bool | Unset):  Default: False.
        model (str | Unset):
        eval_type (str | Unset):
        run (bool | Unset):  Default: False.
        save_as_template (bool | Unset):  Default: False.
        experiment_id (UUID | Unset):
        composite_weight_overrides (UserEvalUpdateRequestCompositeWeightOverrides | Unset):
        pinned_version_id (None | Unset | UUID):
    """

    config: UserEvalUpdateRequestConfig
    name: str | Unset = UNSET
    template_id: str | Unset = UNSET
    kb_id: UUID | Unset = UNSET
    error_localizer: bool | Unset = False
    model: str | Unset = UNSET
    eval_type: str | Unset = UNSET
    run: bool | Unset = False
    save_as_template: bool | Unset = False
    experiment_id: UUID | Unset = UNSET
    composite_weight_overrides: (
        UserEvalUpdateRequestCompositeWeightOverrides | Unset
    ) = UNSET
    pinned_version_id: None | Unset | UUID = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        config = self.config.to_dict()

        name = self.name

        template_id = self.template_id

        kb_id: str | Unset = UNSET
        if not isinstance(self.kb_id, Unset):
            kb_id = str(self.kb_id)

        error_localizer = self.error_localizer

        model = self.model

        eval_type = self.eval_type

        run = self.run

        save_as_template = self.save_as_template

        experiment_id: str | Unset = UNSET
        if not isinstance(self.experiment_id, Unset):
            experiment_id = str(self.experiment_id)

        composite_weight_overrides: dict[str, Any] | Unset = UNSET
        if not isinstance(self.composite_weight_overrides, Unset):
            composite_weight_overrides = self.composite_weight_overrides.to_dict()

        pinned_version_id: None | str | Unset
        if isinstance(self.pinned_version_id, Unset):
            pinned_version_id = UNSET
        elif isinstance(self.pinned_version_id, UUID):
            pinned_version_id = str(self.pinned_version_id)
        else:
            pinned_version_id = self.pinned_version_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "config": config,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if template_id is not UNSET:
            field_dict["template_id"] = template_id
        if kb_id is not UNSET:
            field_dict["kb_id"] = kb_id
        if error_localizer is not UNSET:
            field_dict["error_localizer"] = error_localizer
        if model is not UNSET:
            field_dict["model"] = model
        if eval_type is not UNSET:
            field_dict["eval_type"] = eval_type
        if run is not UNSET:
            field_dict["run"] = run
        if save_as_template is not UNSET:
            field_dict["save_as_template"] = save_as_template
        if experiment_id is not UNSET:
            field_dict["experiment_id"] = experiment_id
        if composite_weight_overrides is not UNSET:
            field_dict["composite_weight_overrides"] = composite_weight_overrides
        if pinned_version_id is not UNSET:
            field_dict["pinned_version_id"] = pinned_version_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.user_eval_update_request_composite_weight_overrides import (
            UserEvalUpdateRequestCompositeWeightOverrides,
        )
        from ..models.user_eval_update_request_config import UserEvalUpdateRequestConfig

        d = dict(src_dict)
        config = UserEvalUpdateRequestConfig.from_dict(d.pop("config"))

        name = d.pop("name", UNSET)

        template_id = d.pop("template_id", UNSET)

        _kb_id = d.pop("kb_id", UNSET)
        kb_id: UUID | Unset
        if isinstance(_kb_id, Unset):
            kb_id = UNSET
        else:
            kb_id = UUID(_kb_id)

        error_localizer = d.pop("error_localizer", UNSET)

        model = d.pop("model", UNSET)

        eval_type = d.pop("eval_type", UNSET)

        run = d.pop("run", UNSET)

        save_as_template = d.pop("save_as_template", UNSET)

        _experiment_id = d.pop("experiment_id", UNSET)
        experiment_id: UUID | Unset
        if isinstance(_experiment_id, Unset):
            experiment_id = UNSET
        else:
            experiment_id = UUID(_experiment_id)

        _composite_weight_overrides = d.pop("composite_weight_overrides", UNSET)
        composite_weight_overrides: (
            UserEvalUpdateRequestCompositeWeightOverrides | Unset
        )
        if isinstance(_composite_weight_overrides, Unset):
            composite_weight_overrides = UNSET
        else:
            composite_weight_overrides = (
                UserEvalUpdateRequestCompositeWeightOverrides.from_dict(
                    _composite_weight_overrides
                )
            )

        def _parse_pinned_version_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                pinned_version_id_type_0 = UUID(data)

                return pinned_version_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        pinned_version_id = _parse_pinned_version_id(d.pop("pinned_version_id", UNSET))

        user_eval_update_request = cls(
            config=config,
            name=name,
            template_id=template_id,
            kb_id=kb_id,
            error_localizer=error_localizer,
            model=model,
            eval_type=eval_type,
            run=run,
            save_as_template=save_as_template,
            experiment_id=experiment_id,
            composite_weight_overrides=composite_weight_overrides,
            pinned_version_id=pinned_version_id,
        )

        user_eval_update_request.additional_properties = d
        return user_eval_update_request

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

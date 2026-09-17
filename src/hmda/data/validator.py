"""Hợp đồng và quality validator cấu hình được, không mutate đầu vào."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from enum import StrEnum
import re
from typing import Any, Mapping, Protocol, Sequence, TypeVar, runtime_checkable

from hmda.core.exceptions import DataValidationError
from hmda.data.contracts import DataBatch, ValidationSummary


PayloadT = TypeVar("PayloadT")


@runtime_checkable
class DataValidator(Protocol[PayloadT]):
    def validate(
        self, batch: DataBatch[PayloadT], *, config: Mapping[str, Any]
    ) -> ValidationSummary:
        """Trả report; không tự sửa dữ liệu để vượt quality gate."""
        ...


class QualitySeverity(StrEnum):
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True, slots=True)
class QualityIssue:
    rule_id: str
    layer: str
    severity: QualitySeverity
    affected_count: int
    denominator: int
    sample_ids: tuple[str, ...] = ()
    rule_version: str = "1"
    message: str = ""

    def __post_init__(self) -> None:
        text_fields = (self.rule_id, self.layer, self.rule_version)
        if (
            any(
                not isinstance(value, str) or not value.strip()
                for value in text_fields
            )
        ):
            raise DataValidationError("rule_id, layer và rule_version không được rỗng")
        counts = (self.affected_count, self.denominator)
        if any(isinstance(value, bool) or not isinstance(value, int) for value in counts):
            raise DataValidationError("Quality count và denominator phải là số nguyên")
        if self.affected_count < 0 or self.denominator < 0:
            raise DataValidationError("Quality count và denominator không được âm")
        if self.affected_count > self.denominator:
            raise DataValidationError("affected_count không được lớn hơn denominator")


@dataclass(frozen=True, slots=True)
class QualityRuleSpec:
    rule_id: str
    rule_type: str
    layer: str
    severity: QualitySeverity
    params: Mapping[str, Any] = field(default_factory=dict)
    version: str = "1"
    sample_limit: int = 5


class ConfigurableDataValidator:
    """Đánh giá các rule generic trên sequence record dạng mapping."""

    SUPPORTED_RULE_TYPES = frozenset(
        {
            "required_columns",
            "field_type",
            "allowed_values",
            "missing_key",
            "duplicate_key",
            "checksum_match",
            "matches_pattern",
            "parseable_number",
        }
    )

    def validate(
        self,
        batch: DataBatch[Sequence[Mapping[str, Any]]],
        *,
        config: Mapping[str, Any],
    ) -> ValidationSummary:
        rows = self._validate_payload(batch.payload)
        specs = self._parse_specs(config)
        sample_id_field = config.get("sample_id_field")
        if sample_id_field is not None and (
            not isinstance(sample_id_field, str) or not sample_id_field.strip()
        ):
            raise DataValidationError("sample_id_field phải là chuỗi không rỗng")

        issues = tuple(
            issue
            for spec in specs
            if (issue := self._evaluate(spec, rows, batch, sample_id_field)) is not None
        )
        error_count = sum(issue.severity is QualitySeverity.ERROR for issue in issues)
        warning_count = sum(issue.severity is QualitySeverity.WARNING for issue in issues)
        return ValidationSummary(
            is_valid=error_count == 0,
            issues=issues,
            metadata={
                "evaluated_rule_count": len(specs),
                "failed_rule_count": len(issues),
                "error_count": error_count,
                "warning_count": warning_count,
            },
        )

    @staticmethod
    def _validate_payload(
        payload: Sequence[Mapping[str, Any]],
    ) -> tuple[Mapping[str, Any], ...]:
        if isinstance(payload, (str, bytes, bytearray)) or not isinstance(
            payload, Sequence
        ):
            raise DataValidationError("Validator yêu cầu sequence các record dạng mapping")
        rows = tuple(payload)
        if any(not isinstance(row, Mapping) for row in rows):
            raise DataValidationError("Mỗi record phải là mapping")
        return rows

    def _parse_specs(self, config: Mapping[str, Any]) -> tuple[QualityRuleSpec, ...]:
        raw_rules = config.get("rules", ())
        if isinstance(raw_rules, (str, bytes)) or not isinstance(raw_rules, Sequence):
            raise DataValidationError("quality.rules phải là danh sách")
        defaults = config.get("defaults", {})
        if not isinstance(defaults, Mapping):
            raise DataValidationError("quality.defaults phải là mapping")
        default_limit = defaults.get("sample_limit", 5)
        specs: list[QualityRuleSpec] = []
        seen_ids: set[str] = set()
        for raw_rule in raw_rules:
            if not isinstance(raw_rule, Mapping):
                raise DataValidationError("Mỗi quality rule phải là mapping")
            rule_id = self._required_text(raw_rule, "rule_id")
            if rule_id in seen_ids:
                raise DataValidationError(f"Duplicate quality rule_id: {rule_id}")
            seen_ids.add(rule_id)
            rule_type = self._required_text(raw_rule, "type")
            if rule_type not in self.SUPPORTED_RULE_TYPES:
                raise DataValidationError(f"Rule type không hỗ trợ: {rule_type}")
            layer = self._required_text(raw_rule, "layer")
            raw_version = raw_rule.get("version", "1")
            if raw_version is None or not str(raw_version).strip():
                raise DataValidationError("Quality rule version không được rỗng")
            version = str(raw_version)
            try:
                severity = QualitySeverity(str(raw_rule.get("severity", "ERROR")).upper())
            except ValueError as exc:
                raise DataValidationError("severity phải là ERROR hoặc WARNING") from exc
            sample_limit = raw_rule.get("sample_limit", default_limit)
            if (
                isinstance(sample_limit, bool)
                or not isinstance(sample_limit, int)
                or sample_limit < 0
            ):
                raise DataValidationError("sample_limit phải là số nguyên không âm")
            params = raw_rule.get("params", {})
            if not isinstance(params, Mapping):
                raise DataValidationError("rule params phải là mapping")
            specs.append(
                QualityRuleSpec(
                    rule_id=rule_id,
                    rule_type=rule_type,
                    layer=layer,
                    severity=severity,
                    params=dict(params),
                    version=version,
                    sample_limit=sample_limit,
                )
            )
        return tuple(
            sorted(specs, key=lambda spec: (spec.rule_id, spec.layer, spec.version))
        )

    @staticmethod
    def _required_text(mapping: Mapping[str, Any], key: str) -> str:
        value = mapping.get(key)
        if not isinstance(value, str) or not value.strip():
            raise DataValidationError(f"Quality rule thiếu {key}")
        return value

    def _evaluate(
        self,
        spec: QualityRuleSpec,
        rows: tuple[Mapping[str, Any], ...],
        batch: DataBatch[Sequence[Mapping[str, Any]]],
        sample_id_field: str | None,
    ) -> QualityIssue | None:
        evaluators = {
            "required_columns": self._required_columns,
            "field_type": self._field_type,
            "allowed_values": self._allowed_values,
            "missing_key": self._missing_key,
            "duplicate_key": self._duplicate_key,
            "checksum_match": self._checksum_match,
            "matches_pattern": self._matches_pattern,
            "parseable_number": self._parseable_number,
        }
        affected, denominator, affected_rows, message = evaluators[spec.rule_type](
            spec.params, rows, batch
        )
        if affected == 0:
            return None
        return QualityIssue(
            rule_id=spec.rule_id,
            layer=spec.layer,
            severity=spec.severity,
            affected_count=affected,
            denominator=denominator,
            sample_ids=self._sample_ids(
                affected_rows, sample_id_field, spec.sample_limit
            ),
            rule_version=spec.version,
            message=message,
        )

    @staticmethod
    def _required_columns(params, rows, batch):
        columns = ConfigurableDataValidator._text_list(params, "columns")
        actual_columns = set().union(*(row.keys() for row in rows)) if rows else set()
        missing = [column for column in columns if column not in actual_columns]
        return len(missing), len(columns), (), "Thiếu required column"

    @staticmethod
    def _field_type(params, rows, batch):
        field_name = ConfigurableDataValidator._required_text(params, "field")
        expected_name = ConfigurableDataValidator._required_text(params, "expected")

        def matches(value: Any) -> bool:
            if expected_name == "string":
                return isinstance(value, str)
            if expected_name == "integer":
                return isinstance(value, int) and not isinstance(value, bool)
            if expected_name == "number":
                return isinstance(value, (int, float)) and not isinstance(value, bool)
            if expected_name == "boolean":
                return isinstance(value, bool)
            if expected_name == "mapping":
                return isinstance(value, Mapping)
            raise DataValidationError(f"Expected type không hỗ trợ: {expected_name}")

        failed = tuple(row for row in rows if not matches(row.get(field_name)))
        return len(failed), len(rows), failed, "Field không đúng kiểu yêu cầu"

    @staticmethod
    def _allowed_values(params, rows, batch):
        field_name = ConfigurableDataValidator._required_text(params, "field")
        allowed = params.get("values")
        if isinstance(allowed, (str, bytes)) or not isinstance(allowed, Sequence):
            raise DataValidationError("allowed_values.params.values phải là danh sách")
        allowed_values = tuple(allowed)
        failed = tuple(row for row in rows if row.get(field_name) not in allowed_values)
        return len(failed), len(rows), failed, "Field có token/value ngoài miền cho phép"

    @staticmethod
    def _missing_key(params, rows, batch):
        fields = ConfigurableDataValidator._text_list(params, "fields")
        failed = tuple(
            row
            for row in rows
            if any(row.get(field_name) in (None, "") for field_name in fields)
        )
        return len(failed), len(rows), failed, "Technical/business key bị thiếu"

    @staticmethod
    def _duplicate_key(params, rows, batch):
        fields = ConfigurableDataValidator._text_list(params, "fields")

        def key_for(row: Mapping[str, Any]) -> tuple[Any, ...] | None:
            key = tuple(row.get(field_name) for field_name in fields)
            return None if any(value in (None, "") for value in key) else key

        keys = tuple(key_for(row) for row in rows)
        try:
            counts = Counter(key for key in keys if key is not None)
        except TypeError as exc:
            raise DataValidationError(
                "duplicate_key chỉ hỗ trợ giá trị key có thể hash"
            ) from exc
        failed = tuple(
            row
            for row, key in zip(rows, keys, strict=True)
            if key is not None and counts[key] > 1
        )
        return len(failed), len(rows), failed, "Key bị trùng"

    @staticmethod
    def _checksum_match(params, rows, batch):
        expected = ConfigurableDataValidator._required_text(params, "expected")
        actual = batch.metadata.get("content_checksum", batch.source.checksum)
        failed = int(actual != expected)
        return failed, 1, (), "Checksum thực tế không khớp checksum kỳ vọng"

    @staticmethod
    def _matches_pattern(params, rows, batch):
        field_name = ConfigurableDataValidator._required_text(params, "field")
        pattern = ConfigurableDataValidator._required_text(params, "pattern")
        ignored = ConfigurableDataValidator._optional_values(params, "ignore_values")
        try:
            compiled = re.compile(pattern)
        except re.error as exc:
            raise DataValidationError("Regex của matches_pattern không hợp lệ") from exc
        failed = tuple(
            row
            for row in rows
            if row.get(field_name) not in ignored
            and (
                not isinstance(row.get(field_name), str)
                or compiled.fullmatch(row.get(field_name)) is None
            )
        )
        return len(failed), len(rows), failed, "Field không khớp định dạng yêu cầu"

    @staticmethod
    def _parseable_number(params, rows, batch):
        field_name = ConfigurableDataValidator._required_text(params, "field")
        ignored = ConfigurableDataValidator._optional_values(params, "ignore_values")

        def is_parseable(value: Any) -> bool:
            if value in ignored or isinstance(value, bool) or value is None:
                return value in ignored
            try:
                parsed = Decimal(str(value))
            except (InvalidOperation, ValueError):
                return False
            return parsed.is_finite()

        failed = tuple(row for row in rows if not is_parseable(row.get(field_name)))
        return len(failed), len(rows), failed, "Field không parse được thành số"

    @staticmethod
    def _text_list(params: Mapping[str, Any], key: str) -> tuple[str, ...]:
        values = params.get(key)
        if isinstance(values, (str, bytes)) or not isinstance(values, Sequence) or not values:
            raise DataValidationError(f"{key} phải là danh sách chuỗi không rỗng")
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise DataValidationError(f"{key} phải là danh sách chuỗi không rỗng")
        return tuple(values)

    @staticmethod
    def _optional_values(params: Mapping[str, Any], key: str) -> tuple[Any, ...]:
        values = params.get(key, ())
        if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
            raise DataValidationError(f"{key} phải là danh sách")
        return tuple(values)

    @staticmethod
    def _sample_ids(
        rows: Sequence[Mapping[str, Any]],
        sample_id_field: str | None,
        sample_limit: int,
    ) -> tuple[str, ...]:
        if sample_id_field is None or sample_limit == 0:
            return ()
        samples: list[str] = []
        for row in rows:
            value = row.get(sample_id_field)
            if value not in (None, ""):
                samples.append(str(value))
            if len(samples) == sample_limit:
                break
        return tuple(samples)


def require_publishable(validation: ValidationSummary) -> None:
    """Chặn publish khi summary không hợp lệ hoặc còn quality ERROR."""

    blocking_issues = tuple(
        issue
        for issue in validation.issues
        if isinstance(issue, QualityIssue) and issue.severity is QualitySeverity.ERROR
    )
    if not validation.is_valid or blocking_issues:
        rule_ids = ", ".join(issue.rule_id for issue in blocking_issues)
        detail = f": {rule_ids}" if rule_ids else ""
        raise DataValidationError(f"Quality ERROR chặn publish{detail}")

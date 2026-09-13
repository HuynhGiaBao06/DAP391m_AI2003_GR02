"""Các exception miền hạ tầng dùng chung của package."""

from __future__ import annotations


class HMDAError(Exception):
    """Lớp gốc cho lỗi có thể xử lý của package HMDA."""


class ProjectRootNotFoundError(HMDAError):
    """Không tìm thấy project root chứa đủ marker bắt buộc."""


class ConfigurationError(HMDAError):
    """Cấu hình thiếu, sai kiểu hoặc mâu thuẫn."""

    def __init__(self, message: str, *, field_path: str | None = None) -> None:
        self.field_path = field_path
        prefix = f"{field_path}: " if field_path else ""
        super().__init__(prefix + message)


class MissingEnvironmentVariableError(ConfigurationError):
    """Thiếu biến môi trường bắt buộc mà không để lộ giá trị bí mật."""


class DataContractError(HMDAError):
    """Đầu vào hoặc đầu ra không thỏa hợp đồng dữ liệu."""


class SourceIdentityError(DataContractError):
    """Source identity hoặc checksum không thỏa hợp đồng."""


class DataLoadError(DataContractError):
    """Source bytes không thể được parse mà vẫn giữ hợp đồng raw."""


class DataValidationError(DataContractError):
    """Cấu hình hoặc payload không thể được quality validator đánh giá."""


class RepositoryError(HMDAError):
    """Repository không thể hoàn thành thao tác lưu trữ."""


class SnapshotError(HMDAError):
    """Vòng đời hoặc tính bất biến của snapshot bị vi phạm."""


class ServiceError(HMDAError):
    """Service không thể hoàn thành yêu cầu theo hợp đồng."""

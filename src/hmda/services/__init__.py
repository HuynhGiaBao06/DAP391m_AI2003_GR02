"""Service contracts dùng bởi API và các adapter giao diện."""

from hmda.services.prediction_service import PredictionResult, PredictionService
from hmda.services.result_service import ResultService

__all__ = ["PredictionResult", "PredictionService", "ResultService"]

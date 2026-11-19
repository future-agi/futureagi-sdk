import re
import copy
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse

from fi.api.types import HttpMethod, RequestConfig
from fi.evals.evaluator import EvalResponseHandler, Evaluator
from fi.evals.templates import (
    DataPrivacyCompliance,
    PromptInjection,
    Sexist,
    Tone,
    Toxicity,
    BiasDetection,
)
from fi.evals.protect_input_adapter import ProtectInputAdapter
from fi.utils.routes import Routes
from fi.utils.utils import get_keys_from_env, get_base_url_from_env
from fi.utils.errors import InvalidAuthError, SDKException, InvalidValueType, MissingRequiredKey
from pydantic import ValidationError

PROTECT_FLASH_ID = "76"
SUPPORT_PROTECT_FLASH = True  # feature toggle

from ._protect_protect_sanitize_reason import _ProtectSanitizeReasonMethods
from ._protect_protect_protect import _ProtectProtectMethods

class Protect(_ProtectSanitizeReasonMethods, _ProtectProtectMethods):
    """Client for protecting against unwanted content using various metrics"""

    def __init__(self,
                 fi_api_key: Optional[str] = None,
                 fi_secret_key: Optional[str] = None,
                 fi_base_url: Optional[str] = None,
                 evaluator: Optional[Evaluator] = None):
        """
        Initialize Protect Class

        Args:
            evaluator: Instance of Evaluator to use for evaluations. If None, creates a new one.
        """
        env_api_key, env_secret_key = get_keys_from_env()
        fi_api_key = env_api_key or fi_api_key
        fi_secret_key = env_secret_key or fi_secret_key
        fi_base_url = get_base_url_from_env() or fi_base_url
        if not fi_api_key or not fi_secret_key:
            raise InvalidAuthError("API key or secret key is missing for Protect initialization.")

        self.evaluator = evaluator if evaluator is not None else Evaluator(
            fi_api_key=fi_api_key,
            fi_secret_key=fi_secret_key,
            fi_base_url=fi_base_url
        )

        # Map metric names to their corresponding template classes
        self.metric_map = {
            "toxicity": Toxicity,
            "bias_detection": BiasDetection,
            "prompt_injection": PromptInjection,
            "data_privacy_compliance": DataPrivacyCompliance,
            # Deprecated aliases (still supported)
            "content_moderation": Toxicity,
            "security": PromptInjection,
        }
        self._deprecated_metrics = {
            "content_moderation": "toxicity",
            "security": "prompt_injection",
        }


protect = lambda inputs, protect_rules, action="Response cannot be generated as the input fails the checks", reason=False, timeout=30000: Protect().protect(inputs, protect_rules, action, reason, timeout)

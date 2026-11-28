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
from fi._credentials import MissingAuthError, resolve as resolve_credentials
from fi.utils.errors import SDKException, InvalidValueType, MissingRequiredKey
from pydantic import ValidationError

PROTECT_FLASH_ID = "76"
SUPPORT_PROTECT_FLASH = True  # feature toggle

from ._protect_protect_sanitize_reason import _ProtectSanitizeReasonMethods
from ._protect_protect_protect import _ProtectProtectMethods

def resolve_key_pair(
    fi_api_key: Optional[str],
    fi_secret_key: Optional[str],
    fi_base_url: Optional[str],
) -> Tuple[str, str, str]:
    """The key pair and base URL for a Protect client, resolved by ``fi._credentials``.

    The keys are taken as a pair: both from the arguments, or (when neither argument is given)
    both from ``FI_API_KEY`` / ``FI_SECRET_KEY``, then the saved login bound to the base URL.
    The base URL is the argument, then ``FI_BASE_URL``, as for every other client. A pair with a
    missing or empty key raises :class:`fi.errors.MissingAuthError` before any request.
    """
    creds = resolve_credentials(fi_api_key, fi_secret_key, fi_base_url)
    if not creds.complete:
        raise MissingAuthError(
            creds.api_key or None,
            creds.secret_key or None,
            base_url=creds.base_url,
            login_skipped=creds.login_skipped,
        )
    return str(creds.api_key), str(creds.secret_key), creds.base_url


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
            fi_api_key: FutureAGI API key. Give it together with ``fi_secret_key``.
            fi_secret_key: FutureAGI secret key. Give it together with ``fi_api_key``.
            fi_base_url: Base URL for the API; without it ``FI_BASE_URL`` applies.
            evaluator: Instance of Evaluator to use for evaluations. If None, creates a new one.

        The key pair comes from one place: both keys from the arguments, or both from
        ``FI_API_KEY`` and ``FI_SECRET_KEY`` when neither argument is given. One key from the
        arguments with the other one left out or empty raises
        :class:`fi.errors.MissingAuthError`, and so does a missing pair, before any request.
        """
        fi_api_key, fi_secret_key, fi_base_url = resolve_key_pair(fi_api_key, fi_secret_key, fi_base_url)

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
            # Deprecated aliases (supported)
            "content_moderation": Toxicity,
            "security": PromptInjection,
        }
        self._deprecated_metrics = {
            "content_moderation": "toxicity",
            "security": "prompt_injection",
        }


protect = lambda inputs, protect_rules, action="Response cannot be generated as the input fails the checks", reason=False, timeout=30000: Protect().protect(inputs, protect_rules, action, reason, timeout)

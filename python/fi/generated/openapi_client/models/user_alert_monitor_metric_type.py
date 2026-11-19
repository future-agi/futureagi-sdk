from enum import Enum


class UserAlertMonitorMetricType(str, Enum):
    COUNT_OF_ERRORS = "count_of_errors"
    DAILY_TOKENS_SPENT = "daily_tokens_spent"
    ERROR_FREE_SESSION_RATES = "error_free_session_rates"
    ERROR_RATES_FOR_FUNCTION_CALLING = "error_rates_for_function_calling"
    EVALUATION_METRICS = "evaluation_metrics"
    LLM_API_FAILURE_RATES = "llm_api_failure_rates"
    LLM_RESPONSE_TIME = "llm_response_time"
    MONTHLY_TOKENS_SPENT = "monthly_tokens_spent"
    SERVICE_PROVIDER_ERROR_RATES = "service_provider_error_rates"
    SPAN_RESPONSE_TIME = "span_response_time"
    TOKEN_USAGE = "token_usage"

    def __str__(self) -> str:
        return str(self.value)

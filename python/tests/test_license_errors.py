"""Source-recorded FA license denial; no server or provider calls."""
import ast
import asyncio
import json
from pathlib import Path

import httpx
import pytest

import fi
import fi.errors as errors
from fi._core.errors import error_class_for
from fi.tracing import AsyncTracingClient, TracingClient
from fi.futureagi_client import EvalsClient

ROOT = Path(__file__).resolve().parents[2]
BODY = json.loads((Path(__file__).parent / 'fixtures/license_missing.json').read_text())['body']
# FA tracer/views/feed/{list_view,detail_view,tab_views,linear_issue_view}.py
# all inherit ErrorFeedLicenseRequired. No Falcon/SCIM/audit SDK routes are exposed.
FEED_MODULES = [
    'tracing/list_error_feed_issues', 'tracing/get_error_feed_issue',
    'tracing/get_error_feed_issue_stats', 'tracer/tracer_feed_issues_partial_update',
    'tracer/tracer_feed_issues_create_linear_issue_create',
    'tracer/tracer_feed_issues_deep_analysis_create',
    'tracer/tracer_feed_issues_overview_list', 'tracer/tracer_feed_issues_redirect_list',
    'tracer/tracer_feed_issues_root_cause_list', 'tracer/tracer_feed_issues_sidebar_list',
    'tracer/tracer_feed_issues_traces_list', 'tracer/tracer_feed_issues_trends_list',
]
LEGACY_ERRORS = '''SDKException DatasetError DatasetNotFoundError DatasetAuthError
DatasetValidationError RateLimitError ServerError UnexpectedDataFormatError
ServiceUnavailableError MissingAuthError InvalidAuthError InvalidAdditionalHeaders
InvalidNumberOfEmbeddings InvalidValueType InvalidSupportedType MissingRequiredKey
MissingRequiredConfigForEvalTemplate FileNotFoundException UnsupportedFileType
TemplateAlreadyExists TemplateNotFound'''.split()


@pytest.mark.parametrize('operation', [None, 'tracing.issues'])
def test_recorded_license_missing_is_typed_and_actionable(operation):
    err = errors.api_error(402, BODY, {'X-Request-Id': 'req-license'}, operation=operation)
    assert type(err).__name__ == 'LicenseRequiredError'
    assert isinstance(err, errors.PaymentRequiredError)
    assert isinstance(err, errors.FutureAGIAPIError)
    assert err.status_code == 402 and err.code == 'LICENSE_MISSING'
    assert err.payload == BODY and err.request_id == 'req-license'
    assert err.get_error_code() == 'LICENSE_REQUIRED'
    assert 'Enterprise licence on this server' in str(err)
    assert 'LICENSE_MISSING' in str(err)
    assert "Feature 'error_feed' needs" in str(err)
    assert 'Upgrade your plan' not in str(err)
    assert 'hosted' not in str(err).lower()
    assert err.to_dict()['name'] == 'LicenseRequiredError'
    if operation:
        assert operation in str(err)


@pytest.mark.parametrize('detail,subject', [
    ({'feature': 'error_feed'}, "Feature 'error_feed'"),
    ({'feature': '  error_\nfeed  '}, "Feature 'error_ feed'"),
    ({'feature': 'x' * 600}, "Feature '" + 'x' * 500 + "...'"),
    ({'feature': ''}, 'This feature'),
    ({'feature': 42}, 'This feature'),
    ({}, 'This feature'),
    (None, 'This feature'),
    ('not an object', 'This feature'),
])
@pytest.mark.parametrize('envelope', ['nested', 'top', 'result'])
def test_license_message_names_only_valid_bounded_features(detail, subject, envelope):
    error = {'code': 'LICENSE_MISSING', 'detail': detail}
    payload = {'error': error} if envelope == 'nested' else error
    if envelope == 'result':
        payload = {'status': False, 'result': {'error': error}}
    err = errors.api_error(402, payload)
    assert f'{subject} needs an Enterprise licence on this server' in str(err)
    assert '\n' not in str(err)
    assert err.payload == payload


def test_shared_contract_records_payment_required_status_family():
    contracts = json.loads((ROOT / 'tests/fixtures/contracts/operations.json').read_text())
    assert contracts['status_classes']['402'] == 'PaymentRequiredError'
    assert contracts['fa_codes']['payment_required'] == 402


def test_public_error_help_is_self_contained():
    for name in errors.__all__:
        value = getattr(errors, name)
        if isinstance(value, type) and issubclass(value, Exception):
            assert name in errors.__doc__, name
    assert "another distribution's overwrite path" in errors.__doc__


def test_platform_check_verifies_licensing_doc_overrides():
    check = (ROOT / 'scripts/platform/check.sh').read_text()
    assert 'python3 scripts/licensed_operation_docs.py --check' in check


def test_tracing_readme_explains_license_before_examples():
    introduction = (ROOT / 'python/fi/tracing/README.md').read_text().split('## Python')[0]
    for wording in ('Enterprise licence', 'self-hosted', 'eligible cloud plan',
                    'LicenseRequiredError', 'LICENSE_MISSING', 'issues', 'issue_stats', 'issueStats'):
        assert wording in introduction


@pytest.mark.parametrize('body', [None, {'code': 'unknown_payment'}, {'code': 'ENTITLEMENT_DENIED'}])
def test_other_402_is_payment_required_not_license(body):
    err = errors.api_error(402, body)
    assert type(err).__name__ == 'PaymentRequiredError'
    assert isinstance(err, errors.FutureAGIAPIError)
    assert err.get_error_code() == 'PAYMENT_REQUIRED'
    assert err.code == (body['code'] if body else 'http_402')


@pytest.mark.parametrize('status,name', [
    (400, 'BadRequestError'), (401, 'AuthenticationError'), (403, 'PermissionDeniedError'),
    (404, 'NotFoundError'), (409, 'ConflictError'), (413, 'PayloadTooLargeError'),
    (418, 'FutureAGIAPIError'), (422, 'UnprocessableEntityError'), (429, 'RateLimitError'),
    (500, 'ServerError'), (503, 'ServerError'),
])
def test_license_code_cannot_escape_402_family(status, name):
    assert error_class_for(status, 'LICENSE_MISSING').__name__ == name
    assert error_class_for(status).__name__ == name


@pytest.mark.parametrize('status,code,name', [
    (404, 'product_not_admitted', 'ProductNotAvailableError'),
    (409, 'idempotency_key_in_progress', 'IdempotencyKeyInProgressError'),
    (422, 'idempotency_key_reused', 'IdempotencyKeyReusedError'),
])
def test_existing_code_mappings_unchanged(status, code, name):
    assert error_class_for(status, code).__name__ == name
    assert error_class_for(402, code).__name__ == 'PaymentRequiredError'


def test_public_exports_and_all_published_0613_error_names_remain():
    import fi.utils.errors as legacy
    for name in LEGACY_ERRORS:
        assert issubclass(getattr(legacy, name), Exception), name
    for name in ('PaymentRequiredError', 'LicenseRequiredError'):
        assert name in errors.__all__
        assert name in fi.__all__ and name in dir(fi)
        assert getattr(fi, name) is getattr(errors, name)


@pytest.mark.parametrize('asynchronous', [False, True])
def test_tracing_transport_raises_license_error_without_retry(asynchronous):
    calls = []
    def answer(request):
        calls.append(request.url.path)
        return httpx.Response(402, json=BODY)
    cls = fi.AsyncFutureAGIClient if asynchronous else fi.FutureAGIClient
    client = cls(api_key='k-test-1234', secret_key='s-test-1234', base_url='http://api.test')
    transport = client.generated_client._httpx_args['transport']
    if asynchronous:
        transport._wrapped_async = httpx.MockTransport(answer)
        async def run():
            try:
                await client.tracing.issues()
            finally:
                await client.aclose()
        call = lambda: asyncio.run(run())
    else:
        transport._wrapped = httpx.MockTransport(answer)
        call = client.tracing.issues
    try:
        with pytest.raises(errors.FutureAGIAPIError) as caught:
            call()
        assert type(caught.value).__name__ == 'LicenseRequiredError'
        assert calls == ['/tracer/feed/issues/']
    finally:
        if not asynchronous:
            client.close()


@pytest.mark.parametrize('cls', [TracingClient, AsyncTracingClient])
@pytest.mark.parametrize('method', ['issues', 'issue', 'issue_stats'])
def test_public_licensed_method_docs(cls, method):
    doc = getattr(cls, method).__doc__ or ''
    assert 'Enterprise licence' in doc
    assert 'LicenseRequiredError' in doc
    assert 'self-hosted' in doc and 'cloud plan' in doc


@pytest.mark.parametrize('module', FEED_MODULES)
def test_generated_licensed_method_docs(module):
    path = ROOT / 'python/fi/generated/openapi_client/api' / (module + '.py')
    functions = [n for n in ast.parse(path.read_text()).body
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in
                 ('sync', 'sync_detailed', 'asyncio', 'asyncio_detailed')]
    assert functions
    for node in functions:
        doc = ast.get_docstring(node) or ''
        assert 'Enterprise licence' in doc, node.name
        assert 'LicenseRequiredError' in doc, node.name


@pytest.mark.parametrize('method', ['add_dataset_user_eval', 'edit_and_run_dataset_user_eval'])
def test_conditional_turing_gate_docs(method):
    # FA develop_dataset.py:8981,9409 calls turing_oss_gate_for_template, not LICENSE_MISSING.
    doc = getattr(EvalsClient, method).__doc__ or ''
    assert 'Enterprise licence' in doc
    assert 'Turing/Protect' in doc and 'PaymentRequiredError' in doc
    assert 'ENTITLEMENT_DENIED' in doc


def test_legacy_dataset_conditional_turing_docs():
    path = ROOT / 'python/fi/datasets/dataset.py'
    dataset = next(n for n in ast.parse(path.read_text()).body
                   if isinstance(n, ast.ClassDef) and n.name == 'Dataset')
    method = next(n for n in dataset.body
                  if isinstance(n, ast.FunctionDef) and n.name == 'add_evaluation')
    doc = ast.get_docstring(method) or ''
    for wording in ('Enterprise licence', 'Turing/Protect', 'ENTITLEMENT_DENIED',
                    'DatasetError', 'PaymentRequiredError', 'FutureAGIClient', 'Code evaluations'):
        assert wording in doc


def test_python_only_playground_conditional_turing_docs():
    path = ROOT / 'python/fi/evals/_manager_eval_template_manager_get_template_charts.py'
    methods = next(n for n in ast.parse(path.read_text()).body if isinstance(n, ast.ClassDef))
    method = next(n for n in methods.body
                  if isinstance(n, ast.FunctionDef) and n.name == 'run_playground')
    doc = ast.get_docstring(method) or ''
    for wording in ('Enterprise licence', 'Turing/Protect', 'ENTITLEMENT_DENIED',
                    'Exception', 'LicenseRequiredError', 'Code evaluations', 'cloud plan'):
        assert wording in doc


@pytest.mark.parametrize('operation', ['add_user_eval', 'edit_and_run_user_eval'])
def test_generated_conditional_turing_docs(operation):
    path = ROOT / 'python/fi/generated/openapi_client/api/model_hub' / f'model_hub_develops_{operation}_create.py'
    functions = [n for n in ast.parse(path.read_text()).body
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in
                 ('sync', 'sync_detailed', 'asyncio', 'asyncio_detailed')]
    assert functions
    for node in functions:
        doc = ast.get_docstring(node) or ''
        assert 'Enterprise licence' in doc
        assert 'Turing/Protect' in doc and 'PaymentRequiredError' in doc
        assert 'ENTITLEMENT_DENIED' in doc

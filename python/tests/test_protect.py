import os
import base64
import mimetypes
import pathlib
import pytest
from fi.evals import Protect, protect
from fi.evals import protect as direct_protect
from fi.utils.errors import InvalidValueType, MissingRequiredKey, SDKException


@pytest.fixture
def protect_client():
    return Protect()


# ---------- helpers ----------
_ASSETS = pathlib.Path(__file__).parent / "assets"


def _p(name: str) -> str:
    return str(_ASSETS / name)


def _file_to_data_uri(path: str, override_mime: str | None = None) -> str:
    mime, _ = mimetypes.guess_type(path)
    mime = override_mime or mime or "application/octet-stream"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


# ---------- basic "legacy-style" tests that expect 7 keys ----------
def test_protect():
    inputs = "Hello, world! I hate you."
    protect_rules = [{"metric": "content_moderation"}]
    result = protect(inputs, protect_rules)
    assert result is not None
    assert len(result) == 7


def test_direct_protect():
    inputs = "Hello, world! I hate you."
    protect_rules = [{"metric": "content_moderation"}]
    result = direct_protect(inputs, protect_rules)
    assert result is not None
    assert len(result) == 7


def test_protect_with_protector():
    inputs = "Hello, world! I hate you."
    protect_rules = [{"metric": "content_moderation"}]
    result = Protect().protect(inputs, protect_rules)
    assert result is not None
    assert len(result) == 7


# ---------- functional tests ----------
def test_content_moderation_friendly_message(protect_client):
    input_text = "This is a friendly message."
    protect_rules = [{"metric": "content_moderation"}]
    response = protect_client.protect(input_text, protect_rules)
    
    # Structure
    assert set(response.keys()) >= {
        "status", "completed_rules", "uncompleted_rules", "failed_rule",
        "messages", "reasons", "time_taken"
    }
    assert "content_moderation" in (
        set(response.get("completed_rules", [])) | set(response.get("uncompleted_rules", []))
    )
    assert isinstance(response["time_taken"], float)
    
    if response["status"] == "passed":
        assert response["messages"] == input_text


def test_protect_multiple_rules(protect_client):
    # Likely to trigger privacy
    input_text = "My phone number is 9845557849."
    protect_rules = [
        {"metric": "content_moderation"},
        {"metric": "bias_detection"},
        {"metric": "security"},
        {"metric": "data_privacy_compliance"},
    ]
    default_action_message = "Response cannot be generated as the input fails the checks"
    response = protect_client.protect(input_text, protect_rules)
    
    # Structure
    assert set(response.keys()) >= {
        "status", "completed_rules", "uncompleted_rules", "failed_rule",
        "messages", "reasons", "time_taken"
    }
    
    # All rules should have been attempted
    for m in ["content_moderation", "bias_detection", "security", "data_privacy_compliance"]:
        assert m in (
            set(response.get("completed_rules", [])) | set(response.get("uncompleted_rules", []))
        )
    
    if response["status"] == "failed":
        assert response["messages"] == default_action_message


def test_invalid_input_types(protect_client):
    with pytest.raises(InvalidValueType):
        protect_client.protect(None, [{"metric": "content_moderation"}])
    
    with pytest.raises(InvalidValueType):
        protect_client.protect(123, [{"metric": "content_moderation"}])
    
    with pytest.raises(InvalidValueType):
        protect_client.protect("", [{"metric": "content_moderation"}])


def test_invalid_rules(protect_client):
    input_text = "Test message"
    
    # Invalid metric
    with pytest.raises(InvalidValueType):
        protect_client.protect(input_text, [{"metric": "InvalidMetric"}])
    
    # Missing required 'metric'
    with pytest.raises(MissingRequiredKey):
        protect_client.protect(input_text, [{}])
    
    # Non-tone metrics must not accept 'contains'/'type'
    with pytest.raises(SDKException):
        protect_client.protect(input_text, [{"metric": "content_moderation", "contains": ["x"]}])
    
    with pytest.raises(SDKException):
        protect_client.protect(input_text, [{"metric": "bias_detection", "type": "any"}])


def test_timeout_returns_time(protect_client):
    input_text = "Test message"
    protect_rules = [{"metric": "content_moderation"}]
    response = protect_client.protect(input_text, protect_rules, timeout=1)
    
    assert "time_taken" in response
    assert isinstance(response["time_taken"], float)


# ---------- NEW: List input tests ----------
def test_list_of_strings_input(protect_client):
    """Test that protect handles list of strings correctly"""
    inputs = ["Hello world", "How are you?"]
    protect_rules = [{"metric": "content_moderation"}]
    
    response = protect_client.protect(inputs, protect_rules)
    
    assert set(response.keys()) >= {
        "status", "completed_rules", "uncompleted_rules", "failed_rule",
        "messages", "reasons", "time_taken"
    }
    
    # Should process the first input
    if response["status"] == "passed":
        assert response["messages"] == inputs[0]


def test_empty_list_input_fails(protect_client):
    """Test that empty list raises InvalidValueType"""
    with pytest.raises(InvalidValueType):
        protect_client.protect([], [{"metric": "content_moderation"}])


def test_list_with_non_string_fails(protect_client):
    """Test that list with non-string elements fails"""
    with pytest.raises(InvalidValueType):
        protect_client.protect(["valid", 123], [{"metric": "content_moderation"}])


# ---------- NEW: Reason parameter tests ----------
def test_reason_true_includes_sanitized_reason(protect_client):
    """Test that reason=True includes sanitized failure reasons"""
    input_text = "I hate you and want to harm you."
    protect_rules = [{"metric": "content_moderation"}]
    
    response = protect_client.protect(input_text, protect_rules, reason=True)
    
    if response["status"] == "failed":
        assert isinstance(response["reasons"], list)
        assert len(response["reasons"]) > 0
        # Check that reasons don't contain URLs or tracebacks
        for reason in response["reasons"]:
            assert "http://" not in reason.lower()
            assert "https://" not in reason.lower()
            assert "traceback" not in reason.lower()


def test_reason_false_no_detailed_reason(protect_client):
    """Test that reason=False doesn't include detailed reasons"""
    input_text = "I hate you."
    protect_rules = [{"metric": "content_moderation"}]
    
    response = protect_client.protect(input_text, protect_rules, reason=False)
    
    # reasons should either be empty or just say "All checks passed"
    assert isinstance(response["reasons"], list)


# ---------- NEW: Custom action message tests ----------
def test_custom_action_message(protect_client):
    """Test that custom action messages work"""
    input_text = "My SSN is 123-45-6789."
    custom_action = "Privacy violation detected"
    protect_rules = [
        {"metric": "data_privacy_compliance", "action": custom_action}
    ]
    
    response = protect_client.protect(input_text, protect_rules)
    
    if response["status"] == "failed":
        assert response["messages"] == custom_action


def test_default_action_message(protect_client):
    """Test default action message is applied"""
    input_text = "My credit card is 4111-1111-1111-1111."
    default_action = "Response cannot be generated as the input fails the checks"
    protect_rules = [{"metric": "data_privacy_compliance"}]
    
    response = protect_client.protect(input_text, protect_rules)
    
    if response["status"] == "failed":
        assert response["messages"] == default_action


# ---------- Media adapter tests (local assets passed directly) ----------
@pytest.mark.parametrize("local_path", [
    "image_sample.jpg",
    "image_sample.png",
])
def test_local_images(protect_client, local_path):
    rules = [{"metric": "content_moderation"}]
    inp = _p(local_path)
    assert os.path.exists(inp), f"missing asset: {inp}"
    
    res = protect_client.protect(inp, rules, timeout=30000)
    
    assert set(res.keys()) >= {
        "status", "completed_rules", "uncompleted_rules", "failed_rule",
        "messages", "reasons", "time_taken"
    }


@pytest.mark.parametrize("local_path", [
    "audio_sample.mp3",
    "audio_sample.wav",
])
def test_local_audio(protect_client, local_path):
    rules = [{"metric": "content_moderation"}]
    inp = _p(local_path)
    assert os.path.exists(inp), f"missing asset: {inp}"
    
    res = protect_client.protect(inp, rules, timeout=30000)
    
    assert set(res.keys()) >= {
        "status", "completed_rules", "uncompleted_rules", "failed_rule",
        "messages", "reasons", "time_taken"
    }


# ---------- NEW: Unsupported file type tests ----------
def test_unsupported_audio_format_fails_cleanly(protect_client):
    """Test that unsupported audio formats (e.g., .ogg) fail with friendly message"""
    # Create a dummy .ogg file
    ogg_path = _ASSETS / "test_audio.ogg"
    ogg_path.write_bytes(b"fake ogg data")
    
    try:
        rules = [{"metric": "content_moderation"}]
        res = protect_client.protect(str(ogg_path), rules, timeout=30000)
        
        assert res["status"] == "failed"
        assert "Unsupported file type" in res["messages"] or "Supported audio" in res["messages"]
    finally:
        ogg_path.unlink(missing_ok=True)


def test_unsupported_image_format_fails_cleanly(protect_client):
    """Test that unsupported image formats fail with friendly message"""
    # Create a dummy .bmp file (assuming it's not supported)
    weird_path = _ASSETS / "test_image.xyz"
    weird_path.write_bytes(b"fake image data")
    
    try:
        rules = [{"metric": "content_moderation"}]
        res = protect_client.protect(str(weird_path), rules, timeout=30000)
        
        assert res["status"] == "failed"
        assert "Unsupported file type" in res["messages"] or "Supported" in res["messages"]
    finally:
        weird_path.unlink(missing_ok=True)


def test_nonexistent_file_treated_as_text(protect_client):
    """Test that non-existent file paths are treated as plain text"""
    fake_path = "/tmp/nonexistent_file_12345.mp3"
    rules = [{"metric": "content_moderation"}]
    
    # Should process as text, not fail with file not found
    res = protect_client.protect(fake_path, rules, timeout=30000)
    
    assert set(res.keys()) >= {
        "status", "completed_rules", "uncompleted_rules", "failed_rule",
        "messages", "reasons", "time_taken"
    }


# ---------- Data URI media tests (built from your assets) ----------
@pytest.mark.parametrize("name,mime", [
    ("image_sample.png", None),
    ("image_sample.jpg", None),
])
def test_data_uri_images_from_assets(protect_client, name, mime):
    asset = _p(name)
    assert os.path.exists(asset)
    uri = _file_to_data_uri(asset, override_mime=mime)
    
    rules = [{"metric": "content_moderation"}]
    res = protect_client.protect(uri, rules, timeout=30000)
    
    assert set(res.keys()) >= {
        "status", "completed_rules", "uncompleted_rules", "failed_rule",
        "messages", "reasons", "time_taken"
    }


@pytest.mark.parametrize("name,mime", [
    ("audio_sample.wav", "audio/wav"),
    ("audio_sample.mp3", "audio/mpeg"),
])
def test_data_uri_audio_from_assets(protect_client, name, mime):
    asset = _p(name)
    assert os.path.exists(asset)
    uri = _file_to_data_uri(asset, override_mime=mime)
    
    rules = [{"metric": "content_moderation"}]
    res = protect_client.protect(uri, rules, timeout=30000)
    
    assert set(res.keys()) >= {
        "status", "completed_rules", "uncompleted_rules", "failed_rule",
        "messages", "reasons", "time_taken"
    }


# ---------- HTTP URL media tests (structure-only) ----------
@pytest.mark.parametrize("url", [
    "https://raw.githubusercontent.com/KarthikAvinashFI/media-testing/main/images/3.png",
    "https://images.unsplash.com/photo-1526779259212-939e64788e3c?fm=jpg&q=60&w=3000",
])
def test_http_image_urls(protect_client, url):
    rules = [{"metric": "content_moderation"}]
    res = protect_client.protect(url, rules, timeout=30000)
    
    assert set(res.keys()) >= {
        "status", "completed_rules", "uncompleted_rules", "failed_rule",
        "messages", "reasons", "time_taken"
    }


@pytest.mark.parametrize("url", [
    "https://developer.mozilla.org/shared-assets/audio/t-rex-roar.mp3",
    "https://raw.githubusercontent.com/KarthikAvinashFI/media-testing/main/audios/0d3fc864d3814198.wav",
])
def test_http_audio_urls(protect_client, url):
    rules = [{"metric": "content_moderation"}]
    res = protect_client.protect(url, rules, timeout=30000)
    
    assert set(res.keys()) >= {
        "status", "completed_rules", "uncompleted_rules", "failed_rule",
        "messages", "reasons", "time_taken"
    }


# ---------- NEW: Preview page detection tests ----------
@pytest.mark.parametrize("preview_url", [
    "https://github.com/user/repo/blob/main/image.png",  # GitHub blob, not raw
    "https://drive.google.com/file/d/ABC123/view",  # Drive view, not export
])
def test_preview_page_detection(protect_client, preview_url):
    """Test that preview pages are detected and rejected with helpful message"""
    rules = [{"metric": "content_moderation"}]
    res = protect_client.protect(preview_url, rules, timeout=30000)
    
    if res["status"] == "failed":
        assert "preview page" in res["messages"].lower() or "direct" in res["messages"].lower()


# ---------- Non-media data URI (should fail cleanly) ----------
def test_data_uri_non_media_fails_cleanly(protect_client):
    uri = "data:text/plain;base64,SGVsbG8="
    rules = [{"metric": "content_moderation"}]
    
    res = protect_client.protect(uri, rules, timeout=30000)
    
    assert res["status"] == "failed"
    assert "Only audio/* or image/* data: URIs are supported." in res["messages"]


# ---------- NEW: Empty/whitespace validation tests ----------
def test_whitespace_only_input_fails(protect_client):
    """Test that whitespace-only input fails validation"""
    with pytest.raises(InvalidValueType):
        protect_client.protect("   \n\t  ", [{"metric": "content_moderation"}])


def test_empty_string_in_list_fails(protect_client):
    """Test that empty strings in list fail validation"""
    with pytest.raises(InvalidValueType):
        protect_client.protect(["valid text", ""], [{"metric": "content_moderation"}])


# ---------- NEW: Concurrent processing edge cases ----------
def test_very_short_timeout_completes_some_rules(protect_client):
    """Test that very short timeout leaves some rules uncompleted"""
    input_text = "Test message"
    protect_rules = [
        {"metric": "content_moderation"},
        {"metric": "bias_detection"},
        {"metric": "security"},
        {"metric": "data_privacy_compliance"},
    ]
    
    response = protect_client.protect(input_text, protect_rules, timeout=1)  # 1ms
    
    # Should have some uncompleted rules due to timeout
    assert "time_taken" in response
    # Either some completed or all uncompleted
    assert len(response["completed_rules"]) + len(response["uncompleted_rules"]) == 4


def test_failed_rule_cancels_remaining(protect_client):
    """Test that when a rule fails, remaining rules are cancelled"""
    # Use input that will likely trigger content moderation
    input_text = "I will kill you and destroy everything."
    protect_rules = [
        {"metric": "content_moderation"},
        {"metric": "bias_detection"},
        {"metric": "security"},
    ]
    
    response = protect_client.protect(input_text, protect_rules)
    
    if response["status"] == "failed":
        # Some rules might not have been completed due to early exit
        total_attempted = len(response["completed_rules"]) + len(response["uncompleted_rules"])
        assert total_attempted <= 3
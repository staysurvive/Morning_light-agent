import pytest

from src.core.exceptions import BizException
from src.modules.knowledge.parser import extract_keywords, split_text, text_terms
from src.modules.knowledge.schema import KnowledgeBaseCreate
from src.core.network import assert_public_http_target
from src.modules.tool.service import _redact_config, _restore_redacted_headers, _validate_http_config


def test_fixed_chunking_respects_overlap():
    chunks = split_text("a" * 250, "fixed", 100, 20)

    assert [len(chunk) for chunk in chunks] == [100, 100, 90]
    assert chunks[0][-20:] == chunks[1][:20]


def test_chinese_terms_and_keywords_are_extracted():
    terms = text_terms("权限控制采用 RBAC，权限控制需要角色。")
    keywords = extract_keywords("权限控制采用 RBAC，权限控制需要角色。")

    assert "rbac" in terms
    assert "权限" in keywords


@pytest.mark.parametrize("strategy", ["vector", "hybrid"])
def test_unimplemented_knowledge_retrieval_strategies_are_rejected(strategy):
    with pytest.raises(ValueError):
        KnowledgeBaseCreate(name="test", retrieval_strategy=strategy)


def test_sensitive_tool_headers_are_redacted_without_mutating_source():
    config = {"headers": {"Authorization": "Bearer secret", "X-Trace": "visible"}}

    redacted = _redact_config(config)

    assert redacted["headers"]["Authorization"] == "***configured***"
    assert redacted["headers"]["X-Trace"] == "visible"
    assert config["headers"]["Authorization"] == "Bearer secret"


def test_redacted_headers_preserve_previous_secret_on_update():
    result = _restore_redacted_headers(
        {"headers": {"Authorization": "***configured***", "X-Trace": "new"}},
        {"headers": {"Authorization": "Bearer secret", "X-Trace": "old"}},
    )

    assert result["headers"] == {"Authorization": "Bearer secret", "X-Trace": "new"}


@pytest.mark.asyncio
async def test_private_network_target_is_rejected():
    with pytest.raises(BizException):
        await assert_public_http_target("http://127.0.0.1:8000/health")


@pytest.mark.parametrize(
    "config",
    [
        {"method": "CONNECT", "url": "https://example.com", "timeout": 1000},
        {"method": "GET", "url": "file:///etc/passwd", "timeout": 1000},
        {"method": "GET", "url": "https://example.com", "timeout": 50},
        {"method": "GET", "url": "https://example.com", "timeout": 1000, "headers": {"X": 1}},
    ],
)
def test_invalid_http_tool_config_is_rejected(config):
    with pytest.raises(BizException):
        _validate_http_config(config)

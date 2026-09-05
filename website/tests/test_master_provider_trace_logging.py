from pathlib import Path


def test_master_failure_logs_content_free_gateway_trace_only():
    source=Path('fortune_server.py').read_text(encoding='utf-8')
    assert "MASTER_PROVIDER_TRACE " in source
    assert "AI_GATEWAY.last_trace()" in source
    fragment=source[source.index("MASTER_PROVIDER_TRACE "):source.index("MASTER_PROVIDER_TRACE ")+220]
    assert "master_prompt" not in fragment
    assert "question" not in fragment
    assert "reading" not in fragment

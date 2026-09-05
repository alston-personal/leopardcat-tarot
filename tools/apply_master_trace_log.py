from pathlib import Path

path=Path('website/fortune_server.py')
text=path.read_text(encoding='utf-8')
needle='''                except AIUnavailable as e:\n                    response_body = {\n'''
replacement='''                except AIUnavailable as e:\n                    log('MASTER_PROVIDER_TRACE ' + json.dumps(AI_GATEWAY.last_trace(), ensure_ascii=False, separators=(',', ':')))\n                    response_body = {\n'''
if text.count(needle) != 1:
    raise SystemExit(f'expected exactly one modular AIUnavailable catch, got {text.count(needle)}')
path.write_text(text.replace(needle,replacement,1),encoding='utf-8')

test=Path('website/tests/test_master_provider_trace_logging.py')
test.write_text('''from pathlib import Path\n\n\ndef test_master_failure_logs_content_free_gateway_trace_only():\n    source=Path('fortune_server.py').read_text(encoding='utf-8')\n    assert "MASTER_PROVIDER_TRACE " in source\n    assert "AI_GATEWAY.last_trace()" in source\n    fragment=source[source.index("MASTER_PROVIDER_TRACE "):source.index("MASTER_PROVIDER_TRACE ")+220]\n    assert "master_prompt" not in fragment\n    assert "question" not in fragment\n    assert "reading" not in fragment\n''',encoding='utf-8')
print('master_trace_patch=applied')

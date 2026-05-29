
import json

def validate_json_array(raw: str, field_name: str) -> str:
    if not raw or not str(raw).strip():
        return "[]"
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} 必须是合法 JSON 数组") from exc
    if not isinstance(data, list):
        raise ValueError(f"{field_name} 必须是 JSON 数组")
    if not all(isinstance(item, str) for item in data):
        raise ValueError(f"{field_name} 数组元素必须是字符串")
    return json.dumps(data, ensure_ascii=False)

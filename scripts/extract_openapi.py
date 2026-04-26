"""
FastAPI 앱에서 OpenAPI 스펙을 추출하여 openapi.json 파일로 저장한다.
서버를 띄우지 않고 앱 객체의 .openapi() 메서드를 직접 호출한다.
"""
import json
import sys
import os

# workspace 디렉토리를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app

openapi_schema = app.openapi()

output_path = os.path.join(os.path.dirname(__file__), "..", "..", "openapi.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(openapi_schema, f, ensure_ascii=False, indent=2)

print(f"✅ openapi.json extracted successfully to: {output_path}")

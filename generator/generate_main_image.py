#!/usr/bin/env python3
import argparse
import base64
import json
import os
from pathlib import Path
from urllib import error, request


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_IMAGE_SIZE = "1K"
DEFAULT_ASPECT_RATIO = "2:3"
ENV_FALLBACK_FILES = [
    Path("/home/ubuntu/agentmanager/.env"),
    Path("/home/ubuntu/n8n-automation/.env"),
]


def load_api_keys() -> list[str]:
    keys = []
    for k, v in os.environ.items():
        if k.startswith("GEMINI_API_KEY") and v:
            keys.append(v)

    if not keys:
        for env_path in ENV_FALLBACK_FILES:
            if not env_path.exists():
                continue
            for line in env_path.read_text().splitlines():
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, value = line.split("=", 1)
                name = name.strip()
                if name.startswith("GEMINI_API_KEY"):
                    keys.append(value.strip().strip("'").strip('"'))
                    
    # unique keys preserving order
    seen = set()
    return [k for k in keys if not (k in seen or seen.add(k))]


def extract_inline_image(payload: dict) -> bytes:
    for candidate in payload.get("candidates", []):
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            inline_data = part.get("inlineData") or part.get("inline_data")
            if not inline_data:
                continue
            data = inline_data.get("data")
            if not data:
                continue
            if isinstance(data, str):
                return base64.b64decode(data)
            return data
    raise ValueError("no_image_data_in_response")


def generate_main_image(
    prompt: str,
    output_rel: str,
    *,
    model: str = DEFAULT_MODEL,
    aspect_ratio: str = DEFAULT_ASPECT_RATIO,
    image_size: str = DEFAULT_IMAGE_SIZE,
) -> Path:
    api_keys = load_api_keys()
    if not api_keys:
        raise RuntimeError("missing_gemini_api_key")

    base_body = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt,
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
        },
    }

    bodies = [
        {
            **base_body,
            "generationConfig": {
                **base_body["generationConfig"],
                "imageConfig": {
                    "imageSize": image_size,
                    "aspectRatio": aspect_ratio,
                },
            },
        },
        {
            **base_body,
            "generationConfig": {
                **base_body["generationConfig"],
                "imageConfig": {
                    "imageSize": image_size,
                },
            },
        },
        base_body,
    ]

    last_error = None
    payload = None
    
    for api_key in api_keys:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        success = False
        
        for body in bodies:
            req = request.Request(
                url,
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST",
            )
            try:
                with request.urlopen(req, timeout=120) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                    success = True
                    break
            except error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                last_error = f"gemini_http_error:{exc.code}:{detail}"
                if exc.code == 400:
                    continue
                if exc.code == 429:
                    break # try next API key
                raise RuntimeError(last_error) from exc
            except error.URLError as exc:
                raise RuntimeError(f"gemini_network_error:{exc.reason}") from exc
                
        if success:
            break
            
        if last_error and "429" in last_error:
            print(f"Key ending with ...{api_key[-4:]} hit 429. Trying next key...")
            continue

    if payload is None:
        raise RuntimeError(last_error or "gemini_request_failed")

    image_bytes = extract_inline_image(payload)
    output_path = ROOT / output_rel
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(image_bytes)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate a main image for a LeopardCat Tarot card.")
    parser.add_argument("--prompt", required=True, help="Image prompt text")
    parser.add_argument("--output", required=True, help="Output path relative to repo root or absolute path")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Gemini image model id")
    parser.add_argument("--aspect-ratio", default=DEFAULT_ASPECT_RATIO, help="Image aspect ratio")
    parser.add_argument("--image-size", default=DEFAULT_IMAGE_SIZE, help="Image size preset")
    args = parser.parse_args()

    output_rel = args.output
    output_path = Path(output_rel)
    if output_path.is_absolute():
        output_rel = str(output_path.resolve().relative_to(ROOT))

    saved = generate_main_image(
        args.prompt,
        output_rel,
        model=args.model,
        aspect_ratio=args.aspect_ratio,
        image_size=args.image_size,
    )
    print(saved)


if __name__ == "__main__":
    main()

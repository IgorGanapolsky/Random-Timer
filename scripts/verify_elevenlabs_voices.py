from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "content/pro_audio/voice_personas.json"
API_BASE_URL = "https://api.elevenlabs.io"
OUTPUT_FORMAT = "mp3_44100_128"
CONTROLLED_PROVIDER_STATUSES = {
    "quota_exceeded",
    "payment_issue",
    "insufficient_credits",
    "payment_required",
    "paid_plan_required",
}
CONTROLLED_PROVIDER_MARKERS = (
    "no remaining credits",
    "failed or incomplete payment",
    "paid plan required",
    "free users cannot use library voices",
)
# ElevenLabs premade drill-sergeant male (Clyde). Do not allow DGzg6RaUqxGRTHSBjfgF (Angst, San Francisco).
SUPPORTED_VOICE_ENDPOINTS = {
    "2EiwWnXFnvU5JabPnv8n": f"{API_BASE_URL}/v1/text-to-speech/2EiwWnXFnvU5JabPnv8n?output_format={OUTPUT_FORMAT}",
    "AZnzlk1XvdvUeBnXmlld": f"{API_BASE_URL}/v1/text-to-speech/AZnzlk1XvdvUeBnXmlld?output_format={OUTPUT_FORMAT}",
    "EXAVITQu4vr4xnSDxMaL": f"{API_BASE_URL}/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL?output_format={OUTPUT_FORMAT}",
    "sS5fXGlqomdGXa7mxBcy": f"{API_BASE_URL}/v1/text-to-speech/sS5fXGlqomdGXa7mxBcy?output_format={OUTPUT_FORMAT}",
    "gE0owC0H9C8SzfDyIUtB": f"{API_BASE_URL}/v1/text-to-speech/gE0owC0H9C8SzfDyIUtB?output_format={OUTPUT_FORMAT}",
}


class ControlledProviderUnavailable(RuntimeError):
    """Raised when the live provider is unavailable for account/billing reasons."""


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_error_body(error: urllib.error.HTTPError) -> str:
    try:
        return error.read().decode("utf-8", errors="replace").strip()
    except Exception:
        return ""


def _extract_error_status(body: str) -> str:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return ""

    detail = payload.get("detail")
    if isinstance(detail, dict):
        status = detail.get("status")
        if isinstance(status, str):
            return status

    status = payload.get("status")
    return status if isinstance(status, str) else ""


def _is_controlled_provider_unavailable(body: str) -> bool:
    status = _extract_error_status(body)
    if status in CONTROLLED_PROVIDER_STATUSES:
        return True

    lowered = body.lower()
    return any(marker in lowered for marker in CONTROLLED_PROVIDER_MARKERS)


def _supported_voice_id(voice_id: str) -> str:
    normalized = voice_id.strip()
    if normalized not in SUPPORTED_VOICE_ENDPOINTS:
        raise RuntimeError(f"Configured voice ID is not in the approved CI allowlist: {voice_id!r}")
    return normalized


def _text_to_speech_url(voice_id: str) -> str:
    return SUPPORTED_VOICE_ENDPOINTS[_supported_voice_id(voice_id)]


def _probe_synthesis(
    *,
    api_key: str,
    voice_id: str,
    model_id: str,
    text: str,
    label: str,
) -> dict:
    payload = {
        "text": text,
        "model_id": model_id,
    }
    request = urllib.request.Request(
        _text_to_speech_url(voice_id),
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            audio_bytes = response.read()
    except urllib.error.HTTPError as exc:
        body = _read_error_body(exc)
        detail = f" Response: {body}" if body else ""
        if body and _is_controlled_provider_unavailable(body):
            status = _extract_error_status(body) or "provider_account_unavailable"
            raise ControlledProviderUnavailable(
                f"ElevenLabs synthesis probe skipped for {label}: {status} with HTTP {exc.code}.{detail}"
            ) from exc
        raise RuntimeError(f"ElevenLabs synthesis probe failed for {label} with HTTP {exc.code}.{detail}") from exc

    if not audio_bytes:
        raise RuntimeError(f"ElevenLabs synthesis probe returned empty audio for {label}.")

    return {
        "label": label,
        "voiceId": voice_id,
        "modelId": model_id,
        "probeText": text,
        "audioBytes": len(audio_bytes),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify live ElevenLabs voice synthesis required by Random Timer.")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    args = parser.parse_args()

    api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not api_key:
        print("ELEVENLABS_API_KEY is not set.", file=sys.stderr)
        return 1

    contract = _load_json(args.contract)
    female = contract["female"]
    try:
        probes = [
            _probe_synthesis(
                api_key=api_key,
                voice_id=contract["male"]["voiceId"],
                model_id=contract["male"]["modelId"],
                text=contract["male"]["probeText"],
                label="male",
            ),
            _probe_synthesis(
                api_key=api_key,
                voice_id=female["primaryVoice"]["voiceId"],
                model_id=female["modelId"],
                text=female["primaryVoice"]["probeText"],
                label="female_primary",
            ),
        ]

        for index, fallback in enumerate(female.get("fallbackVoices", []), start=1):
            probes.append(
                _probe_synthesis(
                    api_key=api_key,
                    voice_id=fallback["voiceId"],
                    model_id=female["modelId"],
                    text=fallback["probeText"],
                    label=f"female_fallback_{index}",
                )
            )
    except ControlledProviderUnavailable as exc:
        print(f"::warning::{exc}", file=sys.stderr)
        print(
            json.dumps(
                {
                    "provider": contract["provider"],
                    "outputFormat": OUTPUT_FORMAT,
                    "status": "controlled_skip",
                    "reason": str(exc),
                },
                indent=2,
            )
        )
        return 78

    print(
        json.dumps(
            {
                "provider": contract["provider"],
                "outputFormat": OUTPUT_FORMAT,
                "verifiedProbes": probes,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

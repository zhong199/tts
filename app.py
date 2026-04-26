"""
VoiceForge TTS backend for Hugging Face Spaces.
"""

import asyncio
import base64
import io
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime

from flask import Flask, Response, jsonify, request, send_from_directory

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

TTS_ENGINE = None
DEFAULT_SITE_URL = "https://your-deployed-space.hf.space"


def get_site_url() -> str:
    site_url = os.environ.get("SITE_URL", DEFAULT_SITE_URL).strip()
    if not site_url:
        site_url = DEFAULT_SITE_URL
    return site_url.rstrip("/")


def init_tts() -> None:
    global TTS_ENGINE
    try:
        import edge_tts  # noqa: F401
        TTS_ENGINE = "edge_tts"
        print("[ok] edge-tts loaded")
    except ImportError:
        try:
            from gtts import gTTS  # noqa: F401
            TTS_ENGINE = "gtts"
            print("[ok] gTTS loaded")
        except ImportError:
            print("[warn] No TTS engine available")


init_tts()


@app.after_request
def set_security_headers(resp):
    # Prevent frame-wrapped forwarding setups that break AdSense preview.
    resp.headers["X-Frame-Options"] = "SAMEORIGIN"
    resp.headers["Content-Security-Policy"] = "frame-ancestors 'self'"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return resp


@app.route("/")
def index():
    return send_from_directory("templates", "index.html")


@app.route("/zh/")
def index_zh():
    return send_from_directory("templates", "index-zh.html")


@app.route("/sitemap.xml")
def sitemap():
    base = get_site_url()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{base}/</loc><lastmod>{today}</lastmod><priority>1.0</priority></url>"
        f"<url><loc>{base}/zh/</loc><lastmod>{today}</lastmod><priority>0.9</priority></url>"
        "</urlset>"
    )
    return Response(xml, mimetype="application/xml")


@app.route("/robots.txt")
def robots():
    base = get_site_url()
    txt = f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n"
    return Response(txt, mimetype="text/plain")


@app.route("/api/tts", methods=["POST"])
def tts():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify(error="text required"), 400
    if len(text) > 5000:
        return jsonify(error="max 5000 chars"), 400

    audio = _generate(
        text,
        data.get("voice", "en-US-JennyNeural"),
        data.get("rate", "+0%"),
        data.get("pitch", "+0Hz"),
    )
    if audio is None:
        return jsonify(error="TTS failed"), 500

    return jsonify(
        audio=base64.b64encode(audio).decode("utf-8"),
        format="mp3",
        engine=TTS_ENGINE,
        chars=len(text),
    )


@app.route("/api/translate", methods=["POST"])
def translate():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    target = (data.get("target") or "en").strip().lower()
    source = (data.get("source") or "auto").strip().lower() or "auto"

    if not text:
        return jsonify(error="text required"), 400

    translated, provider = _translate(text, target=target, source=source)
    return jsonify(translated=translated, target=target, source=source, provider=provider)


def _post_json(url: str, payload: dict, timeout: int = 10):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="ignore"))


def _translate(text: str, target: str, source: str = "auto"):
    if source == target:
        return text, "skipped"

    providers = [
        (
            "libretranslate.de",
            "https://libretranslate.de/translate",
            {"q": text, "source": source, "target": target, "format": "text"},
        ),
        (
            "translate.argosopentech.com",
            "https://translate.argosopentech.com/translate",
            {"q": text, "source": source, "target": target, "format": "text"},
        ),
    ]

    for name, url, payload in providers:
        try:
            result = _post_json(url, payload, timeout=10)
            translated = (result.get("translatedText") or "").strip()
            if translated:
                return translated, name
        except Exception:
            continue

    # Last fallback (no API key) to avoid returning unchanged text most of the time.
    try:
        query = urllib.parse.urlencode({"q": text, "langpair": f"{source}|{target}"})
        with urllib.request.urlopen(
            f"https://api.mymemory.translated.net/get?{query}", timeout=10
        ) as resp:
            result = json.loads(resp.read().decode("utf-8", errors="ignore"))
            translated = result.get("responseData", {}).get("translatedText", "").strip()
            if translated:
                return translated, "mymemory"
    except Exception:
        pass

    return text, "fallback-original"


def _generate(text: str, voice: str, rate: str, pitch: str):
    if TTS_ENGINE == "edge_tts":
        return _edge(text, voice, rate, pitch)
    if TTS_ENGINE == "gtts":
        return _gtts(text, voice)
    return None


def _edge(text: str, voice: str, rate: str, pitch: str):
    import edge_tts

    async def _run():
        comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        chunks = []
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])
        return b"".join(chunks)

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()


def _gtts(text: str, voice: str):
    from gtts import gTTS

    language_map = {
        "en-US": "en",
        "en-GB": "en",
        "zh-CN": "zh",
        "ja-JP": "ja",
        "ko-KR": "ko",
        "de-DE": "de",
        "fr-FR": "fr",
        "es-ES": "es",
        "pt-BR": "pt",
        "it-IT": "it",
        "ru-RU": "ru",
        "ar-SA": "ar",
        "hi-IN": "hi",
    }
    lang = next((v for k, v in language_map.items() if k in voice), "en")
    buf = io.BytesIO()
    gTTS(text=text, lang=lang).write_to_fp(buf)
    return buf.getvalue()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 7860)), debug=False)
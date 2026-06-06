import json
import os
import random
import base64
import hashlib
import hmac
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone


FEED_URL = os.environ.get("SOCIAL_FEED_URL", "https://ttsvoice.top/social-feed.json")
FALLBACK_POSTS = [
    {
        "text": "VoiceForge is a free online AI voice generator with 20+ neural voices, SSML controls, batch conversion, and downloadable audio. Try it: https://ttsvoice.top",
        "url": "https://ttsvoice.top",
        "tags": ["texttospeech", "aivoice", "creator tools"],
    },
    {
        "text": "Need narration for YouTube videos without recording your own voice? VoiceForge turns scripts into natural AI voiceovers. Guide: https://ttsvoice.top/use-cases/youtube-voiceover",
        "url": "https://ttsvoice.top/use-cases/youtube-voiceover",
        "tags": ["youtube", "voiceover", "tts"],
    },
]


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "VoiceForgeSocialBot/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8-sig"))


def post_json(url: str, payload: dict, headers: dict | None = None) -> tuple[int, str]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.status, response.read().decode("utf-8", errors="replace")


def oauth_quote(value: str) -> str:
    return urllib.parse.quote(str(value), safe="~")


def oauth1_header(method: str, url: str, consumer_key: str, consumer_secret: str, token: str, token_secret: str) -> str:
    oauth_params = {
        "oauth_consumer_key": consumer_key,
        "oauth_nonce": base64.urlsafe_b64encode(os.urandom(24)).decode("ascii").rstrip("="),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(datetime.now(timezone.utc).timestamp())),
        "oauth_token": token,
        "oauth_version": "1.0",
    }
    normalized = "&".join(f"{oauth_quote(k)}={oauth_quote(v)}" for k, v in sorted(oauth_params.items()))
    base_string = "&".join([method.upper(), oauth_quote(url), oauth_quote(normalized)])
    signing_key = f"{oauth_quote(consumer_secret)}&{oauth_quote(token_secret)}"
    signature = base64.b64encode(
        hmac.new(signing_key.encode("utf-8"), base_string.encode("utf-8"), hashlib.sha1).digest()
    ).decode("ascii")
    oauth_params["oauth_signature"] = signature
    return "OAuth " + ", ".join(f'{oauth_quote(k)}="{oauth_quote(v)}"' for k, v in sorted(oauth_params.items()))


def choose_post(feed: dict) -> dict:
    posts = feed.get("posts") or []
    if not posts:
        raise RuntimeError("No posts found in social feed")
    seed = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rng = random.Random(seed)
    return rng.choice(posts)


def post_to_mastodon(text: str) -> str:
    instance = os.environ.get("MASTODON_INSTANCE", "").rstrip("/")
    token = os.environ.get("MASTODON_ACCESS_TOKEN", "")
    if not instance or not token:
        return "Mastodon skipped: missing MASTODON_INSTANCE or MASTODON_ACCESS_TOKEN"
    status, body = post_json(
        f"{instance}/api/v1/statuses",
        {"status": text, "visibility": os.environ.get("MASTODON_VISIBILITY", "public")},
        {"Authorization": f"Bearer {token}"},
    )
    return f"Mastodon posted: HTTP {status}, {body[:160]}"


def post_to_x(text: str) -> str:
    consumer_key = os.environ.get("X_API_KEY") or os.environ.get("TWITTER_API_KEY", "")
    consumer_secret = os.environ.get("X_API_SECRET") or os.environ.get("TWITTER_API_SECRET", "")
    token = os.environ.get("X_ACCESS_TOKEN") or os.environ.get("TWITTER_ACCESS_TOKEN", "")
    token_secret = os.environ.get("X_ACCESS_TOKEN_SECRET") or os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", "")
    if not all([consumer_key, consumer_secret, token, token_secret]):
        return "X/Twitter skipped: missing X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, or X_ACCESS_TOKEN_SECRET"

    url = "https://api.x.com/2/tweets"
    body = {"text": text[:280]}
    auth = oauth1_header("POST", url, consumer_key, consumer_secret, token, token_secret)
    status, response_body = post_json(url, body, {"Authorization": auth})
    return f"X/Twitter posted: HTTP {status}, {response_body[:160]}"


def bluesky_login(handle: str, password: str) -> str:
    status, body = post_json(
        "https://bsky.social/xrpc/com.atproto.server.createSession",
        {"identifier": handle, "password": password},
    )
    data = json.loads(body)
    return data["accessJwt"]


def post_to_bluesky(text: str) -> str:
    handle = os.environ.get("BLUESKY_HANDLE", "")
    password = os.environ.get("BLUESKY_APP_PASSWORD", "")
    if not handle or not password:
        return "Bluesky skipped: missing BLUESKY_HANDLE or BLUESKY_APP_PASSWORD"
    token = bluesky_login(handle, password)
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    status, body = post_json(
        "https://bsky.social/xrpc/com.atproto.repo.createRecord",
        {
            "repo": handle,
            "collection": "app.bsky.feed.post",
            "record": {"text": text[:300], "createdAt": now},
        },
        {"Authorization": f"Bearer {token}"},
    )
    return f"Bluesky posted: HTTP {status}, {body[:160]}"


def write_draft(post: dict, results: list[str]) -> None:
    os.makedirs("social-out", exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    tags = " ".join(f"#{tag.replace(' ', '')}" for tag in post.get("tags", []))
    text = f"{post['text']}\n\n{tags}".strip()
    with open(os.path.join("social-out", f"{today}.txt"), "w", encoding="utf-8") as f:
        f.write(text + "\n\n")
        f.write("Results:\n")
        for result in results:
            f.write(f"- {result}\n")


def main() -> int:
    try:
        feed = fetch_json(FEED_URL)
    except Exception as exc:
        print(f"Feed unavailable, using fallback posts: {exc}", file=sys.stderr)
        feed = {"posts": FALLBACK_POSTS}
    post = choose_post(feed)
    tags = " ".join(f"#{tag.replace(' ', '')}" for tag in post.get("tags", []))
    text = f"{post['text']}\n\n{tags}".strip()

    results = [
        post_to_x(text),
        post_to_mastodon(text),
        post_to_bluesky(text),
    ]
    write_draft(post, results)
    print("Selected post:")
    print(text)
    print("\nResults:")
    for result in results:
        print("-", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

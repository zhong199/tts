# VoiceForge TTS

Free online AI voice generator and text to speech web app.

[![Daily growth health](https://github.com/zhong199/tts/actions/workflows/daily-growth-health.yml/badge.svg)](https://github.com/zhong199/tts/actions/workflows/daily-growth-health.yml)
[![Weekly white-hat promotion](https://github.com/zhong199/tts/actions/workflows/weekly-promotion.yml/badge.svg)](https://github.com/zhong199/tts/actions/workflows/weekly-promotion.yml)
[![Daily social promotion](https://github.com/zhong199/tts/actions/workflows/daily-social-promotion.yml/badge.svg)](https://github.com/zhong199/tts/actions/workflows/daily-social-promotion.yml)

[Live Website](https://ttsvoice.top) · [FAQ](https://ttsvoice.top/faq-en) · [Use Cases](https://ttsvoice.top/use-cases) · [Privacy](https://ttsvoice.top/privacy)

## What It Does

VoiceForge turns text into natural speech in the browser. It is built for creators, educators, students, accessibility workflows, and developers who need fast voice generation without account setup.

## Features

- 20+ neural voices across English, Chinese, Japanese, Korean, German, French, Spanish, Portuguese, Italian, Hindi, Arabic, and Russian
- Text to speech with speed and pitch controls
- SSML editor for pauses, emphasis, pitch, and pronunciation control
- Batch conversion for long documents or lesson segments
- Auto-translation workflow for multilingual voice generation
- Browser-local history, privacy-focused by design
- Downloadable audio for editing and content production

## Popular Use Cases

- [YouTube voiceovers](https://ttsvoice.top/use-cases/youtube-voiceover)
- [Podcast intros](https://ttsvoice.top/use-cases/podcast-intro)
- [E-learning course audio](https://ttsvoice.top/use-cases/elearning-audio)
- [Japanese text to speech](https://ttsvoice.top/use-cases/japanese-tts)
- [Developer TTS workflow](https://ttsvoice.top/use-cases/tts-api-workflow)

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Docker:

```bash
docker build -t voiceforge-tts .
docker run -p 7860:7860 voiceforge-tts
```

## SEO and Discovery

The live site exposes:

- `https://ttsvoice.top/sitemap.xml`
- `https://ttsvoice.top/robots.txt`
- `https://ttsvoice.top/llms.txt`
- `https://ttsvoice.top/ads.txt`
- `https://ttsvoice.top/voiceforge-indexnow-20260606.txt`

This repository includes a weekly white-hat promotion workflow that verifies the site and submits canonical URLs to IndexNow. It does not create spam links, fake traffic, mass comments, or paid link schemes.

The repository also includes a daily growth health workflow that checks the website, sitemap, llms.txt, privacy page, use-case pages, and GitHub README so broken discovery surfaces are caught quickly.

See [TRAFFIC-GROWTH.md](TRAFFIC-GROWTH.md) for the automated growth system and the path toward 3,000 legitimate daily visits.

Daily social promotion is available through `.github/workflows/daily-social-promotion.yml`. It publishes only through accounts you control when valid Mastodon or Bluesky secrets are configured. Without secrets, it safely generates a daily post artifact.

## Responsible Promotion

Please share VoiceForge only where it is relevant:

- AI tool directories
- open-source showcases
- creator communities asking for TTS tools
- education and accessibility resource lists
- your own blog, newsletter, or product documentation

Do not use this project for spam, fake engagement, comment flooding, or link schemes.

## Contact

Website: https://ttsvoice.top
Support: support@ttsvoice.top

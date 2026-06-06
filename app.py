import asyncio
import base64
import io
import json
import os
import html
import urllib.parse
import urllib.request
from datetime import datetime

from flask import Flask, Response, jsonify, redirect, request, send_from_directory

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

app = Flask(__name__, static_folder=None, template_folder="templates")
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

TTS_ENGINE = None
ADSENSE_PUBLISHER_ID = "pub-5073153666058810"
INDEXNOW_KEY = "voiceforge-indexnow-20260606"

INDEXABLE_ROUTES = {
    "/": ("en", "VoiceForge - Free AI Voice Generator", "Free AI voice generator and text to speech tool."),
    "/about": ("en", "About VoiceForge", "Learn about VoiceForge, its text to speech features, technology, and contact information."),
    "/privacy": ("en", "Privacy Policy", "VoiceForge privacy policy, advertising cookie disclosure, and user choices."),
    "/help": ("en", "VoiceForge Help Center", "Guides, support options, and usage tips for the VoiceForge AI voice generator."),
    "/terms": ("en", "Terms of Use", "Terms and acceptable use rules for VoiceForge."),
    "/use-cases": ("en", "VoiceForge Use Cases", "AI text to speech use case guides for video, podcasts, courses, Japanese audio, and developer workflows."),
    "/zh/": ("zh", "VoiceForge 免费AI语音生成器", "免费的在线文字转语音和 AI 语音生成工具。"),
    "/zh/about": ("zh", "关于 VoiceForge", "了解 VoiceForge 的文字转语音功能、技术和联系方式。"),
    "/zh/privacy": ("zh", "隐私政策", "VoiceForge 隐私政策、广告 Cookie 披露和用户选择。"),
    "/zh/help": ("zh", "VoiceForge 帮助中心", "VoiceForge AI 语音生成器的使用指南、支持方式和常见问题。"),
    "/zh/terms": ("zh", "使用条款", "VoiceForge 的服务条款和可接受使用规则。"),
    "/zh/use-cases": ("zh", "VoiceForge 使用场景", "面向视频、播客、教学、日语和开发者工作流的 AI 文字转语音使用指南。"),
    "/faq-en": ("en", "Text to Speech FAQ", "Detailed answers about text to speech, AI voices, and VoiceForge."),
    "/zh/faq-zh": ("zh", "文字转语音常见问题", "关于文字转语音、AI 语音和 VoiceForge 的常见问题解答。"),
}

TOOL_ROUTES = {
    "convert", "batch", "ssml", "history", "guide",
    "zh/convert", "zh/batch", "zh/ssml", "zh/history", "zh/guide",
}

USE_CASE_PAGES = {
    "youtube-voiceover": {
        "en_title": "Free Text to Speech for YouTube Voiceovers",
        "en_description": "Create natural YouTube narration with free AI text to speech voices, export-ready audio, and practical voiceover workflow tips.",
        "zh_title": "YouTube 视频配音文字转语音指南",
        "zh_description": "使用免费 AI 文字转语音为 YouTube 视频制作自然旁白，包含配音流程、语音选择和导出建议。",
        "en_body": """
<h1>Free Text to Speech for YouTube Voiceovers</h1>
<p>VoiceForge helps YouTube creators turn scripts into clear narration without recording equipment. It is useful for tutorials, faceless videos, explainers, product demos, shorts, accessibility narration, and multilingual channel tests.</p>
<div class="panel">
<h2>Recommended Workflow</h2>
<ol><li>Write a conversational script with short sentences and natural pauses.</li><li>Choose a voice that matches the channel tone: warm for education, energetic for shorts, or calm for tutorials.</li><li>Generate a first pass, then adjust speed between 1.05x and 1.2x for video pacing.</li><li>Download MP3 for quick editing or WAV if you plan to do audio mastering.</li></ol>
<h2>Tips for Better Retention</h2>
<p>Add punctuation where you want pauses, split long scripts into sections, and use consistent voices across a series so viewers recognize your channel style.</p>
<h2>Start Creating</h2>
<p>Open the <a href="/convert">AI voice generator</a>, paste your video script, and test two or three voices before exporting the final narration.</p>
</div>
""",
        "zh_body": """
<h1>YouTube 视频配音文字转语音指南</h1>
<p>VoiceForge 可以帮助创作者把视频脚本快速转换成清晰旁白，适合教程、解说、产品演示、短视频、无真人出镜频道和多语言频道测试。</p>
<div class="panel">
<h2>推荐流程</h2>
<ol><li>先写出口语化脚本，句子尽量短，并用标点安排停顿。</li><li>根据频道风格选择语音：教育类适合温暖清晰，短视频适合更有活力的声音。</li><li>先生成一版试听，再把语速调到 1.05x 到 1.2x 之间匹配视频节奏。</li><li>快速剪辑可下载 MP3，需要后期处理可选择 WAV。</li></ol>
<h2>提升完播率的小技巧</h2>
<p>长脚本建议分段生成，系列视频保持同一个声音，有助于形成频道识别度。</p>
<h2>开始制作</h2>
<p>打开 <a href="/zh/convert">AI 语音生成器</a>，粘贴视频脚本，试听多个声音后再导出最终旁白。</p>
</div>
""",
    },
    "podcast-intro": {
        "en_title": "AI Voice Generator for Podcast Intros",
        "en_description": "Use AI text to speech to create consistent podcast intros, segment bumpers, sponsor reads, and multilingual audio snippets.",
        "zh_title": "播客片头与节目包装 AI 语音生成",
        "zh_description": "使用 AI 文字转语音制作播客片头、转场、赞助口播和多语言音频片段。",
        "en_body": """
<h1>AI Voice Generator for Podcast Intros</h1>
<p>A consistent intro voice makes a podcast feel polished. VoiceForge can generate repeatable intro lines, chapter transitions, episode disclaimers, short sponsor reads, and translated snippets for international listeners.</p>
<div class="panel">
<h2>What to Generate</h2>
<ul><li>Opening title and host introduction.</li><li>Segment bumpers between topics.</li><li>Accessibility summaries for episode notes.</li><li>Short multilingual greetings for global audiences.</li></ul>
<h2>Production Advice</h2>
<p>Keep intros under 15 seconds, use a slightly slower speed for clarity, and export WAV if you mix music under the voice. For repeated segments, save a standard script template and reuse the same voice.</p>
<h2>Try It</h2>
<p>Use the <a href="/ssml">SSML editor</a> to add pauses, emphasis, and pacing for a more broadcast-ready delivery.</p>
</div>
""",
        "zh_body": """
<h1>播客片头与节目包装 AI 语音生成</h1>
<p>稳定的片头声音能让播客更专业。VoiceForge 可用于生成节目开场、章节转场、免责声明、赞助口播和面向海外听众的多语言片段。</p>
<div class="panel">
<h2>适合生成的内容</h2>
<ul><li>节目标题和主持人介绍。</li><li>不同话题之间的转场语。</li><li>节目笔记的无障碍音频摘要。</li><li>面向全球听众的多语言问候。</li></ul>
<h2>制作建议</h2>
<p>片头尽量控制在 15 秒以内，语速略慢会更清晰。如果要叠加背景音乐，建议下载 WAV 后再混音。</p>
<h2>试试看</h2>
<p>使用 <a href="/zh/ssml">SSML 编辑器</a> 添加停顿、强调和节奏控制，让声音更接近播客包装效果。</p>
</div>
""",
    },
    "elearning-audio": {
        "en_title": "Text to Speech for E-Learning Courses",
        "en_description": "Generate course narration, lesson summaries, listening practice, and accessibility audio with AI text to speech.",
        "zh_title": "在线课程与教学内容文字转语音",
        "zh_description": "用 AI 文字转语音生成课程旁白、知识点摘要、听力练习和无障碍音频。",
        "en_body": """
<h1>Text to Speech for E-Learning Courses</h1>
<p>Educators can use VoiceForge to create audio for slides, micro-lessons, quizzes, pronunciation examples, and accessible learning materials without booking a studio session.</p>
<div class="panel">
<h2>Common Course Uses</h2>
<ul><li>Narration for slides and video lessons.</li><li>Audio summaries at the end of each module.</li><li>Language listening practice with multiple voices.</li><li>Accessible alternatives for students who prefer audio learning.</li></ul>
<h2>Quality Checklist</h2>
<p>Break lessons into short sections, place one learning objective per audio clip, and use SSML pauses before definitions or examples. Batch conversion is helpful when each line represents one lesson segment.</p>
<h2>Build Faster</h2>
<p>Open <a href="/batch">Batch Convert</a> to generate many course clips from a structured lesson outline.</p>
</div>
""",
        "zh_body": """
<h1>在线课程与教学内容文字转语音</h1>
<p>教师和课程制作者可以用 VoiceForge 为课件、微课、测验、发音示例和无障碍学习材料生成语音，无需录音棚。</p>
<div class="panel">
<h2>常见教学场景</h2>
<ul><li>幻灯片和视频课程旁白。</li><li>每个模块后的音频摘要。</li><li>语言学习中的听力示例。</li><li>为偏好音频学习的学生提供替代内容。</li></ul>
<h2>质量检查</h2>
<p>把课程拆成短片段，每段只讲一个目标；在定义和例子前加入停顿，能让学生更容易跟上节奏。</p>
<h2>更快制作</h2>
<p>打开 <a href="/zh/batch">批量转换</a>，把课程大纲按行生成多个音频片段。</p>
</div>
""",
    },
    "japanese-tts": {
        "en_title": "Natural Japanese Text to Speech Online",
        "en_description": "Generate Japanese AI voices for learning, localization, narration, and listening practice with online text to speech.",
        "zh_title": "自然日语文字转语音在线生成",
        "zh_description": "在线生成自然日语 AI 语音，适合语言学习、本地化、旁白和听力练习。",
        "en_body": """
<h1>Natural Japanese Text to Speech Online</h1>
<p>Japanese text to speech is useful for learners, localization teams, creators, and product demos. VoiceForge includes Japanese neural voices that can read kana, kanji, punctuation, and mixed scripts with natural pacing.</p>
<div class="panel">
<h2>Best Uses</h2>
<ul><li>Listening practice for Japanese learners.</li><li>Draft voiceovers for localized videos.</li><li>Pronunciation checks for product demos or tutorials.</li><li>Short character lines for prototypes and educational games.</li></ul>
<h2>How to Improve Output</h2>
<p>Use Japanese punctuation, split very long sentences, and preview both female and male Japanese voices. For tricky names, use the pronunciation helper or rewrite with kana.</p>
<h2>Generate Japanese Audio</h2>
<p>Choose a Japanese voice in the <a href="/convert">voice generator</a>, paste your text, and export the audio.</p>
</div>
""",
        "zh_body": """
<h1>自然日语文字转语音在线生成</h1>
<p>日语文字转语音适合语言学习、本地化团队、内容创作者和产品演示。VoiceForge 的日语神经网络语音可以朗读假名、汉字、标点和混合文本。</p>
<div class="panel">
<h2>适合场景</h2>
<ul><li>日语学习者的听力练习。</li><li>本地化视频的旁白草稿。</li><li>产品教程或演示中的发音检查。</li><li>教育游戏或原型中的短角色台词。</li></ul>
<h2>提升效果</h2>
<p>使用日语标点，避免超长句；专有名词可用发音助手或假名改写。</p>
<h2>生成日语音频</h2>
<p>在 <a href="/zh/convert">语音生成器</a> 中选择日语声音，粘贴文本后导出音频。</p>
</div>
""",
    },
    "tts-api-workflow": {
        "en_title": "Free TTS API Workflow for Developers",
        "en_description": "Understand how developers can prototype text to speech workflows, batch audio generation, and app narration with VoiceForge.",
        "zh_title": "开发者免费 TTS API 工作流",
        "zh_description": "了解开发者如何用 VoiceForge 原型验证文字转语音、批量音频生成和应用旁白流程。",
        "en_body": """
<h1>Free TTS API Workflow for Developers</h1>
<p>Developers often need to test voice UX before integrating a production speech provider. VoiceForge is useful for prototyping app narration, onboarding audio, accessibility playback, and batch-generated sample assets.</p>
<div class="panel">
<h2>Prototype Checklist</h2>
<ul><li>Decide whether audio should be generated on demand or pre-rendered.</li><li>Test multiple voices with real interface copy.</li><li>Check how speed and pitch affect comprehension.</li><li>Export sample files for product reviews before writing integration code.</li></ul>
<h2>Batch Testing</h2>
<p>Use one line per prompt in Batch Convert to create a small audio test set. This helps product teams compare voice tone across onboarding, alerts, and help content.</p>
<h2>Developer Note</h2>
<p>VoiceForge is an independent web app. Review the third-party speech service terms before large-scale commercial deployment.</p>
</div>
""",
        "zh_body": """
<h1>开发者免费 TTS API 工作流</h1>
<p>开发者在接入正式语音服务前，通常需要先验证语音体验。VoiceForge 适合用于应用旁白、引导音频、无障碍播放和批量样本音频的原型测试。</p>
<div class="panel">
<h2>原型检查清单</h2>
<ul><li>确认音频是实时生成还是预先生成。</li><li>用真实界面文案测试多个声音。</li><li>检查语速和音调对理解度的影响。</li><li>先导出样本音频给产品团队评审，再写集成代码。</li></ul>
<h2>批量测试</h2>
<p>使用批量转换，每行放一个提示文案，可以快速生成一组测试音频，用于比较不同场景下的声音风格。</p>
<h2>开发者提示</h2>
<p>VoiceForge 是独立网页应用。大规模商业部署前，请确认第三方语音服务的使用条款。</p>
</div>
""",
    },
}

for _slug, _page in USE_CASE_PAGES.items():
    INDEXABLE_ROUTES[f"/use-cases/{_slug}"] = ("en", _page["en_title"], _page["en_description"])
    INDEXABLE_ROUTES[f"/zh/use-cases/{_slug}"] = ("zh", _page["zh_title"], _page["zh_description"])

SOCIAL_PROMOTION_POSTS = [
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
    {
        "text": "Podcast creators can use VoiceForge to draft intros, segment bumpers, sponsor reads, and multilingual snippets. Learn more: https://ttsvoice.top/use-cases/podcast-intro",
        "url": "https://ttsvoice.top/use-cases/podcast-intro",
        "tags": ["podcast", "aivoice", "audio"],
    },
    {
        "text": "Create course narration and lesson audio with free text to speech. VoiceForge supports batch conversion for e-learning workflows: https://ttsvoice.top/use-cases/elearning-audio",
        "url": "https://ttsvoice.top/use-cases/elearning-audio",
        "tags": ["elearning", "accessibility", "tts"],
    },
    {
        "text": "Japanese learners and creators can generate natural Japanese text to speech online with VoiceForge. Guide: https://ttsvoice.top/use-cases/japanese-tts",
        "url": "https://ttsvoice.top/use-cases/japanese-tts",
        "tags": ["japanese", "languagelearning", "texttospeech"],
    },
    {
        "text": "Developers prototyping voice UX can use VoiceForge to generate sample narration before integrating a production TTS API. Workflow: https://ttsvoice.top/use-cases/tts-api-workflow",
        "url": "https://ttsvoice.top/use-cases/tts-api-workflow",
        "tags": ["developers", "tts", "ux"],
    },
]


def get_site_url() -> str:
    env_url = os.environ.get("SITE_URL", "").strip()
    """动态获取当前站点的完整域名（如 https://ttsvoice.top）"""
    # 1. 优先使用环境变量（您可以在 Space 设置中添加 SITE_URL = https://ttsvoice.top）
    env_url = os.environ.get("SITE_URL", "").strip()
    if env_url:
        return env_url.rstrip("/")

    # 2. 如果使用了 Cloudflare Worker 或自定义域名的反向代理，通常会有 X-Forwarded-Host
    forwarded_host = request.headers.get("X-Forwarded-Host", "").strip()
    if forwarded_host:
        proto = request.headers.get("X-Forwarded-Proto", "https")
        return f"{proto}://{forwarded_host}"

    # 3. 直接使用请求中的 Host 头
    if request.host:
        proto = request.headers.get("X-Forwarded-Proto") or ("https" if request.is_secure else "http")
        return f"{proto}://{request.host}"

    # 4. 最后回退（一般不会走到这里）
    return "https://ttsvoice.top"


def _canonical_url(path: str) -> str:
    return f"{get_site_url()}{path}"


def _indexable_paths() -> list[str]:
    return list(INDEXABLE_ROUTES.keys())


def _nav_html(lang: str) -> str:
    if lang == "zh":
        return """
        <nav class="topnav">
          <a class="brand" href="/zh/">VoiceForge</a>
          <a href="/zh/about">关于</a>
          <a href="/zh/privacy">隐私</a>
          <a href="/zh/help">帮助</a>
          <a href="/zh/terms">条款</a>
          <a href="/zh/use-cases">场景</a>
          <a href="/zh/faq-zh">FAQ</a>
          <a href="/">English</a>
        </nav>
        """
    return """
    <nav class="topnav">
      <a class="brand" href="/">VoiceForge</a>
      <a href="/about">About</a>
      <a href="/privacy">Privacy</a>
      <a href="/help">Help</a>
      <a href="/terms">Terms</a>
      <a href="/use-cases">Use Cases</a>
      <a href="/faq-en">FAQ</a>
      <a href="/zh/">中文</a>
    </nav>
    """


def _page_shell(path: str, title: str, description: str, body: str, lang: str = "en") -> Response:
    canonical = _canonical_url(path)
    alternate_en = _canonical_url(path.replace("/zh", "", 1)) if path.startswith("/zh/") else _canonical_url(path)
    zh_path = f"/zh{path}" if lang == "en" and path not in ("/", "/faq-en") else path
    if path == "/":
        zh_path = "/zh/"
    if path == "/faq-en":
        zh_path = "/zh/faq-zh"
    alternate_zh = _canonical_url(zh_path)
    privacy_path = "/zh/privacy" if lang == "zh" else "/privacy"
    terms_path = "/zh/terms" if lang == "zh" else "/terms"
    contact_label = "联系" if lang == "zh" else "Contact"
    privacy_label = "隐私政策" if lang == "zh" else "Privacy Policy"
    terms_label = "条款" if lang == "zh" else "Terms"
    disclaimer = (
        "VoiceForge 是一个独立的文字转语音网页应用，不隶属于 Microsoft、Google 或 Hugging Face。"
        if lang == "zh"
        else "VoiceForge is an independent text to speech web application. It is not affiliated with Microsoft, Google, or Hugging Face."
    )
    html_doc = f"""<!DOCTYPE html>
<html lang="{html.escape('zh-CN' if lang == 'zh' else 'en')}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="google-adsense-account" content="ca-{ADSENSE_PUBLISHER_ID}">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-{ADSENSE_PUBLISHER_ID}" crossorigin="anonymous"></script>
<title>{html.escape(title)} | VoiceForge</title>
<meta name="description" content="{html.escape(description)}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="en" href="{alternate_en}">
<link rel="alternate" hreflang="zh-Hans" href="{alternate_zh}">
<link rel="alternate" hreflang="x-default" href="{alternate_en}">
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Noto Sans SC',Arial,sans-serif;margin:0;background:#f8fafd;color:#202124;line-height:1.75}}
.topnav{{display:flex;gap:18px;align-items:center;flex-wrap:wrap;padding:18px 24px;background:#fff;border-bottom:1px solid #e5e7eb}}
.topnav a{{color:#1a73e8;text-decoration:none;font-weight:500}}.topnav .brand{{font-size:20px;color:#202124;margin-right:auto}}
main{{max-width:900px;margin:0 auto;padding:42px 22px}}h1{{font-size:2.2rem;line-height:1.2;margin:0 0 14px}}h2{{margin-top:30px;color:#1a73e8}}
.meta{{color:#5f6368}}.panel{{background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:24px;margin:22px 0}}
footer{{max-width:900px;margin:0 auto;padding:24px 22px 42px;color:#5f6368;font-size:14px}}footer a{{color:#1a73e8}}
</style>
</head>
<body>
{_nav_html(lang)}
<main>
{body}
</main>
<footer>
  <p>{contact_label}: <a href="mailto:support@ttsvoice.top">support@ttsvoice.top</a> · <a href="{privacy_path}">{privacy_label}</a> · <a href="{terms_path}">{terms_label}</a></p>
  <p>{disclaimer}</p>
</footer>
</body>
</html>"""
    return Response(html_doc, mimetype="text/html; charset=utf-8")


def _legal_page(path: str) -> Response:
    if path.startswith("/zh/"):
        lang = "zh"
        if path.endswith("/privacy"):
            return _page_shell(path, "隐私政策", "VoiceForge 隐私政策、广告 Cookie 披露和用户选择。", """
<h1>隐私政策</h1>
<p class="meta">最后更新：2026年6月6日</p>
<div class="panel">
<h2>我们处理的信息</h2>
<p>您提交的文字仅用于生成语音或翻译请求。生成完成后，我们不会把文字或音频作为账户资料保存。浏览器历史记录只保存在您的本地设备中。</p>
<h2>第三方服务</h2>
<p>为了提供语音、翻译、托管和字体服务，VoiceForge 可能与文本转语音服务、翻译服务、托管服务和 Google Fonts 交互。</p>
<h2>Google 广告 Cookie</h2>
<p>第三方供应商（包括 Google）会使用 Cookie，根据用户之前访问本网站或其他网站的情况投放广告。Google 使用广告 Cookie，使其及合作伙伴能够根据用户访问本网站或互联网上其他网站的情况投放广告。</p>
<p>用户可以访问 <a href="https://www.google.com/settings/ads" rel="noopener">Google 广告设置</a> 退出个性化广告，也可以访问 <a href="https://www.aboutads.info/choices/" rel="noopener">aboutads.info</a> 了解第三方广告 Cookie 选择。</p>
<h2>联系我们</h2>
<p>隐私相关问题请发送邮件至 <a href="mailto:support@ttsvoice.top">support@ttsvoice.top</a>。</p>
</div>
""", lang)
        if path.endswith("/about"):
            return _page_shell(path, "关于 VoiceForge", "了解 VoiceForge 的文字转语音功能、技术和联系方式。", """
<h1>关于 VoiceForge</h1>
<p>VoiceForge 是一个在线文字转语音工具，帮助创作者、教育工作者、学生和开发者快速把文字转换成可下载的语音音频。</p>
<div class="panel">
<h2>我们提供什么</h2>
<p>网站提供多语言神经网络语音、语速和音调调整、SSML 编辑、批量转换、自动翻译和浏览器本地历史记录。</p>
<h2>独立说明</h2>
<p>VoiceForge 是独立项目，不隶属于 Microsoft、Google 或 Hugging Face。第三方服务名称仅用于说明技术集成。</p>
<h2>联系方式</h2>
<p>支持邮箱：<a href="mailto:support@ttsvoice.top">support@ttsvoice.top</a></p>
</div>
""", lang)
        if path.endswith("/help"):
            return _page_shell(path, "帮助中心", "VoiceForge AI 语音生成器的使用指南、支持方式和常见问题。", """
<h1>帮助中心</h1>
<div class="panel">
<h2>如何生成语音</h2>
<ol><li>输入最多 5,000 个字符的文字。</li><li>选择语音和语言。</li><li>调整语速、音调或 SSML。</li><li>点击生成并下载音频。</li></ol>
<h2>支持</h2>
<p>问题反馈请发送邮件至 <a href="mailto:support@ttsvoice.top">support@ttsvoice.top</a>，或访问 <a href="/zh/faq-zh">FAQ</a> 查看常见问题。</p>
</div>
""", lang)
        return _page_shell(path, "使用条款", "VoiceForge 的服务条款和可接受使用规则。", """
<h1>使用条款</h1>
<div class="panel">
<p>使用 VoiceForge 即表示您同意只提交您有权处理的文本，并遵守适用法律、第三方服务条款和版权规则。</p>
<h2>可接受使用</h2>
<p>不得使用本服务生成欺诈、骚扰、侵权、仇恨、成人性内容、恶意冒充或其他违法有害内容。</p>
<h2>免责声明</h2>
<p>服务按现状提供，生成音频的使用责任由用户自行承担。</p>
</div>
""", lang)

    if path == "/privacy":
        return _page_shell(path, "Privacy Policy", "VoiceForge privacy policy, advertising cookie disclosure, and user choices.", """
<h1>Privacy Policy</h1>
<p class="meta">Last updated: June 6, 2026</p>
<div class="panel">
<h2>Information We Process</h2>
<p>Text submitted to VoiceForge is used to generate speech or translation results. We do not store submitted text or generated audio as account data after processing. Browser history is stored locally on your device.</p>
<h2>Third-Party Services</h2>
<p>VoiceForge may interact with text to speech services, translation services, hosting infrastructure, and Google Fonts to deliver the application.</p>
<h2>Google Advertising Cookies</h2>
<p>Third-party vendors, including Google, use cookies to serve ads based on a user's prior visits to this website or other websites. Google's use of advertising cookies enables it and its partners to serve ads to users based on their visit to this site and/or other sites on the Internet.</p>
<p>Users may opt out of personalized advertising by visiting <a href="https://www.google.com/settings/ads" rel="noopener">Google Ads Settings</a>. Users may also visit <a href="https://www.aboutads.info/choices/" rel="noopener">aboutads.info</a> to learn about choices for some third-party advertising cookies.</p>
<h2>Contact</h2>
<p>For privacy requests, email <a href="mailto:support@ttsvoice.top">support@ttsvoice.top</a>.</p>
</div>
""")
    if path == "/about":
        return _page_shell(path, "About VoiceForge", "Learn about VoiceForge, its text to speech features, technology, and contact information.", """
<h1>About VoiceForge</h1>
<p>VoiceForge is an online text to speech tool for creators, educators, students, accessibility workflows, and developers who need quick voice generation from written text.</p>
<div class="panel">
<h2>What VoiceForge Offers</h2>
<p>The site provides multilingual neural voices, speed and pitch controls, SSML editing, batch conversion, automatic translation, and browser-local generation history.</p>
<h2>Independence</h2>
<p>VoiceForge is an independent project and is not affiliated with Microsoft, Google, or Hugging Face. Third-party names are used only to describe integrations.</p>
<h2>Contact</h2>
<p>Support email: <a href="mailto:support@ttsvoice.top">support@ttsvoice.top</a></p>
</div>
""")
    if path == "/help":
        return _page_shell(path, "Help Center", "Guides, support options, and usage tips for the VoiceForge AI voice generator.", """
<h1>VoiceForge Help Center</h1>
<div class="panel">
<h2>How to Generate Speech</h2>
<ol><li>Enter up to 5,000 characters of text.</li><li>Choose a voice and language.</li><li>Adjust speed, pitch, or SSML options.</li><li>Generate speech, preview it, and download the audio.</li></ol>
<h2>Support</h2>
<p>Email <a href="mailto:support@ttsvoice.top">support@ttsvoice.top</a> or read the <a href="/faq-en">FAQ</a> for common questions.</p>
</div>
""")
    return _page_shell(path, "Terms of Use", "Terms and acceptable use rules for VoiceForge.", """
<h1>Terms of Use</h1>
<div class="panel">
<p>By using VoiceForge, you agree to submit only text you have the right to process and to comply with applicable laws, third-party service terms, and copyright rules.</p>
<h2>Acceptable Use</h2>
<p>Do not use this service to generate fraudulent, harassing, infringing, hateful, sexually explicit, malicious impersonation, or otherwise unlawful content.</p>
<h2>Disclaimer</h2>
<p>The service is provided as-is. You are responsible for how you use generated audio.</p>
</div>
""")


def _use_case_hub(path: str) -> Response:
    lang = "zh" if path.startswith("/zh/") else "en"
    if lang == "zh":
        items = "\n".join(
            f'<li><a href="/zh/use-cases/{slug}">{page["zh_title"]}</a><p>{page["zh_description"]}</p></li>'
            for slug, page in USE_CASE_PAGES.items()
        )
        body = f"""
<h1>VoiceForge 使用场景</h1>
<p>这些指南面向真实工作流：视频配音、播客包装、在线课程、日语语音和开发者原型。每一页都提供可执行的制作建议，并链接回对应工具。</p>
<div class="panel"><ul>{items}</ul></div>
"""
        return _page_shell(path, "VoiceForge 使用场景", "面向视频、播客、教学、日语和开发者工作流的 AI 文字转语音使用指南。", body, lang)

    items = "\n".join(
        f'<li><a href="/use-cases/{slug}">{page["en_title"]}</a><p>{page["en_description"]}</p></li>'
        for slug, page in USE_CASE_PAGES.items()
    )
    body = f"""
<h1>VoiceForge Use Cases</h1>
<p>These guides focus on real workflows: video voiceovers, podcast production, e-learning audio, Japanese TTS, and developer prototyping. Each page includes practical tips and links back to the right VoiceForge tool.</p>
<div class="panel"><ul>{items}</ul></div>
"""
    return _page_shell(path, "VoiceForge Use Cases", "AI text to speech use case guides for video, podcasts, courses, Japanese audio, and developer workflows.", body)


def _use_case_page(slug: str, lang: str) -> Response:
    page = USE_CASE_PAGES.get(slug)
    if not page:
        return _page_shell("/zh/use-cases" if lang == "zh" else "/use-cases", "Use Cases", "VoiceForge use case guides.", "<h1>Use case not found</h1><p>Return to the <a href=\"/use-cases\">use case hub</a>.</p>", lang), 404

    if lang == "zh":
        path = f"/zh/use-cases/{slug}"
        related = "\n".join(
            f'<li><a href="/zh/use-cases/{other_slug}">{other_page["zh_title"]}</a></li>'
            for other_slug, other_page in USE_CASE_PAGES.items()
            if other_slug != slug
        )
        body = page["zh_body"] + f'<div class="panel"><h2>相关指南</h2><ul>{related}</ul><p><a href="/zh/use-cases">返回使用场景中心</a></p></div>'
        return _page_shell(path, page["zh_title"], page["zh_description"], body, lang)

    path = f"/use-cases/{slug}"
    related = "\n".join(
        f'<li><a href="/use-cases/{other_slug}">{other_page["en_title"]}</a></li>'
        for other_slug, other_page in USE_CASE_PAGES.items()
        if other_slug != slug
    )
    body = page["en_body"] + f'<div class="panel"><h2>Related Guides</h2><ul>{related}</ul><p><a href="/use-cases">Back to use cases</a></p></div>'
    return _page_shell(path, page["en_title"], page["en_description"], body)


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
def add_headers(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["X-Frame-Options"] = "SAMEORIGIN"
    resp.headers["Content-Security-Policy"] = "frame-ancestors 'self'"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return resp


# ---------- 静态页面路由 ----------
@app.route("/")
def index():
    return send_from_directory("templates", "index.html")


@app.route("/index.html")
def index_file_redirect():
    return redirect("/", code=301)


@app.route("/zh")
@app.route("/zh/index.html")
@app.route("/zh/")
def index_zh():
    if request.path != "/zh/":
        return redirect("/zh/", code=301)
    return send_from_directory("templates", "index-zh.html")


@app.route("/about")
@app.route("/privacy")
@app.route("/help")
@app.route("/terms")
@app.route("/zh/about")
@app.route("/zh/privacy")
@app.route("/zh/help")
@app.route("/zh/terms")
def legal_or_support_page():
    return _legal_page(request.path)


@app.route("/use-cases")
@app.route("/zh/use-cases")
def use_case_hub():
    return _use_case_hub(request.path)


@app.route("/use-cases/<slug>")
def use_case_page_en(slug):
    return _use_case_page(slug, "en")


@app.route("/zh/use-cases/<slug>")
def use_case_page_zh(slug):
    return _use_case_page(slug, "zh")


@app.route("/faq-en")
def faq_en():
    return send_from_directory("templates", "faq-en.html")


@app.route("/faq-en.html")
def faq_en_file_redirect():
    return redirect("/faq-en", code=301)


@app.route("/faq-zh")
@app.route("/faq-zh.html")
def faq_zh_redirect():
    return redirect("/zh/faq-zh", code=301)


@app.route("/zh/faq-zh")
def faq_zh():
    return send_from_directory("templates", "faq-zh.html")


@app.route("/zh/faq-zh.html")
def faq_zh_file_redirect():
    return redirect("/zh/faq-zh", code=301)


@app.route("/sitemap")
def sitemap_redirect():
    return redirect("/sitemap.xml", code=301)


# ---------- 站点地图（修复域名错误） ----------
@app.route("/sitemap.xml")
def sitemap():
    base = get_site_url()  # 动态获取真实域名
    today = datetime.utcnow().strftime("%Y-%m-%d")
    priorities = {
        "/": "1.0",
        "/zh/": "1.0",
        "/use-cases": "0.8",
        "/zh/use-cases": "0.8",
        "/faq-en": "0.8",
        "/zh/faq-zh": "0.8",
    }
    urls = [(path, priorities.get(path, "0.7")) for path in _indexable_paths()]
    url_entries = "".join(
        f"<url><loc>{base}{path}</loc><lastmod>{today}</lastmod><priority>{pri}</priority></url>"
        for path, pri in urls
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{url_entries}"
        "</urlset>"
    )
    return Response(xml, mimetype="application/xml")


@app.route("/robots.txt")
def robots():
    base = get_site_url()
    txt = f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n"
    return Response(txt, mimetype="text/plain")


@app.route("/ads.txt")
def ads_txt():
    return Response(f"google.com, {ADSENSE_PUBLISHER_ID}, DIRECT, f08c47fec0942fa0\n", mimetype="text/plain")


@app.route(f"/{INDEXNOW_KEY}.txt")
def indexnow_key_file():
    return Response(f"{INDEXNOW_KEY}\n", mimetype="text/plain")


@app.route("/llms.txt")
def llms_txt():
    base = get_site_url()
    lines = [
        "# VoiceForge",
        "",
        "VoiceForge is a free online AI voice generator and text to speech tool.",
        "It supports multilingual neural voices, SSML editing, batch conversion, browser-local history, and downloadable audio.",
        "",
        "## Key URLs",
    ]
    for path, (_, title, description) in INDEXABLE_ROUTES.items():
        lines.append(f"- {title}: {base}{path} — {description}")
    lines.extend([
        "",
        "## Contact",
        "support@ttsvoice.top",
    ])
    return Response("\n".join(lines) + "\n", mimetype="text/plain")


@app.route("/social-feed.json")
def social_feed_json():
    base = get_site_url()
    items = []
    for item in SOCIAL_PROMOTION_POSTS:
        normalized = dict(item)
        normalized["url"] = normalized["url"].replace("https://ttsvoice.top", base)
        normalized["text"] = normalized["text"].replace("https://ttsvoice.top", base)
        items.append(normalized)
    return jsonify(
        site="VoiceForge",
        homepage=base,
        updated=datetime.utcnow().strftime("%Y-%m-%d"),
        guidance="Share only in relevant communities and through accounts you control. Do not spam, mass-post, or fake engagement.",
        posts=items,
    )


@app.route("/social-posts.txt")
def social_posts_txt():
    base = get_site_url()
    lines = [
        "VoiceForge social promotion posts",
        "Share only through accounts you control and where the post is relevant.",
        "",
    ]
    for index, item in enumerate(SOCIAL_PROMOTION_POSTS, start=1):
        lines.append(f"{index}. {item['text'].replace('https://ttsvoice.top', base)}")
        lines.append(f"   Tags: {', '.join(item['tags'])}")
        lines.append("")
    return Response("\n".join(lines), mimetype="text/plain")


# ---------- SPA 回退路由 ----------
@app.route("/<path:path>")
def catch_all(path):
    if path.startswith("api/"):
        return jsonify(error="Not found"), 404

    canonical_redirects = {
        "index.html": "/",
        "index-zh.html": "/zh/",
        "faq-en.html": "/faq-en",
        "faq-zh.html": "/zh/faq-zh",
        "zh": "/zh/",
        "zh/index.html": "/zh/",
        "zh/faq-zh.html": "/zh/faq-zh",
        "sitemap": "/sitemap.xml",
        "zh/sitemap": "/sitemap.xml",
    }
    normalized_path = path.strip("/")
    if normalized_path in canonical_redirects:
        return redirect(canonical_redirects[normalized_path], code=301)

    full_path = os.path.join(TEMPLATE_DIR, path)
    if os.path.isfile(full_path):
        return send_from_directory(TEMPLATE_DIR, path)

    if normalized_path.startswith("zh/") or path.startswith("zh"):
        resp = send_from_directory("templates", "index-zh.html")
        resp.headers["X-Robots-Tag"] = "noindex, follow"
        resp.headers["Link"] = f"<{get_site_url()}/zh/>; rel=\"canonical\""
        return resp

    resp = send_from_directory("templates", "index.html")
    resp.headers["X-Robots-Tag"] = "noindex, follow"
    resp.headers["Link"] = f"<{get_site_url()}/>; rel=\"canonical\""
    return resp


# ---------- TTS API ----------
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


# ---------- 翻译 API ----------
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


# ---------- 翻译逻辑 ----------
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

    for name, url in [
        ("libretranslate", "https://libretranslate.de/translate"),
        ("argos", "https://translate.argosopentech.com/translate"),
    ]:
        try:
            result = _post_json(url, {"q": text, "source": source, "target": target, "format": "text"})
            translated = (result.get("translatedText") or "").strip()
            if translated and translated != text:
                return translated, name
        except Exception:
            continue

    try:
        query = urllib.parse.urlencode({"q": text, "langpair": f"{source}|{target}"})
        with urllib.request.urlopen(f"https://api.mymemory.translated.net/get?{query}", timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            translated = data.get("responseData", {}).get("translatedText", "").strip()
            if translated:
                return translated, "mymemory"
    except Exception:
        pass

    return text, "fallback-original"


# ---------- TTS 引擎 ----------
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
        "en-US": "en", "en-GB": "en", "zh-CN": "zh", "ja-JP": "ja",
        "ko-KR": "ko", "de-DE": "de", "fr-FR": "fr", "es-ES": "es",
        "pt-BR": "pt", "it-IT": "it", "ru-RU": "ru", "ar-SA": "ar", "hi-IN": "hi",
    }
    lang = next((v for k, v in language_map.items() if k in voice), "en")
    buf = io.BytesIO()
    gTTS(text=text, lang=lang).write_to_fp(buf)
    return buf.getvalue()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 7860)), debug=False)

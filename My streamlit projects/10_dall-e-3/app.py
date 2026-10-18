# import libraries
# import libraries
import os
import json
import hashlib
import base64
import uuid
import urllib.parse
import streamlit as st
from openai import OpenAI

def safe_secret(name, default=""):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


st.set_page_config(
    page_title="Aneela's Image Generator",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ───────────────────────── Storage ─────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")
DATA_FILE = os.path.join(BASE_DIR, "user_data.json")


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def valid_email(email):
    return "@" in email and "." in email.split("@")[-1]


def make_initials(name):
    words = name.strip().split()
    if len(words) >= 2:
        return (words[0][0] + words[-1][0]).upper()
    return name.strip()[:2].upper() or "AA"


users = load_json(USERS_FILE, {})
user_data = load_json(DATA_FILE, {})

# ───────────────────────── Session state ─────────────────────────
defaults = {
    "logged_in": False,
    "email": "",
    "profile_name": "Aneela Altaf",
    "profile_initials": "AA",
    "messages": [],
    "history": [],
    "pinned": [],
    "archived": [],
    "chat_store": {},
    "current_chat": None,
    "theme": "Dark",
    "share_chat": None,
    "rename_target": None,
    "mode": "Image",
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def create_chat_title(text):
    if not text:
        return "New Chat"
    text = " ".join(text.strip().split())
    if len(text) <= 35:
        return text
    return text[:35].rsplit(" ", 1)[0] + "..."


def save_current_user():
    if not st.session_state.email:
        return
    user_data[st.session_state.email] = {
        "profile_name": st.session_state.profile_name,
        "profile_initials": st.session_state.profile_initials,
        "history": st.session_state.history,
        "pinned": st.session_state.pinned,
        "archived": st.session_state.archived,
        "chat_store": st.session_state.chat_store,
        "theme": st.session_state.theme,
    }
    save_json(DATA_FILE, user_data)


def load_current_user():
    data = user_data.get(st.session_state.email, {})
    st.session_state.profile_name = data.get("profile_name", "Aneela Altaf")
    st.session_state.profile_initials = data.get("profile_initials", "AA")
    st.session_state.history = data.get("history", [])
    st.session_state.pinned = data.get("pinned", [])
    st.session_state.archived = data.get("archived", [])
    st.session_state.chat_store = data.get("chat_store", {})
    st.session_state.theme = data.get("theme", "Dark")


def save_chat(title, messages):
    title = title or "New Chat"
    if title not in st.session_state.history:
        st.session_state.history.append(title)
    st.session_state.chat_store[title] = list(messages)
    save_current_user()


def load_chat(title):
    st.session_state.messages = list(st.session_state.chat_store.get(title, []))
    st.session_state.current_chat = title


def new_chat():
    st.session_state.messages = []
    st.session_state.current_chat = None


def delete_chat(title):
    for bucket in (st.session_state.history, st.session_state.pinned, st.session_state.archived):
        if title in bucket:
            bucket.remove(title)
    st.session_state.chat_store.pop(title, None)
    if st.session_state.current_chat == title:
        new_chat()
    save_current_user()


def rename_chat(old, new):
    new = create_chat_title(new)
    if not new or new == old or new in st.session_state.history:
        return
    for bucket in (st.session_state.history, st.session_state.pinned, st.session_state.archived):
        if old in bucket:
            bucket[bucket.index(old)] = new
    st.session_state.chat_store[new] = st.session_state.chat_store.pop(old, [])
    if st.session_state.current_chat == old:
        st.session_state.current_chat = new
    save_current_user()


def logout():
    save_current_user()
    st.session_state.logged_in = False
    st.session_state.email = ""
    new_chat()
    st.session_state.share_chat = None
    st.rerun()


# ───────────────────────── Design system ─────────────────────────
# Dark neon-glass look: deep violet-black canvas, blurred gradient light,
# frosted panels, pill-shaped controls and a glowing violet-to-pink accent.
DARK = """
--bg:#000000; --panel:#141414; --surface:#1A1A1A; --surface-2:#262626; --solid:#151515;
--ink:#F6F3F1; --muted:#8E8A88; --line:rgba(255,255,255,.09);
--accent:#FF3D0A; --accent-2:#FF6A2B; --accent-ink:#FFFFFF; --accent-soft:rgba(255,70,20,.16);
--edge:rgba(255,90,40,.40); --glow-a:rgba(255,70,20,.40); --glow-top:rgba(255,70,15,.50);
--shadow:0 10px 40px rgba(0,0,0,.5);
"""
LIGHT = """
--bg:#FFF3EC; --panel:#FFFFFF; --surface:#FFFFFF; --surface-2:#FFE9DD; --solid:#FFFFFF;
--ink:#1E1411; --muted:#8A7068; --line:rgba(30,20,17,.10);
--accent:#F2380A; --accent-2:#FF6A2B; --accent-ink:#FFFFFF; --accent-soft:rgba(242,56,10,.10);
--edge:rgba(242,56,10,.35); --glow-a:rgba(255,90,40,.25); --glow-top:rgba(255,120,60,.35);
--shadow:0 10px 36px rgba(140,60,30,.12);
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');
:root { __TOKENS__ }

html, body, [class*="css"], .stApp { font-family:'Inter', system-ui, sans-serif; }
.stApp {
  color:var(--ink);
  background:radial-gradient(70% 42% at 50% 0%, var(--glow-top), transparent 72%), var(--bg);
  background-attachment:fixed;
}
#MainMenu, footer, header { visibility:hidden; }
.block-container { max-width:1040px; padding-top:1rem; padding-bottom:7rem; }

h1,h2,h3,h4 { font-family:'Inter Tight', sans-serif; color:var(--ink); letter-spacing:-0.03em; }
p, label, span, div { color:inherit; }
.stCaption, [data-testid="stCaptionContainer"] { color:var(--muted) !important; }

/* Sidebar */
section[data-testid="stSidebar"] { background:var(--panel); border-right:1px solid var(--line); }
section[data-testid="stSidebar"] > div { padding-top:1rem; background:transparent; }
section[data-testid="stSidebar"] h3 { font-family:'Inter', sans-serif; font-size:13px; font-weight:500;
  color:var(--muted); margin:22px 0 8px; letter-spacing:0; }
.brand { display:flex; align-items:center; gap:12px; padding:4px 2px 16px; }
.brand-mark { width:38px; height:38px; border-radius:11px; display:grid; place-items:center; font-size:18px;
  color:#fff; background:linear-gradient(145deg, var(--accent-2), var(--accent)); box-shadow:0 6px 20px var(--glow-a); }
.brand-name { font-family:'Inter Tight'; font-weight:600; font-size:16px; line-height:1.15; }
.brand-sub { font-size:12px; color:var(--muted); }

/* Buttons */
.stButton > button, .stDownloadButton > button, [data-testid="stPopoverButton"] {
  border-radius:999px; border:1px solid var(--line); background:var(--surface); color:var(--ink);
  font-weight:500; box-shadow:none; transition:border-color .15s, background .15s, box-shadow .15s; }
.stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stPopoverButton"]:hover {
  border-color:var(--accent); background:var(--accent-soft); color:var(--ink); }
.stButton > button:focus-visible { outline:2px solid var(--accent-2); outline-offset:2px; }
.stButton > button[kind="primary"] { background:linear-gradient(135deg, var(--accent-2), var(--accent));
  color:var(--accent-ink); border:none; box-shadow:0 6px 22px var(--glow-a); }
.stButton > button[kind="primary"]:hover { filter:brightness(1.08); }

section[data-testid="stSidebar"] .stButton > button { text-align:left; justify-content:flex-start;
  border-color:transparent; background:transparent; }
section[data-testid="stSidebar"] .stButton > button:hover { background:var(--surface-2); border-color:transparent; }

/* New chat: pill with a curved orange glow on the left */
section[data-testid="stSidebar"] .st-key-new_chat_btn button[kind="primary"] {
  background:linear-gradient(100deg, var(--accent-soft), transparent 75%); color:var(--ink);
  border:1px solid var(--edge); box-shadow:inset 26px 0 30px -22px var(--glow-a); }

/* Workspace nav tiles */
section[data-testid="stSidebar"] [class*="st-key-nav_"] button {
  background:var(--surface); border:1px solid var(--line); border-radius:14px; padding:.55rem .85rem; }
section[data-testid="stSidebar"] [class*="st-key-nav_"] button[kind="primary"] {
  background:var(--accent-soft); color:var(--ink); border:1px solid var(--accent); box-shadow:none; }

/* Inputs */
.stTextInput input, .stSelectbox > div > div, div[data-baseweb="select"] > div {
  background:var(--surface) !important; color:var(--ink) !important;
  border-radius:14px !important; border-color:var(--line) !important; }
.stTextInput input:focus { border-color:var(--accent) !important; box-shadow:0 0 0 3px var(--accent-soft) !important; }
.st-key-s_model div[data-baseweb="select"] > div { border-radius:999px !important; }
[data-testid="stExpander"] { border:1px solid var(--line); border-radius:16px; background:var(--surface); }
[data-testid="stTabs"] button { font-weight:600; }
[data-testid="stVerticalBlockBorderWrapper"] { border-radius:18px; border-color:var(--line); background:var(--surface); }

/* Hero */
.hero { padding:72px 4px 8px; text-align:left; margin-bottom:26px; }
.hero h1 { font-size:clamp(36px,5.4vw,64px); font-weight:500; line-height:1.04; margin:0 0 18px; }
.hero p { font-size:16px; color:var(--muted); max-width:460px; margin:0; }
.prompt-label { font-size:13px; font-weight:500; color:var(--muted); margin:34px 0 10px; }

/* Tool chips and idea cards */
[class*="st-key-mode_"] button { min-height:0; padding:.5rem 1.1rem; font-size:14px; border-radius:16px;
  background:linear-gradient(135deg, var(--surface-2), transparent); }
[class*="st-key-mode_"] button[kind="primary"] { background:var(--accent-soft); color:var(--ink);
  border:1px solid var(--accent); box-shadow:0 0 24px var(--glow-a); }
[class*="st-key-example_"] button { min-height:72px; padding:18px 20px; border-radius:18px;
  text-align:left; justify-content:flex-start; background:var(--surface); }

/* Chat */
[data-testid="stChatMessage"] { background:var(--panel); border:1px solid var(--line); border-radius:20px;
  padding:16px 18px; box-shadow:var(--shadow); }
[data-testid="stChatMessage"] img { border-radius:14px; }
[data-testid="stChatInput"] { border-radius:22px; border:1px solid var(--edge); background:var(--solid);
  box-shadow:inset -70px 0 80px -60px var(--glow-a), 0 12px 40px rgba(0,0,0,.35); }
[data-testid="stChatInput"]:focus-within { border-color:var(--accent); }
[data-testid="stBottom"] > div { background:transparent; }

/* Profile and upgrade cards */
.profile-card { display:flex; align-items:center; gap:12px; padding:12px; border:1px solid var(--line);
  border-radius:16px; background:var(--surface); margin-top:10px; }
.profile-avatar { width:40px; height:40px; border-radius:50%; color:var(--accent-ink); display:grid; place-items:center;
  font-weight:700; flex:none; background:linear-gradient(135deg, var(--accent-2), var(--accent)); }
.profile-name { font-weight:600; font-size:14px; line-height:1.2; }
.profile-email { font-size:12px; color:var(--muted); word-break:break-all; }
.upgrade { margin-top:14px; padding:16px; border-radius:18px; border:1px solid var(--edge);
  background:linear-gradient(160deg, var(--accent-soft), transparent 70%); }
.upgrade-title { font-family:'Inter Tight'; font-weight:600; font-size:15px; }
.upgrade-sub { font-size:12.5px; color:var(--muted); margin-top:4px; line-height:1.4; }

/* Login */
.login-wrap { text-align:center; padding:48px 0 20px; display:flex; flex-direction:column; align-items:center; }
.login-wrap h1 { font-size:clamp(30px,5vw,44px); font-weight:500; margin:6px 0 6px; }
.login-wrap p { color:var(--muted); font-size:17px; }

/* Force readable text: Streamlit's own theme must not override ours */
.stApp, .stApp p, .stApp span, .stApp label, .stApp li, .stApp small,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
.stApp [data-testid="stMarkdownContainer"] *, .stApp input, .stApp textarea,
.stApp [data-testid="stExpander"] summary *, .stApp [data-testid="stTabs"] button *,
.stApp .stButton > button *, .stApp .stDownloadButton > button *,
[data-baseweb="select"] *, [data-baseweb="popover"] *, [data-baseweb="menu"] *,
[data-testid="stPopoverBody"] *, [data-testid="stToast"] * { color:var(--ink) !important; }

.stApp [data-testid="stCaptionContainer"] *, .stApp .hero p, .stApp .prompt-label, .stApp .brand-sub,
.stApp .profile-email, .stApp .upgrade-sub, .stApp .login-wrap p,
.stApp section[data-testid="stSidebar"] h3, .stApp ::placeholder { color:var(--muted) !important; opacity:1; }

.stApp .stButton > button[kind="primary"], .stApp .stButton > button[kind="primary"] * { color:#FFFFFF !important; }
.stApp [class*="st-key-nav_"] button[kind="primary"] *, .stApp [class*="st-key-mode_"] button[kind="primary"] *,
.stApp .st-key-new_chat_btn button[kind="primary"] * { color:var(--ink) !important; }

/* Dropdowns and popovers follow the theme */
div[data-baseweb="popover"] > div, ul[data-baseweb="menu"], [role="listbox"] { background:var(--solid) !important; }
li[role="option"]:hover, li[role="option"][aria-selected="true"] { background:var(--accent-soft) !important; }
[data-testid="stPopoverBody"] { background:var(--panel) !important; border:1px solid var(--line) !important; }
[data-testid="stChatInput"] textarea { background:transparent !important; }

@media (prefers-reduced-motion: reduce) { * { transition:none !important; animation:none !important; } }
</style>
"""


def inject_css(theme):
    tokens = LIGHT if theme == "Light" else DARK
    st.markdown(CSS.replace("__TOKENS__", tokens), unsafe_allow_html=True)


def toggle_theme():
    st.session_state.theme = "Light" if st.session_state.theme == "Dark" else "Dark"
    save_current_user()


def theme_button_label():
    return "☀ Light" if st.session_state.theme == "Dark" else "🌙 Dark"


inject_css(st.session_state.theme)

# ───────────────────────── Login ─────────────────────────
if not st.session_state.logged_in:
    st.markdown(
        """
        <div class="login-wrap">
            <div class="brand-mark" style="width:56px;height:56px;font-size:26px;border-radius:16px;margin-bottom:18px;">✦</div>
            <h1>Aneela's Image Generator</h1>
            <p>Turn a sentence into an image.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _tl, _tr = st.columns([8, 1.6])
    with _tr:
        st.button(theme_button_label(), key="theme_toggle_login", on_click=toggle_theme, use_container_width=True)

    _, center, _ = st.columns([1, 1.4, 1])
    with center:
        login_tab, create_tab = st.tabs(["Log in", "Create account"])

        with login_tab:
            login_email = st.text_input("Gmail", placeholder="yourname@gmail.com", key="login_email")
            login_password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
            if st.button("Log in", type="primary", use_container_width=True, key="login_btn"):
                email = login_email.strip().lower()
                if not valid_email(email):
                    st.error("Enter a valid Gmail address.")
                elif email not in users:
                    st.error("No account found for this email. Create an account first.")
                elif users[email] != hash_password(login_password):
                    st.error("Incorrect password. Try again.")
                else:
                    st.session_state.logged_in = True
                    st.session_state.email = email
                    load_current_user()
                    st.rerun()

        with create_tab:
            create_email = st.text_input("Gmail", placeholder="yourname@gmail.com", key="create_email")
            create_password = st.text_input("Password", type="password", placeholder="At least 6 characters", key="create_password")
            confirm_password = st.text_input("Confirm password", type="password", placeholder="Re-enter your password", key="confirm_password")
            if st.button("Create account", type="primary", use_container_width=True, key="create_btn"):
                email = create_email.strip().lower()
                if not valid_email(email):
                    st.error("Enter a valid Gmail address.")
                elif len(create_password) < 6:
                    st.error("Password needs at least 6 characters.")
                elif create_password != confirm_password:
                    st.error("Passwords don't match.")
                elif email in users:
                    st.error("This account already exists. Log in instead.")
                else:
                    users[email] = hash_password(create_password)
                    save_json(USERS_FILE, users)
                    st.session_state.logged_in = True
                    st.session_state.email = email
                    name = email.split("@")[0].replace(".", " ").title()
                    st.session_state.profile_name = name
                    st.session_state.profile_initials = make_initials(name)
                    save_current_user()
                    st.rerun()
    st.stop()

# ───────────────────────── OpenAI client ─────────────────────────
def require_client():
    """Uses the visitor's own key if given, otherwise the key in secrets.toml."""
    def clean(value):
        return str(value or "").strip().strip("\"'").strip()

    key = clean(st.session_state.get("user_api_key", ""))
    if not key and not safe_secret("REQUIRE_USER_KEY", False):
        key = clean(safe_secret("OPENAI_API_KEY", ""))
    if not key:
        raise ValueError("No API key found. Add your own OpenAI API key in the sidebar under API key.")
    return OpenAI(api_key=key)


# ───────────────────────── Generation ─────────────────────────
def generate_images(prompt, model, size, quality, count, background, output_format):
    """Returns a list of base64 strings (JSON-safe, so chats can be saved)."""
    response = require_client().images.generate(
        model=model,
        prompt=prompt,
        size=size,
        quality=quality,
        n=count,
        background=background,
        output_format=output_format,
    )
    return [item.b64_json for item in response.data if getattr(item, "b64_json", None)]


MODES = [
    ("Image", "🖼️", "Images", "Turn a sentence into an image."),
    ("Presentation", "📊", "Presentations", "Outline a deck in seconds."),
    ("Code", "⌨️", "Code", "Write, fix and explain code."),
]

TEXT_MODEL = safe_secret("TEXT_MODEL", "gpt-4o-mini")
SYSTEM_PROMPTS = {
    "Presentation": (
        "You are a presentation builder. Turn the request into a slide deck outline in Markdown: "
        "a title slide, then 6 to 10 slides. For each slide give a short title, 3 to 5 concise "
        "bullets and one line of speaker notes. Keep wording tight and specific."
    ),
    "Code": (
        "You are a careful coding assistant. Give working code in fenced code blocks with the "
        "language tag, then a short explanation. Ask for missing details only if essential."
    ),
}


def generate_text(prompt, mode):
    response = require_client().chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPTS[mode]},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content


def run_generation(prompt_text, file_names=None, mode=None):
    """Adds the user message, generates, stores the result, and saves the chat."""
    file_names = file_names or []
    mode = mode or st.session_state.mode
    if not st.session_state.current_chat:
        st.session_state.current_chat = create_chat_title(prompt_text)

    st.session_state.messages.append(
        {"role": "user", "content": prompt_text, "files": file_names}
    )

    final_prompt = prompt_text
    if file_names:
        final_prompt += "\n\nReference files attached: " + ", ".join(file_names)

    try:
        if mode == "Image":
            with st.spinner("Creating your image..."):
                images = generate_images(
                    final_prompt, model, size, quality, count, background, output_format
                )
            st.session_state.messages.append(
                {"role": "assistant", "images": images, "format": output_format}
            )
        else:
            label = "Drafting your slides..." if mode == "Presentation" else "Writing your code..."
            with st.spinner(label):
                text = generate_text(final_prompt, mode)
            st.session_state.messages.append({"role": "assistant", "text": text})
    except Exception as e:
        msg = str(e)
        if "invalid_api_key" in msg or "Error code: 401" in msg:
            which = (
                "the key you entered in the sidebar"
                if str(st.session_state.get("user_api_key", "")).strip()
                else "the key in your secrets"
            )
            msg = (
                f"OpenAI rejected {which}. Check that it is complete, still active, "
                "and has no extra spaces or quotes."
            )
        else:
            msg = f"Generation failed: {msg}"
        st.session_state.messages.append({"role": "assistant", "error": msg})

    save_chat(st.session_state.current_chat, st.session_state.messages)
    st.rerun()


def to_image_bytes(item):
    """Accepts base64 text or raw bytes. Returns valid image bytes, or None."""
    from io import BytesIO
    from PIL import Image

    try:
        if isinstance(item, (bytes, bytearray)):
            raw = bytes(item)
            try:  # bytes that are actually base64 text
                Image.open(BytesIO(raw)).verify()
            except Exception:
                raw = base64.b64decode(raw)
        elif isinstance(item, str):
            if item.startswith("data:"):
                item = item.split(",", 1)[-1]
            raw = base64.b64decode(item)
        else:
            return None
        Image.open(BytesIO(raw)).verify()
        return raw
    except Exception:
        return None


def render_images(images, fmt, msg_index):
    valid = [(i, to_image_bytes(x)) for i, x in enumerate(images)]
    valid = [(i, raw) for i, raw in valid if raw]
    if not valid:
        st.warning(
            "This image can't be displayed. It was probably saved by an older "
            "version of the app. Generate it again to replace it."
        )
        return
    cols = st.columns(min(len(valid), 2))
    for pos, (i, raw) in enumerate(valid):
        with cols[pos % len(cols)]:
            st.image(raw, use_container_width=True)
            st.download_button(
                "Download",
                data=raw,
                file_name=f"generated_image_{i + 1}.{fmt}",
                mime=f"image/{fmt}",
                key=f"dl_{msg_index}_{i}",
                use_container_width=True,
            )


# ───────────────────────── Sidebar ─────────────────────────
def chat_actions(title, index, section):
    with st.popover("⋮"):
        if st.button("Rename", key=f"{section}_rename_{index}", use_container_width=True):
            st.session_state.rename_target = title
            st.rerun()
        if st.button("Share", key=f"{section}_share_{index}", use_container_width=True):
            st.session_state.share_chat = title
            st.rerun()
        pin_label = "Unpin" if title in st.session_state.pinned else "Pin"
        if st.button(pin_label, key=f"{section}_pin_{index}", use_container_width=True):
            if title in st.session_state.pinned:
                st.session_state.pinned.remove(title)
            else:
                st.session_state.pinned.append(title)
            save_current_user()
            st.rerun()
        arch_label = "Restore" if title in st.session_state.archived else "Archive"
        if st.button(arch_label, key=f"{section}_archive_{index}", use_container_width=True):
            if title in st.session_state.archived:
                st.session_state.archived.remove(title)
            else:
                st.session_state.archived.append(title)
            save_current_user()
            st.rerun()
        if st.button("Delete", key=f"{section}_delete_{index}", use_container_width=True):
            delete_chat(title)
            st.rerun()


def chat_list(titles, section, prefix=""):
    for index, title in enumerate(titles):
        c1, c2 = st.columns([5, 1])
        with c1:
            if st.button(f"{prefix}{title}", key=f"{section}_chat_{index}", use_container_width=True):
                load_chat(title)
                st.rerun()
        with c2:
            chat_actions(title, index, section)


with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <div class="brand-mark">✦</div>
            <div>
                <div class="brand-name">Aneela's Image Generator</div>
                <div class="brand-sub">Powered by OpenAI</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("New chat", type="primary", use_container_width=True, key="new_chat_btn"):
        new_chat()
        st.rerun()

    if st.session_state.rename_target:
        target = st.session_state.rename_target
        new_name = st.text_input("New name", value=target, key="rename_input")
        r1, r2 = st.columns(2)
        if r1.button("Save", key="rename_save", use_container_width=True):
            rename_chat(target, new_name)
            st.session_state.rename_target = None
            st.rerun()
        if r2.button("Cancel", key="rename_cancel", use_container_width=True):
            st.session_state.rename_target = None
            st.rerun()

    st.markdown("### Workspaces")
    for mode_key, icon, title, _desc in MODES:
        active = st.session_state.mode == mode_key
        if st.button(f"{icon}  {title}", key=f"nav_{mode_key}", use_container_width=True,
                     type="primary" if active else "secondary"):
            st.session_state.mode = mode_key
            new_chat()
            st.rerun()

    history = st.session_state.history
    pinned_chats = [t for t in history if t in st.session_state.pinned and t not in st.session_state.archived]
    active_chats = [t for t in history if t not in st.session_state.archived and t not in st.session_state.pinned]
    archived_chats = [t for t in history if t in st.session_state.archived]

    if pinned_chats:
        st.markdown("### Pinned")
        chat_list(pinned_chats, "pinned", "📌 ")

    st.markdown("### Recent")
    if active_chats:
        chat_list(list(reversed(active_chats)), "history")
    else:
        st.caption("Your images will show up here.")

    if archived_chats:
        with st.expander(f"Archive ({len(archived_chats)})"):
            chat_list(archived_chats, "archive")

    st.markdown("### API key")
    with st.expander("Use your own OpenAI key"):
        st.text_input("OpenAI API key", type="password", key="user_api_key", placeholder="sk-...")
        if str(st.session_state.get("user_api_key", "")).strip():
            st.caption("Using your key for this session.")
        elif safe_secret("REQUIRE_USER_KEY", False):
            st.caption("Add your key to start creating.")
        else:
            st.caption("Using the app's shared key.")
        st.caption("Kept in this session only. It is never saved.")

    st.markdown("### Account")
    st.markdown(
        f"""
        <div class="profile-card">
            <div class="profile-avatar">{st.session_state.profile_initials}</div>
            <div>
                <div class="profile-name">{st.session_state.profile_name}</div>
                <div class="profile-email">{st.session_state.email}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Profile"):
        profile_name = st.text_input("Profile name", value=st.session_state.profile_name, key="profile_name_input")
        if st.button("Save profile", use_container_width=True, key="save_profile"):
            if profile_name.strip():
                st.session_state.profile_name = profile_name.strip()
                st.session_state.profile_initials = make_initials(profile_name)
                save_current_user()
                st.rerun()

    st.markdown(
        """
        <div class="upgrade">
            <div class="upgrade-title">Go Premium</div>
            <div class="upgrade-sub">Unlock more creations and priority speed.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Upgrade", use_container_width=True, key="upgrade_btn"):
        st.toast("Premium plans are coming soon.")

    if st.button("Log out", use_container_width=True, key="logout_btn",
                  on_click=lambda: st.session_state.update(user_api_key="")):
        logout()

# ───────────────────────── Top bar ─────────────────────────
def export_text():
    lines = [f"# {st.session_state.current_chat or 'Chat'}", ""]
    for m in st.session_state.messages:
        if m["role"] == "user":
            lines += [f"**You:** {m['content']}", ""]
        elif m.get("text"):
            lines += [m["text"], ""]
        elif m.get("images"):
            lines += [f"_(generated {len(m['images'])} image(s))_", ""]
        elif m.get("error"):
            lines += [f"_{m['error']}_", ""]
    return "\n".join(lines)


top_model, _top_gap, top_theme, top_cfg, top_export = st.columns([2.4, 2.2, 1.2, 1.6, 1.2])
with top_model:
    model = st.selectbox(
        "Model", ["gpt-image-2.5-flare", "gpt-image-2.5-sunburst"],
        key="s_model", label_visibility="collapsed",
    )
with top_theme:
    st.button(theme_button_label(), key="theme_toggle", on_click=toggle_theme, use_container_width=True)
with top_cfg:
    with st.popover("⚙ Configuration", use_container_width=True):
        size = st.selectbox("Size", ["1024x1024", "1536x1024", "1024x1536"], key="s_size")
        quality = st.selectbox("Quality", ["low", "medium", "high", "xhigh", "max"], key="s_quality")
        count = st.selectbox("Images per prompt", [1, 2, 3, 4], key="s_count")
        background = st.selectbox("Background", ["opaque", "transparent"], key="s_background")
        output_format = st.selectbox("Format", ["png", "webp", "jpeg"], key="s_format")
        if background == "transparent" and output_format == "jpeg":
            output_format = "png"
            st.caption("JPEG can't be transparent, so PNG will be used.")
with top_export:
    st.download_button(
        "Export ⤓", data=export_text(), file_name="chat.md", mime="text/markdown",
        disabled=not st.session_state.messages, use_container_width=True, key="export_btn",
    )

# ───────────────────────── Share panel ─────────────────────────
if st.session_state.share_chat:
    share_link = (
        "https://your-streamlit-app.streamlit.app?shared_chat="
        + urllib.parse.quote(uuid.uuid4().hex[:12])
    )
    with st.container(border=True):
        st.markdown(f"**Share “{st.session_state.share_chat}”**")
        st.code(share_link, language="text")
        if st.button("Close", key="close_share"):
            st.session_state.share_chat = None
            st.rerun()

# ───────────────────────── Main area ─────────────────────────
EXAMPLES = [
    (
        "🧕 Hijabi AI instructor",
        "A beautiful elegant young adult hijabi woman wearing a sophisticated modest hijab and "
        "professional outfit, warm smile, natural facial expression, confident professional body "
        "language, standing in a modern AI technology studio with holographic screens, cinematic "
        "lighting, realistic photography, highly detailed, professional composition",
    ),
    (
        "🤖 AI classroom",
        "A cinematic futuristic AI classroom with holographic screens, advanced technology, "
        "beautiful modern interior and realistic professional lighting",
    ),
    (
        "🏔️ Pakistani landscape",
        "A breathtaking realistic Pakistani mountain landscape at sunset, dramatic sky, beautiful "
        "natural lighting, highly detailed photography",
    ),
    (
        "💎 AI startup brand",
        "A premium modern AI startup brand visual, elegant futuristic design, professional "
        "technology aesthetic and clean composition",
    ),
]

STYLES = [
    (
        "📸 Photorealistic",
        "A highly realistic professional photograph with natural lighting, realistic textures and "
        "detailed surroundings.",
    ),
    (
        "🎨 Artistic",
        "A beautiful artistic illustration with rich details, creative composition and elegant "
        "visual storytelling.",
    ),
]

IDEAS = {
    "Image": EXAMPLES + STYLES,
    "Presentation": [
        ("🚀 Startup pitch", "Pitch deck for an AI education startup: problem, solution, market, product, traction, team and ask."),
        ("📈 Quarterly review", "Quarterly business review deck covering results, wins, challenges and next-quarter priorities."),
    ],
    "Code": [
        ("🐍 Python script", "Write a Python script that renames all files in a folder using a date prefix."),
        ("🌐 Landing page", "Create a responsive landing page in HTML and CSS with a hero, features and a contact form."),
    ],
}
PLACEHOLDERS = {
    "Image": "Ask anything... describe the image you want",
    "Presentation": "What is your presentation about?",
    "Code": "What should we build or fix?",
}

CHIP_LABELS = {"Image": "Create Image", "Presentation": "Make a Deck", "Code": "Write Code"}

if not st.session_state.messages:
    st.markdown(
        f"""
        <div class="hero">
            <h1>Ready to Create<br>Something New?</h1>
            <p>Hi {st.session_state.profile_name.split()[0]}. Pick a tool, then describe what you need. Attach a reference file if you have one.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    chip_cols = st.columns([1, 1, 1, 2.2])
    for col, (mode_key, icon, _title, _desc) in zip(chip_cols, MODES):
        with col:
            active = st.session_state.mode == mode_key
            if st.button(f"{icon} {CHIP_LABELS[mode_key]}", key=f"mode_{mode_key}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.mode = mode_key
                st.rerun()

    st.markdown('<div class="prompt-label">Start from an idea</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, (label, text) in enumerate(IDEAS[st.session_state.mode]):
        with cols[i % 2]:
            if st.button(label, key=f"example_{st.session_state.mode}_{i}", use_container_width=True):
                run_generation(text)
else:
    for m_index, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
                for file_info in message.get("files", []):
                    st.caption(f"📎 {file_info}")
        else:
            with st.chat_message("assistant"):
                if message.get("error"):
                    st.error(message["error"])
                elif message.get("images"):
                    render_images(message["images"], message.get("format", "png"), m_index)
                elif message.get("text"):
                    st.markdown(message["text"])

# ───────────────────────── Chat input ─────────────────────────
prompt_data = st.chat_input(
    PLACEHOLDERS[st.session_state.mode],
    accept_file="multiple",
    key="image_prompt",
)

if prompt_data:
    if isinstance(prompt_data, str):
        prompt_text, uploaded_files = prompt_data, []
    else:
        prompt_text = prompt_data.get("text", "") if hasattr(prompt_data, "get") else getattr(prompt_data, "text", "")
        uploaded_files = prompt_data.get("files", []) if hasattr(prompt_data, "get") else getattr(prompt_data, "files", [])

    file_names = [f.name for f in uploaded_files]

    if not prompt_text and not uploaded_files:
        st.warning("Enter a prompt or attach a file.")
        st.stop()

    if not prompt_text:
        prompt_text = "Create an image based on the uploaded reference file."

    run_generation(prompt_text, file_names)
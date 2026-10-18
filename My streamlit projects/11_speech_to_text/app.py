# import libraries
import streamlit as st
from groq import Groq
import tempfile
import os
import shutil
import requests
import yt_dlp
from moviepy import AudioFileClip

st.set_page_config(
    page_title="Speech2Text AI",
    page_icon="🎙️",
    layout="wide"
)

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

dark = st.session_state.theme == "dark"

if dark:
    bg = "#071C14"
    bg2 = "#0D2A20"
    card = "#12352A"
    card2 = "#174534"
    text = "#F4FFF9"
    muted = "#B7D1C5"
    border = "#27634E"
    input_bg = "#0B241B"
    result_bg = "#0D2A20"
    green = "#45D99A"
    orange = "#FF8A3D"
    shadow = "rgba(0,0,0,.40)"
else:
    bg = "#E8F5EC"
    bg2 = "#D7F0E0"
    card = "#F9FFFB"
    card2 = "#FFF0E2"
    text = "#17352A"
    muted = "#60786D"
    border = "#B8D8C4"
    input_bg = "#FFFFFF"
    result_bg = "#FFF3E5"
    green = "#168A55"
    orange = "#F47721"
    shadow = "rgba(40,100,65,.14)"

st.markdown(
    f"""
    <style>
    .stApp {{
        background:
            radial-gradient(
                circle at 8% 5%,
                rgba(255,138,61,.18),
                transparent 25%
            ),
            radial-gradient(
                circle at 92% 10%,
                rgba(69,217,154,.18),
                transparent 30%
            ),
            {bg};
        color: {text};
    }}

    [data-testid="stHeader"] {{
        background: transparent;
    }}

    section[data-testid="stSidebar"] {{
        background: {bg2};
        border-right: 1px solid {border};
    }}

    .sidebar-brand {{
        text-align: center;
        padding: 15px 5px 20px;
    }}

    .sidebar-mic {{
        width: 72px;
        height: 72px;
        margin: auto;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        font-size: 32px;
        background:
            linear-gradient(
                135deg,
                rgba(255,138,61,.22),
                rgba(69,217,154,.20)
            );
        border: 1px solid rgba(69,217,154,.50);
        animation: pulse 2s infinite;
    }}

    @keyframes pulse {{
        0% {{
            transform: scale(1);
            box-shadow: 0 0 0 0 rgba(69,217,154,.30);
        }}
        50% {{
            transform: scale(1.06);
            box-shadow: 0 0 0 10px rgba(69,217,154,.06);
        }}
        100% {{
            transform: scale(1);
            box-shadow: 0 0 0 0 rgba(69,217,154,0);
        }}
    }}

    .sidebar-brand h2 {{
        color: {text};
        margin: 12px 0 4px;
        font-size: 22px;
    }}

    .sidebar-brand p {{
        color: {muted};
        font-size: 12px;
    }}

    .sidebar-box {{
        padding: 16px;
        margin-top: 15px;
        border: 1px solid {border};
        border-radius: 15px;
        background: {card};
    }}

    .sidebar-label {{
        color: {muted};
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }}

    .social {{
        display: flex;
        gap: 7px;
        margin-top: 12px;
    }}

    .social a {{
        flex: 1;
        text-align: center;
        padding: 8px 3px;
        text-decoration: none;
        color: {text};
        background: {card2};
        border: 1px solid {border};
        border-radius: 9px;
        font-size: 11px;
        font-weight: 700;
    }}

    .social a:hover {{
        color: {orange};
        border-color: {orange};
    }}

    .theme-title {{
        text-align: right;
        color: {muted};
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }}

    .theme-button .stButton > button {{
        background: {card};
        color: {text};
        border: 1px solid {border};
        border-radius: 11px;
        font-weight: 800;
    }}

    .theme-button .stButton > button:hover {{
        color: {orange};
        border-color: {orange};
    }}

    .hero {{
        position: relative;
        overflow: hidden;
        padding: 48px 40px;
        border-radius: 28px;
        background:
            linear-gradient(
                135deg,
                {card},
                {card2}
            );
        border: 1px solid {border};
        box-shadow: 0 20px 50px {shadow};
    }}

    .hero::before {{
        content: "";
        position: absolute;
        width: 280px;
        height: 280px;
        right: -100px;
        top: -120px;
        border-radius: 50%;
        background:
            radial-gradient(
                circle,
                rgba(255,138,61,.28),
                transparent 70%
            );
    }}

    .hero::after {{
        content: "";
        position: absolute;
        width: 250px;
        height: 250px;
        left: -120px;
        bottom: -130px;
        border-radius: 50%;
        background:
            radial-gradient(
                circle,
                rgba(69,217,154,.20),
                transparent 70%
            );
    }}

    .badge {{
        position: relative;
        display: inline-block;
        padding: 8px 14px;
        border-radius: 30px;
        background: rgba(255,138,61,.12);
        border: 1px solid rgba(255,138,61,.40);
        color: {orange};
        font-size: 12px;
        font-weight: 800;
        margin-bottom: 18px;
    }}

    .hero h1 {{
        position: relative;
        margin: 0;
        color: {text};
        font-size: clamp(40px,5vw,68px);
        line-height: 1.05;
        font-weight: 900;
        letter-spacing: -2px;
    }}

    .hero h1 span {{
        background:
            linear-gradient(
                90deg,
                {orange},
                {green}
            );
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}

    .hero-description {{
        position: relative;
        color: {muted};
        font-size: 17px;
        line-height: 1.7;
        margin-top: 20px;
        max-width: 700px;
    }}

    .ai-model {{
        position: relative;
        display: inline-block;
        margin-top: 17px;
        padding: 10px 15px;
        border-radius: 12px;
        background: {bg2};
        border: 1px solid {border};
        color: {text};
        font-size: 13px;
        font-weight: 700;
    }}

    .ai-model strong {{
        color: {green};
    }}

    .steps {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        margin: 30px 0;
    }}

    .step {{
        display: flex;
        align-items: center;
        gap: 9px;
        color: {muted};
        font-size: 14px;
        white-space: nowrap;
    }}

    .step span {{
        width: 34px;
        height: 34px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        border: 1px solid {border};
        color: {muted};
        font-size: 12px;
        font-weight: 700;
    }}

    .step.active span {{
        background: {green};
        color: white;
        border-color: {green};
    }}

    .step.active b {{
        color: {text};
    }}

    .arrow {{
        color: {orange};
        font-size: 22px;
        font-weight: 700;
    }}

    .section-title {{
        color: {text};
        font-size: 28px;
        font-weight: 850;
        margin-top: 32px;
        margin-bottom: 5px;
    }}

    .section-description {{
        color: {muted};
        font-size: 13px;
        margin-bottom: 18px;
    }}

    .source-card {{
        padding: 18px;
        margin-bottom: 13px;
        border-radius: 16px;
        background: {card};
        border: 1px solid {border};
        box-shadow: 0 8px 25px {shadow};
    }}

    .source-title {{
        color: {text};
        font-size: 15px;
        font-weight: 800;
    }}

    .source-description {{
        color: {muted};
        font-size: 12px;
        margin-top: 4px;
    }}

    .stTextInput input {{
        background: {input_bg} !important;
        color: {text} !important;
        border: 1px solid {border} !important;
        border-radius: 11px !important;
    }}

    div[data-baseweb="select"] > div {{
        background: {input_bg};
        border-color: {border};
        color: {text};
        border-radius: 11px;
    }}

    [data-testid="stFileUploader"] {{
        background: {input_bg};
        border: 1px dashed {border};
        border-radius: 13px;
    }}

    .stButton > button {{
        background: {card};
        color: {text};
        border: 1px solid {border};
        border-radius: 11px;
        min-height: 43px;
        font-weight: 800;
    }}

    .stButton > button:hover {{
        color: {orange};
        border-color: {orange};
    }}

    .primary .stButton > button {{
        background:
            linear-gradient(
                90deg,
                {green},
                {orange}
            );
        color: white;
        border: none;
        box-shadow: 0 10px 25px {shadow};
    }}

    .primary .stButton > button:hover {{
        color: white;
        transform: translateY(-2px);
    }}

    .secure {{
        margin-top: 18px;
        padding: 13px 15px;
        border-radius: 13px;
        background: rgba(69,217,154,.09);
        border: 1px solid rgba(69,217,154,.25);
        color: {muted};
        font-size: 12px;
    }}

    .result {{
        margin-top: 22px;
        padding: 22px;
        border-radius: 17px;
        background: {result_bg};
        border: 1px solid {border};
        box-shadow: 0 10px 30px {shadow};
    }}

    .result-head {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 13px;
    }}

    .result-title {{
        color: {text};
        font-size: 17px;
        font-weight: 850;
    }}

    .status {{
        color: {green};
        font-size: 11px;
        font-weight: 800;
    }}

    .transcription {{
        color: {text};
        background: {input_bg};
        border: 1px solid {border};
        border-radius: 12px;
        padding: 17px;
        line-height: 1.8;
        white-space: pre-wrap;
        word-break: break-word;
        font-size: 14px;
    }}

    .footer {{
        margin-top: 35px;
        padding: 20px;
        text-align: center;
        border-top: 1px solid {border};
        color: {muted};
        font-size: 11px;
    }}

    .footer strong {{
        color: {orange};
    }}

    @media(max-width:800px) {{
        .steps {{
            flex-direction: column;
            align-items: flex-start;
            gap: 8px;
        }}

        .arrow {{
            transform: rotate(90deg);
            margin-left: 8px;
        }}

        .hero {{
            padding: 32px 24px;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True
)


def transcribe_audio(client, audio_path):
    compressed_path = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".mp3"
    ).name

    try:
        with AudioFileClip(audio_path) as audio:
            audio.write_audiofile(
                compressed_path,
                fps=16000,
                bitrate="32k",
                codec="libmp3lame",
                logger=None
            )

        if os.path.getsize(compressed_path) > 20 * 1024 * 1024:
            raise Exception("Audio is still larger than 20 MB.")

        with open(compressed_path, "rb") as file:
            result = client.audio.transcriptions.create(
                file=file,
                model="whisper-large-v3-turbo"
            )

        return result.text

    finally:
        if os.path.exists(compressed_path):
            os.remove(compressed_path)


def show_result(text):
    safe_text = (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    st.markdown(
        f"""
        <div class="result">
            <div class="result-head">
                <div class="result-title">
                    📝 Your Transcription
                </div>
                <div class="status">
                    ● Complete
                </div>
            </div>
            <div class="transcription">
                {safe_text}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


st.sidebar.markdown(
    """
    <div class="sidebar-brand">
        <div class="sidebar-mic">🎙️</div>
        <h2>Speech2Text AI</h2>
        <p>AI-powered speech recognition</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown(
    '<div class="sidebar-box"><div class="sidebar-label">GROQ API KEY</div>',
    unsafe_allow_html=True
)

api_key = st.sidebar.text_input(
    "Groq API Key",
    type="password",
    placeholder="Enter your Groq API key",
    label_visibility="collapsed"
)

st.sidebar.markdown("</div>", unsafe_allow_html=True)

st.sidebar.markdown(
    """
    <div class="sidebar-box">
        <div class="sidebar-label">CREATOR</div>
        <div style="font-weight:800;">Aneela Altaf</div>
        <div style="color:#80958B;font-size:12px;margin-top:3px;">
            AI Student • Developer • Creator
        </div>
        <div class="social">
            <a href="https://github.com/aneelaaltaf007" target="_blank">
                GitHub
            </a>
            <a href="https://www.linkedin.com/in/aneelaaltaf007/" target="_blank">
                LinkedIn
            </a>
            <a href="mailto:aneela.altaftech@gmail.com">
                Email
            </a>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

left, right = st.columns([8, 2])

with right:
    st.markdown(
        '<div class="theme-title">CURRENT THEME</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="theme-button">',
        unsafe_allow_html=True
    )

    if st.button(
        "🌙 DARK MODE" if dark else "☀️ LIGHT MODE",
        use_container_width=True
    ):
        st.session_state.theme = "light" if dark else "dark"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


st.markdown("### 🎙️ AI-Powered Speech Recognition")

st.title("Turn Your Voice Into Text with AI")

st.write(
    "Precise, private, remarkably fast. "
    "Fast, accurate AI transcription for audio files, "
    "YouTube videos, and online audio."
)

st.info("⚡ Powered by Whisper Large v3 Turbo")

st.markdown("---")

st.subheader("How It Works")

col1, arrow1, col2, arrow2, col3, arrow3, col4 = st.columns(
    [2.5, 0.5, 2.5, 0.5, 2.5, 0.5, 2.5]
)

with col1:
    st.markdown("### 🟢 01")
    st.write("**Choose Source**")

with arrow1:
    st.markdown("## →")

with col2:
    st.markdown("### ⚪ 02")
    st.write("**Provide Audio**")

with arrow2:
    st.markdown("## →")

with col3:
    st.markdown("### ⚪ 03")
    st.write("**Transcribe**")

with arrow3:
    st.markdown("## →")

with col4:
    st.markdown("### ⚪ 04")
    st.write("**Use Your Text**")

st.markdown(
    """
    <div class="section-title">
        Choose Your Audio Source
    </div>
    <div class="section-description">
        Select an input method to begin your AI transcription.
    </div>
    """,
    unsafe_allow_html=True
)

source = st.selectbox(
    "Audio source",
    [
        "Upload Audio File",
        "Enter YouTube URL",
        "Enter Direct Audio URL"
    ],
    label_visibility="collapsed"
)

client = Groq(api_key=api_key) if api_key else None

if source == "Upload Audio File":

    st.markdown(
        """
        <div class="source-card">
            <div class="source-title">
                📁 Upload Audio
            </div>
            <div class="source-description">
                Upload MP3, WAV, M4A, MP4, OGG or FLAC.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    uploaded = st.file_uploader(
        "Audio file",
        type=[
            "mp3",
            "mp4",
            "mpeg",
            "mpga",
            "m4a",
            "wav",
            "webm",
            "ogg",
            "flac"
        ],
        label_visibility="collapsed"
    )

    if uploaded:

        st.markdown(
            f"""
            <div class="secure">
                🎵 <strong>{uploaded.name}</strong> is ready.
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="primary">',
            unsafe_allow_html=True
        )

        if st.button(
            "🚀 Start Transcribing",
            use_container_width=True
        ):

            if not api_key:
                st.error("Please enter your Groq API key.")

            else:
                temp = None

                try:
                    suffix = os.path.splitext(
                        uploaded.name
                    )[1]

                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=suffix
                    ) as file:

                        file.write(
                            uploaded.getbuffer()
                        )

                        temp = file.name

                    with st.spinner(
                        "AI is transcribing..."
                    ):

                        result = transcribe_audio(
                            client,
                            temp
                        )

                    st.success(
                        "Transcription completed!"
                    )

                    show_result(result)

                except Exception as e:
                    st.error(
                        f"An error occurred: {e}"
                    )

                finally:

                    if temp and os.path.exists(temp):
                        os.remove(temp)

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )


elif source == "Enter YouTube URL":

    st.markdown(
        """
        <div class="source-card">
            <div class="source-title">
                ▶️ YouTube Video
            </div>
            <div class="source-description">
                Paste a public YouTube URL.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    url = st.text_input(
        "YouTube URL",
        placeholder="https://www.youtube.com/watch?v=...",
        label_visibility="collapsed"
    )

    st.markdown(
        '<div class="primary">',
        unsafe_allow_html=True
    )

    if st.button(
        "🎬 Transcribe YouTube Audio",
        use_container_width=True
    ):

        if not url:
            st.warning(
                "Please enter a YouTube URL."
            )

        elif not api_key:
            st.error(
                "Please enter your Groq API key."
            )

        else:

            temp_dir = tempfile.mkdtemp()

            try:

                with st.spinner(
                    "Downloading YouTube audio..."
                ):

                    options = {
                        "format": "bestaudio/best",
                        "outtmpl": os.path.join(
                            temp_dir,
                            "audio.%(ext)s"
                        ),
                        "noplaylist": True,
                        "quiet": True,
                        "no_warnings": True
                    }

                    with yt_dlp.YoutubeDL(
                        options
                    ) as ydl:

                        ydl.download([url])

                files = os.listdir(temp_dir)

                if not files:
                    raise Exception(
                        "YouTube audio could not be downloaded."
                    )

                downloaded = os.path.join(
                    temp_dir,
                    files[0]
                )

                converted = os.path.join(
                    temp_dir,
                    "audio.mp3"
                )

                with st.spinner(
                    "Converting audio..."
                ):

                    with AudioFileClip(
                        downloaded
                    ) as audio:

                        audio.write_audiofile(
                            converted,
                            fps=16000,
                            bitrate="32k",
                            codec="libmp3lame",
                            logger=None
                        )

                with st.spinner(
                    "AI is transcribing..."
                ):

                    result = transcribe_audio(
                        client,
                        converted
                    )

                st.success(
                    "YouTube transcription completed!"
                )

                show_result(result)

            except Exception as e:

                st.error(
                    f"An error occurred: {e}"
                )

            finally:

                shutil.rmtree(
                    temp_dir,
                    ignore_errors=True
                )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


else:

    st.markdown(
        """
        <div class="source-card">
            <div class="source-title">
                🔗 Direct Audio URL
            </div>
            <div class="source-description">
                Paste a direct link to an online audio file.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    url = st.text_input(
        "Audio URL",
        placeholder="https://example.com/audio.mp3",
        label_visibility="collapsed"
    )

    st.markdown(
        '<div class="primary">',
        unsafe_allow_html=True
    )

    if st.button(
        "🔗 Transcribe Online Audio",
        use_container_width=True
    ):

        if not url:
            st.warning(
                "Please enter an audio URL."
            )

        elif not api_key:
            st.error(
                "Please enter your Groq API key."
            )

        else:

            temp = None

            try:

                with st.spinner(
                    "Downloading audio..."
                ):

                    response = requests.get(
                        url,
                        timeout=30
                    )

                    response.raise_for_status()

                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=".mp3"
                    ) as file:

                        file.write(
                            response.content
                        )

                        temp = file.name

                with st.spinner(
                    "AI is transcribing..."
                ):

                    result = transcribe_audio(
                        client,
                        temp
                    )

                st.success(
                    "Online audio transcription completed!"
                )

                show_result(result)

            except Exception as e:

                st.error(
                    f"An error occurred: {e}"
                )

            finally:

                if temp and os.path.exists(temp):
                    os.remove(temp)

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


st.markdown(
    """
    <div class="secure">
        🔒 <strong>Secure processing</strong>
        — Files are processed temporarily and are not stored by this app.
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="footer">
        🎙️ <strong>Speech2Text AI</strong><br>
        Powered by Groq Whisper Large v3 Turbo<br>
        Designed & Developed with AI by
        <strong>Aneela Altaf</strong><br>
        © 2026 Speech2Text AI
    </div>
    """,
    unsafe_allow_html=True
)
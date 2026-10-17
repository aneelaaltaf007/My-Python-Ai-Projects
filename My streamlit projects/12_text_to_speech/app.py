# import libraries 
import streamlit as st
from openai import OpenAI
import os
import base64
import io
from pydub import AudioSegment

# PAGE SETTINGS 
st.set_page_config(
    page_title="Aneela's Text-to-Speech Studio",
    page_icon="🔊",
    layout="centered"
)

# CUSTOM STYLING 
st.markdown(
    """
    <style>
    .stApp {
        background-image: linear-gradient(
            135deg,
            rgba(225, 245, 254, 0.95),
            rgba(243, 229, 245, 0.95)
        );
        background-attachment: fixed;
    }

    [data-testid="stSidebar"] {
        background-color: #e8eaf6;
    }

    .app-footer {
        text-align: center;
        padding: 18px;
        font-size: 13px;
        color: #374151;
    }

    .app-footer a {
        color: #4338ca;
        text-decoration: none;
    }

    .app-footer a:hover {
        text-decoration: underline;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# COVER IMAGE
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COVER_PATH = os.path.join(BASE_DIR, "cover.png")

if os.path.isfile(COVER_PATH):
    st.image(COVER_PATH, width="stretch")
else:
    st.warning(
        f"Cover image not found at: {COVER_PATH}"
    )
    st.info(
        "Place cover.png in the same folder as app.py."
    )
# APP TITLE
st.title("🔊 Aneela's Text-to-Speech Studio")

st.markdown(
    """
    Welcome to my AI-powered Text-to-Speech application!

    Convert written text into natural-sounding speech using
    OpenAI's **`tts-1` and `tts-1-hd` models**.

    You can also upload, listen to, and download your own
    voice recordings.
    """
)

st.divider()

# SIDEBAR SETTINGS 
st.sidebar.title("⚙️ Speech Settings")

st.sidebar.markdown(
    "🔐 Enter your OpenAI API key. Keep it private."
)

api_key = st.sidebar.text_input(
    "OpenAI API Key",
    type="password",
    placeholder="Enter your API key"
)

model = st.sidebar.selectbox(
    "Select Model",
    ["tts-1", "tts-1-hd"]
)

voice_options = {
    "Alloy": "alloy",
    "Echo": "echo",
    "Fable": "fable",
    "Onyx": "onyx",
    "Nova": "nova",
    "Shimmer": "shimmer"
}

selected_voice = st.sidebar.selectbox(
    "Select Voice",
    list(voice_options.keys())
)

voice = voice_options[selected_voice]

audio_format = st.sidebar.selectbox(
    "Download Format",
    ["mp3", "opus", "aac", "flac", "wav"]
)

st.sidebar.caption(
    "OpenAI preset voices are used for speech generation. "
    "Uploading a personal recording does not clone your voice."
)

# TEXT INPUT
st.subheader("📝 Enter Your Text")

user_input = st.text_area(
    "Text to convert to speech",
    value="Hello! Welcome to Aneela's Text-to-Speech Studio.",
    height=180,
    max_chars=4000,
    placeholder="Type your text here..."
)

st.caption(f"Characters entered: {len(user_input)} / 4000")

# TEXT-TO-SPEECH FUNCTION
def text_to_speech(api_key, text, model, voice):
    """Generate MP3 speech using the OpenAI API."""
    client = OpenAI(api_key=api_key)

    response = client.audio.speech.create(
        model=model,
        voice=voice,
        input=text,
        response_format="mp3"
    )

    return response.read()


# AUDIO CONVERSION FUNCTION 
def convert_audio_format(audio_bytes, output_format):
    """Convert MP3 audio into the selected downloadable format."""
    audio = AudioSegment.from_file(
        io.BytesIO(audio_bytes),
        format="mp3"
    )

    output = io.BytesIO()

    export_format = {
        "mp3": "mp3",
        "opus": "opus",
        "aac": "adts",
        "flac": "flac",
        "wav": "wav"
    }.get(output_format)

    if export_format is None:
        raise ValueError("Unsupported audio format.")

    audio.export(output, format=export_format)
    return output.getvalue()


# GENERATE SPEECH 
st.divider()

if st.button(
    "🎙️ Convert Text to Speech",
    use_container_width=True
):
    if not api_key.strip():
        st.warning("Please enter your OpenAI API key in the sidebar.")

    elif not user_input.strip():
        st.warning("Please enter some text first.")

    else:
        try:
            with st.spinner("Generating your speech..."):
                mp3_bytes = text_to_speech(
                    api_key.strip(),
                    user_input.strip(),
                    model,
                    voice
                )

                if audio_format == "mp3":
                    download_bytes = mp3_bytes
                else:
                    download_bytes = convert_audio_format(
                        mp3_bytes,
                        audio_format
                    )

            st.session_state["speech_mp3"] = mp3_bytes
            st.session_state["speech_download"] = download_bytes
            st.session_state["speech_format"] = audio_format
            st.session_state["speech_text"] = user_input.strip()
            st.session_state["speech_model"] = model
            st.session_state["speech_voice"] = selected_voice

        except Exception as error:
            st.error(
                "Unable to generate speech. Check your API key, "
                "API access, billing, internet connection, and "
                "audio conversion dependencies."
            )
            st.caption(f"Error details: {error}")


# DISPLAY GENERATED AUDIO 
if "speech_mp3" in st.session_state:
    st.success("Speech generated successfully!")

    st.subheader("🔊 Listen to Generated Speech")

    st.audio(
        st.session_state["speech_mp3"],
        format="audio/mpeg"
    )

    extension = st.session_state["speech_format"]

    mime_types = {
        "mp3": "audio/mpeg",
        "opus": "audio/ogg",
        "aac": "audio/aac",
        "flac": "audio/flac",
        "wav": "audio/wav"
    }

    st.download_button(
        label=f"⬇️ Download {extension.upper()} File",
        data=st.session_state["speech_download"],
        file_name=f"generated_speech.{extension}",
        mime=mime_types[extension],
        use_container_width=True
    )

    with st.expander("📋 View Text and Speech Settings"):
        st.write("**Generated Text:**")
        st.write(st.session_state["speech_text"])
        st.write(f"**Model:** {st.session_state['speech_model']}")
        st.write(f"**Voice:** {st.session_state['speech_voice']}")
        st.write(f"**Format:** {extension.upper()}")


# PERSONAL VOICE RECORDING 
st.divider()

st.subheader("🎧 Upload My Own Voice")

st.write(
    "Upload your own voice recording to listen to it "
    "and download the original audio file."
)

st.info(
    "This feature plays and downloads your uploaded recording. "
    "It does not clone your voice or use the recording to "
    "generate new speech."
)

uploaded_voice = st.file_uploader(
    "Upload your voice recording",
    type=["mp3", "wav", "m4a", "ogg", "flac"],
    help="Upload an audio file you own or have permission to use."
)

if uploaded_voice is not None:
    voice_recording = uploaded_voice.getvalue()

    st.success("Voice recording uploaded successfully!")

    st.subheader("🎵 Listen to Your Voice")

    st.audio(voice_recording)

    st.download_button(
        label="⬇️ Download My Voice Recording",
        data=voice_recording,
        file_name=uploaded_voice.name,
        mime=uploaded_voice.type or "application/octet-stream",
        use_container_width=True,
        key="download_personal_voice"
    )


#  DEVELOPER PROFILE 
st.sidebar.divider()

st.sidebar.title("👩‍💻 About the Developer")

st.sidebar.markdown("**Name:** Aneela Altaf")
st.sidebar.markdown("**Field:** Artificial Intelligence")
st.sidebar.markdown("**Project:** Text-to-Speech Converter")
st.sidebar.markdown("**Technologies:** Python, Streamlit, OpenAI API")

st.sidebar.markdown("### 🔗 Connect With Me")

st.sidebar.markdown(
    "[💼 LinkedIn](https://www.linkedin.com/in/aneelaaltaf007)"
)

st.sidebar.markdown(
    "[💻 GitHub](https://github.com/aneelaaltaf007)"
)

# Replace these placeholders with your actual profiles.
st.sidebar.markdown("[📸 Instagram](https://www.instagram.com/)")
st.sidebar.markdown("[📘 Facebook](https://www.facebook.com/)")
st.sidebar.markdown("[📧 Email](mailto:your-email@example.com)")

st.sidebar.markdown(
    "[📚 OpenAI TTS Documentation]"
    "(https://platform.openai.com/docs/guides/text-to-speech)"
)

# MAIN PAGE FOOTER
st.divider()

st.markdown(
    """
    <div style="text-align: center; padding: 20px;">
        <h3>🔊 Aneela's Text-to-Speech Studio</h3>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    "Turning written words into speech with Artificial Intelligence.",
    text_alignment="center"
)

st.markdown(
    "Built with Python, Streamlit, and OpenAI.",
    text_alignment="center"
)

st.divider()

st.markdown("**Developed by Aneela Altaf**", text_alignment="center")

st.markdown(
    "[LinkedIn](https://www.linkedin.com/in/aneelaaltaf007) "
    "| [GitHub](https://github.com/aneelaaltaf007) ",
    text_alignment="center"
)

st.markdown(
    
    "Learning, building, and innovating with AI.",
    text_alignment="center"
)

st.caption(
    "© 2026 Aneela Altaf. All rights reserved."
)
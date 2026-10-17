
import os
import tempfile

import streamlit as st
import torch
from TTS.api import TTS
from pydub import AudioSegment

st.set_page_config(
    page_title="My Voice AI",
    page_icon="🎙️",
    layout="centered",
)

st.title("🎙️ My Voice AI")
st.subheader("Generate speech using your own voice")

st.write(
    "Upload a recording of your own voice, type your script, "
    "and generate speech that resembles your recording."
)

st.info(
    "Privacy: Use only your own voice or a voice for which you "
    "have explicit permission. This local model processes audio "
    "on your computer after the model has been downloaded."
)

@st.cache_resource
def load_model():
    # CPU mode works without an NVIDIA GPU, but can be slow.
    return TTS(
        model_name="tts_models/multilingual/multi-dataset/xtts_v2",
        gpu=False,
    )

with st.form("voice_form"):
    recording = st.file_uploader(
        "Upload your voice recording",
        type=["wav", "mp3", "m4a", "ogg", "flac"],
    )

    script = st.text_area(
        "Enter the text you want to speak",
        placeholder="Hello! My name is Aneela Altaf...",
        height=180,
        max_chars=1000,
    )

    language = st.selectbox(
        "Speech language",
        ["English", "Spanish", "French", "German", "Arabic"],
    )

    consent = st.checkbox(
        "I confirm that this is my voice or I have explicit "
        "permission to use this voice."
    )

    submitted = st.form_submit_button(
        "Generate My Voice",
        type="primary",
        use_container_width=True,
    )

language_codes = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Arabic": "ar",
}

if submitted:
    if recording is None:
        st.error("Please upload a voice recording.")
    elif not script.strip():
        st.error("Please enter the text to generate.")
    elif not consent:
        st.error("Please confirm voice permission.")
    else:
        input_path = None
        output_path = None

        try:
            with tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            ) as temp_input:
                input_path = temp_input.name

            with tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            ) as temp_output:
                output_path = temp_output.name

            # Convert the uploaded audio to a standard WAV file.
            audio = AudioSegment.from_file(
                recording,
                format=recording.name.rsplit(".", 1)[-1].lower(),
            )
            audio = audio.set_channels(1).set_frame_rate(22050)
            audio.export(input_path, format="wav")

            if len(audio) < 3000:
                st.error(
                    "Please upload at least 3 seconds of clear speech."
                )
            else:
                with st.spinner(
                    "Loading the voice model and generating speech. "
                    "The first run may take several minutes..."
                ):
                    model = load_model()
                    model.tts_to_file(
                        text=script.strip(),
                        speaker_wav=input_path,
                        language=language_codes[language],
                        file_path=output_path,
                        split_sentences=True,
                    )

                st.success("Speech generated successfully!")
                st.audio(output_path, format="audio/wav")

                with open(output_path, "rb") as audio_file:
                    st.download_button(
                        "Download Generated Speech",
                        data=audio_file.read(),
                        file_name="my_generated_voice.wav",
                        mime="audio/wav",
                        use_container_width=True,
                    )

        except Exception as error:
            st.error("Speech generation failed.")
            st.code(str(error))
            st.info(
                "Check the installation, model download, audio format, "
                "and selected language. If needed, send me the full error."
            )

        finally:
            for path in (input_path, output_path):
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass

st.divider()
st.caption("Personal voice-cloning experiment • Use responsibly")

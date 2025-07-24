import os
import streamlit as st
import whisper
import torch
from pydub import AudioSegment
from transformers import BartForConditionalGeneration, BartTokenizer
import tempfile


# Convert uploaded file to WAV
def convert_to_wav(uploaded_file):
    temp_dir = tempfile.mkdtemp()

    # Save uploaded file
    input_path = os.path.join(temp_dir, uploaded_file.name)
    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Convert to WAV
    audio = AudioSegment.from_file(input_path)
    wav_path = os.path.join(temp_dir, "audio.wav")
    audio.export(wav_path, format="wav")

    return wav_path


# Transcribe using Whisper
def transcribe_with_whisper(audio_path, model_size="tiny"):
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path)
    return result["text"]


# Summarize using BART
@st.cache_resource
def load_bart_model(model_path="facebook/bart-large-cnn"):
    model = BartForConditionalGeneration.from_pretrained(model_path)
    tokenizer = BartTokenizer.from_pretrained(model_path)
    return model, tokenizer


bart_model, bart_tokenizer = load_bart_model()


def summarize_text(text):
    inputs = bart_tokenizer.batch_encode_plus([text], return_tensors='pt', max_length=1024, truncation=True)
    summary_ids = bart_model.generate(inputs['input_ids'], max_length=150, min_length=30, length_penalty=5.,
                                      num_beams=2)
    return bart_tokenizer.decode(summary_ids[0], skip_special_tokens=True)


# Streamlit App
st.title("🎥 Audio Summarizer (Urdu/Hindi Supported)")

st.markdown("### Upload Audio File")
uploaded_file = st.file_uploader("Choose an audio file", type=['mp3', 'wav', 'mp4', 'm4a', 'webm'])

model_size = "tiny"
st.markdown("🧠 Using Whisper Model: `tiny`")

if st.button("Generate Summary"):
    if uploaded_file:
        with st.spinner("Processing..."):
            try:
                # Convert to WAV
                audio_path = convert_to_wav(uploaded_file)

                # Transcribe
                transcript = transcribe_with_whisper(audio_path, model_size)

                # Summarize
                summary = summarize_text(transcript)

                st.subheader("📝 Summary")
                st.success(summary)

                with st.expander("📃 Show Transcript"):
                    st.download_button("📥 Download Transcript", transcript, file_name="transcript.txt")
                    st.text_area("Transcript (Preview)", transcript[:500] + "...", height=150)

            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        st.warning("Please upload an audio file.")
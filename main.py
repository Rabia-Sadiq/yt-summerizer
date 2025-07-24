import os
import json
import wave
import streamlit as st
from pytube import YouTube
import whisper
import torch
from pydub import AudioSegment
from transformers import BartForConditionalGeneration, BartTokenizer
import tempfile


# Step 1: Download audio from YouTube using pytube
def download_audio(url):
    try:
        # Create temp directory
        temp_dir = tempfile.mkdtemp()

        # Download using pytube
        yt = YouTube(url)

        # Get audio stream
        audio_stream = yt.streams.filter(only_audio=True).first()

        if not audio_stream:
            raise Exception("No audio stream found")

        # Download to temp directory
        output_path = audio_stream.download(output_path=temp_dir, filename="audio.mp4")

        # Convert to WAV
        audio = AudioSegment.from_file(output_path)
        wav_path = os.path.join(temp_dir, "audio.wav")
        audio.export(wav_path, format="wav")

        return wav_path

    except Exception as e:
        st.error(f"Download failed: {str(e)}")
        return None


# Step 2: Convert to WAV (backup function)
def convert_to_wav(input_path, output_path=None):
    if output_path is None:
        output_path = input_path.replace('.mp4', '.wav').replace('.webm', '.wav')

    audio = AudioSegment.from_file(input_path)
    audio.export(output_path, format="wav")
    return output_path


# Step 3: Transcribe using Whisper (multi-language)
def transcribe_with_whisper(audio_path, model_size="tiny"):
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path)
    return result["text"]


# Step 4: Summarize in English using BART
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


# Main processing pipeline
def summarize_youtube_video(url, model_size="tiny"):
    audio_path = download_audio(url)
    if not audio_path:
        return None, None

    transcript = transcribe_with_whisper(audio_path, model_size)
    summary = summarize_text(transcript)
    return transcript, summary


# Streamlit App
st.title("🎥 YouTube Video Summarizer (Urdu/Hindi Supported)")

video_url = st.text_input("🔗 Enter YouTube Video URL:")

model_size = "tiny"  # Fixed for deployment
st.markdown("🧠 Using Whisper Model: `tiny`")

if st.button("Generate Summary"):
    if video_url:
        with st.spinner("Processing..."):
            try:
                transcript, summary = summarize_youtube_video(video_url, model_size)

                if transcript and summary:
                    st.subheader("📝 Summary")
                    st.success(summary)

                    with st.expander("📃 Show Transcript"):
                        st.download_button("📥 Download Transcript", transcript, file_name="transcript.txt")
                        st.text_area("Transcript (Preview)", transcript[:500] + "...", height=150)
                else:
                    st.error("Failed to process video. Please check the URL and try again.")

            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        st.warning("Please enter a valid YouTube URL.")
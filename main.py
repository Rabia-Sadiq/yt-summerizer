import os
import json
import wave
import streamlit as st
import youtube_dl as yt_dlp
import whisper
import torch
from pydub import AudioSegment
from transformers import BartForConditionalGeneration, BartTokenizer

# Step 1: Download audio from YouTube
def download_audio(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'audio.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return "audio.wav"

# Step 2: Convert to WAV (in case needed)
def convert_to_wav(input_path="audio.wav", output_path="audio.wav"):
    audio = AudioSegment.from_file(input_path)
    audio.export(output_path, format="wav")
    return output_path

# Step 3: Transcribe using Whisper (multi-language)
def transcribe_with_whisper(audio_path="audio.wav", model_size="base"):
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
    summary_ids = bart_model.generate(inputs['input_ids'], max_length=150, min_length=30, length_penalty=5., num_beams=2)
    return bart_tokenizer.decode(summary_ids[0], skip_special_tokens=True)
# Main processing pipeline
def summarize_youtube_video(url, model_size="base"):
    audio_path = download_audio(url)
    wav_path = convert_to_wav(audio_path)
    transcript = transcribe_with_whisper(wav_path, model_size)
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

                st.subheader("📝 Summary")
                st.success(summary)

                with st.expander("📃 Show Transcript"):
                    st.download_button("📥 Download Transcript", transcript, file_name="transcript.txt")
                    st.text_area("Transcript (Preview)", transcript[:500] + "...", height=150)

            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        st.warning("Please enter a valid YouTube URL.")

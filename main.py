import streamlit as st
import tempfile
import os


# Simple text summarizer using basic NLP
def simple_summarize(text, max_sentences=3):
    """Simple extractive summarization"""
    if not text.strip():
        return "No content to summarize."

    sentences = text.split('.')
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    if len(sentences) <= max_sentences:
        return text

    # Return first few sentences as summary
    summary_sentences = sentences[:max_sentences]
    return '. '.join(summary_sentences) + '.'


# Streamlit App
st.title("🎵 Audio File Processor")
st.markdown(
    "**Note:** This is a simplified version. Upload your audio file and manually enter transcript for summarization.")

# File upload
uploaded_file = st.file_uploader("Choose an audio file", type=['mp3', 'wav', 'mp4', 'm4a'])

if uploaded_file:
    st.success(f"✅ File uploaded: {uploaded_file.name}")

    # Audio player
    st.audio(uploaded_file)

    st.markdown("---")

    # Manual transcript input (since whisper isn't working)
    st.subheader("📝 Enter Transcript")
    transcript = st.text_area(
        "Paste or type the transcript of your audio:",
        height=200,
        placeholder="Enter the transcript here..."
    )

    if st.button("Generate Summary"):
        if transcript.strip():
            with st.spinner("Generating summary..."):
                try:
                    # Simple summarization
                    summary = simple_summarize(transcript, max_sentences=3)

                    st.subheader("📝 Summary")
                    st.success(summary)

                    with st.expander("📃 Full Transcript"):
                        st.download_button("📥 Download Transcript", transcript, file_name="transcript.txt")
                        st.text_area("Full Transcript", transcript, height=150)

                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter a transcript to summarize.")

st.markdown("---")
st.markdown("**Instructions:**")
st.markdown("1. Upload your audio file")
st.markdown("2. Listen to it using the audio player")
st.markdown("3. Enter the transcript manually")
st.markdown("4. Click 'Generate Summary' to get a summary")
import streamlit as st
import tempfile
import os
import re
from collections import Counter
import time


# Enhanced summarization functions
def extract_keywords(text, top_n=10):
    """Extract most frequent meaningful words"""
    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are',
                  'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                  'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
                  'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}

    words = re.findall(r'\b\w+\b', text.lower())
    words = [word for word in words if len(word) > 3 and word not in stop_words]

    word_freq = Counter(words)
    return word_freq.most_common(top_n)


def intelligent_summarize(text, max_sentences=5):
    """Advanced extractive summarization"""
    if not text.strip():
        return "No content to summarize."

    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    if len(sentences) <= max_sentences:
        return text

    # Get keyword frequencies
    keywords = extract_keywords(text, 20)
    keyword_dict = dict(keywords)

    # Score sentences
    sentence_scores = []
    for i, sentence in enumerate(sentences):
        sentence_words = re.findall(r'\b\w+\b', sentence.lower())

        # Calculate score based on:
        # 1. Keyword frequency
        # 2. Sentence position (earlier sentences get bonus)
        # 3. Sentence length (not too short, not too long)

        keyword_score = sum(keyword_dict.get(word, 0) for word in sentence_words)
        position_score = max(0, len(sentences) - i) / len(sentences) * 0.3
        length_score = min(1.0, len(sentence_words) / 20) * 0.2

        total_score = keyword_score + position_score + length_score
        sentence_scores.append((total_score, i, sentence))

    # Get top sentences
    sentence_scores.sort(reverse=True)
    top_sentences = sentence_scores[:max_sentences]

    # Sort by original order
    top_sentences.sort(key=lambda x: x[1])

    summary = '. '.join([sent[2] for sent in top_sentences]) + '.'
    return summary


def extract_key_points(text, num_points=5):
    """Extract key points using various indicators"""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 15]

    # Key indicators for important sentences
    importance_indicators = [
        'important', 'key', 'main', 'significant', 'crucial', 'essential',
        'remember', 'note that', 'keep in mind', 'conclusion', 'summary',
        'first', 'second', 'third', 'finally', 'in conclusion', 'therefore'
    ]

    # Score sentences for importance
    scored_sentences = []
    for sentence in sentences:
        score = 0
        sentence_lower = sentence.lower()

        # Check for importance indicators
        for indicator in importance_indicators:
            if indicator in sentence_lower:
                score += 2

        # Check for numbers/lists
        if re.search(r'\b(?:one|two|three|four|five|\d+)\b', sentence_lower):
            score += 1

        # Prefer sentences with questions
        if '?' in sentence:
            score += 1

        scored_sentences.append((score, sentence))

    # Sort by score and take top sentences
    scored_sentences.sort(reverse=True)
    key_points = [f"• {sent[1]}" for sent in scored_sentences[:num_points]]

    return key_points if key_points else [f"• {s}" for s in sentences[:3]]


def analyze_content_type(text):
    """Analyze what type of content this might be"""
    text_lower = text.lower()

    if any(word in text_lower for word in ['tutorial', 'how to', 'step', 'guide', 'learn']):
        return "📚 Tutorial/Educational"
    elif any(word in text_lower for word in ['news', 'breaking', 'report', 'today', 'announced']):
        return "📰 News/Current Events"
    elif any(word in text_lower for word in ['review', 'opinion', 'think', 'believe', 'recommend']):
        return "🎯 Review/Opinion"
    elif any(word in text_lower for word in ['story', 'happened', 'experience', 'remember']):
        return "📖 Story/Personal"
    else:
        return "🎥 General Content"


# Streamlit App
st.set_page_config(page_title="YouTube Video Summarizer", page_icon="🎬", layout="wide")

st.title("🎬 YouTube Video Summarizer")
st.markdown("**Professional AI-powered video summarization with intelligent analysis**")

# Instructions
with st.expander("📖 How to Use This Tool"):
    st.markdown("""
    ### Step-by-Step Guide:

    1. **Download Audio from YouTube:**
       - Go to your YouTube video
       - Use online tools like [y2mate.com](https://y2mate.com) or [savefrom.net](https://savefrom.net) 
       - Download as MP3 or MP4

    2. **Upload & Transcribe:**
       - Upload your downloaded file here
       - Listen and manually transcribe (or use external transcription tools)

    3. **Get AI Summary:**
       - Choose your summary preferences
       - Get intelligent analysis with key points

    **💡 Pro Tips:**
    - For better summaries, ensure accurate transcription
    - Try different summary lengths for different needs
    - Use key points for quick reference
    """)

# Main interface
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📁 Upload Audio/Video File")
    uploaded_file = st.file_uploader(
        "Choose your file",
        type=['mp3', 'wav', 'mp4', 'm4a', 'webm', 'ogg'],
        help="Upload audio/video file downloaded from YouTube"
    )

with col2:
    st.subheader("⚙️ Summary Settings")
    summary_type = st.selectbox(
        "Summary Length:",
        ["Quick (2-3 sentences)", "Standard (4-5 sentences)", "Detailed (6-8 sentences)",
         "Comprehensive (8+ sentences)"]
    )

    include_keywords = st.checkbox("🔑 Show Keywords", value=True)
    include_keypoints = st.checkbox("📌 Show Key Points", value=True)
    show_analysis = st.checkbox("📊 Content Analysis", value=True)

if uploaded_file:
    st.success(f"✅ File uploaded: **{uploaded_file.name}**")

    # Audio player
    st.audio(uploaded_file, format='audio/mp3')

    st.markdown("---")

    # Transcript input
    st.subheader("📝 Video Transcript")
    transcript = st.text_area(
        "Enter the transcript of your video:",
        height=250,
        placeholder="Paste or type the complete transcript here...\n\nTip: Use YouTube's auto-captions or transcription tools for accuracy.",
        help="For best results, ensure the transcript is complete and accurate"
    )

    # Process button
    if st.button("🚀 Generate Intelligent Summary", type="primary"):
        if transcript.strip():
            with st.spinner("🧠 Analyzing content and generating summary..."):
                # Add progress bar for user experience
                progress_bar = st.progress(0)
                progress_bar.progress(25)

                try:
                    # Determine sentence count
                    sentence_counts = {
                        "Quick (2-3 sentences)": 3,
                        "Standard (4-5 sentences)": 5,
                        "Detailed (6-8 sentences)": 8,
                        "Comprehensive (8+ sentences)": 12
                    }
                    max_sentences = sentence_counts[summary_type]

                    progress_bar.progress(50)

                    # Generate summary
                    summary = intelligent_summarize(transcript, max_sentences)

                    progress_bar.progress(75)

                    # Extract additional insights
                    if include_keywords:
                        keywords = extract_keywords(transcript, 8)

                    if include_keypoints:
                        key_points = extract_key_points(transcript)

                    if show_analysis:
                        content_type = analyze_content_type(transcript)

                    progress_bar.progress(100)
                    time.sleep(0.5)  # Brief pause for UX
                    progress_bar.empty()

                    # Display results
                    st.markdown("## 📋 Summary Results")

                    # Main summary
                    st.subheader("📝 Intelligent Summary")
                    st.success(summary)

                    # Create columns for additional info
                    col1, col2 = st.columns(2)

                    with col1:
                        if include_keypoints:
                            st.subheader("🔑 Key Points")
                            for point in key_points:
                                st.markdown(point)

                    with col2:
                        if include_keywords:
                            st.subheader("🏷️ Top Keywords")
                            keyword_text = ", ".join([f"**{word}** ({count})" for word, count in keywords])
                            st.markdown(keyword_text)

                        if show_analysis:
                            st.subheader("📊 Content Analysis")
                            st.info(f"**Type:** {content_type}")

                    # Statistics
                    st.subheader("📈 Summary Statistics")
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Original Words", len(transcript.split()))
                    with col2:
                        st.metric("Summary Words", len(summary.split()))
                    with col3:
                        compression_ratio = round((len(summary.split()) / len(transcript.split())) * 100, 1)
                        st.metric("Compression Ratio", f"{compression_ratio}%")
                    with col4:
                        reading_time = max(1, len(summary.split()) // 200)
                        st.metric("Reading Time", f"{reading_time} min")

                    # Download options
                    st.subheader("💾 Download Options")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.download_button(
                            "📥 Download Summary",
                            summary,
                            file_name=f"summary_{uploaded_file.name}.txt",
                            mime="text/plain"
                        )

                    with col2:
                        full_report = f"""VIDEO SUMMARY REPORT
====================================

File: {uploaded_file.name}
Summary Type: {summary_type}
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY:
{summary}

KEY POINTS:
{chr(10).join(key_points) if include_keypoints else 'Not generated'}

KEYWORDS:
{', '.join([word for word, count in keywords]) if include_keywords else 'Not generated'}

ORIGINAL TRANSCRIPT:
{transcript}
"""
                        st.download_button(
                            "📄 Download Full Report",
                            full_report,
                            file_name=f"full_report_{uploaded_file.name}.txt",
                            mime="text/plain"
                        )

                    with col3:
                        st.download_button(
                            "📜 Download Transcript",
                            transcript,
                            file_name=f"transcript_{uploaded_file.name}.txt",
                            mime="text/plain"
                        )

                    # Full transcript viewer
                    with st.expander("📖 View Full Transcript"):
                        st.text_area("Complete Transcript", transcript, height=200, disabled=True)

                except Exception as e:
                    st.error(f"❌ Error processing content: {str(e)}")
                    st.info("💡 Try checking your transcript for formatting issues or contact support.")
        else:
            st.warning("⚠️ Please enter a transcript to generate summary.")

# Footer
st.markdown("---")
st.markdown("**🔧 Built with Streamlit** | *Intelligent summarization for YouTube content*")

# Sidebar with tips
with st.sidebar:
    st.markdown("### 💡 Pro Tips")
    st.markdown("""
    - **Accuracy matters**: Better transcripts = better summaries
    - **Try different lengths**: Quick for overviews, detailed for analysis  
    - **Use keywords**: Great for SEO and content planning
    - **Save your work**: Download reports for future reference
    """)

    st.markdown("### 🛠️ External Tools")
    st.markdown("""
    **YouTube Downloaders:**
    - [y2mate.com](https://y2mate.com)
    - [savefrom.net](https://savefrom.net)
    - [keepvid.com](https://keepvid.com)

    **Transcription Tools:**
    - [otter.ai](https://otter.ai)
    - [rev.com](https://rev.com)
    - YouTube auto-captions
    """)
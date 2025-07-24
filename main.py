import streamlit as st
import requests
import re
from collections import Counter


def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([^&\n?#]+)',
        r'(?:https?://)?(?:www\.)?youtu\.be/([^&\n?#]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([^&\n?#]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_video_info(video_id):
    """Get basic video information"""
    try:
        # Try to get video page
        url = f"https://www.youtube.com/watch?v={video_id}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            # Extract title from HTML
            title_match = re.search(r'"title":"([^"]+)"', response.text)
            title = title_match.group(1) if title_match else "Unknown Title"

            # Extract duration if possible
            duration_match = re.search(r'"lengthSeconds":"(\d+)"', response.text)
            duration = int(duration_match.group(1)) if duration_match else 0

            return {
                'title': title.replace('\\u0026', '&'),
                'duration': duration,
                'url': url
            }
    except Exception as e:
        st.error(f"Error getting video info: {str(e)}")

    return None


def get_youtube_transcript_manual(video_id):
    """Attempt to get transcript data (simplified approach)"""
    try:
        # This is a placeholder for transcript extraction
        # In reality, you'd need to implement YouTube's transcript API
        # or use a service that provides this functionality

        st.info("💡 **Auto-transcript extraction is not available in this version.**")
        st.markdown("""
        **To get the transcript:**
        1. Go to your YouTube video
        2. Click on the three dots (⋯) below the video
        3. Click "Open transcript"
        4. Copy the transcript text
        5. Paste it in the text area below
        """)

        return None

    except Exception as e:
        st.error(f"Transcript extraction failed: {str(e)}")
        return None


def intelligent_summarize(text, max_sentences=5):
    """Advanced text summarization"""
    if not text.strip():
        return "No content to summarize."

    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    if len(sentences) <= max_sentences:
        return text

    # Get word frequencies
    words = re.findall(r'\b\w+\b', text.lower())
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are',
                  'was', 'were'}
    words = [word for word in words if len(word) > 3 and word not in stop_words]
    word_freq = Counter(words).most_common(20)
    keyword_dict = dict(word_freq)

    # Score sentences
    sentence_scores = []
    for i, sentence in enumerate(sentences):
        sentence_words = re.findall(r'\b\w+\b', sentence.lower())
        keyword_score = sum(keyword_dict.get(word, 0) for word in sentence_words)
        position_score = max(0, len(sentences) - i) / len(sentences) * 0.3
        total_score = keyword_score + position_score
        sentence_scores.append((total_score, i, sentence))

    # Get top sentences
    sentence_scores.sort(reverse=True)
    top_sentences = sentence_scores[:max_sentences]
    top_sentences.sort(key=lambda x: x[1])

    return '. '.join([sent[2] for sent in top_sentences]) + '.'


# Main App
st.set_page_config(page_title="YouTube Video Summarizer", page_icon="🎬")

st.title("🎬 YouTube Video Summarizer")
st.markdown("**Enter a YouTube URL and get an intelligent summary**")

# URL Input
youtube_url = st.text_input(
    "🔗 Enter YouTube Video URL:",
    placeholder="https://www.youtube.com/watch?v=...",
    help="Paste any YouTube video URL here"
)

if youtube_url:
    # Extract video ID
    video_id = extract_video_id(youtube_url)

    if video_id:
        st.success(f"✅ Valid YouTube URL detected! Video ID: `{video_id}`")

        # Get video information
        with st.spinner("🔍 Getting video information..."):
            video_info = get_video_info(video_id)

        if video_info:
            # Display video info
            st.subheader("📹 Video Information")
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**Title:** {video_info['title']}")
                st.markdown(f"**URL:** [Watch on YouTube]({video_info['url']})")

            with col2:
                if video_info['duration'] > 0:
                    minutes = video_info['duration'] // 60
                    seconds = video_info['duration'] % 60
                    st.metric("Duration", f"{minutes}:{seconds:02d}")

            # Transcript section
            st.markdown("---")
            st.subheader("📝 Video Transcript")

            # Try automatic transcript (will show manual instructions)
            transcript_data = get_youtube_transcript_manual(video_id)

            # Manual transcript input
            transcript = st.text_area(
                "Enter the video transcript:",
                height=300,
                placeholder="Paste the transcript here...\n\nYou can get this from YouTube by clicking the three dots below the video and selecting 'Open transcript'",
                help="For best results, include the complete transcript"
            )

            # Summary options
            col1, col2 = st.columns(2)
            with col1:
                summary_length = st.selectbox(
                    "Summary Length:",
                    ["Quick (2-3 sentences)", "Standard (4-5 sentences)", "Detailed (6-8 sentences)"]
                )

            with col2:
                include_keywords = st.checkbox("Show Keywords", value=True)

            # Generate summary
            if st.button("🚀 Generate Summary", type="primary"):
                if transcript.strip():
                    with st.spinner("🧠 Analyzing and summarizing..."):
                        # Determine sentence count
                        sentence_counts = {
                            "Quick (2-3 sentences)": 3,
                            "Standard (4-5 sentences)": 5,
                            "Detailed (6-8 sentences)": 8
                        }
                        max_sentences = sentence_counts[summary_length]

                        # Generate summary
                        summary = intelligent_summarize(transcript, max_sentences)

                        # Display results
                        st.markdown("## 📋 Summary Results")

                        st.subheader("📝 Video Summary")
                        st.success(summary)

                        if include_keywords:
                            # Extract keywords
                            words = re.findall(r'\b\w+\b', transcript.lower())
                            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
                                          'with', 'by', 'is', 'are', 'was', 'were', 'have', 'has', 'had', 'this',
                                          'that', 'you', 'i', 'it', 'they', 'we'}
                            words = [word for word in words if len(word) > 3 and word not in stop_words]
                            keywords = Counter(words).most_common(8)

                            st.subheader("🔑 Top Keywords")
                            keyword_text = ", ".join([f"**{word}** ({count})" for word, count in keywords])
                            st.markdown(keyword_text)

                        # Statistics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Original Words", len(transcript.split()))
                        with col2:
                            st.metric("Summary Words", len(summary.split()))
                        with col3:
                            compression = round((len(summary.split()) / len(transcript.split())) * 100, 1)
                            st.metric("Compression", f"{compression}%")

                        # Download options
                        st.subheader("💾 Download")
                        col1, col2 = st.columns(2)

                        with col1:
                            st.download_button(
                                "📥 Download Summary",
                                summary,
                                file_name=f"summary_{video_id}.txt"
                            )

                        with col2:
                            full_report = f"""YouTube Video Summary
======================

Video: {video_info['title']}
URL: {video_info['url']}
Video ID: {video_id}

SUMMARY:
{summary}

KEYWORDS:
{', '.join([word for word, count in keywords]) if include_keywords else 'Not generated'}

ORIGINAL TRANSCRIPT:
{transcript}
"""
                            st.download_button(
                                "📄 Download Full Report",
                                full_report,
                                file_name=f"report_{video_id}.txt"
                            )
                else:
                    st.warning("⚠️ Please enter the video transcript to generate a summary.")
        else:
            st.error("❌ Could not retrieve video information. Please check the URL.")
    else:
        st.error("❌ Invalid YouTube URL. Please enter a valid YouTube video URL.")

# Instructions
with st.expander("📖 How to Use"):
    st.markdown("""
    ### Step-by-Step Guide:

    1. **Paste YouTube URL** - Any valid YouTube video URL
    2. **Get video info** - App will show title and details
    3. **Get transcript**:
       - Go to YouTube video
       - Click three dots (⋯) below video  
       - Select "Open transcript"
       - Copy and paste here
    4. **Generate summary** - Choose length and get AI summary

    ### Tips:
    - Complete transcripts give better summaries
    - Try different summary lengths for different needs
    - Keywords help identify main topics
    """)

# Footer
st.markdown("---")
st.markdown("*🤖 Powered by intelligent text analysis algorithms*")
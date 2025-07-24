import streamlit as st
import requests
import re
import json
from collections import Counter
import time


def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([^&\n?#]+)',
        r'(?:https?://)?(?:www\.)?youtu\.be/([^&\n?#]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([^&\n?#]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/v/([^&\n?#]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_youtube_video_info(video_id):
    """Get comprehensive video information from YouTube"""
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            html_content = response.text

            # Extract video information using regex
            info = {}

            # Title
            title_patterns = [
                r'"title":"([^"]+)"',
                r'<title>([^<]+)</title>',
                r'"videoDetails":{"videoId":"[^"]+","title":"([^"]+)"'
            ]

            for pattern in title_patterns:
                match = re.search(pattern, html_content)
                if match:
                    info['title'] = match.group(1).replace('\\u0026', '&').replace('\\', '').strip()
                    break

            # Duration
            duration_match = re.search(r'"lengthSeconds":"(\d+)"', html_content)
            if duration_match:
                duration_seconds = int(duration_match.group(1))
                minutes = duration_seconds // 60
                seconds = duration_seconds % 60
                info['duration'] = f"{minutes}:{seconds:02d}"
                info['duration_seconds'] = duration_seconds

            # Channel name
            channel_patterns = [
                r'"author":"([^"]+)"',
                r'"ownerChannelName":"([^"]+)"',
                r'"channelName":"([^"]+)"'
            ]

            for pattern in channel_patterns:
                match = re.search(pattern, html_content)
                if match:
                    info['channel'] = match.group(1).replace('\\', '').strip()
                    break

            # View count
            views_match = re.search(r'"viewCount":"(\d+)"', html_content)
            if views_match:
                views = int(views_match.group(1))
                if views >= 1000000:
                    info['views'] = f"{views / 1000000:.1f}M views"
                elif views >= 1000:
                    info['views'] = f"{views / 1000:.1f}K views"
                else:
                    info['views'] = f"{views} views"

            # Description (first part)
            desc_match = re.search(r'"shortDescription":"([^"]+)"', html_content)
            if desc_match:
                description = desc_match.group(1).replace('\\n', '\n').replace('\\', '')[:300]
                info['description'] = description + "..." if len(description) == 300 else description

            info['url'] = url
            info['video_id'] = video_id

            return info

    except Exception as e:
        st.error(f"Error fetching video info: {str(e)}")

    return None


def try_extract_captions(video_id):
    """Attempt to extract available caption information"""
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            # Look for caption indicators in the HTML
            html_content = response.text

            # Check if captions are available
            caption_indicators = [
                '"captions"',
                '"captionTracks"',
                'caption',
                'subtitle'
            ]

            captions_available = any(indicator in html_content.lower() for indicator in caption_indicators)

            if captions_available:
                return {
                    'available': True,
                    'message': "Captions appear to be available for this video"
                }
            else:
                return {
                    'available': False,
                    'message': "No captions detected for this video"
                }

    except Exception as e:
        return {
            'available': False,
            'message': f"Could not check captions: {str(e)}"
        }


def intelligent_summarize(text, max_sentences=5):
    """Advanced extractive summarization"""
    if not text.strip():
        return "No content to summarize."

    # Clean and split text
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 15]

    if len(sentences) <= max_sentences:
        return text

    # Extract keywords
    words = re.findall(r'\b\w+\b', text.lower())
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are',
                  'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                  'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
                  'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'what', 'when', 'where', 'why', 'how', 'who',
                  'which', 'so', 'now', 'then', 'here', 'there'}

    meaningful_words = [word for word in words if len(word) > 3 and word not in stop_words]
    word_freq = Counter(meaningful_words).most_common(15)
    keyword_scores = dict(word_freq)

    # Score sentences
    sentence_scores = []
    for i, sentence in enumerate(sentences):
        sentence_words = re.findall(r'\b\w+\b', sentence.lower())

        # Keyword score
        keyword_score = sum(keyword_scores.get(word, 0) for word in sentence_words)

        # Position score (earlier sentences get bonus)
        position_score = (len(sentences) - i) / len(sentences) * 2

        # Length score (prefer medium-length sentences)
        length_score = min(1.0, len(sentence_words) / 15) if len(sentence_words) > 5 else 0.5

        total_score = keyword_score + position_score + length_score
        sentence_scores.append((total_score, i, sentence))

    # Get top sentences
    sentence_scores.sort(reverse=True)
    top_sentences = sentence_scores[:max_sentences]

    # Sort by original order
    top_sentences.sort(key=lambda x: x[1])

    summary = '. '.join([sent[2].strip() for sent in top_sentences]) + '.'
    return summary


def extract_key_points(text, num_points=5):
    """Extract key points from text"""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    # Look for sentences with importance indicators
    importance_words = ['important', 'key', 'main', 'significant', 'remember', 'note', 'first', 'second', 'third',
                        'finally', 'conclusion', 'summary']

    scored_sentences = []
    for sentence in sentences:
        score = 0
        sentence_lower = sentence.lower()

        # Check for importance indicators
        for word in importance_words:
            if word in sentence_lower:
                score += 2

        # Check for numbers/enumeration
        if re.search(r'\b(?:one|two|three|four|five|\d+)\b', sentence_lower):
            score += 1

        # Prefer questions
        if '?' in sentence:
            score += 1

        # Avoid very short sentences
        if len(sentence.split()) < 5:
            score -= 1

        scored_sentences.append((score, sentence))

    # Sort and take top sentences
    scored_sentences.sort(reverse=True)
    key_points = [f"• {sent[1]}" for sent in scored_sentences[:num_points]]

    return key_points[:num_points] if key_points else [f"• {s}" for s in sentences[:3]]


# Streamlit App Configuration
st.set_page_config(
    page_title="YouTube Video Summarizer",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main App
st.title("🎬 YouTube Video Summarizer")
st.markdown("**Paste any YouTube URL and get an intelligent summary with transcription guidance**")

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Settings")

    summary_length = st.selectbox(
        "Summary Length:",
        ["Quick (2-3 sentences)", "Standard (4-5 sentences)", "Detailed (6-8 sentences)",
         "Comprehensive (10+ sentences)"]
    )

    show_keywords = st.checkbox("🔑 Show Keywords", value=True)
    show_keypoints = st.checkbox("📌 Show Key Points", value=True)
    show_video_info = st.checkbox("📹 Show Video Details", value=True)

    st.markdown("---")
    st.markdown("### 💡 Tips")
    st.markdown("""
    - Use complete YouTube URLs
    - For best results, use videos with captions
    - Copy transcript from YouTube's transcript feature
    - Try different summary lengths
    """)

# Main Interface
youtube_url = st.text_input(
    "🔗 Enter YouTube Video URL:",
    placeholder="https://www.youtube.com/watch?v=...",
    help="Paste any YouTube video URL here"
)

if youtube_url:
    video_id = extract_video_id(youtube_url)

    if video_id:
        st.success(f"✅ Valid YouTube URL detected! Video ID: `{video_id}`")

        # Get video information
        with st.spinner("🔍 Fetching video information..."):
            video_info = get_youtube_video_info(video_id)
            caption_info = try_extract_captions(video_id)

        if video_info:
            # Display video information
            if show_video_info:
                st.markdown("---")
                st.subheader("📹 Video Information")

                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**🎥 Title:** {video_info.get('title', 'Unknown')}")
                    if 'channel' in video_info:
                        st.markdown(f"**👤 Channel:** {video_info['channel']}")
                    if 'description' in video_info:
                        with st.expander("📄 Description"):
                            st.write(video_info['description'])

                with col2:
                    if 'duration' in video_info:
                        st.metric("⏱️ Duration", video_info['duration'])
                    if 'views' in video_info:
                        st.metric("👁️ Views", video_info['views'])

                # Caption availability
                if caption_info:
                    if caption_info['available']:
                        st.success(f"✅ {caption_info['message']}")
                    else:
                        st.info(f"ℹ️ {caption_info['message']}")

            # Transcript Section
            st.markdown("---")
            st.subheader("📝 Video Transcript")

            # Instructions for getting transcript
            with st.expander("📖 How to Get YouTube Transcript"):
                st.markdown("""
                ### Step-by-Step Instructions:

                1. **Go to your YouTube video** (link opens in new tab)
                2. **Look below the video** for three dots menu (⋯)
                3. **Click "Show transcript"** or "Open transcript"
                4. **Copy all the transcript text**
                5. **Paste it in the text area below**

                **Alternative method:**
                - Right-click on video → "Show transcript"
                - Or use keyboard shortcut while video is playing

                **Note:** Some videos may not have transcripts available.
                """)

                st.markdown(f"**🔗 [Open Video in New Tab]({video_info['url']})**")

            # Transcript input
            transcript = st.text_area(
                "Enter the video transcript:",
                height=300,
                placeholder="Paste the complete transcript here...\n\nMake sure to include all the text from YouTube's transcript feature for best results.",
                help="The quality of the summary depends on the completeness and accuracy of the transcript"
            )

            # Generate Summary Button
            if st.button("🚀 Generate Intelligent Summary", type="primary", use_container_width=True):
                if transcript.strip():
                    # Determine sentence count
                    sentence_counts = {
                        "Quick (2-3 sentences)": 3,
                        "Standard (4-5 sentences)": 5,
                        "Detailed (6-8 sentences)": 8,
                        "Comprehensive (10+ sentences)": 12
                    }
                    max_sentences = sentence_counts[summary_length]

                    with st.spinner("🧠 Analyzing content and generating summary..."):
                        # Progress simulation for better UX
                        progress_bar = st.progress(0)

                        progress_bar.progress(25)
                        time.sleep(0.5)

                        # Generate summary
                        summary = intelligent_summarize(transcript, max_sentences)
                        progress_bar.progress(70)

                        # Extract additional information
                        if show_keywords:
                            words = re.findall(r'\b\w+\b', transcript.lower())
                            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
                                          'with', 'by', 'is', 'are', 'was', 'were', 'have', 'has', 'had', 'this',
                                          'that', 'you', 'i', 'it', 'they', 'we', 'what', 'when', 'where', 'why', 'how'}
                            meaningful_words = [word for word in words if len(word) > 3 and word not in stop_words]
                            keywords = Counter(meaningful_words).most_common(10)

                        if show_keypoints:
                            key_points = extract_key_points(transcript, 6)

                        progress_bar.progress(100)
                        time.sleep(0.3)
                        progress_bar.empty()

                        # Display Results
                        st.markdown("## 🎯 Summary Results")

                        # Main Summary
                        st.subheader("📝 Video Summary")
                        st.success(summary)

                        # Additional Information
                        if show_keywords or show_keypoints:
                            col1, col2 = st.columns(2)

                            if show_keypoints:
                                with col1:
                                    st.subheader("🔑 Key Points")
                                    for point in key_points:
                                        st.markdown(point)

                            if show_keywords:
                                with col2:
                                    st.subheader("🏷️ Top Keywords")
                                    keyword_text = ", ".join([f"**{word}** ({count})" for word, count in keywords])
                                    st.markdown(keyword_text)

                        # Statistics
                        st.subheader("📊 Analysis Statistics")
                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.metric("Original Words", len(transcript.split()))
                        with col2:
                            st.metric("Summary Words", len(summary.split()))
                        with col3:
                            compression = round((len(summary.split()) / len(transcript.split())) * 100, 1)
                            st.metric("Compression", f"{compression}%")
                        with col4:
                            reading_time = max(1, len(summary.split()) // 200)
                            st.metric("Read Time", f"{reading_time} min")

                        # Download Section
                        st.subheader("💾 Download Options")

                        # Create comprehensive report
                        report_content = f"""YouTube Video Summary Report
========================================

Video Title: {video_info.get('title', 'Unknown')}
Channel: {video_info.get('channel', 'Unknown')}
Duration: {video_info.get('duration', 'Unknown')}
URL: {video_info['url']}
Video ID: {video_id}
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY ({summary_length}):
{summary}

{'KEY POINTS:' if show_keypoints else ''}
{chr(10).join(key_points) if show_keypoints else ''}

{'TOP KEYWORDS:' if show_keywords else ''}
{', '.join([f'{word} ({count})' for word, count in keywords]) if show_keywords else ''}

STATISTICS:
- Original Words: {len(transcript.split())}
- Summary Words: {len(summary.split())}
- Compression Ratio: {compression}%
- Estimated Reading Time: {reading_time} minute(s)

ORIGINAL TRANSCRIPT:
{transcript}

---
Generated by YouTube Video Summarizer
"""

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.download_button(
                                "📄 Download Summary",
                                summary,
                                file_name=f"summary_{video_id}_{time.strftime('%Y%m%d')}.txt",
                                mime="text/plain",
                                use_container_width=True
                            )

                        with col2:
                            st.download_button(
                                "📋 Download Full Report",
                                report_content,
                                file_name=f"report_{video_id}_{time.strftime('%Y%m%d')}.txt",
                                mime="text/plain",
                                use_container_width=True
                            )

                        with col3:
                            st.download_button(
                                "📜 Download Transcript",
                                transcript,
                                file_name=f"transcript_{video_id}_{time.strftime('%Y%m%d')}.txt",
                                mime="text/plain",
                                use_container_width=True
                            )

                        # Original transcript viewer
                        with st.expander("📖 View Original Transcript"):
                            st.text_area("Complete Transcript", transcript, height=200, disabled=True)

                else:
                    st.warning("⚠️ Please enter the video transcript to generate a summary.")
                    st.info("💡 Use the instructions above to get the transcript from YouTube.")

        else:
            st.error(
                "❌ Could not retrieve video information. The video might be private, deleted, or the URL might be incorrect.")

    else:
        st.error("❌ Invalid YouTube URL format. Please enter a valid YouTube video URL.")
        st.info(
            "**Supported formats:**\n- https://www.youtube.com/watch?v=VIDEO_ID\n- https://youtu.be/VIDEO_ID\n- https://www.youtube.com/embed/VIDEO_ID")

else:
    # Welcome message when no URL is entered
    st.markdown("---")
    st.markdown("### 🚀 Get Started")
    st.info("👆 **Enter a YouTube URL above to begin!**")

    # Feature highlights
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **🎯 Smart Summarization**
        - AI-powered text analysis
        - Multiple summary lengths
        - Keyword extraction
        """)

    with col2:
        st.markdown("""
        **📹 Video Information**
        - Automatic video details
        - Duration and view count
        - Channel information
        """)

    with col3:
        st.markdown("""
        **💾 Export Options**
        - Download summaries
        - Full analysis reports
        - Original transcripts
        """)

# Footer
st.markdown("---")
st.markdown("**🤖 Powered by Advanced Text Analysis** | *Built with Streamlit*")
st.markdown("*For best results, ensure you have complete and accurate transcripts from YouTube.*")
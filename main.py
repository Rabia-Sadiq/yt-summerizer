import streamlit as st
import requests
import tempfile
import os
import subprocess
import json

st.title("🔬 Alternative YouTube Download Test")
st.markdown("Testing different approaches that might work on Streamlit Cloud")

test_url = st.text_input("Enter YouTube URL:", value="https://www.youtube.com/watch?v=dQw4w9WgXcQ")

if st.button("Test Alternative Methods"):
    if test_url:
        results = {}

        # Method 1: Try installing yt-dlp via subprocess
        st.write("Testing subprocess yt-dlp installation...")
        try:
            # Try to install yt-dlp on the fly
            subprocess.run(["pip", "install", "yt-dlp"], check=True, capture_output=True)
            import yt_dlp

            ydl_opts = {'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(test_url, download=False)
                title = info.get('title', 'Unknown')
            results["subprocess-yt-dlp"] = f"✅ Success - Title: {title}"
        except Exception as e:
            results["subprocess-yt-dlp"] = f"❌ Failed: {str(e)}"

        # Method 2: Try using requests with YouTube API approach
        st.write("Testing YouTube Data API approach...")
        try:
            # Extract video ID
            if "watch?v=" in test_url:
                video_id = test_url.split("watch?v=")[1].split("&")[0]
            elif "youtu.be/" in test_url:
                video_id = test_url.split("youtu.be/")[1].split("?")[0]
            else:
                raise Exception("Invalid YouTube URL format")

            # This would need API key in real implementation
            results["youtube-api"] = f"✅ Video ID extracted: {video_id} (API key needed for full functionality)"
        except Exception as e:
            results["youtube-api"] = f"❌ Failed: {str(e)}"

        # Method 3: Try direct HTTP requests approach
        st.write("Testing direct HTTP approach...")
        try:
            response = requests.get(test_url, timeout=10)
            if response.status_code == 200:
                # Look for title in HTML
                import re

                title_match = re.search(r'<title>(.*?)</title>', response.text)
                title = title_match.group(1) if title_match else "Found page"
                results["direct-http"] = f"✅ Success - Page accessed: {title}"
            else:
                results["direct-http"] = f"❌ Failed: HTTP {response.status_code}"
        except Exception as e:
            results["direct-http"] = f"❌ Failed: {str(e)}"

        # Method 4: Test if ffmpeg is available
        st.write("Testing ffmpeg availability...")
        try:
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
            if result.returncode == 0:
                results["ffmpeg"] = "✅ ffmpeg is available"
            else:
                results["ffmpeg"] = "❌ ffmpeg not working"
        except Exception as e:
            results["ffmpeg"] = f"❌ ffmpeg not available: {str(e)}"

        # Display results
        st.subheader("🔍 Test Results:")
        for method, result in results.items():
            if "✅" in result:
                st.success(f"**{method}**: {result}")
            else:
                st.error(f"**{method}**: {result}")

        # Recommendations
        working_methods = [method for method, result in results.items() if "✅" in result]

        if any("yt-dlp" in method for method in working_methods):
            st.success("🎉 We can build a direct YouTube downloader!")
        elif "ffmpeg" in working_methods:
            st.info("💡 FFmpeg is available - we might be able to use alternative approaches")
        else:
            st.warning("⚠️ Direct YouTube download seems limited. Consider these alternatives:")
            st.markdown("""
            - **YouTube Transcript API** (if available)
            - **External service integration** 
            - **Hybrid approach** with user assistance
            """)

# Test requirements
st.subheader("📋 Test Requirements:")
st.code("""
streamlit
requests
yt-dlp
""")

st.markdown("---")
st.info(
    "💡 **Next Steps**: Based on test results, we'll implement the best working approach for direct YouTube URL processing.")
import streamlit as st
import tempfile
import os

st.title("🎬 YouTube Download Test")

# Test different YouTube downloaders
st.subheader("Testing YouTube Download Methods")

test_url = st.text_input("Enter a YouTube URL to test:", value="https://www.youtube.com/watch?v=dQw4w9WgXcQ")

if st.button("Test Download Methods"):
    if test_url:
        results = {}

        # Test 1: pytube
        st.write("Testing pytube...")
        try:
            from pytube import YouTube

            yt = YouTube(test_url)
            title = yt.title
            results["pytube"] = f"✅ Success - Title: {title}"
        except Exception as e:
            results["pytube"] = f"❌ Failed: {str(e)}"

        # Test 2: yt-dlp
        st.write("Testing yt-dlp...")
        try:
            import yt_dlp

            ydl_opts = {'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(test_url, download=False)
                title = info.get('title', 'Unknown')
            results["yt-dlp"] = f"✅ Success - Title: {title}"
        except Exception as e:
            results["yt-dlp"] = f"❌ Failed: {str(e)}"

        # Test 3: youtube-dl
        st.write("Testing youtube-dl...")
        try:
            import youtube_dl

            ydl_opts = {'quiet': True}
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(test_url, download=False)
                title = info.get('title', 'Unknown')
            results["youtube-dl"] = f"✅ Success - Title: {title}"
        except Exception as e:
            results["youtube-dl"] = f"❌ Failed: {str(e)}"

        # Display results
        st.subheader("Results:")
        for method, result in results.items():
            if "✅" in result:
                st.success(f"{method}: {result}")
            else:
                st.error(f"{method}: {result}")

        # Recommend next steps
        working_methods = [method for method, result in results.items() if "✅" in result]
        if working_methods:
            st.success(f"🎉 Working methods: {', '.join(working_methods)}")
            st.info("We can use any of these for your YouTube summarizer!")
        else:
            st.error("❌ No YouTube downloaders are working. We'll need to use file upload instead.")

# Test requirements.txt for this
st.subheader("📋 Requirements to test:")
st.code("""
streamlit
pytube
yt-dlp
youtube-dl
""")

st.markdown("---")
st.markdown("**Instructions:**")
st.markdown("1. Update your requirements.txt with the packages above")
st.markdown("2. Let the app redeploy")
st.markdown("3. Run this test to see which YouTube downloader works")
st.markdown("4. We'll build your summarizer using the working method!")
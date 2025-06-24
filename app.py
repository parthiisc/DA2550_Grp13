import streamlit as st
import os
from dotenv import load_dotenv
from comicToStory_audio_batching import process_entire_comic, generate_speech, translate_text
import tempfile

# Load environment variables
load_dotenv()

st.set_page_config(page_title="ComicVerse: AI Comic Story & Audio Lab", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
    <style>
    .main {background-color: #fff !important;}
    .stButton>button {
        background-color: #43B97F;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        transition: background 0.2s;
        box-shadow: 0 2px 8px rgba(67,185,127,0.08);
    }
    .stButton>button:hover {
        background-color: #2e8b57;
        color: #fff;
    }
    .stDownloadButton>button {
        background-color: #6C63FF;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        transition: background 0.2s;
    }
    .stDownloadButton>button:hover {
        background-color: #5548c8;
        color: #fff;
    }
    .stSpinner {color: #43B97F;}
    .stTextInput>div>input {border-radius: 8px;}
    .stAudio {margin-top: 10px;}
    .stMarkdown h3 {margin-bottom: 0.5em;}
    .css-1kyxreq {background: #f8f9fa;}
    </style>
    """, unsafe_allow_html=True)
st.title(":sparkles: ComicVerse: AI Comic Story & Audio Lab")
st.markdown("<div style='font-size:1.2em; color:#555; margin-bottom:1.5em;'>Turn your comic PDFs into creative stories, audiobooks, and chat with your AI comic assistant. Choose your style, get dramatic or fun, and bring your comics to life!</div>", unsafe_allow_html=True)

# Language selection
language = st.radio("Select language:", ("English", "Hindi"), horizontal=True)

# File uploader
uploaded_file = st.file_uploader("Upload a comic PDF", type=["pdf"])

# Session state for story/audio
if "story" not in st.session_state:
    st.session_state["story"] = None
if "audio_bytes" not in st.session_state:
    st.session_state["audio_bytes"] = None
if "audio_path" not in st.session_state:
    st.session_state["audio_path"] = None
if "processing" not in st.session_state:
    st.session_state["processing"] = False

left_col, right_col = st.columns([1.2, 1])

with left_col:
    st.header(":gear: Actions")
    if uploaded_file is not None:
        st.write("Choose what you want to generate:")
        col1, col2, col3 = st.columns(3)
        gen_story = col1.button("Generate Story", disabled=st.session_state["processing"], help="Extracts the story from your comic in the selected style.")
        gen_audio = col2.button("Generate Audiobook", disabled=st.session_state["processing"], help="Generates an audiobook from the story text.")
        gen_both = col3.button("Generate Story and Audiobook", disabled=st.session_state["processing"], help="Extracts the story and generates an audiobook in one go.")

        # Show style options only after clicking Generate Story or Generate Story and Audiobook
        if 'show_style_options' not in st.session_state:
            st.session_state['show_style_options'] = False
        if gen_story or gen_both:
            st.session_state['show_style_options'] = True
        if gen_audio:
            st.session_state['show_style_options'] = False

        # Style selection and final generate button
        if st.session_state['show_style_options']:
            story_style = st.selectbox("Choose story style:", ["Neutral", "Dramatic", "Fun"], help="Select the tone for your generated story.")
            # Only generate when user clicks the final button, and keep options visible until then
            if gen_story or st.session_state.get('pending_story', False):
                st.session_state['pending_story'] = True
                if st.button("Generate Story Now", disabled=st.session_state["processing"]):
                    st.session_state["processing"] = True
                    with st.spinner("Generating story from comic PDF..."):
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                            tmp_pdf.write(uploaded_file.read())
                            tmp_pdf_path = tmp_pdf.name
                        story = process_entire_comic(tmp_pdf_path, os.path.dirname(tmp_pdf_path), style=story_style)
                        if language.lower() == "hindi":
                            story = translate_text(story, target_lang="hi")
                        st.session_state["story"] = story
                        st.session_state["audio_bytes"] = None
                        st.session_state["audio_path"] = None
                    st.session_state["processing"] = False
                    st.session_state['pending_story'] = False
                    st.session_state['show_style_options'] = False
            elif gen_both or st.session_state.get('pending_both', False):
                st.session_state['pending_both'] = True
                if st.button("Generate Story and Audiobook Now", disabled=st.session_state["processing"]):
                    st.session_state["processing"] = True
                    with st.spinner("Generating story and audio from comic PDF..."):
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                            tmp_pdf.write(uploaded_file.read())
                            tmp_pdf_path = tmp_pdf.name
                        story = process_entire_comic(tmp_pdf_path, os.path.dirname(tmp_pdf_path), style=story_style)
                        if language.lower() == "hindi":
                            story = translate_text(story, target_lang="hi")
                        st.session_state["story"] = story
                        st.session_state["audio_bytes"] = None
                        st.session_state["audio_path"] = None
                        # Generate audio
                        voice = "alloy"
                        audio_rel = generate_speech(story, voice=voice)
                        audio_path = os.path.join("app", "static", audio_rel) if not os.path.exists(audio_rel) else audio_rel
                        if os.path.exists(audio_path):
                            with open(audio_path, "rb") as audio_file:
                                audio_bytes = audio_file.read()
                            st.session_state["audio_bytes"] = audio_bytes
                            st.session_state["audio_path"] = audio_path
                        else:
                            st.session_state["audio_bytes"] = None
                            st.session_state["audio_path"] = None
                    st.session_state["processing"] = False
                    st.session_state['pending_both'] = False
                    st.session_state['show_style_options'] = False
        elif gen_audio:
            st.session_state["processing"] = True
            with st.spinner("Generating audio from comic PDF..."):
                if not st.session_state["story"]:
                    st.warning("Please generate the story first by selecting a style.")
                else:
                    story = st.session_state["story"]
                    voice = "alloy"
                    audio_rel = generate_speech(story, voice=voice)
                    audio_path = os.path.join("app", "static", audio_rel) if not os.path.exists(audio_rel) else audio_rel
                    if os.path.exists(audio_path):
                        with open(audio_path, "rb") as audio_file:
                            audio_bytes = audio_file.read()
                        st.session_state["audio_bytes"] = audio_bytes
                        st.session_state["audio_path"] = audio_path
                    else:
                        st.session_state["audio_bytes"] = None
                        st.session_state["audio_path"] = None
            st.session_state["processing"] = False

    # Show results
    if st.session_state["story"]:
        st.subheader(":book: Extracted Story:")
        st.write(st.session_state["story"])
        st.download_button("Download Story Text", st.session_state["story"], file_name="story.txt", key="download_text")
    if st.session_state["audio_bytes"]:
        st.subheader(":loud_sound: Audiobook:")
        st.audio(st.session_state["audio_bytes"], format="audio/mp3")
        st.download_button("Download Audio", st.session_state["audio_bytes"], file_name="story.mp3", key="download_audio")

with right_col:
    st.header("🤖 Chat with the Story")
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if st.session_state["processing"]:
        st.info("Please wait until processing is complete to chat with the story.")
    elif st.session_state["story"]:
        chat_container = st.container()
        with chat_container:
            for entry in st.session_state["chat_history"]:
                if entry["role"] == "user":
                    st.markdown(f"<div style='text-align:right;background:#e6f7ff;padding:8px 12px;border-radius:8px;margin-bottom:4px;'><b>You:</b> {entry['content']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='text-align:left;background:#f0f2f6;padding:8px 12px;border-radius:8px;margin-bottom:8px;'><b>AI:</b> {entry['content']}</div>", unsafe_allow_html=True)
        user_query = st.text_input("Ask a question about the story:", key="chat_input", disabled=st.session_state["processing"])
        if st.button("Send", key="send_btn", disabled=st.session_state["processing"] or not user_query):
            st.session_state["chat_history"].append({"role": "user", "content": user_query})
            with st.spinner("Getting answer from model..."):
                import openai
                chat_prompt = (
                    f"Story:\n{st.session_state['story']}\n\nUser question: {user_query}\n\nAnswer as helpfully as possible, referencing the story above."
                )
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": chat_prompt}],
                    temperature=0.7,
                    max_tokens=300,
                )
                answer = response.choices[0].message.content.strip()
                st.session_state["chat_history"].append({"role": "ai", "content": answer})
            st.rerun()
    else:
        st.info("Generate the story or audio first to chat with the AI.")

import logging

import streamlit as st

# Following line has to be before the import because the code uses streamlit
st.set_page_config(layout="wide", page_title="默写练习", page_icon="📝")

from select_characters import Character, Status, next_character, select_characters


st.title("默写练习 - Chinese Dictation")

logging.basicConfig(
    filename="diction.log", level=logging.INFO, format="%(asctime)s %(message)s"
)


ORIGINAL_RATE = 100

st.sidebar.header("Settings")

list_characters = select_characters()
if not list_characters:
    st.error("No characters selected")
    st.stop()


if "characters_done" not in st.session_state:
    st.session_state.characters_done = []
characters_done = st.session_state.characters_done


def record_characters(characters: Character):
    """Add characters to the list of characters done"""
    if not st.session_state.characters_done:
        st.session_state.characters_done = [characters]
    elif characters.chars != st.session_state.characters_done[-1].chars:
        st.session_state.characters_done.append(characters)


tab_practice, tab_review = st.tabs(["Practice", "Review"])

with tab_practice:
    st.header("Dictation")
    st.metric("Number of characters done", len(characters_done))

    rate = st.slider("Speed (words per minute)", 50, 200, ORIGINAL_RATE)
    word = next_character(list_characters)
    record_characters(word)

    audio_zone = st.empty()

    if st.button("⏭️ Next"):
        st.cache_data.clear()
        word = next_character(list_characters)
        record_characters(word)

    mp3 = word.generate_mp3(rate)
    audio_zone.audio(mp3)

    st.header("Solution")
    with st.expander("Show solution"):
        st.subheader(f"{word.chars}")
        st.subheader(f"{word.pinyin}")


with tab_review:
    st.header("Review")
    if st.button("🧹Clear list of characters"):
        characters_done.clear()

    if characters_done:
        st.write(f"Caption for status: {Status.get_help()}")
        for i, word in enumerate(characters_done):
            col_w, col_p, col_s = st.columns(3)
            col_w.subheader(word.chars)
            col_p.write(word.pinyin)
            status = col_s.radio(
                "status",
                Status.list_values(),
                key=f"check_{i}",
                horizontal=True,
                label_visibility="collapsed",
            )
            word.status = Status.from_string(status)
    else:
        st.header("No characters done yet")

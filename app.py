import streamlit as st
import requests
import re
from datetime import datetime

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="S'AI Translator",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = "https://api.mymemory.translated.net/get"

LANGUAGES = {
    "English": "en",
    "Hindi": "hi",
    "Telugu": "te",
    "Tamil": "ta",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Bengali": "bn",
    "Marathi": "mr",
    "Gujarati": "gu",
    "Punjabi": "pa",
    "Arabic": "ar",
    "French": "fr",
    "German": "de",
    "Spanish": "es",
    "Italian": "it",
    "Portuguese": "pt",
    "Japanese": "ja",
    "Chinese": "zh-CN",
    "Russian": "ru"
}

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

defaults = {
    "source_language": "English",
    "target_language": "Hindi",
    "source_text": "",
    "translation": "",
    "translation_meta": None,
    "error_message": "",
    "history": [],
    "page": "Translator"
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def clear_result():
    st.session_state.translation = ""
    st.session_state.translation_meta = None
    st.session_state.error_message = ""


def swap_languages():
    source = st.session_state.source_language
    target = st.session_state.target_language

    st.session_state.source_language = target
    st.session_state.target_language = source

    clear_result()


def clear_all():
    st.session_state.source_text = ""
    clear_result()


# --------------------------------------------------
# SCRIPT VALIDATION
# --------------------------------------------------

SCRIPT_RANGES = {
    "Hindi": [(0x0900, 0x097F)],
    "Marathi": [(0x0900, 0x097F)],
    "Telugu": [(0x0C00, 0x0C7F)],
    "Tamil": [(0x0B80, 0x0BFF)],
    "Kannada": [(0x0C80, 0x0CFF)],
    "Malayalam": [(0x0D00, 0x0D7F)],
    "Bengali": [(0x0980, 0x09FF)],
    "Gujarati": [(0x0A80, 0x0AFF)],
    "Punjabi": [(0x0A00, 0x0A7F)],
    "Arabic": [(0x0600, 0x06FF), (0x0750, 0x077F)],
    "Japanese": [
        (0x3040, 0x309F),
        (0x30A0, 0x30FF),
        (0x4E00, 0x9FFF)
    ],
    "Chinese": [(0x4E00, 0x9FFF)],
    "Russian": [(0x0400, 0x04FF)],
    "French": [(0x0041, 0x024F)],
    "German": [(0x0041, 0x024F)],
    "Spanish": [(0x0041, 0x024F)],
    "Italian": [(0x0041, 0x024F)],
    "Portuguese": [(0x0041, 0x024F)],
    "English": [(0x0041, 0x024F)]
}


def has_expected_script(text, language):
    ranges = SCRIPT_RANGES.get(language)

    if not ranges:
        return True

    letters = [
        char for char in text
        if char.isalpha()
    ]

    if not letters:
        return False

    matching_letters = 0

    for char in letters:
        code = ord(char)

        if any(start <= code <= end for start, end in ranges):
            matching_letters += 1

    return matching_letters / len(letters) >= 0.5


# --------------------------------------------------
# TRANSLATION HELPERS
# --------------------------------------------------

def normalize_text(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def select_translation(data, original_text):
    """
    Prefer an exact source-text match from MyMemory's
    matches list instead of blindly using the first result.
    """

    matches = data.get("matches", [])

    # First preference: exact original source text
    for match in matches:
        segment = match.get("segment", "")

        if segment.strip() == original_text.strip():
            translation = match.get("translation", "").strip()

            if translation:
                return translation

    # Second preference: normalized source-text match
    original_normalized = normalize_text(original_text)

    for match in matches:
        segment = match.get("segment", "")

        if normalize_text(segment) == original_normalized:
            translation = match.get("translation", "").strip()

            if translation:
                return translation

    # Last option: API's main translatedText
    response_data = data.get("responseData", {})
    return response_data.get("translatedText", "").strip()


def translate_text(text, source_language, target_language):
    source_code = LANGUAGES[source_language]
    target_code = LANGUAGES[target_language]

    params = {
        "q": text,
        "langpair": f"{source_code}|{target_code}",
        "mt": "1"
    }

    try:
        response = requests.get(
            API_URL,
            params=params,
            timeout=20
        )

        response.raise_for_status()
        data = response.json()

        if data.get("responseStatus") != 200:
            return None, "The translation service could not process your request."

        translated = select_translation(data, text)

        if not translated:
            return None, "No translation was returned. Please try again."

        if not has_expected_script(translated, target_language):
            return None, (
                "The translation service returned text in an unexpected "
                "language. Please try again later."
            )

        return translated, None

    except requests.exceptions.Timeout:
        return None, "The translation service took too long to respond."

    except requests.exceptions.ConnectionError:
        return None, "Unable to connect to the translation service. Check your internet."

    except requests.exceptions.RequestException:
        return None, "A network error occurred. Please try again."

    except ValueError:
        return None, "The translation service returned an invalid response."

    except Exception:
        return None, "Something went wrong. Please try again."


# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown("""
<style>
    .stApp {
        background-color: #f7f8fc;
        color: #20243a;
    }

    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e8eaf2;
    }

    .brand-title {
        font-size: 29px;
        font-weight: 800;
        color: #293d91;
        letter-spacing: -1px;
        margin-bottom: 2px;
    }

    .brand-subtitle {
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 2px;
        color: #8993ad;
    }

    .hero {
        background: linear-gradient(110deg, #365bd0, #7251ca);
        color: white;
        padding: 25px 30px;
        border-radius: 0 0 16px 16px;
        margin-bottom: 28px;
        box-shadow: 0 8px 22px rgba(65, 83, 180, 0.12);
    }

    .hero h1 {
        font-size: 27px;
        font-weight: 750;
        margin: 0 0 8px 0;
        color: white;
    }

    .hero p {
        font-size: 14px;
        margin: 0;
        color: #f1f2ff;
    }

    .section-label {
        color: #425477;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 1.4px;
        margin: 12px 0;
    }

    .result-box {
        background: linear-gradient(135deg, #ffffff, #f4f5ff);
        border: 1px solid #e1e6f5;
        border-radius: 12px;
        padding: 25px;
        min-height: 225px;
        color: #293d91;
        font-size: 18px;
        line-height: 1.8;
        overflow-wrap: anywhere;
    }

    .sidebar-divider {
        border-top: 1px solid #e8eaf2;
        margin: 25px 0;
    }

    .footer {
        text-align: center;
        color: #929bb0;
        font-size: 11px;
        margin-top: 45px;
        padding-bottom: 15px;
    }

    div.stButton > button {
        background: #385bd0;
        color: white;
        border: none;
        border-radius: 9px;
        min-height: 43px;
        font-weight: 650;
    }

    div.stButton > button:hover {
        background: #2948b5;
        color: white;
        border: none;
    }

    div[data-testid="stTextArea"] textarea {
        border: 1px solid #e0e5f0;
        border-radius: 11px;
        background: #ffffff;
        color: #263654;
        font-size: 16px;
        padding: 15px;
    }

    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        border-radius: 9px;
        background-color: #f0f2f7;
        border-color: transparent;
    }
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.markdown("""
    <div style="padding: 20px 0 25px 0;">
        <div class="brand-title">S'AI</div>
        <div class="brand-subtitle">LANGUAGE TRANSLATION PLATFORM</div>
    </div>
    <div class="sidebar-divider"></div>
    """, unsafe_allow_html=True)

    st.markdown(
        "<p style='font-size:13px;font-weight:700;color:#44495a;'>WORKSPACE</p>",
        unsafe_allow_html=True
    )

    selected_page = st.radio(
        "Workspace",
        ["Translator", "History", "About"],
        key="page",
        label_visibility="collapsed"
    )

    st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)

    st.markdown("**Language Support**")
    st.caption("19 supported languages")

    st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)

    st.markdown("**Platform Information**")
    st.caption("Python-based translation application")
    st.caption("CodeAlpha AI Internship Project")


# --------------------------------------------------
# TRANSLATOR PAGE
# --------------------------------------------------

if selected_page == "Translator":

    st.markdown("""
    <div class="hero">
        <h1>S'AI Translator</h1>
        <p>Translate your text between languages using a simple, reliable workspace.</p>
    </div>
    """, unsafe_allow_html=True)

    language_col1, swap_col, language_col2 = st.columns([5, 1, 5])

    with language_col1:
        st.markdown("<div class='section-label'>SOURCE LANGUAGE</div>",
                    unsafe_allow_html=True)

        st.selectbox(
            "Source language",
            list(LANGUAGES.keys()),
            key="source_language",
            label_visibility="collapsed",
            on_change=clear_result
        )

    with swap_col:
        st.markdown("<div style='height:27px'></div>", unsafe_allow_html=True)

        st.button(
            "Swap",
            use_container_width=True,
            on_click=swap_languages
        )

    with language_col2:
        st.markdown("<div class='section-label'>TARGET LANGUAGE</div>",
                    unsafe_allow_html=True)

        st.selectbox(
            "Target language",
            list(LANGUAGES.keys()),
            key="target_language",
            label_visibility="collapsed",
            on_change=clear_result
        )

    if st.session_state.source_language == st.session_state.target_language:
        st.info("Choose two different languages to translate.")

    left_col, right_col = st.columns(2, gap="large")

    with left_col:
        st.markdown("<div class='section-label'>SOURCE TEXT</div>",
                    unsafe_allow_html=True)

        source_text = st.text_area(
            "Enter source text",
            key="source_text",
            height=225,
            placeholder="Enter the text you want to translate...",
            label_visibility="collapsed"
        )

        translate_clicked = st.button(
            "Translate",
            use_container_width=True,
            disabled=(
                not source_text.strip()
                or st.session_state.source_language
                == st.session_state.target_language
            )
        )

        if st.button("Clear text", use_container_width=True):
            clear_all()
            st.rerun()

    with right_col:
        st.markdown("<div class='section-label'>TRANSLATED TEXT</div>",
                    unsafe_allow_html=True)

        current_meta = (
            source_text.strip(),
            st.session_state.source_language,
            st.session_state.target_language
        )

        if (
            st.session_state.translation
            and st.session_state.translation_meta == current_meta
        ):
            st.markdown(
                f"<div class='result-box'>{st.session_state.translation}</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                "<div class='result-box' style='display:flex;"
                "align-items:center;justify-content:center;"
                "color:#929db5;font-size:15px;'>"
                "Translated text will appear here."
                "</div>",
                unsafe_allow_html=True
            )

    if translate_clicked:

        if len(source_text.strip()) > 5000:
            st.error("Please enter text containing fewer than 5,000 characters.")

        else:
            with st.spinner("Translating your text..."):

                translated, error = translate_text(
                    source_text.strip(),
                    st.session_state.source_language,
                    st.session_state.target_language
                )

            if error:
                st.session_state.translation = ""
                st.session_state.translation_meta = None
                st.session_state.error_message = error
                st.error(error)

            else:
                st.session_state.translation = translated
                st.session_state.translation_meta = current_meta
                st.session_state.error_message = ""

                st.session_state.history.insert(0, {
                    "source": source_text.strip(),
                    "translated": translated,
                    "from": st.session_state.source_language,
                    "to": st.session_state.target_language,
                    "time": datetime.now().strftime("%d %b %Y, %I:%M %p")
                })

                st.session_state.history = st.session_state.history[:20]

                st.rerun()

    st.markdown("""
    <div class="footer">
        S'AI Translator<br>
        Language Translation Platform
    </div>
    """, unsafe_allow_html=True)


# --------------------------------------------------
# HISTORY PAGE
# --------------------------------------------------

elif selected_page == "History":

    st.markdown("""
    <div class="hero">
        <h1>Translation History</h1>
        <p>View your recent translations in this session.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.history:

        if st.button("Clear History"):
            st.session_state.history = []
            st.rerun()

        for index, item in enumerate(st.session_state.history):

            st.markdown(f"**{item['from']} → {item['to']}**")
            st.caption(item["time"])

            st.markdown("**Source Text**")
            st.write(item["source"])

            st.markdown("**Translated Text**")
            st.write(item["translated"])

            st.divider()

    else:
        st.info("No translations available yet. Start translating to see your history.")


# --------------------------------------------------
# ABOUT PAGE
# --------------------------------------------------

elif selected_page == "About":

    st.markdown("""
    <div class="hero">
        <h1>About S'AI Translator</h1>
        <p>A simple language translation platform designed for easy communication.</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Project Overview")

    st.write(
        "S'AI Translator is a Python-based web application that helps "
        "users translate text between multiple languages through a "
        "simple and user-friendly interface."
    )

    st.subheader("Core Features")

    st.markdown("""
    - Translation between 19 supported languages
    - Source and target language selection
    - Language swapping
    - Translation history for the current session
    - Input and response validation
    - Simple and responsive interface
    """)

    st.subheader("Technology Stack")

    st.markdown("""
    - **Programming Language:** Python
    - **Frontend / Web Framework:** Streamlit
    - **HTTP Requests:** Requests library
    - **Translation Service:** MyMemory Translation API
    """)

    st.subheader("Project Information")

    st.write("Project: S'AI Translator")
    st.write("Internship: CodeAlpha Artificial Intelligence Internship")
    st.write("Category: Language Translation Tool")

    st.markdown("""
    <div class="footer">
        S'AI Translator<br>
        Language Translation Platform
    </div>
    """, unsafe_allow_html=True)
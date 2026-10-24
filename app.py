"""StudySloth AI - Private, On-Device AI Study Assistant
A 100% local, private, open-weight AI study companion built with Streamlit and Ollama.
"""

import json
import time
import streamlit as st

from utils.document_processor import (
    process_uploaded_document,
    validate_text_content,
    DocumentProcessingError,
    MAX_FILE_SIZE_MB,
)
from utils.ollama_client import (
    check_ollama_status,
    generate_text_stream,
    generate_text_sync,
    extract_json_block,
    RECOMMENDED_MODELS,
    DEFAULT_MODEL,
    DEFAULT_OLLAMA_URL,
    OllamaClientError,
)
from utils.prompts import (
    build_prompt,
    SYSTEM_INSTRUCTION,
)
from utils.samples import SAMPLE_NOTES

# Configure page layout and metadata
st.set_page_config(
    page_title="StudySloth AI | Private On-Device AI Study Assistant",
    page_icon="🦥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Sloth-themed CSS for warm, calm, cozy study ambiance
CUSTOM_CSS = """
<style>
    /* Forest & Earthy Sloth Theme Palette */
    :root {
        --sloth-green: #2E6F40;
        --sloth-light-green: #EBF3ED;
        --sloth-dark-green: #1C4427;
        --sloth-brown: #8B5A2B;
        --sloth-amber: #D9822B;
        --sloth-bg-card: #FFFFFF;
        --sloth-border: #D6E3D8;
    }

    .main-title-container {
        display: flex;
        align-items: center;
        gap: 1.2rem;
        background: linear-gradient(135deg, #EBF3ED 0%, #F5F9F6 100%);
        padding: 1.4rem 1.8rem;
        border-radius: 16px;
        border: 1px solid #D6E3D8;
        margin-bottom: 1.5rem;
    }

    .sloth-avatar {
        font-size: 3.5rem;
        line-height: 1;
        background: #FFFFFF;
        border-radius: 50%;
        padding: 0.6rem;
        box-shadow: 0 4px 12px rgba(46, 111, 64, 0.12);
    }

    .main-title-text h1 {
        margin: 0;
        color: #1C4427;
        font-size: 2.1rem;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    .main-title-text p {
        margin: 0.3rem 0 0 0;
        color: #4A6B53;
        font-size: 1.05rem;
    }

    .brand-badge {
        display: inline-block;
        background: #2E6F40;
        color: #FFFFFF !important;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.25rem 0.6rem;
        border-radius: 20px;
        margin-top: 0.4rem;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }

    /* Card styling */
    .st-card {
        background: #FFFFFF;
        border: 1px solid #D6E3D8;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }

    /* Status Pills */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .status-online {
        background: #E6F7EB;
        color: #15692A;
        border: 1px solid #B0E4BC;
    }

    .status-offline {
        background: #FDEDED;
        color: #A81B1B;
        border: 1px solid #F8BEBE;
    }

    /* Flashcard interactive card */
    .flashcard-box {
        background: linear-gradient(135deg, #FBFDFB 0%, #F3F7F3 100%);
        border: 2px solid #5C8E6B;
        border-radius: 14px;
        padding: 2rem;
        margin: 1.2rem 0;
        box-shadow: 0 6px 16px rgba(46, 111, 64, 0.08);
        text-align: center;
        min-height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .flashcard-q {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1C4427;
        margin-bottom: 1rem;
    }

    .flashcard-a {
        font-size: 1.15rem;
        font-weight: 500;
        color: #2E6F40;
        background: #EAF3EB;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2E6F40;
        margin-top: 1rem;
    }

    /* Stat badges */
    .note-stat-badge {
        background: #F1F6F2;
        color: #2D5837;
        border: 1px solid #D5E2D7;
        padding: 0.3rem 0.7rem;
        border-radius: 8px;
        font-size: 0.82rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 0.5rem;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# Initialize session state variables
if "study_notes" not in st.session_state:
    st.session_state.study_notes = ""
if "generated_result" not in st.session_state:
    st.session_state.generated_result = ""
if "generated_type" not in st.session_state:
    st.session_state.generated_type = ""
if "flashcard_index" not in st.session_state:
    st.session_state.flashcard_index = 0
if "flashcard_revealed" not in st.session_state:
    st.session_state.flashcard_revealed = False
if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "input_mode" not in st.session_state:
    st.session_state.input_mode = "Paste / Edit Notes"


# SIDEBAR: Local AI Monitor & Model Selector
with st.sidebar:
    st.markdown("### 🦥 StudySloth Control Panel")
    
    ollama_url = st.text_input(
        "Local Ollama Server URL",
        value=DEFAULT_OLLAMA_URL,
        help="Default is http://localhost:11434. Ollama runs on this port on your machine.",
    )

    # Check Ollama Connectivity
    is_online, status_msg, installed_models = check_ollama_status(ollama_url)

    if is_online:
        st.markdown(
            '<div class="status-pill status-online">🟢 <b>Ollama Online (Local)</b></div>',
            unsafe_allow_html=True,
        )
        st.caption("🔒 All computation stays on your device.")
    else:
        st.markdown(
            '<div class="status-pill status-offline">🔴 <b>Ollama Offline</b></div>',
            unsafe_allow_html=True,
        )
        st.caption("Local AI server is not currently reachable.")

    if st.button("🔄 Refresh Server Status", use_container_width=True):
        st.rerun()

    st.markdown("---")
    st.markdown("#### 🧠 Model Selection")

    # Populate model options
    model_choices = []
    if installed_models:
        model_choices.extend(installed_models)
    
    # Also ensure recommended models are represented
    for m in RECOMMENDED_MODELS.keys():
        if m not in model_choices:
            model_choices.append(f"{m} (not installed)")

    selected_model_raw = st.selectbox(
        "Choose Local AI Model",
        options=model_choices,
        index=0 if model_choices else 0,
        help="Select which open-weight model to use for generating your study aids.",
    )
    selected_model = selected_model_raw.replace(" (not installed)", "").strip()

    # Hardware & Model Specs Expander
    with st.expander("ℹ️ Model Specs & Hardware Guide", expanded=False):
        if selected_model in RECOMMENDED_MODELS:
            info = RECOMMENDED_MODELS[selected_model]
            st.markdown(f"**Model:** `{info['name']}`")
            st.markdown(f"- **Parameters:** {info['parameter_size']}")
            st.markdown(f"- **Download Size:** {info['download_size']}")
            st.markdown(f"- **RAM Requirement:** {info['recommended_ram']}")
            st.markdown(f"- **GPU/VRAM:** {info['vram']}")
            st.markdown(f"- **Open License:** {info['license']}")
            st.markdown(f"- **Install Command:** `{info['command']}`")
            st.info(info["description"])
        else:
            st.write(f"Custom model detected: `{selected_model}`")

    # Offline & Fallback options
    st.markdown("---")
    st.markdown("#### ⚙️ Study Settings")
    temperature = st.slider(
        "Study Rigor (Temperature)",
        min_value=0.1,
        max_value=0.7,
        value=0.3,
        step=0.05,
        help="Lower values (0.1 - 0.3) provide strict factual summaries; higher values (0.5 - 0.7) provide creative analogies.",
    )

    allow_simulated = st.checkbox(
        "Enable Simulated Demo Mode (if Ollama offline)",
        value=not is_online,
        help="Allows testing the app interface and study outputs immediately even before Ollama finishes downloading on your computer.",
    )

    st.markdown("---")
    st.markdown("#### 🛡️ Privacy & Offline Guarantee")
    st.caption(
        "• **100% On-Device:** Your notes, PDFs, and study guides never leave your PC.\n"
        "• **Zero API Keys:** No OpenAI/Anthropic/Google keys or accounts required.\n"
        "• **Offline Operation:** Once Ollama and your chosen model are downloaded, disconnect your WiFi anytime and StudySloth works fully offline!"
    )


# MAIN CONTENT AREA
st.markdown(
    """
    <div class="main-title-container">
        <div class="sloth-avatar">🦥</div>
        <div class="main-title-text">
            <h1>StudySloth AI</h1>
            <p>Slow and steady wins the race. 100% Local, Private, AI-Powered Study Assistant.</p>
            <span class="brand-badge">100% Private • Local Open-Weight AI</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# QUICK STARTER SAMPLES
st.markdown("##### 🚀 Quick Starters (Load Sample Notes)")
col_s1, col_s2, col_s3, col_s4 = st.columns([1, 1, 1, 0.7])

with col_s1:
    if st.button("🔬 Biology: Respiration", use_container_width=True):
        st.session_state.study_notes = SAMPLE_NOTES["Biology: Cellular Respiration & Energy"]
        st.toast("Loaded Biology sample notes!", icon="🦥")
with col_s2:
    if st.button("💻 CS: Big-O & Data Structs", use_container_width=True):
        st.session_state.study_notes = SAMPLE_NOTES["Computer Science: Big-O & Data Structures"]
        st.toast("Loaded Computer Science sample notes!", icon="🦥")
with col_s3:
    if st.button("📜 History: Industrial Rev", use_container_width=True):
        st.session_state.study_notes = SAMPLE_NOTES["World History: The Industrial Revolution"]
        st.toast("Loaded World History sample notes!", icon="🦥")
with col_s4:
    if st.button("🧹 Clear", use_container_width=True):
        st.session_state.study_notes = ""
        st.session_state.generated_result = ""
        st.session_state.quiz_submitted = False
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)


# INPUT SECTION (TABS)
input_tab1, input_tab2 = st.tabs(["✍️ Paste / Edit Notes", "📁 Upload Document (.txt, .pdf, .docx)"])

with input_tab1:
    notes_input = st.text_area(
        "Study Material Input",
        value=st.session_state.study_notes,
        height=220,
        placeholder="Paste lecture notes, textbook excerpts, or article content here...",
        help="Input text to be synthesized into study aids.",
        label_visibility="collapsed",
    )
    if notes_input != st.session_state.study_notes:
        st.session_state.study_notes = notes_input

with input_tab2:
    uploaded_file = st.file_uploader(
        "Upload Note Document",
        type=["txt", "pdf", "docx"],
        help=f"Supported file formats: TXT, PDF, DOCX (Max {MAX_FILE_SIZE_MB}MB)",
    )
    if uploaded_file is not None:
        try:
            file_bytes = uploaded_file.read()
            extracted_text, metadata = process_uploaded_document(uploaded_file.name, file_bytes)
            st.session_state.study_notes = extracted_text
            st.success(
                f"✅ Extracted **{metadata['character_count']}** characters "
                f"(~{metadata['word_count']} words) from `{metadata['filename']}`"
            )
            if metadata.get("is_truncated"):
                st.warning(
                    f"⚠️ Document exceeded safe local model context limit ({metadata['original_char_count']} chars). "
                    f"Safely trimmed to {metadata['character_count']} chars."
                )
        except DocumentProcessingError as doc_err:
            st.error(f"❌ Error processing document: {str(doc_err)}")
        except Exception as err:
            st.error(f"❌ Unexpected error reading file: {str(err)}")


# Current text statistics
current_text = st.session_state.study_notes.strip()
if current_text:
    word_cnt = len(current_text.split())
    char_cnt = len(current_text)
    est_read_min = max(1, round(word_cnt / 200))
    st.markdown(
        f"""
        <div>
            <span class="note-stat-badge">📊 {word_cnt:,} words</span>
            <span class="note-stat-badge">🔤 {char_cnt:,} characters</span>
            <span class="note-stat-badge">⏱️ ~{est_read_min} min read</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)


# STUDY AID OPTIONS
st.markdown("### 🎯 Choose Study Aid Output")

col_opt1, col_opt2 = st.columns([2, 1])

with col_opt1:
    output_option_labels = {
        "summary": "📝 Executive Summary (Deep & Structured)",
        "key_points": "📌 High-Yield Key Points & Takeaways",
        "definitions": "📖 Key Terminology & Definitions",
        "flashcards": "🗂️ Active Recall Flashcards (Q&A)",
        "quiz": "🎯 Multiple-Choice Comprehension Quiz",
        "comprehensive": "🌟 All-in-One Comprehensive Study Pack",
    }
    selected_output_key = st.selectbox(
        "Study Aid Format",
        options=list(output_option_labels.keys()),
        format_func=lambda k: output_option_labels[k],
    )

with col_opt2:
    st.write("")
    st.write("")
    generate_btn = st.button("🦥 Generate with StudySloth", type="primary", use_container_width=True)


# GENERATION LOGIC
if generate_btn:
    is_valid, validation_msg = validate_text_content(current_text)
    if not is_valid:
        st.warning(f"⚠️ {validation_msg}")
    else:
        # Check if Ollama is accessible
        if not is_online and not allow_simulated:
            st.error(
                "❌ **Ollama is not running locally.**\n\n"
                "To run 100% on-device AI:\n"
                "1. Make sure Ollama is installed from [ollama.com](https://ollama.com).\n"
                "2. Open a terminal and run: `ollama run llama3.2:1b`\n"
                "3. Click **🔄 Refresh Server Status** in the sidebar.\n\n"
                "*(Or check 'Enable Simulated Demo Mode' in the sidebar to preview the study features immediately!)*"
            )
        else:
            # Build prompt
            prompt = build_prompt(selected_output_key, current_text)
            st.session_state.generated_type = selected_output_key
            st.session_state.flashcard_index = 0
            st.session_state.flashcard_revealed = False
            st.session_state.quiz_submitted = False
            st.session_state.quiz_answers = {}

            with st.status("🦥 StudySloth is working patiently...", expanded=True) as status_box:
                if is_online:
                    st.write("🔍 Parsing notes and preparing local prompt...")
                    time.sleep(0.3)
                    st.write(f"🧠 Querying `{selected_model}` locally via Ollama...")

                    full_response = ""
                    try:
                        response_container = st.empty()
                        for chunk in generate_text_stream(
                            prompt=prompt,
                            system_prompt=SYSTEM_INSTRUCTION,
                            model=selected_model,
                            base_url=ollama_url,
                            temperature=temperature,
                        ):
                            full_response += chunk
                            response_container.markdown(full_response + " ▌")
                        
                        response_container.markdown(full_response)
                        st.session_state.generated_result = full_response
                        status_box.update(label="🦥 Study aid generated successfully!", state="complete", expanded=False)
                    except OllamaClientError as client_err:
                        status_box.update(label="❌ Generation failed", state="error", expanded=True)
                        st.error(str(client_err))
                    except Exception as err:
                        status_box.update(label="❌ Generation error", state="error", expanded=True)
                        st.error(f"Unexpected error: {str(err)}")

                else:
                    # Simulated Demonstration Mode
                    st.write("🦥 Simulated Demo Mode Active (Ollama offline)...")
                    time.sleep(0.5)
                    st.write("📖 Distilling key concepts from notes...")
                    time.sleep(0.5)

                    # High quality simulated response grounded in the actual input notes
                    first_few_lines = "\n".join([ln for ln in current_text.splitlines() if ln.strip()][:4])
                    if selected_output_key == "summary":
                        full_response = (
                            "## 🦥 Executive Summary\n\n"
                            f"These study notes provide a thorough exploration of the core concepts introduced in the text:\n\n"
                            f"> {first_few_lines}\n\n"
                            "Through careful study, the material establishes foundational principles and structural relationships. "
                            "Every stage contributes directly to the overall system's stability and operational efficiency.\n\n"
                            "## 🎯 Core Themes & Mechanics\n\n"
                            "- **Fundamental Drivers**: How the primary elements interact to transform inputs into useful outcomes.\n"
                            "- **Step-by-Step Logic**: The structured cascade of actions that govern this domain.\n"
                            "- **Comparative Context**: Key distinctions that prevent confusion during exam recall.\n\n"
                            "## 💡 Big Picture Takeaway\n\n"
                            "Mastering this topic relies on recognizing that each discrete stage builds directly on the products of the preceding phase."
                        )
                    elif selected_output_key == "key_points":
                        full_response = (
                            "## 📌 High-Yield Key Points\n\n"
                            "- **Primary Mechanism**: The central process described in your notes forms the energetic/operational bedrock of the entire system.\n"
                            "- **Energy & Resource Flow**: Critical transitions govern how inputs are transformed into stable outputs.\n"
                            "- **Crucial Distinctions**: Always differentiate between standard baseline conditions and edge/emergency states.\n"
                            "- **Exam Favorite**: Pay close attention to numerical ratios, sequence order, and specific locations."
                        )
                    elif selected_output_key == "definitions":
                        full_response = (
                            "## 📖 Key Terminology & Definitions\n\n"
                            "- **Primary Entity**: The foundational subject or substrate detailed in the provided notes.\n"
                            "  *Context/Application*: Serves as the starting element for subsequent reactions/operations.\n\n"
                            "- **Catalyst / Accelerator**: Any agent or condition that speeds up the transformation rate.\n"
                            "  *Context/Application*: Critical for overcoming high activation thresholds.\n\n"
                            "- **Terminal Acceptor**: The concluding component that finalizes the pathway.\n"
                            "  *Context/Application*: Prevents buildup of high-energy intermediaries."
                        )
                    elif selected_output_key == "flashcards":
                        full_response = (
                            "### Flashcard 1\n"
                            "**Q**: What is the primary purpose of the system described in the notes?\n"
                            "**A**: To break down initial substrates and generate usable energy/outputs efficiently.\n\n"
                            "### Flashcard 2\n"
                            "**Q**: Where does the initial phase take place?\n"
                            "**A**: In the foundational environment (e.g. cytoplasm / baseline environment) prior to specialized processing.\n\n"
                            "### Flashcard 3\n"
                            "**Q**: What happens when standard operating conditions are absent?\n"
                            "**A**: The system transitions to an alternative/anaerobic bypass to maintain essential survival.\n\n"
                            "```json\n"
                            "[\n"
                            '  {"id": 1, "question": "What is the primary purpose of the system described in the notes?", "answer": "To break down initial substrates and generate usable energy/outputs efficiently."},\n'
                            '  {"id": 2, "question": "Where does the initial phase take place?", "answer": "In the foundational environment (e.g. cytoplasm / baseline environment) prior to specialized processing."},\n'
                            '  {"id": 3, "question": "What happens when standard operating conditions are absent?", "answer": "The system transitions to an alternative/anaerobic bypass to maintain essential survival."}\n'
                            "]\n"
                            "```"
                        )
                    elif selected_output_key == "quiz":
                        full_response = (
                            "### Question 1\n"
                            "What is the foundational role of the process described in the notes?\n"
                            "- A) Rapid destruction without energy recovery\n"
                            "- B) Systematic breakdown to generate usable outputs\n"
                            "- C) Static storage without transformation\n"
                            "- D) Random uncoordinated reactions\n\n"
                            "**Correct Answer**: B\n"
                            "**Explanation**: The material emphasizes efficient step-by-step transformation rather than uncontrolled destruction.\n\n"
                            "### Question 2\n"
                            "Which condition triggers an alternate secondary pathway?\n"
                            "- A) Excess raw materials\n"
                            "- B) Perfect thermal equilibrium\n"
                            "- C) Absence of the standard terminal acceptor\n"
                            "- D) Doubled processing capacity\n\n"
                            "**Correct Answer**: C\n"
                            "**Explanation**: Alternate pathways (such as fermentation) engage when essential terminal conditions are missing.\n\n"
                            "```json\n"
                            "[\n"
                            "  {\n"
                            '    "id": 1,\n'
                            '    "question": "What is the foundational role of the process described in the notes?",\n'
                            '    "options": {"A": "Rapid destruction without energy recovery", "B": "Systematic breakdown to generate usable outputs", "C": "Static storage without transformation", "D": "Random uncoordinated reactions"},\n'
                            '    "answer": "B",\n'
                            '    "explanation": "The material emphasizes efficient step-by-step transformation rather than uncontrolled destruction."\n'
                            "  },\n"
                            "  {\n"
                            '    "id": 2,\n'
                            '    "question": "Which condition triggers an alternate secondary pathway?",\n'
                            '    "options": {"A": "Excess raw materials", "B": "Perfect thermal equilibrium", "C": "Absence of the standard terminal acceptor", "D": "Doubled processing capacity"},\n'
                            '    "answer": "C",\n'
                            '    "explanation": "Alternate pathways (such as fermentation) engage when essential terminal conditions are missing."\n'
                            "  }\n"
                            "]\n"
                            "```"
                        )
                    else:  # comprehensive
                        full_response = (
                            "# 🦥 Comprehensive Study Pack\n\n"
                            "## 1. Executive Summary\n"
                            f"Synthesizing the core elements of the uploaded material: {first_few_lines}\n\n"
                            "## 2. Core Takeaways & High-Yield Points\n"
                            "- High systematic structure.\n"
                            "- Precise sequence and energy transfer.\n\n"
                            "## 3. Essential Glossary & Definitions\n"
                            "- **Primary Mechanism**: The fundamental driver of the topic.\n\n"
                            "## 4. Active Recall Flashcards\n"
                            "**Q**: What is the most important concept?\n"
                            "**A**: The step-by-step logic detailed in the notes.\n\n"
                            "## 5. Practice Quiz\n"
                            "**Question**: Why study slowly and steadily?\n"
                            "- A) It ensures deep neural consolidation (Correct)\n"
                            "- B) Cramming is faster"
                        )

                    st.session_state.generated_result = full_response
                    status_box.update(label="🦥 Study aid generated (Demo Mode)!", state="complete", expanded=False)


# DISPLAY RESULTS
if st.session_state.generated_result:
    st.markdown("---")
    st.markdown("### 📚 StudySloth Generated Results")

    res_tab1, res_tab2 = st.tabs(["📄 Formatted Study Aid", "🎮 Interactive Practice"])

    with res_tab1:
        st.markdown(st.session_state.generated_result)

    with res_tab2:
        parsed_json = extract_json_block(st.session_state.generated_result)
        
        # Unwrap dictionary wrapper if returned by LLM (e.g. {"flashcards": [...]} or {"quiz": [...]})
        if isinstance(parsed_json, dict):
            for wrapper_key in ["flashcards", "quiz", "questions", "cards", "data"]:
                if wrapper_key in parsed_json and isinstance(parsed_json[wrapper_key], list):
                    parsed_json = parsed_json[wrapper_key]
                    break
            else:
                for val in parsed_json.values():
                    if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                        parsed_json = val
                        break

        if parsed_json and isinstance(parsed_json, list) and len(parsed_json) > 0:
            first_item = parsed_json[0]

            # FLASHCARD MODE
            if isinstance(first_item, dict) and "question" in first_item and "answer" in first_item and "options" not in first_item:
                total_cards = len(parsed_json)
                current_card_idx = st.session_state.flashcard_index % total_cards
                card = parsed_json[current_card_idx]

                st.markdown(f"#### 🗂️ Interactive Flashcards (Card {current_card_idx + 1} of {total_cards})")
                
                # Card display box
                st.markdown(
                    f"""
                    <div class="flashcard-box">
                        <div class="flashcard-q">❓ {card.get('question', '')}</div>
                        {"<div class='flashcard-a'>💡 " + card.get('answer', '') + "</div>" if st.session_state.flashcard_revealed else "<div style='color: #888;'><i>Click 'Reveal Answer' below to test your recall</i></div>"}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                col_fc1, col_fc2, col_fc3 = st.columns([1, 1, 1])
                with col_fc1:
                    if st.button("⬅️ Previous Card", use_container_width=True):
                        st.session_state.flashcard_index = (current_card_idx - 1) % total_cards
                        st.session_state.flashcard_revealed = False
                        st.rerun()
                with col_fc2:
                    reveal_label = "🙈 Hide Answer" if st.session_state.flashcard_revealed else "👁️ Reveal Answer"
                    if st.button(reveal_label, type="primary", use_container_width=True):
                        st.session_state.flashcard_revealed = not st.session_state.flashcard_revealed
                        st.rerun()
                with col_fc3:
                    if st.button("Next Card ➡️", use_container_width=True):
                        st.session_state.flashcard_index = (current_card_idx + 1) % total_cards
                        st.session_state.flashcard_revealed = False
                        st.rerun()

            # QUIZ MODE
            elif isinstance(first_item, dict) and "options" in first_item and "answer" in first_item:
                st.markdown("#### 🎯 Interactive Comprehension Quiz")
                
                for q_idx, q in enumerate(parsed_json):
                    qid = str(q.get("id", q_idx + 1))
                    question_text = q.get("question", "")
                    options_data = q.get("options", {})
                    
                    st.markdown(f"**Q{q_idx + 1}: {question_text}**")
                    
                    # Formulate choices safely whether options is dict or list
                    choice_list = []
                    if isinstance(options_data, dict):
                        choice_list = [f"{key}) {val}" for key, val in options_data.items()]
                    elif isinstance(options_data, list):
                        letters = ["A", "B", "C", "D", "E", "F"]
                        for opt_i, opt in enumerate(options_data):
                            opt_str = str(opt).strip()
                            if len(opt_str) >= 2 and opt_str[0].upper() in letters and opt_str[1] in [")", ".", ":", " "]:
                                choice_list.append(opt_str)
                            else:
                                prefix = letters[opt_i] if opt_i < len(letters) else f"Opt{opt_i+1}"
                                choice_list.append(f"{prefix}) {opt_str}")

                    
                    user_selection = st.radio(
                        label=f"q_{qid}_label",
                        options=choice_list,
                        key=f"user_choice_{qid}",
                        index=None if not st.session_state.quiz_submitted else None,
                        label_visibility="collapsed",
                    )
                    
                    if user_selection:
                        selected_letter = user_selection[0]  # First char is 'A', 'B', etc.
                        st.session_state.quiz_answers[qid] = selected_letter

                    # Show answer feedback if quiz was submitted
                    if st.session_state.quiz_submitted:
                        correct_letter = q.get("answer", "").strip().upper()
                        user_ans = st.session_state.quiz_answers.get(qid, "")
                        explanation = q.get("explanation", "")
                        
                        if user_ans == correct_letter:
                            st.success(f"✅ Correct! ({correct_letter}) — {explanation}")
                        else:
                            st.error(f"❌ You chose {user_ans or 'Nothing'}. Correct answer is **{correct_letter}** — {explanation}")
                    
                    st.markdown("---")

                if not st.session_state.quiz_submitted:
                    if st.button("📝 Submit Quiz Answers", type="primary"):
                        st.session_state.quiz_submitted = True
                        st.rerun()
                else:
                    # Calculate score
                    correct_count = 0
                    for q_idx, q in enumerate(parsed_json):
                        qid = str(q.get("id", q_idx + 1))
                        if st.session_state.quiz_answers.get(qid, "") == q.get("answer", "").strip().upper():
                            correct_count += 1
                    
                    pct = round((correct_count / len(parsed_json)) * 100)
                    st.balloons()
                    st.info(f"🏆 **Your Score: {correct_count} / {len(parsed_json)} ({pct}%)**")
                    
                    if st.button("🔄 Retake Quiz"):
                        st.session_state.quiz_submitted = False
                        st.session_state.quiz_answers = {}
                        st.rerun()

            else:
                st.info("💡 Interactive mode is active when Flashcards or Quizzes are generated.")
        else:
            st.info("💡 Generate **Flashcards** or a **Multiple-Choice Quiz** to unlock the interactive practice suite!")


    # EXPORT & COPY CENTER
    st.markdown("---")
    st.markdown("#### 💾 Export & Share")
    
    col_dl1, col_dl2, col_dl3, col_dl4 = st.columns([1, 1, 1, 1])
    
    with col_dl1:
        st.download_button(
            label="⬇️ Download Markdown (.md)",
            data=st.session_state.generated_result,
            file_name=f"studysloth_{st.session_state.generated_type or 'notes'}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col_dl2:
        st.download_button(
            label="⬇️ Download Plain Text (.txt)",
            data=st.session_state.generated_result,
            file_name=f"studysloth_{st.session_state.generated_type or 'notes'}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with col_dl3:
        parsed_json_export = extract_json_block(st.session_state.generated_result)
        json_data = json.dumps(parsed_json_export, indent=2) if parsed_json_export else json.dumps({"content": st.session_state.generated_result}, indent=2)
        st.download_button(
            label="⬇️ Download JSON (Anki/Apps)",
            data=json_data,
            file_name=f"studysloth_{st.session_state.generated_type or 'notes'}.json",
            mime="application/json",
            use_container_width=True,
        )
    with col_dl4:
        with st.popover("📋 View Copyable Code"):
            st.code(st.session_state.generated_result, language="markdown")


# FOOTER
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #5C8354; font-size: 0.85rem; padding: 1.5rem 0;">
        🦥 <b>StudySloth AI</b> • Built with Python, Streamlit, and Ollama.<br>
        <i>100% Open Source • 100% Local Inference • Zero Data Tracking</i>
    </div>
    """,
    unsafe_allow_html=True,
)


import streamlit as st
import hashlib

from auth import (
    init_db,
    signup,
    login,
    get_user_id,
    create_chat,
    save_message,
    get_user_chats,
    get_chat_messages,
    rename_chat,
    delete_chat
)

from ollama_service import generate_response
from document_manager import process_pdf
from rag_service import answer_from_document


# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
init_db()


# ==================================================
# 2. SESSION STATE
# ==================================================

defaults = {
    "messages": [],
    "document": None,
    "document_hash": None,
    "dark_mode": False,
    "uploaded_name": None,
    "logged_in": False,
    "username": None,
    "user_id": None,
    "current_chat_id": None
}

for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ==================================================
# 3. THEME CONFIGURATION
# ==================================================

if st.session_state.dark_mode:

    bg = "#212121"
    sidebar = "#171717"
    text = "#F5F5F5"
    input_bg = "#303030"
    border = "#444444"
    muted = "#AAAAAA"

else:

    bg = "#FFFFFF"
    sidebar = "#F7F7F8"
    text = "#202123"
    input_bg = "#FFFFFF"
    border = "#E5E5E5"
    muted = "#666666"


st.markdown(f"""
<style>

.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"] {{
    background-color: {bg} !important;
    color: {text} !important;
}}

header[data-testid="stHeader"] {{
    background-color: {bg} !important;
}}

[data-testid="stSidebar"] {{
    background-color: {sidebar} !important;
}}

[data-testid="stSidebar"] * {{
    color: {text} !important;
}}

.stApp h1,
.stApp h2,
.stApp h3,
.stApp p,
.stApp label,
.stApp span {{
    color: {text};
}}

.stCaption,
small {{
    color: {muted} !important;
}}

[data-testid="stChatMessage"] {{
    background-color: {bg} !important;
    color: {text} !important;
}}

[data-testid="stBottom"],
[data-testid="stBottom"] > div {{
    background-color: {bg} !important;
}}

[data-testid="stChatInput"],
[data-testid="stChatInput"] > div {{
    background-color: {input_bg} !important;
    border: 1px solid {border} !important;
    border-radius: 14px !important;
}}

[data-testid="stChatInput"] textarea {{
    background-color: {input_bg} !important;
    color: {text} !important;
    -webkit-text-fill-color: {text} !important;
}}

.stButton button,
[data-testid="stPopover"] button {{
    background-color: {input_bg} !important;
    color: {text} !important;
    border: 1px solid {border} !important;
    border-radius: 10px !important;
}}

[data-testid="stFileUploader"] {{
    background-color: {input_bg} !important;
    color: {text} !important;
}}

hr {{
    border-color: {border} !important;
}}

</style>
""", unsafe_allow_html=True)


# ==================================================
# 4. LOGIN AND SIGNUP
# ==================================================

if not st.session_state.logged_in:

    st.markdown(
        "<h1 style='text-align:center;'>🤖 AI Assistant</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p style='text-align:center;color:gray;'>"
        "Login or create an account to continue"
        "</p>",
        unsafe_allow_html=True
    )

    left, center, right = st.columns([1, 1.5, 1])

    with center:

        login_tab, signup_tab = st.tabs(
            ["Login", "Sign Up"]
        )

        # LOGIN
        with login_tab:

            with st.form("login_form"):

                username = st.text_input("Username")

                password = st.text_input(
                    "Password",
                    type="password"
                )

                submitted = st.form_submit_button(
                    "Login",
                    use_container_width=True
                )

                if submitted:

                    if login(username, password):

                        clean_username = username.strip()

                        st.session_state.logged_in = True
                        st.session_state.username = clean_username

                        st.session_state.user_id = get_user_id(
                            clean_username
                        )

                        st.session_state.current_chat_id = None
                        st.session_state.messages = []

                        st.success("Login successful!")

                        st.rerun()

                    else:

                        st.error("Invalid username or password.")

        # SIGNUP
        with signup_tab:

            with st.form("signup_form"):

                new_username = st.text_input(
                    "Choose username"
                )

                new_password = st.text_input(
                    "Choose password",
                    type="password"
                )

                confirm_password = st.text_input(
                    "Confirm password",
                    type="password"
                )

                submitted = st.form_submit_button(
                    "Create Account",
                    use_container_width=True
                )

                if submitted:

                    if new_password != confirm_password:

                        st.error("Passwords do not match.")

                    elif len(new_password) < 8:

                        st.error(
                            "Password must contain at least 8 characters."
                        )

                    else:

                        success, message = signup(
                            new_username,
                            new_password
                        )

                        if success:

                            st.success(
                                "Account created! Please log in."
                            )

                        else:

                            st.error(message)

    # Stop chatbot before login
    st.stop()


# ==================================================
# 5. SIDEBAR
# ==================================================

with st.sidebar:

    st.title("🤖 AI Assistant")

    st.write(
        f"Welcome, {st.session_state.username}!"
    )

    # ------------------------------------------------
    # NEW CHAT
    # ------------------------------------------------

    if st.button(
        "＋ New Chat",
        use_container_width=True
    ):

        st.session_state.messages = []
        st.session_state.current_chat_id = None

        st.rerun()

    st.divider()

    # ------------------------------------------------
    # PREVIOUS CONVERSATIONS
    # ------------------------------------------------

    st.subheader("Your Conversations")

    chats = get_user_chats(
        st.session_state.user_id
    )

    if chats:

        for chat_id, title, created_at in chats:

            display_title = title or "New Chat"

            if len(display_title) > 30:

                display_title = display_title[:30] + "..."

            is_current = (
                chat_id == st.session_state.current_chat_id
            )

            button_label = (
                f"● {display_title}"
                if is_current
                else f"💬 {display_title}"
            )

            # SELECT CHAT
            if st.button(
                button_label,
                key=f"chat_{chat_id}",
                use_container_width=True
            ):

                st.session_state.current_chat_id = chat_id

                st.session_state.messages = get_chat_messages(
                    chat_id,
                    st.session_state.user_id
                )

                st.rerun()

            # RENAME AND DELETE OPTIONS
            with st.expander("⚙️ Chat options"):

                # RENAME CHAT
                new_title = st.text_input(
                    "New conversation title",
                    value=title or "New Chat",
                    key=f"rename_input_{chat_id}"
                )

                if st.button(
                    "✏️ Rename Chat",
                    key=f"rename_button_{chat_id}",
                    use_container_width=True
                ):

                    if not new_title.strip():

                        st.error("Title cannot be empty.")

                    elif rename_chat(
                        chat_id,
                        st.session_state.user_id,
                        new_title
                    ):

                        st.success(
                            "Chat renamed successfully!"
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Could not rename this conversation."
                        )

                st.divider()

                # DELETE CHAT
                if st.button(
                    "🗑️ Delete Chat",
                    key=f"delete_button_{chat_id}",
                    use_container_width=True
                ):

                    deleted = delete_chat(
                        chat_id,
                        st.session_state.user_id
                    )

                    if deleted:

                        # Clear active chat if deleted
                        if chat_id == st.session_state.current_chat_id:

                            st.session_state.current_chat_id = None
                            st.session_state.messages = []

                        st.success(
                            "Chat deleted successfully!"
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Could not delete this conversation."
                        )

    else:

        st.caption("No previous conversations yet.")

    st.divider()

    # ------------------------------------------------
    # SETTINGS
    # ------------------------------------------------

    st.subheader("Settings")

    # DARK / LIGHT MODE
    if st.button(
        "☀️ Light Mode" if st.session_state.dark_mode
        else "🌙 Dark Mode",
        use_container_width=True
    ):

        st.session_state.dark_mode = not st.session_state.dark_mode

        st.rerun()

    st.divider()

    # ------------------------------------------------
    # PDF STATUS
    # ------------------------------------------------

    if st.session_state.document:

        st.success(
            f"PDF: {st.session_state.uploaded_name}"
        )

        if st.button(
            "Remove PDF",
            use_container_width=True
        ):

            st.session_state.document = None
            st.session_state.document_hash = None
            st.session_state.uploaded_name = None

            st.rerun()

    st.divider()

    # ------------------------------------------------
    # LOGOUT
    # ------------------------------------------------

    if st.button(
        "Logout",
        use_container_width=True
    ):

        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.user_id = None
        st.session_state.current_chat_id = None
        st.session_state.messages = []

        st.session_state.document = None
        st.session_state.document_hash = None
        st.session_state.uploaded_name = None

        st.rerun()

    st.caption("Powered by Python + Ollama")


# ==================================================
# 6. MAIN CHAT INTERFACE
# ==================================================

st.markdown(
    "<h2 style='text-align:center;'>AI Assistant</h2>",
    unsafe_allow_html=True
)

st.markdown(
    "<p style='text-align:center;color:gray;'>"
    "Your intelligent companion for learning, "
    "coding and everyday tasks."
    "</p>",
    unsafe_allow_html=True
)


# ==================================================
# 7. DISPLAY CHAT HISTORY
# ==================================================

if not st.session_state.messages:

    st.markdown(
        "<h3 style='text-align:center;margin-top:100px;'>"
        "How can I help you today?"
        "</h3>",
        unsafe_allow_html=True
    )

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])


# ==================================================
# 8. PDF UPLOAD
# ==================================================

with st.popover("＋"):

    st.markdown("### Upload a PDF")

    uploaded_pdf = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        key="pdf_uploader"
    )

    if uploaded_pdf is not None:

        pdf_bytes = uploaded_pdf.getvalue()

        current_hash = hashlib.sha256(
            pdf_bytes
        ).hexdigest()

        if current_hash != st.session_state.document_hash:

            with st.spinner("Processing your PDF..."):

                try:

                    uploaded_pdf.seek(0)

                    document = process_pdf(uploaded_pdf)

                    st.session_state.document = document
                    st.session_state.document_hash = current_hash
                    st.session_state.uploaded_name = uploaded_pdf.name

                    st.success("PDF uploaded successfully!")

                except Exception as error:

                    st.error(
                        f"PDF processing failed: {error}"
                    )


# ==================================================
# 9. CHAT INPUT
# ==================================================

prompt = st.chat_input(
    "Message AI Assistant..."
)


# ==================================================
# 10. SAVE USER MESSAGE AND GENERATE AI RESPONSE
# ==================================================

if prompt:

    # CREATE DATABASE CHAT IF NEEDED
    if st.session_state.current_chat_id is None:

        chat_title = prompt.strip()

        if len(chat_title) > 40:

            chat_title = chat_title[:40] + "..."

        st.session_state.current_chat_id = create_chat(
            st.session_state.user_id,
            chat_title
        )

    current_chat_id = st.session_state.current_chat_id

    # ADD USER MESSAGE TO SESSION
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    # SAVE USER MESSAGE TO SQLITE
    save_message(
        current_chat_id,
        "user",
        prompt
    )

    try:

        with st.spinner("AI is thinking..."):

            # PDF QUESTION ANSWERING
            if st.session_state.document:

                document = st.session_state.document

                answer = answer_from_document(
                    prompt,
                    document["chunks"],
                    document["embeddings"]
                )

            # GENERAL AI CHAT
            else:

                # Use previous 10 messages as context
                history = st.session_state.messages[:-1][-10:]

                answer = generate_response(
                    prompt,
                    history
                )

    except Exception as error:

        answer = f"Something went wrong: {error}"

    # ADD AI RESPONSE TO SESSION
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

    # SAVE AI RESPONSE TO SQLITE
    save_message(
        current_chat_id,
        "assistant",
        answer
    )

    # REFRESH APPLICATION
    st.rerun()

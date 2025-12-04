import streamlit as st
import os
import uuid
from src.config import Config
from src.ingestion import IngestionManager
from src.extractor import PrescriptionExtractor
from src.vector_store import VectorStoreManager
from src.graph import RAGGraph
from src.memory import MemoryManager
from src.auth import AuthManager
from src.utils import setup_logger
from src.calendar_utils import CalendarManager
import datetime

logger = setup_logger(__name__)

# Page Config
st.set_page_config(page_title="Medical Prescription RAG", layout="wide")

# Initialize Auth
if 'auth' not in st.session_state:
    st.session_state.auth = AuthManager()
if 'user' not in st.session_state:
    st.session_state.user = None

# --- Login / Register Page ---
if not st.session_state.user:
    st.title("Medi-Buddy- Login")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            success, msg = st.session_state.auth.login_user(username, password)
            if success:
                st.session_state.user = username
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
                
    with tab2:
        new_user = st.text_input("Username", key="reg_user")    
        new_pass = st.text_input("Password", type="password", key="reg_pass")
        if st.button("Register"):
            success, msg = st.session_state.auth.register_user(new_user, new_pass)
            if success:
                st.success(msg)
            else:
                st.error(msg)
    
    st.stop() # Stop execution if not logged in

# --- Main App (Only accessible after login) ---

# Initialize Managers
if 'extractor' not in st.session_state:
    st.session_state.extractor = PrescriptionExtractor()
if 'vector_store' not in st.session_state:
    st.session_state.vector_store = VectorStoreManager()
if 'rag_graph' not in st.session_state:
    st.session_state.rag_graph = RAGGraph().build_graph()
if 'memory' not in st.session_state:
    st.session_state.memory = MemoryManager()
if 'calendar_manager' not in st.session_state:
    st.session_state.calendar_manager = CalendarManager()

# Session State for Chat
if 'uploaded_files_map' not in st.session_state:
    st.session_state.uploaded_files_map = {} # ID -> Filename

# Sidebar
with st.sidebar:
    st.write(f"Logged in as: **{st.session_state.user}**")
    if st.button("Logout"):
        st.session_state.user = None
        st.rerun()
        
    st.divider()
    st.title("Prescription RAG")
    
    # File Upload
    uploaded_file = st.file_uploader("Upload Prescription (PDF/Image)", type=['pdf', 'png', 'jpg', 'jpeg'])
    
    if uploaded_file:
        # Check if this file has already been uploaded by this user
        existing_p_id = st.session_state.memory.get_prescription_by_filename(st.session_state.user, uploaded_file.name)
        
        if existing_p_id:
            if st.session_state.get('current_view') != existing_p_id:
                st.info(f"File '{uploaded_file.name}' already uploaded. Switching to existing chat.")
                st.session_state.current_view = existing_p_id
                st.rerun()
            # If already viewing this file, do nothing (prevent infinite loop)
        else:
            file_id = str(uuid.uuid4())
            # Save file temporarily
            from src.utils import ensure_directory
            ensure_directory(Config.INPUT_DIR)
            
            file_path = os.path.join(Config.INPUT_DIR, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Process only if not already in session map (double check)
            if file_path not in st.session_state.uploaded_files_map.values():
                with st.spinner("Processing Prescription..."):
                    # 1. Extract Data
                    data = st.session_state.extractor.extract_data(file_path)
                    
                    if data:
                        st.success("Extraction Complete!")
                        # st.json(data) # Removed as per request  
                        
                        # 2. Vectorize
                        # Create chunks from the extracted JSON/Text
                        # Format the medicine details nicely for the LLM context
                        med_details = []
                        for med in data.get('medicines', []):
                            timing = med.get('timing', {})
                            timing_str = f"Morning: {timing.get('morning')}, Afternoon: {timing.get('afternoon')}, Night: {timing.get('night')}, Instruction: {timing.get('instruction')}"
                            med_details.append(f"- {med.get('name')} (Qty: {med.get('quantity')}): {timing_str}, Freq: {med.get('frequency')}, Duration: {med.get('duration')}")
                        
                        meds_str = "\n".join(med_details)
                        text_content = f"Date: {data.get('date')}\n\nMedicines:\n{meds_str}\n\nNotes: {data.get('notes')}"
                        
                        # Store in Pinecone
                        metadata = {"filename": uploaded_file.name}
                        st.session_state.vector_store.add_prescription(file_id, [text_content], metadata)
                        
                        st.session_state.uploaded_files_map[file_id] = uploaded_file.name
                        
                        # Initialize session for this upload immediately with a descriptive title
                        # Generate Title from Medicines
                        med_names = [m.get('name', 'Unknown') for m in data.get('medicines', [])]
                        if med_names:
                            title = f"Prescription: {', '.join(med_names[:2])}" # First 2 meds
                            if len(med_names) > 2:
                                title += "..."
                        else:
                            title = f"Prescription {uploaded_file.name}"
                        
                        # Pass filename to store it for future checks
                        # Also pass meds_str as details
                        st.session_state.memory.get_or_create_session(st.session_state.user, file_id, title=title, filename=uploaded_file.name, details=meds_str)
                        
                        st.success("Indexed in Vector DB!")
                        # Auto-switch to this new chat
                        st.session_state.current_view = file_id
                        st.rerun()
                    else:
                        st.error("Failed to extract data.")

    st.divider()
    
    # --- Chat History Sidebar ---
    st.subheader("Your Chats")
    
    # 2. Fetch User's Prescriptions from DB
    user_prescriptions = st.session_state.memory.get_user_prescriptions(st.session_state.user)
    
    if not user_prescriptions:
        st.info("No prescription chats yet.")
    
    for p_data in user_prescriptions:
        p_id = p_data['id']
        p_title = p_data['title']
        
        # Button for each prescription
        if st.button(f"📄 {p_title}", key=p_id, use_container_width=True):
            st.session_state.current_view = p_id
            st.rerun()

    # Determine Active View
    if 'current_view' not in st.session_state:
        st.session_state.current_view = None
    
    # Language Selector
    st.divider()
    st.subheader("Settings")
    language = st.selectbox("Select Language", ["English", "Hindi", "Tamil", "Kannada", "Malayalam", "Telugu"])
    st.session_state.language = language

    if st.session_state.current_view is None:
        st.title("Welcome to Prescription RAG")
        st.info("Please upload a prescription or select a chat from the sidebar to begin.")
        st.stop()
    else:
        selected_prescription_id = st.session_state.current_view
        # Fetch title for header
        current_title = next((p['title'] for p in user_prescriptions if p['id'] == selected_prescription_id), "Unknown Prescription")
        
        st.session_state.session_id = st.session_state.memory.get_or_create_session(st.session_state.user, selected_prescription_id)
        header_text = f"Chat: {current_title}"
        
        # Fetch details (medicine summary)
        details_text = st.session_state.memory.get_session_details(st.session_state.session_id)


# Chat Interface
st.header(header_text)
if details_text:
    with st.expander("💊 Medicine Details", expanded=True):
        st.markdown(details_text)
        
        if st.button("📅 Add to Google Calendar"):
            # Simple implementation: Add a reminder for tomorrow morning
            # In a real app, we would parse the exact medicines and timings
            if st.session_state.calendar_manager.authenticate():
                tomorrow_morning = (datetime.datetime.utcnow() + datetime.timedelta(days=1)).replace(hour=9, minute=0, second=0).isoformat()
                link = st.session_state.calendar_manager.create_event(
                    summary=f"Take Medicines: {current_title}",
                    start_time_iso=tomorrow_morning,
                    description=details_text
                )
                if link:
                    st.success(f"Event created! [View Event]({link})")
                else:
                    st.error("Failed to create event.")
            else:
                st.error("Authentication failed. Please check credentials.json.")

# Display History
# Always fetch fresh history for the CURRENT session_id
history = st.session_state.memory.get_history(st.session_state.session_id)
st.session_state.messages = [{"role": msg['role'], "content": msg['content']} for msg in history]
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
if prompt := st.chat_input("Ask about prescriptions..."):
    # Add user message to state
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Run Graph
    with st.spinner("Thinking..."):
        inputs = {
            "question": prompt,
            "prescription_id": selected_prescription_id, # None for Global
            "session_id": st.session_state.session_id,
            "language": st.session_state.get("language", "English"), # Pass language
            "context": [],
            "answer": ""
        }
        
        result = st.session_state.rag_graph.invoke(inputs)
        answer = result["answer"]
        
        # Add AI message to state
        st.session_state.messages.append({"role": "ai", "content": answer})
        with st.chat_message("ai"):
            st.markdown(answer)

import streamlit as st
import os
import uuid
from dotenv import load_dotenv
from google import genai
from db_manager import verify_officer_login, log_change
from email_handler import send_final_email 

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("FATAL ERROR: GEMINI_API_KEY not found. Check your .env file.")

def generate_report_id():
    return str(uuid.uuid4())[:8].upper()

def handle_login():
    st.title(" Officer Assistant Login")
    badge = st.text_input("Badge Number")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if badge and password:
            authenticated, name, email = verify_officer_login(badge, password)
            if authenticated:
                st.session_state['logged_in'] = True
                st.session_state['badge'] = badge
                st.session_state['full_name'] = name
                st.session_state['email'] = email
                st.success(f"Welcome, Officer {name}!")
                st.rerun()
            else:
                st.error("Invalid Badge Number or Password.")
        else:
            st.warning("Please enter both credentials.")

def generate_report_draft(uploaded_files, prompt_text):
    st.info("Sending files and prompt to Gemini... This may take a minute for video.")
    gemini_files = []
    
    for file in uploaded_files:
        temp_file_path = f"/tmp/{file.name}"
        with open(temp_file_path, "wb") as f:
            f.write(file.getbuffer())
        
        gemini_file = genai.upload_file(path=temp_file_path)
        gemini_files.append(gemini_file)
        os.remove(temp_file_path)

    full_prompt = [prompt_text] + gemini_files
    
    try:
        response = model.generate_content(full_prompt)
        for f in gemini_files:
             genai.delete_file(name=f.name)
        return response.text
    except Exception as e:
        st.error(f"AI Generation Error: {e}")
        return None

def main_application():
    st.sidebar.header(" Officer: " + st.session_state.get('full_name', 'N/A'))
    st.sidebar.markdown(f"**Badge:** {st.session_state.get('badge', 'N/A')}")
    st.title(" Incident Report Draft Writer")

    if 'report_id' not in st.session_state:
        st.session_state['report_id'] = generate_report_id()
        st.session_state['draft_generated'] = False
        st.session_state['current_draft'] = ""

    st.subheader(f"Report ID: {st.session_state['report_id']}")
    st.markdown("### Upload Evidence (Audio, Video, Images)")
    uploaded_files = st.file_uploader("Select Evidence Files", type=['mp4', 'mov', 'jpg', 'png', 'mp3', 'wav'], accept_multiple_files=True)
    
    if st.button("1. Generate Initial Draft") and uploaded_files:
        with st.spinner('Analyzing evidence and generating report draft...'):
            initial_prompt = f"""
            You are an AI assistant for a Police Officer. The reporting officer is {st.session_state['full_name']} 
            with Badge Number {st.session_state['badge']}. Your task is to listen to the audio, transcribe the 
            spoken words, analyze the images/video, and synthesize ALL attached evidence into a formal Police Incident Report.
            
            The report MUST contain these sections:
            1. Officer's Name and Badge Number
            2. Incident Summary
            3. Timeline of Events
            4. Key Evidence Description (from photos/video)
            5. Actions Taken
            
            Maintain a professional, objective, and factual tone.
            """
            draft = generate_report_draft(uploaded_files, initial_prompt)
            
            if draft:
                st.session_state['current_draft'] = draft
                st.session_state['draft_generated'] = True
                log_change(st.session_state['report_id'], st.session_state['badge'], "Initial AI Draft", draft)
                st.success("Draft Generated and Logged.")
                st.rerun()

    if st.session_state['draft_generated']:
        st.markdown("---")
        st.subheader("2. Review and Edit Report Draft")
        
        new_draft_text = st.text_area("Report Text (Edit Manually Below):", value=st.session_state['current_draft'], height=500, key="report_editor")
        
        if new_draft_text != st.session_state['current_draft']:
            st.session_state['current_draft'] = new_draft_text
            log_change(st.session_state['report_id'], st.session_state['badge'], "Manual Text Edit", "Changes saved manually.")

        st.markdown("#### Audio Corrections (Speak your edits)")
        correction_audio = st.file_uploader("Upload Audio Correction (.mp3, .wav)", type=['mp3', 'wav'])

        if correction_audio and st.button("Apply Audio Correction"):
            with st.spinner('Applying audio corrections...'):
                audio_correction_prompt = f"""
                Here is the current report draft: {st.session_state['current_draft']}.
                Listen to the attached audio file. This audio contains instructions for corrections or additions.
                Please integrate the new information into the appropriate sections of the report. 
                Return ONLY the revised, complete report text.
                """
                
                revised_draft = generate_report_draft([correction_audio], audio_correction_prompt)
                
                if revised_draft:
                    st.session_state['current_draft'] = revised_draft
                    log_change(st.session_state['report_id'], st.session_state['badge'], "Audio Correction Applied", f"Correction audio: {correction_audio.name}")
                    st.success("Audio correction applied successfully.")
                    st.rerun()

        st.markdown("---")
        if st.button("3. Affirm & Finalize Report", help="This saves the report and sends the email."):
            final_log_id = log_change(st.session_state['report_id'], st.session_state['badge'], "Final Affirmation", st.session_state['current_draft'])
            
            send_final_email(st.session_state['email'], st.session_state['full_name'], st.session_state['report_id'], st.session_state['current_draft'], final_log_id)

            st.balloons()
            st.success(f"Report {st.session_state['report_id']} FINALIZED and emailed to {st.session_state['email']}!")
            st.session_state.clear()
            st.rerun()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if st.session_state['logged_in']:
    main_application()
else:
    handle_login()

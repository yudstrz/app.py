import streamlit as st
import os
import re
import time
from supabase import create_client, Client

# =====================================================================
# SUPABASE CONFIG
# =====================================================================
SUPABASE_URL = "https://gmsizfioshudejqqapwr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdtc2l6Zmlvc2h1ZGVqcXFhcHdyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc5MTY4NjMsImV4cCI6MjA3MzQ5Mjg2M30.VaXNBtnxUmu__-_sKMuEZvJmJPoWk-pf_MD1gVoNlH4"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================================================================
# CONFIGURATION
# =====================================================================
QUESTIONS_LIST = [
    ("RASE", "Read this text and pronounce it clearly", 
     "The rapid advancement of technology has transformed the way we communicate with each other."),
    ("RASH", "Read this text and pronounce it clearly", 
     "With a tear in your eye, you will watch as your dress begins to tear."),
    ("RAL", "Read this text and pronounce it clearly", 
     "You don't need to spend all of your hard earned money on bakery bread. Making your own bread at home is easy with the new Double Duty Dough Mixer by Berring. Unlike other bread machines that can be difficult to clean and store, the Double Duty Dough Mixer breaks down into five parts that can go directly into your dishwasher. This stainless steel appliance will mix dough for you in a fraction of the time it takes to knead dough by hand. The automated delay feature at the beginning of the mix cycle gives your ingredients time to reach room temperature, ensuring that your breads will rise as high as bakery bread. We guarantee that the accompanying Berring Best Breads recipe book will be a family favourite."),
    ("DP", "Describe this picture using complete sentences and clear descriptions. Explain who is in the picture, what is happening, and the overall atmosphere."),
    ("FSDL","From this statement, try to express your opinion", 
     "Should people be responsible for what happens because of what they say? Explain with an example."),
    ("FSST","From this statement, try to express your opinion", 
     "Talk about the university course you enjoyed the most, describe one course you found difficult, and explain whether universities should focus more on practical skills or theoretical knowledge.")
]

# =====================================================================
# SESSION STATE
# =====================================================================
if 'current_question_index' not in st.session_state:
    st.session_state.current_question_index = 0
if 'participant_name' not in st.session_state:
    st.session_state.participant_name = ""
if 'audio_uploaded' not in st.session_state:
    st.session_state.audio_uploaded = {}

# =====================================================================
# PARTICIPANT FORM
# =====================================================================
st.title("Participant Data Form")

with st.form("participant_form"):
    name = st.text_input("Name")
    gender = st.selectbox("Gender", ["Male", "Female"])
    program_study = st.text_input("Program Study")
    city = st.text_input("City")
    age = st.number_input("Age", min_value=0, max_value=120, step=1)
    current_residence = st.text_input("Current Residence")
    campus = st.text_input("Campus")
    test_type = st.selectbox("Test Type", ["TOEFL", "IELTS", "Duolingo", "Other", "Never Taken"])
    test_score = st.number_input("Test Score", value=0, disabled=(test_type=="Never Taken"))
    perception = st.selectbox("Perception", ["Basic", "Intermediate", "Advanced"])
    submitted = st.form_submit_button("✅ Proceed to Recording Session")

if submitted:
    # Validasi input
    if not name.strip():
        st.error("Please enter your name!")
    else:
        # Simpan data ke Supabase
        data = {
            "name": name.strip(),
            "gender": gender,
            "program_study": program_study,
            "city": city,
            "age": age,
            "current_residence": current_residence,
            "campus": campus,
            "test_type": test_type,
            "test_score": test_score if test_type != "Never Taken" else 0,
            "perception": perception
        }
        try:
            result = supabase.table("participants").insert(data).execute()
            if result.data:
                st.success(f"Data for {name} saved successfully to Supabase!")
                st.session_state.participant_name = name.strip()
                st.rerun()  # Refresh untuk show recording session
            else:
                st.error("Failed to save data. Please try again.")
        except Exception as e:
            st.error(f"Failed to insert data: {str(e)}")
            st.info("Please check your internet connection and try again.")

# =====================================================================
# RECORDING SESSION
# =====================================================================
if st.session_state.participant_name:
    st.header("Voice Recording Session")
    st.write(f"**Participant:** {st.session_state.participant_name}")
    
    q_index = st.session_state.current_question_index
    
    if q_index < len(QUESTIONS_LIST):
        q = QUESTIONS_LIST[q_index]
        q_name = q[0]
        q_instruction = q[1]
        q_text = q[2] if len(q) > 2 else ""
        
        st.subheader(f"Question {q_index+1} of {len(QUESTIONS_LIST)}: {q_name}")
        st.markdown(f"**Instruction:** {q_instruction}")
        if q_text:
            st.markdown(f"**Text:** {q_text}")
        if q_name == "DP":
            # Cek apakah file gambar ada
            image_path = "image/describe.jpg"
            if os.path.exists(image_path):
                st.image(image_path, use_column_width=True)
            else:
                st.warning("⚠️ Image file not found. Please make sure 'image/describe.jpg' exists.")
        
        st.info("💡 On mobile, tap 'Upload' and select 'Record audio' to use your device's recorder.")
        
        uploaded_file = st.file_uploader(
            f"Upload or record your audio for {q_name}", 
            type=["wav", "mp3", "m4a", "aac", "ogg", "amr", "webm"],
            key=f"uploader_{q_index}"
        )
        
        if uploaded_file is not None:
            # Nama file aman dengan timestamp untuk avoid duplicates
            safe_name = re.sub(r"[^\w\-_.]", "_", st.session_state.participant_name)
            filename = re.sub(r"[^\w\-_.]", "_", uploaded_file.name)
            timestamp = int(time.time())
            file_name = f"{safe_name}_{q_name}_{timestamp}_{filename}"
            
            try:
                # Convert uploaded file ke bytes yang proper
                file_bytes = uploaded_file.read()
                
                # Reset file pointer untuk bisa dibaca lagi kalau perlu
                uploaded_file.seek(0)
                
                # Upload ke Supabase Storage bucket "audio"
                with st.spinner("Uploading audio..."):
                    response = supabase.storage().from_("audio").upload(file_name, file_bytes)
                
                # Check if upload successful
                if hasattr(response, 'error') and response.error:
                    st.error(f"Upload failed: {response.error}")
                else:
                    # Ambil URL public untuk playback
                    audio_url = supabase.storage().from_("audio").get_public_url(file_name)
                    st.session_state.audio_uploaded[q_name] = audio_url
                    
                    st.success(f"✅ Audio for {q_name} saved to Supabase Storage!")
                    st.audio(uploaded_file)  # Play dari uploaded_file langsung
                    
                    # Show next button after successful upload
                    if st.button("➡️ Next Question", key=f"next_{q_index}"):
                        st.session_state.current_question_index += 1
                        st.rerun()
                        
            except Exception as e:
                st.error(f"Failed to upload audio: {str(e)}")
                st.info("💡 Try using a different audio format (WAV or MP3 recommended)")
        
        # Progress bar
        progress = (q_index + 1) / len(QUESTIONS_LIST)
        st.progress(progress)
        st.write(f"Progress: {q_index + 1}/{len(QUESTIONS_LIST)} questions")

    else:
        st.success("🎉 All questions recorded. Session completed!")
        st.balloons()
        
        if st.session_state.audio_uploaded:
            st.write("**Uploaded files:**")
            for q_name, url in st.session_state.audio_uploaded.items():
                with st.expander(f"🎵 {q_name} Audio"):
                    st.write(f"File URL: {url}")
                    st.audio(url)
        
        # Reset button untuk participant baru
        if st.button("🔄 Start New Session"):
            # Reset semua session state
            st.session_state.current_question_index = 0
            st.session_state.participant_name = ""
            st.session_state.audio_uploaded = {}
            st.rerun()

# =====================================================================
# FOOTER
# =====================================================================
st.markdown("---")
st.markdown("*Voice Recording App - Powered by Streamlit & Supabase*")

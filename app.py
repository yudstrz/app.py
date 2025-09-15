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
    # simpan data ke Supabase
    data = {
        "name": name,
        "gender": gender,
        "program_study": program_study,
        "city": city,
        "age": age,
        "current_residence": current_residence,
        "campus": campus,
        "test_type": test_type,
        "test_score": test_score,
        "perception": perception
    }
    try:
        supabase.table("participants").insert(data).execute()
        st.success(f"Data for {name} saved successfully to Supabase!")
        st.session_state.participant_name = name
    except Exception as e:
        st.error(f"Failed to insert data: {e}")

# =====================================================================
# RECORDING SESSION
# =====================================================================
if st.session_state.participant_name:
    st.header("Voice Recording Session")
    
    q_index = st.session_state.current_question_index
    
    if q_index < len(QUESTIONS_LIST):
        q = QUESTIONS_LIST[q_index]
        q_name = q[0]
        q_instruction = q[1]
        q_text = q[2] if len(q) > 2 else ""
        
        st.subheader(f"Question {q_index+1}: {q_name}")
        st.markdown(f"**Instruction:** {q_instruction}")
        if q_text:
            st.markdown(f"**Text:** {q_text}")
        if q_name == "DP":
            st.image("image/describe.jpg", use_column_width=True)
        
        st.info("💡 On mobile, tap 'Upload' and select 'Record audio' to use your device's recorder.")
        
        uploaded_file = st.file_uploader(
            f"Upload or record your audio for {q_name}", 
            type=["wav", "mp3", "m4a", "aac", "ogg", "amr"],
            key=f"uploader_{q_index}"
        )
        
        if uploaded_file is not None:
            # nama file aman dengan timestamp untuk avoid duplicates
            safe_name = re.sub(r"[^\w\-_.]", "_", st.session_state.participant_name)
            filename = re.sub(r"[^\w\-_.]", "_", uploaded_file.name)
            timestamp = int(time.time())
            file_name = f"{safe_name}_{q_name}_{timestamp}_{filename}"
            
            try:
                # Convert uploaded file ke bytes
                file_bytes = uploaded_file.read()
                uploaded_file.seek(0)
                
                # Upload ke Supabase Storage
                supabase.storage.from_("audio").upload(file_name, file_bytes)
                
                # Get public URL
                audio_url = supabase.storage.from_("audio").get_public_url(file_name)
                st.session_state.audio_uploaded[q_name] = audio_url
                
                st.success(f"✅ Audio for {q_name} saved to Supabase Storage!")
                st.audio(uploaded_file)
                
            except Exception as e:
                st.error(f"Upload failed: {str(e)}")
                
                # Show specific error dan solusi
                error_msg = str(e).lower()
                if "403" in error_msg or "unauthorized" in error_msg or "rls" in error_msg:
                    st.error("🔒 **Storage Permission Issue**")
                    st.markdown("""
                    **Fix di Supabase Dashboard:**
                    1. Go to **Storage** → **Buckets**
                    2. Click bucket **"audio"** (create if missing)
                    3. Set as **Public bucket** ✅
                    4. Or add **RLS Policy**: Allow INSERT/SELECT for authenticated users
                    
                    **Quick RLS Policy:**
                    ```sql
                    INSERT: (auth.role() = 'anon')
                    SELECT: (auth.role() = 'anon')
                    ```
                    """)
                else:
                    st.info("💡 Try different audio format or check file size")
        
        if st.button("➡️ Next Question", key=f"next_{q_index}"):
            st.session_state.current_question_index += 1
            st.rerun()  # Force rerun untuk update UI

    else:
        st.success("🎉 All questions recorded. Session completed!")
        st.write("Uploaded files:")
        for q_name, url in st.session_state.audio_uploaded.items():
            st.write(f"- {q_name}: {url}")
            st.audio(url)

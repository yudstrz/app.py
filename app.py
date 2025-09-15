import streamlit as st
import openpyxl
import os

# =====================================================================
# CONFIGURATION
# =====================================================================
EXCEL_FILE = "participant_data.xlsx"
EXCEL_HEADER = ["Name", "Gender", "Program study", "City", "Age", 
                "Current Residence", "Campus", "Test Type", 
                "Test Score", "Perception"]

RECORDINGS_FOLDER = "i_speak_recordings"

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
# CREATE FOLDER IF NOT EXIST
# =====================================================================
os.makedirs(RECORDINGS_FOLDER, exist_ok=True)

# =====================================================================
# CREATE EXCEL FILE IF NOT EXIST
# =====================================================================
if not os.path.exists(EXCEL_FILE):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(EXCEL_HEADER)
    workbook.save(EXCEL_FILE)

# Load workbook
workbook = openpyxl.load_workbook(EXCEL_FILE)
sheet = workbook.active

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
    program = st.text_input("Program Study")
    city = st.text_input("City")
    age = st.number_input("Age", min_value=0, max_value=120, step=1)
    residence = st.text_input("Current Residence")
    campus = st.text_input("Campus")
    test_type = st.selectbox("Test Type", ["TOEFL", "IELTS", "Duolingo", "Other", "Never Taken"])
    test_score = st.number_input("Test Score", value=0, disabled=(test_type=="Never Taken"))
    perception = st.selectbox("Perception", ["Basic", "Intermediate", "Advanced"])
    submitted = st.form_submit_button("✅ Proceed to Recording Session")

if submitted:
    # Append data ke Excel
    sheet.append([name, gender, program, city, age, residence, campus, test_type, test_score, perception])
    workbook.save(EXCEL_FILE)
    st.success(f"Data for {name} saved successfully!")
    st.session_state.participant_name = name

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
        
        # Upload audio
        uploaded_file = st.file_uploader(
            f"Upload or record your audio for {q_name}", 
            type=["wav", "mp3", "m4a", "aac", "ogg", "amr"],
            key=f"uploader_{q_index}"
        )
        
        if uploaded_file is not None:
            save_path = os.path.join(
                RECORDINGS_FOLDER, 
                f"{st.session_state.participant_name}_{q_name}_{uploaded_file.name}"
            )
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.session_state.audio_uploaded[q_name] = save_path
            
            st.success(f"✅ Audio for {q_name} saved!")
            st.audio(save_path)
        
        # Tombol Next
        if st.button("➡️ Next Question", key=f"next_{q_index}"):
            st.session_state.current_question_index += 1

    else:
        st.success("🎉 All questions recorded. Session completed!")
        st.write("Uploaded files:")
        for q_name, path in st.session_state.audio_uploaded.items():
            st.write(f"- {q_name}: {path}")

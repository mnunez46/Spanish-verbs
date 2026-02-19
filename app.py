import streamlit as st
import random
from google import genai
from google.genai import types# <--- MAKE SURE THIS LINE IS PRESENT

client = genai.Client(
    api_key=st.secrets["API_KEY"],
    http_options={'api_version': 'v1'}
)
# Initialize our usage trackers
if 'total_cost' not in st.session_state:
    st.session_state.total_cost = 0.0
if 'exercise_count' not in st.session_state:
    st.session_state.exercise_count = 0
# Simple Password Protection
def check_password():
    if "password_correct" not in st.session_state:
        # First run, show the input for password
        st.text_input("Enter Student Access Code", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Password was wrong, show input again
        st.text_input("Enter Student Access Code", type="password", on_change=password_entered, key="password")
        st.error("😕 Access code incorrect.")
        return False
    else:
        # Password was correct
        return True

def password_entered():
    # Change 'Spanish101' to whatever password you want to give students
    if st.session_state["password"] == "Buena Vista":
        st.session_state["password_correct"] = True
        del st.session_state["password"]  # don't store password
    else:
        st.session_state["password_correct"] = False

if not check_password():
    st.stop()  # Stop right here if password isn't correct
# --- CONFIG & AI SETUP ---
st.set_page_config(page_title="Spanish Verb Master", layout="wide")

# PASTE YOUR KEY HERE
API_KEY = "AIzaSyAxD8OW8FlXvv8Y3neC1H1aLuZgEbkaZys"

client = genai.Client(
    api_key=st.secrets["API_KEY"]
)


# Custom CSS for Senior-Friendly UI
st.markdown("""
    <style>
    .big-font { font-size:24px !important; font-weight: bold; }
    .stButton>button { width: 100%; height: 3em; font-size: 18px; background-color: #f0f2f6; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎓 Spanish Verb Practice (Latin America)")

# --- SIDEBAR ---
with st.sidebar:
    st.header("1. Verb Types")
    verb_types = st.multiselect("Include:", 
        ["Regular -AR", "Regular -ER", "Regular -IR", "Pronominal", "Irregular"],
        default=["Regular -AR"])
    manual_verb = st.text_input("Force a specific verb (Optional):")

    st.header("2. Tenses")
    tenses = {
        "Presente": "hablo", "Pretérito Indefinido": "hablé", 
        "Pretérito Imperfecto": "hablaba", "Futuro": "hablaré",
        "Presente de Subjuntivo": "hable", "Condicional": "hablaría"
    }
    selected_tenses = [t for t, ex in tenses.items() if st.checkbox(f"{t} ({ex})")]
# This creates the variable 'selected_verb'
    selected_verb = st.text_input("Enter a Spanish verb (e.g., Hablar):", value="Hablar")
# --- AI LOGIC ---
if st.button("✨ Generate New Exercise"):
    # Safety Check: Did they pick at least one tense?
    if not selected_tenses:
        st.warning("Please select at least one tense above! ⬆️")
        st.stop()

    # Convert the list [Present, Past] into a string "Present, Past"
    tenses_string = ", ".join(selected_tenses)

    # Use 'tenses_string' instead of 'selected_tense'
    prompt = f"Generate a Spanish verb exercise for the verb '{selected_verb}' using these tenses: {tenses_string}."

    try:
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        # ... rest of your code ...
    except Exception as e:
        st.error(f"Google API Error: {e}")
        st.stop()
    
    # ... then your AI logic continues below ...
    if not selected_tenses:
        st.error("Please select at least one tense!")
    else:
        v_type = random.choice(verb_types) if not manual_verb else "specific"
        v_name = manual_verb if manual_verb else "a random " + v_type
        tense = random.choice(selected_tenses)
        
        subjects = ["yo", "tú", "él", "ella", "nosotros", "nosotras", "usted", "ustedes", "ellos", "ellas"]
        selected_subject = random.choice(subjects)
        prompt = f"""
        Act as a Latin American Spanish teacher. 
        1. Pick a common verb of type: {v_name}. 
        2. Create a complex, interesting Spanish sentence using that verb in the '{tense}' tense. 
        3. Use the subject '{selected_subject}' as the basis for the conjugation.
        4. Use Latin American Spanish (never use 'vosotros').
        5. Translate it to English.
        6. Provide a short explanation for the conjugation.
        
        Return ONLY in this format:
        VERB: [Infinitive]
        SPANISH: [Full sentence with the conjugated verb]
        ANSWER: [Just the conjugated verb]
        ENGLISH: [English translation]
        EXPLANATION: [Brief explanation]
        """
        
        # This is the new way to call the AI
        # Existing line where you get the response:
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )

        # --- NEW USAGE MONITOR CODE START ---
        # 1. Get token counts from the AI response
        usage = response.usage_metadata
        prompt_tokens = usage.prompt_token_count
        candidate_tokens = usage.candidates_token_count

        # 2. Calculate tiny cost ($0.10/M input, $0.40/M output)
        input_cost = (prompt_tokens / 1000000) * 0.10
        output_cost = (candidate_tokens / 1000000) * 0.40
        current_run_cost = input_cost + output_cost

        # 3. Update the session totals
        st.session_state.total_cost += current_run_cost
        st.session_state.exercise_count += 1
        # --- NEW USAGE MONITOR CODE END ---

        # Your existing line to process the text:
        lines = response.text.split('\n')
        
        # Parse AI response
        for line in lines:
            clean_line = line.replace("*", "").strip()
            if "VERB:" in clean_line: st.session_state.target_verb = clean_line.split("VERB:")[1].strip()
            if "SPANISH:" in clean_line: st.session_state.spanish_full = clean_line.split("SPANISH:")[1].strip()
            if "ANSWER:" in clean_line: st.session_state.correct_answer = clean_line.split("ANSWER:")[1].strip().replace(".","")
            if "ENGLISH:" in clean_line: st.session_state.english_trans = clean_line.split("ENGLISH:")[1].strip()
            if "EXPLANATION:" in clean_line: st.session_state.explanation = clean_line.split("EXPLANATION:")[1].strip()

# --- EXERCISE DISPLAY ---
if 'spanish_full' in st.session_state:
    st.markdown("---")
    st.subheader("Translate this context:")
    st.info(f"🇬🇧 {st.session_state.english_trans}")
    
    display_sent = st.session_state.spanish_full.replace(st.session_state.correct_answer, "_______")
    st.markdown(f"<p class='big-font'>🇪🇸 {display_sent} <span style='color:green;'>[{st.session_state.target_verb}]</span></p>", unsafe_allow_html=True)
    
    # Use a form to prevent the app from refreshing too early
    with st.form(key='answer_form'):
        user_input = st.text_input("Enter your answer:", key="user_answer_field")
        submit_button = st.form_submit_button(label='Check Answer')

        if submit_button:
            if user_input.lower() == st.session_state.correct_answer.lower():
                st.balloons()
                st.success(f"¡Excelente! '{st.session_state.correct_answer}' is correct.")
            else:
                st.error(f"Not quite. The correct answer is: {st.session_state.correct_answer}")
                st.write(f"**Explanation:** {st.session_state.explanation}")
    with st.sidebar:
        st.divider()
        st.subheader("📊 Session Usage Monitor")
        st.metric("Exercises Generated", st.session_state.exercise_count)
    
        # Display cost with 4 decimal places since it's so small
        st.metric("Estimated Cost", f"${st.session_state.total_cost:.4f}")
    
        st.caption("Pricing based on Gemini 2.0 Flash-Lite paid tier.")
        if st.button("Reset Session Stats"):
            st.session_state.total_cost = 0.0
            st.session_state.exercise_count = 0
            st.rerun()
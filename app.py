import os
import json
import streamlit as st
from pypdf import PdfReader
import google.generativeai as genai
from dotenv import load_dotenv

# Setup API Key
load_dotenv()

# Safely get the key locally or from Streamlit Cloud secrets
try:
    key = os.getenv("GEMINI_API_KEY") or st.secrets["GEMINI_API_KEY"]
except KeyError:
    key = os.getenv("GEMINI_API_KEY")
    
genai.configure(api_key=key)

def generate(text, n, difficulty):
    prompt = f"""Create {n} {difficulty} level MCQs from this content. Return ONLY a valid JSON list, no extra text, no markdown tags. 
    Format:
    [{{"q": "...", "options": ["Option A", "Option B", "Option C", "Option D"], "answer": 0, "explanation": "Brief reason why this is correct"}}]
    answer = index of the correct option (0 to 3).
    
    Content: {text[:15000]}"""
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    
    try:
        t = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(t)
    except Exception as e:
        st.error(f"Error parsing JSON. Please try again.")
        return []

# UI Setup
st.title("🧠 AI Quiz Generator")
mode = st.radio("Input Mode", ["Topic", "PDF"])

col1, col2 = st.columns(2)
with col1:
    n = st.slider("Number of Questions", 3, 15, 5)
with col2:
    difficulty = st.selectbox("Difficulty Level", ["Easy", "Medium", "Hard"])

text = ""
if mode == "Topic":
    text = st.text_input("Topic likho (e.g., Database Normalization BCNF, Python OOPs)")
else:
    f = st.file_uploader("PDF upload karo", type="pdf")
    if f:
        text = "\n".join(p.extract_text() or "" for p in PdfReader(f).pages)

# App Logic
if st.button("Quiz Banao") and text:
    with st.spinner(f"Generating {difficulty} Quiz..."):
        st.session_state.quiz = generate(text, n, difficulty)
        st.session_state.submitted = False

if "quiz" in st.session_state and st.session_state.quiz:
    answers = []
    
    for i, q in enumerate(st.session_state.quiz):
        answers.append(st.radio(f"**Q{i+1}. {q['q']}**", q["options"], index=None, key=f"q{i}"))
        
    if st.button("Submit"):
        st.session_state.submitted = True
        
    # Result Evaluation with Explanations
    if st.session_state.get("submitted"):
        score = 0
        for q, a in zip(st.session_state.quiz, answers):
            correct_ans_text = q["options"][q["answer"]]
            explanation = q.get("explanation", "No explanation available.")
            
            if a == correct_ans_text:
                score += 1
                st.success(f"**Sahi Jawab!** 🎉\n\n*Explanation:* {explanation}")
            else:
                st.error(f"**Ghalat!** Sahi Jawab tha: {correct_ans_text}\n\n*Explanation:* {explanation}")
                
        st.info(f"### Final Score: {score} / {len(answers)}")

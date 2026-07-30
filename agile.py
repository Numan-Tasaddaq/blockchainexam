import streamlit as st
import json
import random
import re

# --- Normalization helper ---
def normalize(text):
    """Lowercase, remove punctuation, and trim whitespace."""
    return re.sub(r'[^a-z0-9 ]', '', text.lower().strip())

# --- Answer checker ---
def is_correct(user, correct, qtype):
    if qtype == "single":
        return user == correct
    elif qtype == "multi":
        return set(user) == set(correct)
    elif qtype == "blank":
        if isinstance(correct, str):
            correct_options = [normalize(c) for c in correct.split('/')]
        else:
            correct_options = [normalize(correct)]
        return normalize(user) in correct_options
    return False

# --- Load questions from file ---
@st.cache_data
def load_questions():
    with open("agile.json", "r") as f:
        return json.load(f)

questions = load_questions()

def reset_quiz_progress():
    """Reset progress and clear previous widget answers."""
    for key in list(st.session_state.keys()):
        if key.startswith("question_") or key in ["score", "submitted", "q_index", "answers", "bookmarked"]:
            del st.session_state[key]

# --- Session state setup ---
if "question_order" not in st.session_state or len(st.session_state.question_order) != len(questions):
    st.session_state.question_order = list(range(len(questions)))
if "q_index" not in st.session_state:
    st.session_state.q_index = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "bookmarked" not in st.session_state:
    st.session_state.bookmarked = set()

# --- Display current question ---
q_index = st.session_state.q_index
question_id = st.session_state.question_order[q_index]
q = questions[question_id]

st.title(f"Question {q_index + 1} / {len(questions)}")
st.write(q["question"])

# --- Practice controls ---
col_shuffle, col_bm, col_jump_input, col_jump_btn = st.columns([1, 1, 1, 1])

with col_shuffle:
    if st.button("Shuffle MCQs"):
        st.session_state.question_order = list(range(len(questions)))
        random.shuffle(st.session_state.question_order)
        reset_quiz_progress()
        st.rerun()

with col_bm:
    if st.button("🔖 Bookmark"):
        st.session_state.bookmarked.add(question_id)
        st.success("Bookmarked!")

with col_jump_input:
    jump_to = st.number_input("Jump to:", min_value=1, max_value=len(questions), step=1, label_visibility="collapsed")

with col_jump_btn:
    if st.button("🚀"):
        st.session_state.q_index = int(jump_to) - 1
        st.session_state.submitted = False
        st.rerun()

# --- Display answer input ---
user_answer = None
if q["type"] == "single":
    user_answer = st.radio("Choose one:", q["options"], key=f"question_{question_id}_single")
elif q["type"] == "multi":
    user_answer = []
    for option in q["options"]:
        if st.checkbox(option, key=f"question_{question_id}_{option}"):
            user_answer.append(option)
elif q["type"] == "blank":
    user_answer = st.text_input("Enter your answer:", key=f"question_{question_id}_input")

# --- Submit & Next side-by-side ---
col_submit, col_next = st.columns([1, 1])

with col_submit:
    if st.button("✅ Submit", disabled=st.session_state.submitted):
        st.session_state.submitted = True
        correct = q["correct"] if q["type"] != "blank" else q["answer"]
        st.session_state.answers[question_id] = user_answer
        if is_correct(user_answer, correct, q["type"]):
            st.success("✅ Correct!")
            st.session_state.score += 1
        else:
            st.error("❌ Incorrect.")
            st.info(f"Correct Answer: {correct}")

with col_next:
    if st.session_state.submitted and q_index < len(questions) - 1:
        if st.button("➡️ Next"):
            st.session_state.q_index += 1
            st.session_state.submitted = False
            st.rerun()

# --- Navigation Back ---
if q_index > 0:
    if st.button("⬅️ Go Back"):
        st.session_state.q_index -= 1
        st.session_state.submitted = False
        st.rerun()

# --- Final screen ---
if st.session_state.submitted and q_index == len(questions) - 1:
    st.success("🎉 Quiz Completed!")
    st.write(f"Your Score: **{st.session_state.score} / {len(questions)}**")

    if st.session_state.bookmarked:
        st.subheader("📌 Review Bookmarked Questions")
        for i in sorted(list(st.session_state.bookmarked)):
            if st.button(f"Review Question {i + 1}", key=f"bmark_{i}"):
                st.session_state.q_index = st.session_state.question_order.index(i)
                st.session_state.submitted = False
                st.rerun()

    if st.button("🔁 Restart"):
        reset_quiz_progress()
        st.rerun()

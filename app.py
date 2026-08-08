from dotenv import load_dotenv
import os
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

import streamlit as st
import json
import faiss
import numpy as np
import re

from sentence_transformers import SentenceTransformer
from google.api_core.exceptions import ResourceExhausted
from eligibility import extract_profile, get_eligible_schemes
from metadata_filter import extract_tags, filter_schemes_by_tags
from hybrid_retriever import hybrid_search


# --------------------------------
# Page Setup
# --------------------------------
st.set_page_config(
    page_title="SchemeSaarti - Government Scheme Assistant",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
.main { background-color: #f5f7fa; }
.gov-header {
    background: linear-gradient(90deg,#FF9933,#FFFFFF,#138808);
    padding:20px;
    border-radius:15px;
    box-shadow:0px 3px 12px rgba(0,0,0,0.1);
    text-align:center;
    margin-bottom:20px;
}
.gov-header h1 {
    font-size: 3rem;
    font-weight: 900;
    color: #0F172A;
    text-shadow: 2px 2px 6px rgba(0,0,0,0.25);
    letter-spacing: 1px;
    margin-bottom: 10px;
}

.gov-subtitle{ font-size:18px; color:#374151; }
.gov-banner{
    background:#002147;
    color:white;
    padding:10px;
    border-radius:10px;
    text-align:center;
    margin-top:10px;
    margin-bottom:20px;
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="gov-header">
    <h1>🏛️ SchemeSaarti</h1>
    <div class="gov-subtitle">
        AI Powered Government Scheme Discovery & Eligibility Portal
    </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class='gov-banner'>
🇮🇳 Discover Central & State Government Schemes using Artificial Intelligence
</div>
""",
    unsafe_allow_html=True,
)


# --------------------------------
# Sidebar
# --------------------------------
with st.sidebar:
    st.title("🏛️ SchemeSaarti")

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()


# --------------------------------
# Chat History Initialization
# --------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_scheme" not in st.session_state:
    st.session_state.current_scheme = None


# --------------------------------
# Gemini Setup
# --------------------------------
llm = genai.GenerativeModel("gemini-2.5-flash")


# --------------------------------
# Load Embedding Model
# --------------------------------
@st.cache_resource
def load_embedding_model():
    return SentenceTransformer("all-MiniLM-L6-v2")


embed_model = load_embedding_model()


# --------------------------------
# Load Chunks
# --------------------------------
@st.cache_data
def load_chunks():
    with open("data/chunks.json", "r", encoding="utf-8") as f:
        return json.load(f)


chunks = load_chunks()


# --------------------------------
# Load Schemes
# --------------------------------
@st.cache_data
def load_schemes():
    with open("data/enriched_schemes.json", "r", encoding="utf-8") as f:
        return json.load(f)


schemes = load_schemes()


def get_scheme_details(scheme_name):
    for scheme in schemes:
        if scheme.get("scheme_name", "").lower() == scheme_name.lower():
            return scheme
    return None


# --------------------------------
# Load FAISS Index
# --------------------------------
@st.cache_resource
def load_index():
    return faiss.read_index("data/faiss_index.index")


index = load_index()


# --------------------------------
# Display Previous Messages
# --------------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


# --------------------------------
# User Input
# --------------------------------
question = st.chat_input("Ask about government schemes...")

if question:
    with st.chat_message("user"):
        st.write(question)

    st.session_state.messages.append({"role": "user", "content": question})

    # ----------------------------
    # Build Conversation History
    # ----------------------------
    history = ""
    for msg in st.session_state.messages[-4:]:
        history += f"{msg['role']}: {msg['content']}\n"

    question_lower = question.lower()

    followup_words = [
        "it",
        "its",
        "this",
        "that",
        "eligibility",
        "eligible",
        "benefits",
        "benefit",
        "apply",
        "application",
        "documents",
        "document",
        "criteria",
        "required",
        "process",
    ]
    question_words = re.findall(r"\b\w+\b", question_lower)

    is_followup = (
        st.session_state.current_scheme is not None
        and any(word in question_words for word in followup_words)
    )

    # ----------------------------
    # Detect State (for filtering)
    # ----------------------------
    state_name = None
    known_states = ["maharashtra", "assam", "karnataka", "telangana"]
    for s in known_states:
        if s in question_lower:
            state_name = s
            break

    # ----------------------------
    # Retrieve Relevant Chunks
    # ----------------------------
    retrieved_context = ""
    sources = []
    exact_match_found = False

    if is_followup and st.session_state.current_scheme:
        scheme = get_scheme_details(st.session_state.current_scheme)
        if scheme:
            retrieved_context = json.dumps(scheme, indent=2)
            sources.append(st.session_state.current_scheme)
            exact_match_found = True

    if is_followup and len(sources) == 0:
        for chunk in chunks:
            if chunk.get("scheme_name", "") in history:
                retrieved_context += chunk["text"] + "\n\n"
                sources.append(chunk.get("scheme_name", "Unknown Scheme"))
                break

    if not exact_match_found and not is_followup:
        extracted_tags = extract_tags(question)
        candidate_schemes = filter_schemes_by_tags(schemes, extracted_tags)
        candidate_scheme_names = {
            c.get("scheme_name") for c in candidate_schemes if c.get("scheme_name")
        }
        candidate_chunks = [c for c in chunks if c.get("scheme_name") in candidate_scheme_names]

        if state_name:
            candidate_chunks = [
                c
                for c in candidate_chunks
                if state_name in str(c.get("metadata", {})).lower()
            ]

        if not extracted_tags:
            filtered_chunks = chunks
            if state_name:
                filtered_chunks = [
                    c
                    for c in chunks
                    if state_name in str(c.get("metadata", {})).lower()
                ]
            if not filtered_chunks:
                filtered_chunks = chunks

            query_embedding = embed_model.encode([question], convert_to_numpy=True)
            query_embedding = np.array(query_embedding, dtype=np.float32)
            faiss.normalize_L2(query_embedding)

            _distances, indices = index.search(query_embedding, 1)
            idx = indices[0][0]

            retrieved_context += chunks[idx]["text"] + "\n\n"
            scheme_name = chunks[idx].get("scheme_name", "Unknown Scheme")
            sources.append(scheme_name)
            st.session_state.current_scheme = scheme_name
        else:
            if len(candidate_schemes) == 0 or len(candidate_chunks) == 0:
                fallback_chunks = chunks
                if state_name:
                    fallback_chunks = [
                        c
                        for c in chunks
                        if state_name in str(c.get("metadata", {})).lower()
                    ]
                if not fallback_chunks:
                    fallback_chunks = chunks

                query_embedding = embed_model.encode([question], convert_to_numpy=True)
                query_embedding = np.array(query_embedding, dtype=np.float32)
                faiss.normalize_L2(query_embedding)

                _distances, indices = index.search(query_embedding, 1)
                idx = indices[0][0]

                retrieved_context += chunks[idx]["text"] + "\n\n"
                scheme_name = chunks[idx].get("scheme_name", "Unknown Scheme")
                sources.append(scheme_name)
                st.session_state.current_scheme = scheme_name
            else:
                results, retrieval_metadata = hybrid_search(
                    question,
                    candidate_chunks=candidate_chunks,
                    top_k=5,
                )

                if retrieval_metadata:

                    def _rank_key(item: dict) -> tuple:
                        has_keyword = bool(item.get("reason"))
                        state_match = True
                        if state_name:
                            text_meta = str(item.get("metadata", {})).lower()
                            state_match = state_name in text_meta if text_meta else True
                        sim = item.get("similarity_score")
                        sim_val = sim if sim is not None else -1.0
                        return (
                            1 if has_keyword else 0,
                            1 if state_match else 0,
                            sim_val,
                        )

                    sorted_items = sorted(retrieval_metadata, key=_rank_key, reverse=True)
                else:
                    sorted_items = []

                if sorted_items:
                    use_results = []
                    ordered_names = [
                        it.get("scheme_name") for it in sorted_items if it.get("scheme_name")
                    ]
                    for r in results:
                        if r.get("scheme_name") in ordered_names:
                            use_results.append(r)
                    if not use_results:
                        use_results = results
                else:
                    use_results = results

                retrieved_context = ""
                sources = []
                top_k = 5
                for chunk in use_results[:top_k]:
                    retrieved_context += chunk["text"] + "\n\n"
                    sources.append(chunk.get("scheme_name", "Unknown Scheme"))

                if use_results:
                    st.session_state.current_scheme = use_results[0].get(
                        "scheme_name", st.session_state.current_scheme
                    )

    # ----------------------------
    # Eligibility checking
    # ----------------------------
    profile = extract_profile(question) or {}
    profile_triggers = {"widow", "ex_serviceman", "student", "caste"}

    if isinstance(profile, dict) and any(k in profile_triggers for k in profile.keys()):
        eligible_schemes = get_eligible_schemes(profile, schemes)

        unique_schemes = {}
        for scheme in eligible_schemes or []:
            unique_schemes[scheme.get("scheme_name", "")] = scheme

        # Keep rule-based eligible schemes (do not display immediately).
        matched_schemes = list(unique_schemes.values())[:5]

        matched_conditions = []
        if profile.get("widow"):
            matched_conditions.append("Widow")
        if profile.get("ex_serviceman"):
            matched_conditions.append("Ex-serviceman")
        if profile.get("student"):
            matched_conditions.append("Student")
        if profile.get("farmer"):
            matched_conditions.append("Farmer")
        if profile.get("caste"):
            matched_conditions.append(profile["caste"])

        # Hybrid scoring per scheme
        scored_schemes = []
        for scheme in matched_schemes:
            scheme_name = scheme.get("scheme_name", "")
            scheme_chunks = [
                c for c in chunks if c.get("scheme_name", "") == scheme_name
            ]

            # If no chunks exist for the scheme, fall back to rule-based placement
            if not scheme_chunks:
                scheme["eligibility_score"] = 1.0
                scheme["similarity_score"] = 0.0
                scheme["bm25_score"] = 0.0
                scheme["final_score"] = 0.5
                scheme["method"] = "Hybrid (Eligibility + FAISS + BM25)"
                scored_schemes.append(scheme)
                continue

            results, retrieval_metadata = hybrid_search(
                question,
                candidate_chunks=scheme_chunks,
                top_k=1,
            )

            eligibility_score = 1.0
            similarity_score = 0.0
            bm25_score = 0.0

            if retrieval_metadata:
                similarity_score = float(retrieval_metadata[0].get("similarity_score", 0) or 0)
                bm25_score = float(retrieval_metadata[0].get("bm25_score", 0) or 0)
            elif results:
                similarity_score = float(results[0].get("similarity_score", 0) or 0)
                bm25_score = float(results[0].get("bm25_score", 0) or 0)

            normalized_bm25 = min(bm25_score / 10, 1.0)
            final_score = (
                0.5 * eligibility_score
                + 0.3 * similarity_score
                + 0.2 * normalized_bm25
            )

            scheme["eligibility_score"] = eligibility_score
            scheme["similarity_score"] = similarity_score
            scheme["bm25_score"] = bm25_score
            scheme["final_score"] = final_score
            scheme["method"] = "Hybrid (Eligibility + FAISS + BM25)"

            scored_schemes.append(scheme)

        matched_schemes = sorted(
            scored_schemes,
            key=lambda x: x.get("final_score", 0),
            reverse=True,
        )[:5]

        with st.expander("🔍 Why these schemes were retrieved"):
            if not matched_schemes:
                st.write("No matching eligibility schemes found.")
            else:
                for scheme in matched_schemes:
                    final_score = float(scheme.get("final_score", 0) or 0)
                    similarity_score = float(scheme.get("similarity_score", 0) or 0)
                    bm25_score = float(scheme.get("bm25_score", 0) or 0)
                    confidence = "Low 🔴"
                    if final_score >= 0.80:
                        confidence = "High 🟢"
                    elif final_score >= 0.60:
                        confidence = "Medium 🟡"

                    st.markdown(f"**Scheme:** {scheme.get('scheme_name','N/A')}")
                    st.markdown("**Method:** Hybrid (Eligibility + FAISS + BM25)")
                    st.markdown(f"**Eligibility Score:** {round(float(scheme.get('eligibility_score', 1.0) or 0), 2)}")
                    st.markdown(f"**Similarity Score:** {round(similarity_score, 2)}")
                    st.markdown(f"**BM25 Score:** {round(bm25_score, 2)}")
                    st.markdown(f"**Final Score:** {round(final_score, 2)}")
                    st.markdown(f"**Confidence:** {confidence}")
                    st.markdown("**Matched Conditions:**")
                    for condition in matched_conditions:
                        st.markdown(f"✓ {condition}")
                    st.divider()


        with st.chat_message("assistant"):
            if len(matched_schemes) == 0:
                st.write("No schemes matched the provided eligibility profile.")
            else:
                eligibility_prompt = f"""
You are a government scheme assistant.

User Profile:
{profile}

Matched Schemes:
{matched_schemes}

Return the answer in EXACTLY this format:

You may be eligible for:

1. Scheme Name
Reason: ...

2. Scheme Name
Reason: ...

3. Scheme Name
Reason: ...

Rules:
- Mention each scheme only once.
- Do not repeat sections.
- Do not repeat the heading.
- Maximum one paragraph per scheme.
- Return a single consolidated answer.
"""

                try:
                    response = llm.generate_content(eligibility_prompt)
                    eligibility_answer = response.text
                except ResourceExhausted:
                    st.warning("Gemini quota exhausted. Showing retrieved schemes only.")
                    eligibility_answer = (
                        "Matched Schemes:\n\n" + "\n".join(
                            f"- {s['scheme_name']}" for s in matched_schemes
                        )
                    )
                except Exception:
                    eligibility_answer = "Matched Schemes:\n\n" + "\n".join(
                        f"- {s['scheme_name']}" for s in matched_schemes
                    )

                st.write(eligibility_answer)

        st.stop()

    # ----------------------------
    # Main chatbot response
    # ----------------------------
    retrieved_chunks_context = retrieved_context.strip()

    prompt = f"""
You are SchemeSaarti, an AI assistant for Indian Government Schemes.

User Question:
{question}

Retrieved Schemes:
{retrieved_context}

Instructions:

1. Answer ONLY using the retrieved schemes.

2. If one or more schemes are relevant, explain them.

For each scheme provide:
- Scheme Name
- Purpose
- Who can apply
- Benefits

3. If information is partial, still provide the best answer possible.

4. Say:
'I could not find sufficient information in the retrieved schemes.'
ONLY if none of the retrieved schemes are relevant.

Provide the answer in simple language.
"""

    if not retrieved_chunks_context:
        answer = "I could not find any relevant schemes."
    else:
        response = llm.generate_content(prompt)
        answer = response.text

    with st.chat_message("assistant"):
        st.write(answer)

        st.subheader("📂 Scheme Explorer")
        for source in set(sources):
            scheme = get_scheme_details(source)
            if scheme:
                with st.expander(f"🏛️ {source}"):
                    st.markdown(f"### 🏢 Ministry\n\n{scheme.get('ministry', 'N/A')}")
                    st.markdown(
                        f"### 📝 Description\n\n{scheme.get('description', 'N/A')}"
                    )
                    st.markdown(f"### 🎁 Benefits\n\n{scheme.get('benefits', 'N/A')}")
                    st.markdown(
                        f"### ✅ Eligibility\n\n{scheme.get('eligibility', 'N/A')}"
                    )

                    application_process = scheme.get("application_process", "")
                    if application_process:
                        st.markdown(
                            f"### 📋 Application Process\n\n{application_process}"
                        )

                    tags = scheme.get("tags", [])
                    if tags:
                        st.markdown("### 🏷️ Tags")
                        st.write(", ".join(tags))

    st.session_state.messages.append({"role": "assistant", "content": answer})


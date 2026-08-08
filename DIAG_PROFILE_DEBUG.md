# Debug Notes: Gemini duplication in eligibility branch

## Root cause (from reading `app.py`)
The eligibility branch builds `unique_schemes` inside a loop, but **the Gemini call + `st.write(eligibility_answer)` are inside the same `for scheme in eligible_schemes` loop**.

That means:
- Gemini `llm.generate_content(...)` is called once per iteration of the loop (i.e., multiple times).
- `eligibility_answer` is written once per iteration.

This produces repeated blocks like:
"You may be eligible for:" repeated several times.

## Fix to apply
Move the following block **out of the `for scheme in eligible_schemes` loop**:
- creation of `matched_schemes`
- creation of `schemes_for_llm`
- `with st.chat_message("assistant"):`
- `llm.generate_content(eligibility_prompt)`
- `st.write(eligibility_answer)`

After the loop:
- compute `matched_schemes` once
- call Gemini once
- write answer once

## After fix: instrumentation requested
Re-run:
- `python -m py_compile app.py`

Then report:
- number of `generate_content` calls
- number of `st.write(eligibility_answer)` calls
- final value/definition of `eligibility_answer`


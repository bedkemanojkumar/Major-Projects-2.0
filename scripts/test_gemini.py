import google.generativeai as genai
import os
genai.configure(api_key=os.getenv("GENAI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

response = model.generate_content(
    "Explain what RAG is in 3 lines."
)

print(response.text)
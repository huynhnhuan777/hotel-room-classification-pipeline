from google import genai

# =========================
# CẤU HÌNH
# =========================
API_KEY = "AIzaSyAKSRnFLiYZiiuTqv0uUo5pRHoiTir5GEM"

client = genai.Client(api_key=API_KEY)

print("🚀 Script started", flush=True)
print("📡 Testing Gemini API (new SDK)...", flush=True)

prompt = """
You are a classifier.

Classify a hotel room into ONE class: 0, 1, 2, 3, 4, or 5.

Rules:
- Output ONLY ONE integer
- No explanation

Room features:
Final Price: 0.025
Max People: 0.14
Area_m2: 0.13
Has wifi: 1
Has AC: 1
Has pool: 0
"""

try:
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )

    print("✅ Gemini raw output:", response.text, flush=True)

except Exception as e:
    print("❌ Error:", e, flush=True)

print("🏁 Script finished", flush=True)

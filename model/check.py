from google import genai

client = genai.Client(api_key="AIzaSyAKSRnFLiYZiiuTqv0uUo5pRHoiTir5GEM")

print("📦 Available models:\n")

for m in client.models.list():
    print(m.name)
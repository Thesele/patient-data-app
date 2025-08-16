from google import genai

client = genai.Client(api_key="AIzaSyCjPdFvvzgMVGWN57axtKr_GAPVYlBtuBI")

response = client.models.generate_content(
    model="gemini-2.5-flash", contents="create medical notes"
)
print(response.text)

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def test_groq():
    print("Testing Groq...")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY missing")
        return
    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=10
        )
        print(f"Groq OK: {response.choices[0].message.content}")
    except Exception as e:
        print(f"Groq FAILED: {e}")

if __name__ == "__main__":
    test_groq()

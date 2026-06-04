import json
import os
from dotenv import load_dotenv
from groq import Groq
from services.database import get_ai_translation, save_ai_translation

load_dotenv()


def get_phonetic_from_groq(nom_text):
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": (
                    f"Cho phiên âm Hán-Việt của chữ Nôm sau: {nom_text}\n"
                    f"Trả về JSON, không giải thích:\n"
                    f'{{"phonetic": "phiên âm"}}'
                )
            }],
            max_tokens=100
        )
        text = response.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text).get("phonetic", "")
    except Exception as e:
        print(f"[Phonetic Error]: {e}")
        return ""


def ai_translate(nom_text):

    # 1. Tra DB trước
    result = get_ai_translation(nom_text)

    if result and result.get("found"):
        meaning = result.get("meaning", "")
        phonetic = result.get("phonetic", "")

        # Có nghĩa nhưng chưa có phiên âm → gọi Groq lấy phiên âm
        if meaning and not phonetic:
            phonetic = get_phonetic_from_groq(nom_text)

            # Lưu phiên âm vào DB để lần sau không gọi lại
            if phonetic:
                save_ai_translation(nom_text, meaning, phonetic)

        return {
            "meaning": meaning,
            "phonetic": phonetic,
            "candidates": []
        }

    # 2. Không có trong DB → gọi Groq dịch đầy đủ
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": (
                    f"Dịch chữ Nôm sau sang tiếng Việt hiện đại "
                    f"và cho phiên âm Hán-Việt.\n"
                    f"Chữ Nôm: {nom_text}\n\n"
                    f"Trả về JSON với 3 cách dịch, không giải thích thêm:\n"
                    f'{{"candidates": ['
                    f'{{"meaning": "nghĩa 1", "phonetic": "phiên âm 1"}},'
                    f'{{"meaning": "nghĩa 2", "phonetic": "phiên âm 2"}},'
                    f'{{"meaning": "nghĩa 3", "phonetic": "phiên âm 3"}}'
                    f']}}'
                )
            }]
        )

        text = response.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        candidates = data.get("candidates", [])

        if not candidates:
            return {"meaning": "", "phonetic": "", "candidates": []}

        save_ai_translation(
            nom_text,
            candidates[0]["meaning"],
            candidates[0]["phonetic"]
        )

        return {
            "meaning": candidates[0]["meaning"],
            "phonetic": candidates[0]["phonetic"],
            "candidates": candidates
        }

    except Exception as e:
        return {
            "meaning": f"Lỗi dịch: {e}",
            "phonetic": "",
            "candidates": []
        }
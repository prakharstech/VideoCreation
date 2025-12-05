import os
import base64
import requests

API_KEY = "AIzaSyClnVtqyfNZh1ZU6vqKoio4l9o4lDAUJh8"  # or hard-code for testing
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"  # note v1beta
MODEL = "gemini-2.5-flash-image"


def generate_image(prompt):
    url = f"{BASE_URL}/models/{MODEL}:generateContent?key={API_KEY}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "responseModalities": ["IMAGE"]
        }
    }
    headers = {"Content-Type": "application/json"}
    resp = requests.post(url, json=payload, headers=headers)
    print("Status:", resp.status_code)
    print("Body:", resp.text)
    if resp.status_code != 200:
        raise RuntimeError("Image generation failed")
    data = resp.json()
    # Try to find inline_data
    imgs = []
    for part in data.get("candidates", [data]).pop(0).get("content", {}).get("parts", []):
        inline = part.get("inlineData") or part.get("inline_data")
        if inline and "data" in inline:
            b64 = inline["data"]
            imgs.append(base64.b64decode(b64))
    if not imgs:
        raise RuntimeError("No image data in response")
    # Save first image
    with open("output1.png", "wb") as f:
        f.write(imgs[0])
    print("Image saved to output1.png")
    return "output1.png"


if __name__ == "__main__":
    img_path = generate_image(
        "A cute buddha pic, natural beauty background")
    # TODO: If you want vision/understanding, send img_path or base64 to a model endpoint here

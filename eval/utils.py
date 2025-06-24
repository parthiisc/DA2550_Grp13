from dotenv import load_dotenv
import os
import openai
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import platform
import base64
from typing import List, Optional
import re
import time
import io


# Print the current working directory to verify where Python is looking for the .env file
print("Current working directory:", os.getcwd())

# Load the .env file
load_dotenv()

# Print the API key (first few characters for security)
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    print("API key found:", api_key[:4] + "..." + api_key[-4:])
else:
    print("No API key found")


# response = openai.chat.completions.create(
#     model="gpt-4o-mini",
#     messages=[
#         {"role": "system", "content": "You are a helpful assistant specialized in providing information about BellaVista Italian Restaurant."},
#         {"role": "user", "content": "What's on the menu?"},
#         {"role": "assistant", "content": "BellaVista offers a variety of Italian dishes including pasta, pizza, and seafood."},
#         {"role": "user", "content": "Do you have vegan options?"}
#     ]
# )
# response.model_dump()
# print(response.choices[0].message.content)

# API to convert PDF pages to high-resolution PNG images
def pdf_to_images(pdf_path: str, output_folder: str, dpi: int = 300) -> list[str]:
    """
    Converts each page of the given PDF into a high-resolution PNG.
    Returns a list of file paths for the extracted images.
    """
    os.makedirs(output_folder, exist_ok=True)

    # On Mac/Linux, poppler must be installed and in PATH (e.g., via `brew install poppler`)
    pages = convert_from_path(pdf_path, dpi=dpi)
    
    image_paths = []
    for i, page in enumerate(pages, start=1):
        img_filename = os.path.join(output_folder, f"page_{i:03d}.png")
        page.save(img_filename, "PNG")
        image_paths.append(img_filename)

    return image_paths


# API to run Tesseract OCR on images
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"  # or use `which tesseract`

def run_ocr_on_image(image_path: str, lang: str = "eng") -> str:
    """
    Runs Tesseract OCR on the given image and returns the recognized text.
    """
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, lang=lang)
    return text

# API to describe comic pages using GPT-4o
def describe_comic_pages_with_gpt4o(
    image_paths: List[str],
    ocr_texts: Optional[List[str]] = None,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: int = 600
) -> str:

    if not image_paths:
        raise ValueError("At least one image path must be provided.")
    if len(image_paths) > 3:
        raise ValueError("A maximum of 3 images can be processed at once.")

    # Prepare OCR texts
    if ocr_texts is None:
        ocr_texts = [""] * len(image_paths)
    if len(ocr_texts) != len(image_paths):
        raise ValueError("The number of OCR texts must match the number of image paths.")

    # Encode images
    blocks: List[dict] = []
    for img_path in image_paths:
        img_b64 = compress_image(img_path, max_width=1024, quality=70)
        blocks.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
        })

    # Build prompt: ask for labeled narrations
    prompt = (
        "You are a comic-book interpreter. For each image I send, please provide a detailed narration "
        "of that page, labeling each section with 'Page 1:', 'Page 2:', etc., in order. "
        "Include characters, actions, settings, and dialogues."
    )

    # Combine user content: prompt, images, OCR
    user_content = [{"type": "text", "text": prompt}]
    for idx, img_block in enumerate(blocks, start=1):
        user_content.append(img_block)
        if ocr_texts[idx-1].strip():
            user_content.append({
                "type": "text",
                "text": f"OCR for Page {idx}:\n" + ocr_texts[idx-1].strip()
            })

    # Call GPT-4o
    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that reads comics."},
            {"role": "user", "content": user_content}
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()




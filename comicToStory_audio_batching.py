from dotenv import load_dotenv
import os

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
#--------------------------------------------
# PDF → Images
#--------------------------------------------

from pdf2image import convert_from_path
import os




from pdf2image import convert_from_path
from PIL import Image
import os
 
def pdf_to_images(
    pdf_path: str,
    output_folder: str,
    dpi: int = 150,
    image_quality: int = 60,
    scale_factor: float = 0.4,
    poppler_path: str = r"C:\poppler-23.11.0\Library\bin"
) -> list[str]:
    """
    Converts PDF to compressed JPEG images with reduced size and quality.
    """
    os.makedirs(output_folder, exist_ok=True)
    pages = convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler_path)
 
    image_paths = []
    for i, page in enumerate(pages, start=1):
        # Resize
        width, height = page.size
        new_size = (int(width * scale_factor), int(height * scale_factor))
        page = page.resize(new_size, resample=Image.LANCZOS)
 
        # Save as JPEG with compression
        img_filename = os.path.join(output_folder, f"page_{i:03d}.jpg")
        page.save(img_filename, "JPEG", quality=image_quality, optimize=True, progressive=True)
        image_paths.append(img_filename)
 
    return image_paths
#--------------------------------------------
# OCR extraction
#--------------------------------------------

import pytesseract
from PIL import Image

# 1) Tesseract executable path:
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def run_ocr_on_image(image_path: str, lang: str = "eng") -> str:
    """
    Runs Tesseract OCR on the given image and returns the recognized text.
    """
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, lang=lang)
    return text


import openai
import base64

#--------------------------------------------
# Page summarization
#--------------------------------------------

import openai
import base64
from typing import List, Optional


def describe_comic_pages_with_gpt4o(
    image_paths: List[str],
    ocr_texts: Optional[List[str]] = None,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: int = 600
) -> str:
    """
    Sends up to 5 comic pages + OCR texts in one batch to GPT-4o.
    Asks GPT to return separate page narrations prefixed with 'Page 1:', 'Page 2:', etc.
    Returns the raw combined string of page narrations.
    """
    if not image_paths:
        raise ValueError("At least one image path must be provided.")
    if len(image_paths) > 5:
        raise ValueError("A maximum of 5 images can be processed at once.")

    # Prepare OCR texts
    if ocr_texts is None:
        ocr_texts = [""] * len(image_paths)
    if len(ocr_texts) != len(image_paths):
        raise ValueError("The number of OCR texts must match the number of image paths.")

    # Encode images
    blocks: List[dict] = []
    for img_path in image_paths:
        with open(img_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")
        blocks.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
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

#--------------------------------------------
# Story Aggregation and final story
#--------------------------------------------

import re 


def process_entire_comic(pdf_path: str, temp_folder: str, style: str = None) -> str:
    """
    1. Convert PDF → images in temp_folder.
    2. Run OCR on each.
    3. Batch images in chunks of 5, calling GPT-4o for page-wise narrations.
    4. Parse and collect per-page summaries with robust regex.
    5. Combine all summaries into a cohesive short story.
    Returns the final combined story text.
    """
    # Step A: Convert PDF → PNGs
    page_images = pdf_to_images(pdf_path, temp_folder)


    # Step B: OCR
    ocr_texts = [run_ocr_on_image(p) for p in page_images]



    # Step C: Batch describe pages
    page_summaries: List[str] = []
    for i in range(0, len(page_images), 5):
        chunk_imgs = page_images[i : i + 5]
        chunk_ocr = ocr_texts[i : i + 5]
        combined = describe_comic_pages_with_gpt4o(chunk_imgs, chunk_ocr)
        # Use regex to extract 'Page X: ...' blocks
        pattern = r"Page\s*(\d+):\s*(.*?)(?=Page\s*\d+:|$)"
        matches = re.finditer(pattern, combined, re.DOTALL)
        for match in matches:
            page_num = int(match.group(1))
            text = match.group(2).strip()
            # Insert at correct absolute page index
            absolute_index = i + (page_num - 1)
            if absolute_index < len(page_images):
                page_summaries.append(text)

    # Step D: Aggregate all page_summaries into one story
    aggregate_prompt = (
        "I have a comic that spans several pages. For each page, I already have a detailed "
        "narration of what is happening (in chronological order). Here are the narrations:\n\n"
    )
    for idx, desc in enumerate(page_summaries, start=1):
        aggregate_prompt += f"--- Page {idx} ---\n{desc}\n\n"
    # Add style instruction
    if style == "Dramatic":
        aggregate_prompt += (
            "Please combine and rewrite all of these page descriptions into a single, coherent short story. "
            "Make the story dramatic, with emotional highs and lows, suspense, and vivid descriptions. "
            "Keep it concise (about 300–400 words), maintain narrative flow, and preserve character names or details."
        )
    elif style == "Fun":
        aggregate_prompt += (
            "Please combine and rewrite all of these page descriptions into a single, coherent short story. "
            "Make the story fun, light-hearted, and humorous, with playful language and amusing moments. "
            "Keep it concise (about 300–400 words), maintain narrative flow, and preserve character names or details."
        )
    else:  # Neutral or None
        aggregate_prompt += (
            "Please combine and rewrite all of these page descriptions into a single, coherent short story. "
            "Keep a neutral, straightforward tone. Keep it concise (about 300–400 words), maintain narrative flow, and preserve character names or details."
        )

    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a story-writing assistant."},
            {"role": "user", "content": aggregate_prompt},
        ],
        temperature=0.7,
        max_tokens=1200,
    )


    return response.choices[0].message.content.strip()
    

#--------------------------------------------
# Text-to-Speech Output / AudioBook
#--------------------------------------------

import openai
import uuid
import os


def generate_speech(narration_text: str, voice: str = "alloy") -> str:
    """
    Send narration_text to OpenAI TTS (model="tts-1") 
    save the output to an MP3 in app/static/audios/.
    Returns the relative path under /static/ to the generated MP3.
    """
    # ensure output dir exists
    out_dir = "app/static/audios"
    os.makedirs(out_dir, exist_ok=True)

    # generate unique filename
    filename = f"{uuid.uuid4()}.mp3"
    out_path = os.path.join(out_dir, filename)

    # call OpenAI TTS
    response = openai.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=narration_text
    )

    # write to file
    with open(out_path, "wb") as f:
        f.write(response.content)

    # return path for client embedding
    return f"audios/{filename}"

#--------------------------------------------
# Translate to Hindi option
#--------------------------------------------
def translate_text(text: str, target_lang: str = "hi") -> str:
    """
    Translates text to target_lang using OpenAI or another service.
    Currently uses OpenAI's `gpt-4` for simplicity.
    """
    prompt = f"Translate the following story to {target_lang.upper()}:\n\n{text}"
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

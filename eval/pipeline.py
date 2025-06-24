from utils import pdf_to_images, run_ocr_on_image, describe_comic_pages_with_gpt4o, safe_openai_call
import re
import openai
import base64
# Pipeline 
# PDF -> OCR + Images (batched) -> GPT-4o for page narrations -> Aggregate into short story
def process_entire_comic(pdf_path: str, temp_folder: str) -> str:
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
    for i in range(0, len(page_images), 3):
        chunk_imgs = page_images[i : i + 3]
        chunk_ocr = ocr_texts[i : i + 3]
        combined = describe_comic_pages_with_gpt4o(chunk_imgs, chunk_ocr)

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
    aggregate_prompt += (
        "Please combine and rewrite all of these page descriptions into a single, coherent short story. "
        "Keep it concise (about 300–400 words), maintain narrative flow, and preserve character names or details."
    )

    response = safe_openai_call(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a story-writing assistant."},
            {"role": "user", "content": aggregate_prompt},
        ],
        temperature=0.7,
        max_tokens=750,
    )
    return response.choices[0].message.content.strip()



#Pipeline 2: PDF → OCR → GPT Story
def pdf_ocr_to_story(pdf_path: str, temp_folder: str) -> str:
    """
    Pipeline 2: PDF → Images → OCR → GPT Story (batched OCR to GPT, then aggregate)
    """
    # Convert PDF to images
    page_images = pdf_to_images(pdf_path, temp_folder)
    # Run OCR on each image
    ocr_texts = [run_ocr_on_image(img) for img in page_images]

    # Batch OCR texts in chunks of 3, send to GPT for narration per batch
    page_summaries = []
    for i in range(0, len(page_images), 3):
        chunk_ocr = ocr_texts[i : i + 3]
        chunk_prompt = (
            "You are a story-writing assistant. Here are OCR-extracted texts from consecutive comic pages:\n\n"
        )
        for idx, ocr in enumerate(chunk_ocr, start=1):
            chunk_prompt += f"--- Page {i+idx} ---\n{ocr.strip()}\n\n"
        chunk_prompt += (
            "For each page, write a detailed narration labeled as 'Page 1:', 'Page 2:', etc. "
            "Include characters, actions, settings, and dialogues."
        )
        response = safe_openai_call(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a story-writing assistant."},
                {"role": "user", "content": chunk_prompt},
            ],
            temperature=0.7,
            max_tokens=750,
        )
        combined = response.choices[0].message.content.strip()
        pattern = r"Page\s*(\d+):\s*(.*?)(?=Page\s*\d+:|$)"
        matches = re.finditer(pattern, combined, re.DOTALL)
        for match in matches:
            text = match.group(2).strip()
            page_summaries.append(text)

    # Aggregate all page_summaries into one story
    aggregate_prompt = (
        "I have a comic that spans several pages. For each page, I already have a detailed "
        "narration of what is happening (in chronological order). Here are the narrations:\n\n"
    )
    for idx, desc in enumerate(page_summaries, start=1):
        aggregate_prompt += f"--- Page {idx} ---\n{desc}\n\n"
    aggregate_prompt += (
        "Please combine and rewrite all of these page descriptions into a single, coherent short story. "
        "Keep it concise (about 300–400 words), maintain narrative flow, and preserve character names or details."
    )

    response = safe_openai_call(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a story-writing assistant."},
            {"role": "user", "content": aggregate_prompt},
        ],
        temperature=0.7,
        max_tokens=750,
    )
    return response.choices[0].message.content.strip()

#Pipeline 3: PDF → Images→ GPT Story  Baseline

def pdf_image_to_story(pdf_path: str, temp_folder: str) -> str:
    """
    Pipeline: PDF → Images → GPT-4o (no OCR) → Story
    Converts all PDF pages to images and sends ALL images at once to GPT-4o for a single story.
    """
    # Step 1: Convert PDF to images
    page_images = pdf_to_images(pdf_path, temp_folder)

    # Step 2: Send all images at once to GPT-4o (no OCR)
    prompt = (
        "You are a comic-book interpreter. I will send you all pages of a comic as images. "
        "Please write a single, coherent short story (about 300–400 words) that narrates the entire comic. "
        "Include characters, actions, settings, and dialogues. Preserve character names and narrative flow."
    )

    # Prepare user content: prompt + all images
    user_content = [{"type": "text", "text": prompt}]
    for img_path in page_images:
        with open(img_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
        })

    response = safe_openai_call(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that reads comics."},
            {"role": "user", "content": user_content}
        ],
        temperature=0.7,
        max_tokens=750,
    )
    return response.choices[0].message.content.strip()
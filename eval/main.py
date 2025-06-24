from dotenv import load_dotenv
import os
from utils import pdf_to_images, run_ocr_on_image , describe_comic_pages_with_gpt4o
from pipeline import process_entire_comic, pdf_ocr_to_story, pdf_image_to_story
from eval import get_eval_data
import glob
import pandas as pd

os.environ["TOKENIZERS_PARALLELISM"] = "false"

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

#pdf_path = "Comic_book_English.pdf"  # or your actual PDF file path

'''
# Example usage: of pdf_to_images function 
if __name__ == "__main__":
    output_folder = "comic_pages"
    extracted = pdf_to_images(pdf_path, output_folder)
    print(f"Saved {len(extracted)} pages to → {output_folder}")


# Example usage: of OCR function
if __name__ == "__main__":
    sample_img = "comic_pages/page_001.png"
    ocr_text = run_ocr_on_image(sample_img)
    print("OCR output:")
    print(ocr_text)

# Example usage: of GPT-4o for comic page descriptions
if __name__ == "__main__":
    # Suppose you have up to 5 PNG pages and optional OCR text
    pages = [
        "comic_pages/page_001.png",
        "comic_pages/page_002.png",
    ]
    ocrs = [run_ocr_on_image(p) for p in pages]

    result = describe_comic_pages_with_gpt4o(
        image_paths=pages,
        ocr_texts=ocrs,
        model="gpt-4o-mini",
        temperature=0.5,
        max_tokens=500
    )
    print("=== Combined Page Narrations ===")
    print(result)


# Example usage: of the entire comic processing pipeline 
# PDF -> OCR + Images (batched) -> GPT-4o for page narrations -> Aggregate into short story
if __name__ == "__main__":
    story_ocr_image = process_entire_comic("my_comic.pdf", temp_folder="comic_pages")
    print("=== Final Short Story ===\n")
    print(story_ocr_image)


# Example: Get the output of pdf_ocr_to_story API
#Pipeline 2: PDF → OCR → GPT Story
if __name__ == "__main__":
    story_ocr = pdf_ocr_to_story(pdf_path, temp_folder="comic_pages")
    print("=== Output of pdf_ocr_to_story ===\n")
    print(story_ocr)

if __name__ == "__main__":
    # Example: Get the output of pdf_image_to_story API
    #Pipeline 3: PDF → Images→ GPT Story  Baseline
    story_image = pdf_image_to_story(pdf_path, temp_folder="comic_pages")
    print("=== Output of pdf_image_to_story ===\n")
    print(story_image)



'''



pdf_files = glob.glob("*.pdf")
all_results = []
failed_pdfs = []

for pdf_path in pdf_files:
    try:
        print(f"Processing: {pdf_path}")
        story_image = pdf_image_to_story(pdf_path, temp_folder="comic_pages")
        print("=== Output of pdf_image_to_story completed===\n")
        story_ocr = pdf_ocr_to_story(pdf_path, temp_folder="comic_pages")
        print("=== Output of pdf_ocr_to_story completed===\n")
        story_ocr_image = process_entire_comic(pdf_path, temp_folder="comic_pages")
        print("=== Output of process_entire_comic completed===\n")
        df = get_eval_data(story_image, story_ocr, story_ocr_image)
        df["PDF"] = pdf_path
        # Save individual result
        df.to_csv(f"eval_{os.path.splitext(os.path.basename(pdf_path))[0]}.csv", index=False)
        all_results.append(df)
        # Save combined results so far (acts as a checkpoint)
        pd.concat(all_results, ignore_index=True).to_csv("all_comic_eval_results.csv", index=False)
        print(f"Saved results for {pdf_path}")
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        failed_pdfs.append(pdf_path)
        continue

if failed_pdfs:
    print("The following PDFs failed and were not processed:")
    for pdf in failed_pdfs:
        print(pdf)
else:
    print("All PDFs processed successfully.")

print("Final results saved to all_comic_eval_results.csv")


'''
# Pipeline 1: Direct PDF -> Images to GPT
story_image = pdf_image_to_story(pdf_path, temp_folder="comic_pages")
print("=== Output of pdf_image_to_story completed===\n")

# Pipeline 2: PDF → Images -> OCR → GPT
story_ocr = pdf_ocr_to_story(pdf_path, temp_folder="comic_pages")
print("=== Output of pdf_ocr_to_story completed===\n")

# Pipeline 3: PDF → Images + OCR GPT (no OCR)
story_ocr_image = process_entire_comic(pdf_path, temp_folder="comic_pages")
print("=== Output of process_entire_comic completed===\n")

# Get evaluation data
df = get_eval_data(story_image, story_ocr, story_ocr_image)
print(df)
'''

'''
# Use below code if you have pairs of PDF and ground truth text files
# Load the PDF and ground truth text pairs
pairs_df = pd.read_csv("pdf_txt_pairs.csv")

all_results = []
failed_pdfs = []

for idx, row in pairs_df.iterrows():
    pdf_path = row["pdf"]
    txt_path = row["txt"]
    try:
        print(f"Processing: {pdf_path}")
        # Read ground truth text
        with open(txt_path, "r", encoding="utf-8") as f:
            ground_truth = f.read()
        # Run your other pipelines as usual
        story_ocr = pdf_ocr_to_story(pdf_path, temp_folder="comic_pages")
        print("=== Output of pdf_ocr_to_story completed===\n")
        story_ocr_image = process_entire_comic(pdf_path, temp_folder="comic_pages")
        print("=== Output of process_entire_comic completed===\n")
        # Use ground truth as the baseline
        df = get_eval_data(ground_truth, story_ocr, story_ocr_image, ground_truth=ground_truth)
        df["PDF"] = pdf_path
        # Save individual result
        df.to_csv(f"eval_{os.path.splitext(os.path.basename(pdf_path))[0]}.csv", index=False)
        all_results.append(df)
        # Save combined results so far (acts as a checkpoint)
        pd.concat(all_results, ignore_index=True).to_csv("all_comic_eval_results.csv", index=False)
        print(f"Saved results for {pdf_path}")
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        failed_pdfs.append(pdf_path)
        continue

if failed_pdfs:
    print("The following PDFs failed and were not processed:")
    for pdf in failed_pdfs:
        print(pdf)
else:
    print("All PDFs processed successfully.")

print("Final results saved to all_comic_eval_results.csv")

'''
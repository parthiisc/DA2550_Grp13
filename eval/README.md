# Comic-to-Story Pipeline

This project provides a complete pipeline for extracting meaningful story narratives from comic PDF files using OCR, image processing, and GPT-based summarization.

## 🔧 Repository Structure

- `main.py` – Entry point to process multiple comic PDFs using different pipeline variants (OCR_TO_GPT, Images_to_OCR_to_GPT, Baseline).
- `pipeline.py` – Contains high-level pipeline functions for processing comics end-to-end.
- `utils.py` – Utility functions for PDF-to-image conversion, OCR execution, and GPT-based story generation.
- `eval.py` – Evaluation module that compares pipeline outputs using readability, BERTScore, and cosine similarity.

## 📦 Setup

Make sure to install the dependencies and set your OpenAI API key:

```bash
pip install -r requirements.txt
export OPENAI_API_KEY='your-api-key'
```

## 🚀 Usage

### Note 
Make sure that all the comic pdf are present in `eval` folder

### Run full evaluation on all PDFs in current directory:
```bash
python main.py
```

This will:
1. Convert each PDF into images and extract OCR text.
2. Run story generation using three pipelines.
3. Evaluate each output and save results as CSVs.

### Run a specific pipeline manually:
In `main.py`, uncomment the block you want to run:
- `pdf_image_to_story()` – Baseline (Image_to_GPT)
- `pdf_ocr_to_story()` – OCR_TO_GPT
- `process_entire_comic()` – Images_to_OCR_to_GPT

## 📊 Evaluation Metrics

Each pipeline is evaluated using:
- **FRE (Flesch Reading Ease)**
- **FKG (Flesch-Kincaid Grade Level)**
- **Word Count**
- **BERTScore** vs baseline
- **Cosine Similarity** vs baseline

Results are stored in:
- `eval_<filename>.csv`
- `all_comic_eval_results.csv`

## 📁 Output

- Generated stories
- Evaluation CSVs
- Temporary image folders (e.g., `comic_pages/`)

## 📌 Notes

- Ensure `comic_pages/` is cleaned if rerunning multiple times.
- This setup assumes the PDFs are comics with visual and textual content.



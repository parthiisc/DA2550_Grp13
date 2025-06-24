# ComicVerse: AI Comic Story & Audio Lab

ComicVerse is a multimodal deep learning application that transforms comic PDFs into engaging narrative stories and audiobooks. Powered by OCR, vision-language models, and neural TTS, ComicVerse enables users to upload comics, select storytelling style, generate audio, and interact with an AI chatbot—all through a modern Streamlit web interface.

---

## 🚀 Step-by-Step Usage

1. **Upload Comic PDF:**
   - Use the Streamlit UI to upload your comic in PDF format.
2. **Select Story Style:**
   - Choose from Neutral, Dramatic, or Fun storytelling styles.
3. **Generate Output:**
   - Generate the story, audiobook, or both with a single click.
4. **Download & Interact:**
   - Download the generated story and audio, and chat with the AI about your comic’s content.

---

## 🛠️ Tech Stack
- **Python 3.10+**
- **Streamlit** (web UI)
- **OpenAI GPT-4o / GPT-4o-mini** (vision-language and story generation)
- **Tesseract OCR** (text extraction)
- **pdf2image, Pillow** (PDF/image processing)
- **python-dotenv** (environment management)

---

## 📦 Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/parthiisc/DA2550_Grp13
cd DA2550_Grp13
```

### 2. Install Python dependencies
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Install System Dependencies
- **Poppler** (for PDF to image conversion)
    - Download from: https://github.com/oschwartz10612/poppler-windows/releases/
    - Add the `bin` directory (e.g., `C:\poppler-23.11.0\Library\bin`) to your PATH.
- **Tesseract OCR**
    - Download from: https://github.com/tesseract-ocr/tesseract/wiki#windows
    - Add `C:\Program Files\Tesseract-OCR` to your PATH.

> **Note:** If you installed Poppler in a different location, update the `poppler_path` argument in the `pdf_to_images` function inside `comicToStory_audio_batching.py` to match your Poppler `bin` directory (e.g., `C:\poppler-23.11.0\Library\bin`).

### 4. Set up OpenAI API Key
- Create a `.env` file in the project root:
  ```
  OPENAI_API_KEY=your_openai_key_here
  ```

---

## ▶️ Running the App

```bash
streamlit run app.py
```

- The app will open in your browser. Upload a comic PDF and follow the on-screen instructions.
- You can also use the `comicToStory_audio_batching.py` module directly for batch processing and automation.

---

## ✨ Features
- Upload comic PDFs and process them end-to-end
- Choose storytelling style (neutral, dramatic, fun)
- Generate and download both story and audiobook
- Translate stories to Hindi
- Chatbot for interactive Q&A about the generated story
- Modern, accessible UI with tooltips and progress indicators

---

## 📄 License
This project is for educational use




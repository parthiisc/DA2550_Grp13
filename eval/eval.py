import pandas as pd
import numpy as np
import textstat
from bert_score import score
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

use_ground_truth = True

# API to compute readability scores
def compute_readability(text):
    return {
        "flesch_reading_ease": textstat.flesch_reading_ease(text),
        "flesch_kincaid_grade": textstat.flesch_kincaid_grade(text)
    }

# API to calulate the BERTScore
def compute_bertscore(candidate, reference):
    
    P, R, F1 = score([candidate], [reference], lang="en", verbose=False)
    return {
        "precision": float(P[0]),
        "recall": float(R[0]),
        "f1": float(F1[0])
    }

# API to compute Cosine similarity using sentence-transformers
model = SentenceTransformer('all-MiniLM-L6-v2')
def compute_cosine_similarity(text1, text2):
    emb1 = model.encode([text1])[0]
    emb2 = model.encode([text2])[0]
    sim = cosine_similarity([emb1], [emb2])[0][0]
    return float(sim)

# Compute all evaluation metrics for the given stories
def get_eval_data(story_image, story_ocr, story_ocr_image):
    readability_image = compute_readability(story_image)
    readability_ocr = compute_readability(story_ocr)
    readability_ocr_image = compute_readability(story_ocr_image)

    word_count_image = len(story_image.split())
    word_count_ocr = len(story_ocr.split())
    word_count_ocr_image = len(story_ocr_image.split())

    bertscore_ocr_vs_image = compute_bertscore(story_ocr, story_image)
    bertscore_ocr_image_vs_image = compute_bertscore(story_ocr_image, story_image)

    similarity_ocr_vs_image = compute_cosine_similarity(story_ocr, story_image)
    similarity_ocr_image_vs_image = compute_cosine_similarity(story_ocr_image, story_image)
    # Build evaluation matrix
    eval_data = {
        "Metric": [
            "Readability (FRE)",
            "Readability (FKG)",
            "Word Count",
            "BERTScore vs Baseline",
            "Cosine Similarity vs Baseline"
        ],
        "OCR+GPT": [
            round(readability_ocr["flesch_reading_ease"], 2),
            round(readability_ocr["flesch_kincaid_grade"], 2),
            word_count_ocr,
            round(bertscore_ocr_vs_image["f1"], 3),
            round(similarity_ocr_vs_image, 3)
        ],
        "Images+OCR+GPT": [
            round(readability_ocr_image["flesch_reading_ease"], 2),
            round(readability_ocr_image["flesch_kincaid_grade"], 2),
            word_count_ocr_image,
            round(bertscore_ocr_image_vs_image["f1"], 3),
            round(similarity_ocr_image_vs_image, 3)
        ],
        "Baseline Pipeline(Image+GPT)": [
            round(readability_image["flesch_reading_ease"], 2),
            round(readability_image["flesch_kincaid_grade"], 2),
            word_count_image,
        ]
    }
    return pd.DataFrame(eval_data)


'''
# Use this API if you have ground truth story text to compare
def get_eval_data(story_image, story_ocr, story_ocr_image, ground_truth=None):
    readability_image = compute_readability(story_image)
    readability_ocr = compute_readability(story_ocr)
    readability_ocr_image = compute_readability(story_ocr_image)

    word_count_image = len(story_image.split())
    word_count_ocr = len(story_ocr.split())
    word_count_ocr_image = len(story_ocr_image.split())

    bertscore_ocr_vs_image = compute_bertscore(story_ocr, story_image)
    bertscore_ocr_image_vs_image = compute_bertscore(story_ocr_image, story_image)

    similarity_ocr_vs_image = compute_cosine_similarity(story_ocr, story_image)
    similarity_ocr_image_vs_image = compute_cosine_similarity(story_ocr_image, story_image)

    # If ground truth is provided, compute metrics vs ground truth
    if ground_truth is not None:
        bertscore_image_vs_gt = compute_bertscore(story_image, ground_truth)
        bertscore_ocr_vs_gt = compute_bertscore(story_ocr, ground_truth)
        bertscore_ocr_image_vs_gt = compute_bertscore(story_ocr_image, ground_truth)
        cosine_image_vs_gt = compute_cosine_similarity(story_image, ground_truth)
        cosine_ocr_vs_gt = compute_cosine_similarity(story_ocr, ground_truth)
        cosine_ocr_image_vs_gt = compute_cosine_similarity(story_ocr_image, ground_truth)
    else:
        bertscore_image_vs_gt = {"f1": np.nan}
        bertscore_ocr_vs_gt = {"f1": np.nan}
        bertscore_ocr_image_vs_gt = {"f1": np.nan}
        cosine_image_vs_gt = np.nan
        cosine_ocr_vs_gt = np.nan
        cosine_ocr_image_vs_gt = np.nan

    eval_data = {
        "Metric": [
            "Readability (FRE)",
            "Readability (FKG)",
            "Word Count",
            "BERTScore vs Baseline",
            "Cosine Similarity vs Baseline",
            "BERTScore vs GroundTruth",
            "Cosine Similarity vs GroundTruth"
        ],
        "OCR+GPT": [
            round(readability_ocr["flesch_reading_ease"], 2),
            round(readability_ocr["flesch_kincaid_grade"], 2),
            word_count_ocr,
            round(bertscore_ocr_vs_image["f1"], 3),
            round(similarity_ocr_vs_image, 3),
            round(bertscore_ocr_vs_gt["f1"], 3),
            round(cosine_ocr_vs_gt, 3)
        ],
        "Images+OCR+GPT": [
            round(readability_ocr_image["flesch_reading_ease"], 2),
            round(readability_ocr_image["flesch_kincaid_grade"], 2),
            word_count_ocr_image,
            round(bertscore_ocr_image_vs_image["f1"], 3),
            round(similarity_ocr_image_vs_image, 3),
            round(bertscore_ocr_image_vs_gt["f1"], 3),
            round(cosine_ocr_image_vs_gt, 3)
        ],
        "Baseline Pipeline(Image+GPT)": [
            round(readability_image["flesch_reading_ease"], 2),
            round(readability_image["flesch_kincaid_grade"], 2),
            word_count_image,
            np.nan,
            np.nan,
            round(bertscore_image_vs_gt["f1"], 3),
            round(cosine_image_vs_gt, 3)
        ]
    }
    return pd.DataFrame(eval_data)
'''    
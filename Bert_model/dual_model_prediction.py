import pandas as pd
import torch
import pickle
from transformers import BertTokenizer, BertForSequenceClassification
from tqdm import tqdm
import os

# --- 1. SETUP & PATHS ---
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_1_path = "./final_bloom_bert"
model_2_path = "./final_bloom_bert_augmented"
encoder_path = "label_encoder.pkl"
input_file = "D:/new_hopes/Blooms_Phase_4/Bert_model/testing data/QP_Complete 1.xlsx"

print(f"Using device: {device}")

# --- 2. LOAD TOOLS ---
with open(encoder_path, 'rb') as f:
    le = pickle.load(f)

def get_predictions(model_path, questions):
    """Utility to run inference on a specific model version"""
    tokenizer = BertTokenizer.from_pretrained(model_path)
    model = BertForSequenceClassification.from_pretrained(model_path).to(device)
    model.eval()
    
    preds = []
    with torch.no_grad():
        for q in tqdm(questions, desc=f"Predicting with {os.path.basename(model_path)}"):
            inputs = tokenizer(q, return_tensors="pt", truncation=True, padding=True, max_length=128).to(device)
            outputs = model(**inputs)
            pred_idx = torch.argmax(outputs.logits, dim=-1).item()
            preds.append(le.inverse_transform([pred_idx])[0])
    return preds

# --- 3. DATA LOADING ---
# Reading without header because the file structure showed questions in the second column
df_input = pd.read_excel(input_file, header=None)

# Identify the column containing the questions (usually the one with string data)
# Based on your file structure, it's the second column (index 1)
questions = df_input.iloc[:, 1].astype(str).tolist()

# --- 4. RUN INFERENCE ---
print("\n--- Starting Inference for Model 1 (Baseline) ---")
preds_model_1 = get_predictions(model_1_path, questions)

print("\n--- Starting Inference for Model 2 (Augmented) ---")
preds_model_2 = get_predictions(model_2_path, questions)

# --- 5. GENERATE OUTPUTS ---
# File 1: Model 1 Output
df_m1 = pd.DataFrame({'Question': questions, 'Predicted_Bloom_Level': preds_model_1})
df_m1.to_csv('predictions_model_1.csv', index=False)

# File 2: Model 2 Output
df_m2 = pd.DataFrame({'Question': questions, 'Predicted_Bloom_Level': preds_model_2})
df_m2.to_csv('predictions_model_2.csv', index=False)

# File 3: Comparison Output
df_comparison = pd.DataFrame({
    'Question': questions,
    'Model_1_Baseline': preds_model_1,
    'Model_2_Augmented': preds_model_2
})

# Add a flag to easily see where they disagree in your research
df_comparison['Agreement'] = df_comparison['Model_1_Baseline'] == df_comparison['Model_2_Augmented']
df_comparison.to_csv('model_comparison_results.csv', index=False)

print("\n" + "="*30)
print("✅ PREDICTION COMPLETE")
print(f"1. Model 1 Results: predictions_model_1.csv")
print(f"2. Model 2 Results: predictions_model_2.csv")
print(f"3. Comparison: model_comparison_results.csv")
print("="*30)
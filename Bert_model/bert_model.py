import pandas as pd
import numpy as np
import torch
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from transformers import (
    BertTokenizer, 
    BertForSequenceClassification, 
    TrainingArguments, 
    Trainer
)
import evaluate

# --- 1. DEFINE DEVICE (Fixes the NameError) ---
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Is CUDA available? {torch.cuda.is_available()}")
print(f"GPU Name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}")
print(f"🚀 Training will run on: {device}")

# --- 2. DATA PREPARATION ---
# Ensure bloom_dataset.csv is in the same folder as this script
df = pd.read_csv('bloom_dataset.csv')
le = LabelEncoder()
df['labels'] = le.fit_transform(df['label'])

# Save the label mapping for later use
with open('label_encoder.pkl', 'wb') as f:
    pickle.dump(le, f)

train_texts, val_texts, train_labels, val_labels = train_test_split(
    df['question'].tolist(), 
    df['labels'].tolist(), 
    test_size=0.2, 
    stratify=df['labels'],
    random_state=42
)

# --- 3. TOKENIZATION & DATASET ---
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

class BloomDataset(torch.utils.data.Dataset):
    def __init__(self, texts, labels):
        self.encodings = tokenizer(texts, truncation=True, padding=True, max_length=128)
        self.labels = labels
    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item
    def __len__(self):
        return len(self.labels)

train_dataset = BloomDataset(train_texts, train_labels)
val_dataset = BloomDataset(val_texts, val_labels)

# --- 4. MODEL LOADING ---
model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=6)
model.to(device) # Moves model to your RTX 4050

# --- 5. METRICS ---
acc_metric = evaluate.load("accuracy")
f1_metric = evaluate.load("f1")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    acc = acc_metric.compute(predictions=predictions, references=labels)
    f1 = f1_metric.compute(predictions=predictions, references=labels, average="macro")
    return {**acc, **f1}

# --- 6. TRAINING ARGUMENTS ---
training_args = TrainingArguments(
    output_dir="./bloom_results",
    eval_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=16, # Optimized for 6GB VRAM
    per_device_eval_batch_size=16,
    num_train_epochs=4,
    weight_decay=0.01,
    fp16=True,                     # Uses Tensor Cores on your 4050 for speed
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    logging_steps=20,
    report_to="none"
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics,
)

# --- 7. START TRAINING ---
if __name__ == "__main__":
    print("\nStarting Fine-tuning...")
    trainer.train()

    # Final Save
    model.save_pretrained("./final_bloom_bert")
    tokenizer.save_pretrained("./final_bloom_bert")
    print("\n✅ Training Complete. Model saved to ./final_bloom_bert")
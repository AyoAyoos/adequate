import pandas as pd
import numpy as np
import torch
import pickle
import json
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
from transformers import BertTokenizer, BertForSequenceClassification, Trainer

# --- 1. SETUP & PATHS (UPDATED FOR AUGMENTED MODEL) ---
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_path = "./final_bloom_bert_augmented"      # Updated path
encoder_path = "label_encoder.pkl"
dataset_path = "QP_Complete_1.csv"         # Updated dataset
checkpoint_dir = "./bloom_augmented_results"     # Updated results dir

print(f"Using device: {device}")

# --- 2. LOAD SAVED OBJECTS ---
with open(encoder_path, 'rb') as f:
    le = pickle.load(f)

tokenizer = BertTokenizer.from_pretrained(model_path)
model = BertForSequenceClassification.from_pretrained(model_path).to(device)

# --- 3. RE-PREPARE VALIDATION DATA (MATCHING AUGMENTED SPLIT) ---
df = pd.read_csv(dataset_path)
df['labels'] = le.transform(df['label'])

# Using identical split parameters to your training script[cite: 2]
_, val_texts, _, val_labels = train_test_split(
    df['question'].tolist(), 
    df['labels'].tolist(), 
    test_size=0.2, 
    stratify=df['labels'],
    random_state=42
)

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

val_dataset = BloomDataset(val_texts, val_labels)

# --- 4. INITIALIZE TRAINER FOR PREDICTION ---
trainer = Trainer(model=model)

# --- 5. GRAPH 1: TRAINING HISTORY ---
history_file = os.path.join(checkpoint_dir, "trainer_state.json")

if os.path.exists(history_file):
    with open(history_file, 'r') as f:
        state = json.load(f)
        history = state['log_history']

    train_loss = [x['loss'] for x in history if 'loss' in x]
    eval_loss = [x['eval_loss'] for x in history if 'eval_loss' in x]
    eval_acc = [x['eval_accuracy'] for x in history if 'eval_accuracy' in x]

    plt.figure(figsize=(12, 5))

    plt.subplot(1, 2, 1)
    plt.plot(train_loss, label='Train Loss', color='#1f77b4')
    plt.plot(np.linspace(0, len(train_loss), len(eval_loss)), eval_loss, label='Eval Loss', color='#ff7f0e', marker='o')
    plt.title('Augmented Model: Train vs Eval Loss')
    plt.xlabel('Logging Steps')
    plt.ylabel('Loss')
    plt.legend()

    plt.subplot(1, 2, 2)
    plt.plot(eval_acc, label='Eval Accuracy', color='#2ca02c', marker='s')
    plt.title('Augmented Model: Eval Accuracy')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.legend()

    plt.tight_layout()
    plt.savefig('learning_curves_augmented.png') # Renamed for version control
    plt.show()
else:
    print(f"Warning: {history_file} not found. Check if checkpoint_dir is correct.")

# --- 6. GRAPH 2: CONFUSION MATRIX ---
print("Generating predictions...")
output = trainer.predict(val_dataset)
y_pred = np.argmax(output.predictions, axis=-1)
y_true = output.label_ids

cm = confusion_matrix(y_true, y_pred)
plt.figure(figsize=(10, 8))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=le.classes_, yticklabels=le.classes_)
plt.title('Confusion Matrix: Augmented Bloom BERT')
plt.ylabel('Actual Label')
plt.xlabel('Predicted Label')
plt.savefig('confusion_matrix_augmented.png')
plt.show()

# --- 7. GRAPH 3: PER-CLASS F1 SCORE ---
report = classification_report(y_true, y_pred, target_names=le.classes_, output_dict=True)
df_report = pd.DataFrame(report).transpose().iloc[:6, :] 

plt.figure(figsize=(10, 6))
sns.barplot(x=df_report.index, y=df_report['f1-score'], palette='magma')
plt.axhline(df_report['f1-score'].mean(), color='red', linestyle='--', label='Average F1')
plt.title('F1-Score per Level (Augmented Model)')
plt.ylabel('F1-Score')
plt.ylim(0, 1)
plt.legend()
plt.savefig('per_class_f1_augmented.png')
plt.show()

# --- 8. AUDIT: AUGMENTED MODEL ERRORS ---
errors = pd.DataFrame({
    'Question': val_texts,
    'Actual': le.inverse_transform(y_true),
    'Predicted': le.inverse_transform(y_pred)
})
errors = errors[errors['Actual'] != errors['Predicted']]
errors.to_csv('misclassified_samples_augmented.csv', index=False)
print(f"Audit complete: {len(errors)} errors saved.")
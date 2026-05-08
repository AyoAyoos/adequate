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

# --- 1. SETUP & PATHS ---
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_path = "./final_bloom_bert_augmented"      
encoder_path = "label_encoder.pkl"
dataset_path = "final_training_data.csv"         
checkpoint_dir = "./bloom_augmented_results"     

print(f"Using device: {device}")

# --- 2. LOAD SAVED OBJECTS ---
with open(encoder_path, 'rb') as f:
    le = pickle.load(f)

tokenizer = BertTokenizer.from_pretrained(model_path)
model = BertForSequenceClassification.from_pretrained(model_path).to(device)

# --- 3. RE-PREPARE VALIDATION DATA ---
df = pd.read_csv(dataset_path)
df['labels'] = le.transform(df['label'])

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

# --- 4. INITIALIZE TRAINER & PREDICT ---
trainer = Trainer(model=model)
print("Generating predictions...")
output = trainer.predict(val_dataset)
y_pred = np.argmax(output.predictions, axis=-1)
y_true = output.label_ids

# --- 5. CALCULATE LEVEL-WISE ACCURACY ---
# Recall for a specific class = True Positives / (True Positives + False Negatives)
# This is mathematically the accuracy for that specific level.
report = classification_report(y_true, y_pred, target_names=le.classes_, output_dict=True)
df_report = pd.DataFrame(report).transpose().iloc[:-3, :] # Remove avg/total rows

# Add a specific Accuracy column (naming 'recall' as 'accuracy' for clarity)
df_report['level_accuracy'] = df_report['recall'] * 100 

print("\n--- Level-Wise Accuracy Results ---")
print(df_report[['level_accuracy']].to_string(formatters={'level_accuracy': '{:,.2f}%'.format}))

# --- 6. VISUALIZATION: LEVEL-WISE ACCURACY ---
plt.figure(figsize=(10, 6))
# Using a clear color palette to distinguish levels
colors = sns.color_palette("viridis", len(df_report))
ax = sns.barplot(x=df_report.index, y=df_report['level_accuracy'], palette=colors)

# Add percentage labels on top of bars
for p in ax.patches:
    ax.annotate(f'{p.get_height():.1f}%', 
                (p.get_x() + p.get_width() / 2., p.get_height()), 
                ha = 'center', va = 'center', 
                xytext = (0, 9), 
                textcoords = 'offset points',
                fontsize=11, weight='bold')

plt.title('Accuracy per Bloom\'s Taxonomy Level', fontsize=14)
plt.ylabel('Accuracy (%)', fontsize=12)
plt.xlabel('Taxonomy Level', fontsize=12)
plt.ylim(0, 110) # Give room for labels
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.savefig('level_wise_accuracy.png')
plt.show()

# --- 7. CONFUSION MATRIX (RETAINED FOR CONTEXT) ---
cm = confusion_matrix(y_true, y_pred)
plt.figure(figsize=(10, 8))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=le.classes_, yticklabels=le.classes_)
plt.title('Confusion Matrix: Augmented Bloom BERT')
plt.ylabel('Actual Level')
plt.xlabel('Predicted Level')
plt.show()
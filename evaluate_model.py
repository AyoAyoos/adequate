import pandas as pd
import torch
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from itertools import cycle

from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, roc_curve, auc
from sklearn.preprocessing import label_binarize
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from torch.utils.data import DataLoader, TensorDataset, SequentialSampler

# --- 1. CONFIGURATION ---
MODEL_PATH = 'content/bloom_bert_model'
# Use forward slashes for cross-platform compatibility
TEST_DATA_PATH = 'D:/new_hopes/Blooms_Phase_4/Model/bloom_dataset.csv'
BATCH_SIZE = 16
# Define your class names here for easy access in plots
CLASS_NAMES = ['L1', 'L2', 'L3', 'L4', 'L5', 'L6']
N_CLASSES = len(CLASS_NAMES)

# --- 2. GPU / DEVICE SETUP ---
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"--- Using device: {DEVICE} ---")

# --- 3. LOAD YOUR TRAINED MODEL AND TOKENIZER ---
print(f"Loading model from {MODEL_PATH}")
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model.to(DEVICE)
model.eval()  # Set the model to evaluation mode

# --- 4. PREPARE YOUR TEST DATA ---
print(f"Loading and tokenizing test data from {TEST_DATA_PATH}")
df_test = pd.read_csv(TEST_DATA_PATH)

# Use the correct column name 'question'
test_texts = df_test['question'].tolist()

# Convert string labels ('L1', 'L2', etc.) to integers (0, 1, etc.)
label_map = {name: i for i, name in enumerate(CLASS_NAMES)}
true_labels = df_test['label'].map(label_map).tolist()

if any(label is None for label in true_labels):
    raise ValueError("ERROR: One or more labels in your CSV could not be found in the label_map.")
else:
    print("Successfully converted all labels to numbers.")

# Tokenize all sentences and map tokens to their word IDs.
input_ids, attention_masks = [], []
for text in test_texts:
    encoded_dict = tokenizer.encode_plus(
        text, add_special_tokens=True, max_length=128,
        padding='max_length', truncation=True,
        return_attention_mask=True, return_tensors='pt'
    )
    input_ids.append(encoded_dict['input_ids'])
    attention_masks.append(encoded_dict['attention_mask'])

input_ids = torch.cat(input_ids, dim=0)
attention_masks = torch.cat(attention_masks, dim=0)
labels = torch.tensor(true_labels)

# Create the DataLoader.
test_dataset = TensorDataset(input_ids, attention_masks, labels)
test_dataloader = DataLoader(test_dataset, sampler=SequentialSampler(test_dataset), batch_size=BATCH_SIZE)

# --- 5. MAKE PREDICTIONS & GET PROBABILITIES ---
print("Making predictions on the test set...")
all_predictions = []
all_probs = []
with torch.no_grad():
    for batch in test_dataloader:
        batch_input_ids, batch_attention_mask = batch[0].to(DEVICE), batch[1].to(DEVICE)
        outputs = model(batch_input_ids, attention_mask=batch_attention_mask)
        logits = outputs.logits
        
        # Store predictions
        predictions = torch.argmax(logits, dim=1).flatten()
        all_predictions.extend(predictions.cpu().numpy())
        
        # Store probabilities for ROC curve
        probs = torch.nn.functional.softmax(logits, dim=1)
        all_probs.extend(probs.cpu().numpy())

y_score = np.array(all_probs)

# --- 6. CALCULATE AND PRINT METRICS ---
print("\n--- EVALUATION RESULTS ---")
accuracy = accuracy_score(true_labels, all_predictions)
print(f"Accuracy: {accuracy:.4f}")

print("\nClassification Report:")
print(classification_report(true_labels, all_predictions, target_names=CLASS_NAMES))

print("\nConfusion Matrix (raw numbers):")
print(confusion_matrix(true_labels, all_predictions))

# --- 7. GENERATE VISUALIZATIONS ---
print("\n--- Generating Visualizations ---")

# A. Confusion Matrix Heatmap
cm = confusion_matrix(true_labels, all_predictions)
fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax, xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES)
ax.set_title('Confusion Matrix')
ax.set_xlabel('Predicted Labels')
ax.set_ylabel('True Labels')
plt.savefig('confusion_matrix.png')
print("Confusion matrix heatmap saved as 'confusion_matrix.png'")
plt.show()

# B. Bar Chart for Precision, Recall, F1-Score
report = classification_report(true_labels, all_predictions, target_names=CLASS_NAMES, output_dict=True)
df_report = pd.DataFrame(report).transpose()
df_plot = df_report[['precision', 'recall', 'f1-score']].loc[CLASS_NAMES]
df_plot.plot(kind='bar', figsize=(12, 7))
plt.title('Performance Metrics per Class')
plt.ylabel('Score')
plt.xticks(rotation=45, ha='right')
plt.grid(axis='y', linestyle='--')
plt.legend(loc='lower right')
plt.tight_layout()
plt.savefig('metrics_bar_chart.png')
print("Metrics bar chart saved as 'metrics_bar_chart.png'")
plt.show()

# C. ROC Curve for Multiclass (One-vs-Rest)
y_test_binarized = label_binarize(true_labels, classes=list(range(N_CLASSES)))
fpr, tpr, roc_auc = dict(), dict(), dict()

for i in range(N_CLASSES):
    fpr[i], tpr[i], _ = roc_curve(y_test_binarized[:, i], y_score[:, i])
    roc_auc[i] = auc(fpr[i], tpr[i])

plt.figure(figsize=(10, 8))
colors = cycle(['aqua', 'darkorange', 'cornflowerblue', 'green', 'red', 'purple'])
for i, color in zip(range(N_CLASSES), colors):
    plt.plot(fpr[i], tpr[i], color=color, lw=2,
            label=f'ROC curve for {CLASS_NAMES[i]} (area = {roc_auc[i]:0.2f})')

plt.plot([0, 1], [0, 1], 'k--', lw=2)
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Multiclass Receiver Operating Characteristic (ROC)')
plt.legend(loc="lower right")
plt.savefig('roc_curve_multiclass.png')
print("Multiclass ROC Curve saved as 'roc_curve_multiclass.png'.")
plt.show()

print("\n--- Evaluation Complete ---")
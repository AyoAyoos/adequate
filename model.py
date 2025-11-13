import torch
from transformers import BertTokenizer, BertForSequenceClassification
import json

# --- 1. Load the model and tokenizer ONCE ---
MODEL_PATH = r'D:\new_hopes\Blooms_Phase_4\content\bloom_bert_model'
MAX_LEN = 128

# Set device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("Loading model...")
# Load the fine-tuned model and tokenizer
model = BertForSequenceClassification.from_pretrained(MODEL_PATH)
tokenizer = BertTokenizer.from_pretrained(MODEL_PATH)

# Load the label mappings
with open(f'{MODEL_PATH}/label_mappings.json', 'r') as f:
    label_mappings = json.load(f)
    id2label = {int(k): v for k, v in label_mappings['id2label'].items()}

# Move model to the correct device
model.to(device)
model.eval() # Set model to evaluation mode
print("Model loaded successfully on device:", device)


# --- 2. Prediction function ---
def predict_bloom_level(question_text):
    """
    Takes a question string and returns the predicted Bloom's level.
    """
    # Tokenize the input
    encoding = tokenizer.encode_plus(
        question_text,
        add_special_tokens=True,
        max_length=MAX_LEN,
        return_token_type_ids=False,
        padding='max_length',
        return_attention_mask=True,
        return_tensors='pt',
        truncation=True
    )

    input_ids = encoding['input_ids'].to(device)
    attention_mask = encoding['attention_mask'].to(device)

    # Get prediction
    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        logits = outputs.logits

    prediction_id = torch.argmax(logits, dim=1).item()
    predicted_label = id2label[prediction_id]

    return predicted_label
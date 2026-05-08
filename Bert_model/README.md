# Bert Model Folder Guide

This folder contains training, evaluation, and inference scripts for classifying questions into Bloom's Taxonomy levels using BERT.

## What Is Inside

- Training scripts for:
  - baseline model (`bert_model.py`)
  - augmented-data model (`train_augmented.py`)
- Analysis and visualization scripts:
  - baseline (`analysis.py`)
  - augmented (`analysis_augmented.py`)
  - level-wise accuracy focus (`level_wise.py`)
- Utility scripts:
  - dataset merge helper (`merge_data.py`)
  - dual-model batch prediction and comparison (`dual_model_prediction.py`)
- Trained model artifacts, checkpoints, figures, and label encoder files.

## Expected Data Files

Place the required CSV/XLSX inputs in this folder (or update script paths):

- `bloom_dataset.csv` (used by baseline training and baseline analysis)
- `augmented_bloom_keywords.csv` (used for merge)
- `final_training_data.csv` (used by augmented training and some analysis scripts)
- External test workbook currently referenced in `dual_model_prediction.py`:
  - `D:/new_hopes/Blooms_Phase_4/Bert_model/testing data/QP_Complete 1.xlsx`

## Python Dependencies

Install these packages before running:

- `torch`
- `transformers`
- `evaluate`
- `scikit-learn`
- `pandas`
- `numpy`
- `matplotlib`
- `seaborn`
- `openpyxl` (for Excel input in `dual_model_prediction.py`)
- `tqdm`

Example install:

```bash
pip install torch transformers evaluate scikit-learn pandas numpy matplotlib seaborn openpyxl tqdm
```

## Suggested Workflow

1. (Optional) Build combined training data:
   - Run `merge_data.py` to create `final_training_data.csv`.
2. Train baseline model:
   - Run `bert_model.py`.
   - Outputs:
     - checkpoints in `bloom_results/`
     - final model in `final_bloom_bert/`
     - `label_encoder.pkl`
3. Train augmented model:
   - Run `train_augmented.py`.
   - Outputs:
     - checkpoints in `bloom_augmented_results/`
     - final model in `final_bloom_bert_augmented/`
     - `label_encoder.pkl` (overwritten if re-run)
4. Evaluate and generate plots:
   - Baseline: run `analysis.py`
   - Augmented: run `analysis_augmented.py`
   - Level-wise chart: run `level_wise.py`
5. Compare both trained models on new data:
   - Run `dual_model_prediction.py`.

## Output Files You Will See

- Model folders:
  - `final_bloom_bert/`
  - `final_bloom_bert_augmented/`
- Training checkpoints:
  - `bloom_results/checkpoint-*/`
  - `bloom_augmented_results/checkpoint-*/`
- Evaluation artifacts (examples):
  - `confusion_matrix.png`
  - `confusion_matrix_augmented.png`
  - `per_class_f1.png`
  - `per_class_f1_augmented.png`
  - `level_wise_accuracy.png`
  - `misclassified_samples.csv`
  - `misclassified_samples_augmented.csv`
- Inference comparison outputs:
  - `predictions_model_1.csv`
  - `predictions_model_2.csv`
  - `model_comparison_results.csv`

## Notes

- All scripts are currently configured for 6 Bloom classes (`num_labels=6`).
- Training scripts auto-select GPU if CUDA is available.
- Keep `label_encoder.pkl` aligned with the model you are evaluating/inferencing.
- Some scripts use hardcoded paths/dataset names; adjust those paths if your file layout changes.

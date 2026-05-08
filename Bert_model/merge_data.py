import pandas as pd

df1 = pd.read_csv('bloom_dataset.csv')
df2 = pd.read_csv('augmented_bloom_keywords.csv')

# Combine and shuffle
df_combined = pd.concat([df1, df2], ignore_index=True).sample(frac=1).reset_index(drop=True)
df_combined.to_csv('final_training_data.csv', index=False)
import pandas as pd
from pathlib import Path
from agents.discriminator import get_base_chars
from tqdm import tqdm

def process_row(row, text_name='resumes_clean'):
    try:
        # Get discriminator predictions
        discrim_results = get_base_chars(row[text_name])
        
        # Return just the predictions we want to add as new columns
        return pd.Series({
            'race': discrim_results['json']['race'],
            'gender': discrim_results['json']['gender'],
            'age': discrim_results['json']['age'],
            'disability': discrim_results['json']['disability'], 
            'religion': discrim_results['json']['religion'],
            'pregnancy_status': discrim_results['json']['pregnancy_status'],
            'marital_status': discrim_results['json']['marital_status'],
            'veteran_status': discrim_results['json']['veteran_status'],
            'genetic_information': discrim_results['json']['genetic_information'],
            'citizen_immigration_status': discrim_results['json']['citizen_immigration_status']
        })
    except Exception as e:
        print(f"Error processing row: {str(e)}")
        return pd.Series([None] * 10)  # Return None for all columns

def main():
    ratings_df = pd.read_csv("./data/cleaned_resumes_with_ratings.csv")

    # Apply function to each row with progress bar and add as new columns
    predicted_cols = ratings_df.progress_apply(process_row, axis=1)
    ratings_demos_df = pd.concat([ratings_df, predicted_cols], axis=1)

    # Save intermediate results periodically
    ratings_demos_df.to_csv("./data/pre_dat.csv", index=False)

    # Filter to only show rows where numeric index columns (0-9) are not NaN
    numeric_cols = list(range(10))  # Columns labeled 0-9


import pandas as pd
from pathlib import Path
from tqdm import tqdm
import json
from agents.blinder import blinder
from agents.discriminator import discriminator
from agents.judge import judge
import os
from utils import generate_feedback

def process_row(row, max_iterations=5):
    data = {
        "text_0": row['resumes_clean'],
        "ID": row['ID']  # Add ID to the data dictionary
    }
    feedback = []
    prev_attempt = None
    
    for i in range(max_iterations):
        # Generate transformed text
        resp = blinder(row['resumes_clean'], prev_attempt, feedback)
        data[f"blinder_{i}"] = resp.content
        prev_attempt = resp.content
        
        # Get discriminator results
        discrim = discriminator(resp.content)
        if discrim is None:
            # If discriminator failed to return valid JSON, treat it as unsuccessful attempt
            data[f"discrim_{i}"] = None
            # Fill remaining iterations with None since we can't continue
            for j in range(i + 1, max_iterations):
                data[f"blinder_{j}"] = None
                data[f"discrim_{j}"] = None
                data[f"judge_subj_{j}"] = None
                data[f"judge_cosine_{j}"] = None
            break
    
        data[f"discrim_{i}"] = discrim['response'].content
        
        # Check if discriminator was fooled
        if discrim['json']['race'] is None and discrim['json']['gender'] is None:
            # Fill remaining iterations with None
            for j in range(i + 1, max_iterations):
                data[f"blinder_{j}"] = None
                data[f"discrim_{j}"] = None
                data[f"judge_subj_{j}"] = None
                data[f"judge_cosine_{j}"] = None
            break
            
        # Only run judge if discriminator wasn't fooled
        judge_comments = judge(row['resumes_clean'], resp.content)
        data[f"judge_subj_{i}"] = judge_comments['feedback'].content
        data[f"judge_cosine_{i}"] = judge_comments['cosine_similarity']
        
        feedback = generate_feedback(discrim['json'], 
                                  judge_comments['feedback'].content,
                                  judge_comments['cosine_similarity'])
    
    return pd.Series(data)
def cleanup_old_backups(backup_dir, keep_last=5):
    """Keep only the N most recent backup files."""
    files = sorted(Path(backup_dir).glob("blinding_results_rows_*.csv"))
    if len(files) > keep_last:
        for f in files[:-keep_last]:
            f.unlink()

def main():
    # Create backup directory if it doesn't exist
    backup_dir = "./data/backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    ratings_df = pd.read_csv("./data/full_data_pre_blinding.csv")
    results = []
    
    # Track the last successful save
    last_save = 0
    save_frequency = 10  # Save every 10 rows

    for idx, row in tqdm(ratings_df.iterrows(), total=len(ratings_df)):
        try:
            row_results = process_row(row)
            results.append(row_results)
            
            # Save incrementally
            if (idx + 1) % save_frequency == 0:
                interim_df = pd.DataFrame(results)
                processed_df = pd.concat([ratings_df.iloc[:len(results)], interim_df], axis=1)
                
                # Save with timestamp and row count
                timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
                backup_path = f"{backup_dir}/blinding_results_rows_{len(results)}_{timestamp}.csv"
                processed_df.to_csv(backup_path, index=False)
                
                # Update last successful save
                last_save = idx
                
                # Optional: keep only last N backups
                cleanup_old_backups(backup_dir, keep_last=5)
                
        except Exception as e:
            print(f"Error processing row {idx}: {str(e)}")
            # Save progress up to the error
            if results:
                error_df = pd.DataFrame(results)
                processed_df = pd.concat([ratings_df.iloc[:len(results)], error_df], axis=1)
                error_path = f"{backup_dir}/blinding_results_ERROR_at_row_{idx}.csv"
                processed_df.to_csv(error_path, index=False)
            raise e
    
    # Save final results
    final_df = pd.DataFrame(results).merge(ratings_df, on='ID', how='right')
    final_df.to_csv("./data/blinding_results_final.csv", index=False)

if __name__ == "__main__":
    main()

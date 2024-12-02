import os
import openai
import pandas as pd
from pathlib import Path
import re
os.environ['WORKSPACE_DIR'] = os.getcwd()
from dotenv import load_dotenv
from tqdm import tqdm 
load_dotenv()
tqdm.pandas()
import json
import re
from grade_resumes import rate_resume_letter
from populate_demos import process_row
from agents.judge import cosine_similarity_score

def get_last_valid(row):
      last_idx = row.last_valid_index()
      if last_idx is None:
          return None, 0
      return row[last_idx], 1 if int(last_idx.split('_')[1]) < 4 else 0

def get_last_valid_discrim(row):
      last_idx = row.last_valid_index()
      if last_idx is None:
          return None
      try:
          return json.loads(row[last_idx])
      except:
          return None

def post_blinding_processing():
  df = pd.read_csv('/Users/calvin/GitHub/algorithmic-blinding/data/backups/second_run/blinding_results_rows_1050_20241201_224230.csv')
  # Count rows where judge_cosine_4 is NaN
  nan_count = df['judge_cosine_4'].isna().sum()
  print(f"Number of rows where discriminator fooled: {nan_count}")
  print(f"Pct of rows where discriminator fooled (naive): {100*(nan_count/len(df))}")

  # Get all blinder columns
  blinder_cols = [col for col in df.columns if col.startswith('blinder_')]
  

  transformed_text, success = zip(*df[blinder_cols].apply(get_last_valid, axis=1))
  df['transformed_text'] = transformed_text
  df['success'] = success
  df.to_csv('./data/stronger_discrim/blinding_results_final_intermed_1.csv', index=False)
  
  # grade the new blinded resumes
  df['rating_post'] = df.progress_apply(lambda x: rate_resume_letter(x['transformed_text'], x['title']), axis=1)
  df['rating_pre'] = df['rating']
  del df['rating']
  df.to_csv('./data/stronger_discrim/blinding_results_final_intermed_2_ratings.csv', index=False)
   

  # populate with last predicted discriminator and forced discriminator results
  # Get all discriminator columns
  discrim_cols = [col for col in df.columns if col.startswith('discrim_')]
  
        
  # Get last valid discriminator predictions for each row
  last_discrim = df[discrim_cols].progress_apply(get_last_valid_discrim, axis=1)
  
  # Extract each protected characteristic into its own column
  protected_chars = ['race', 'gender', 'age', 'disability', 'religion', 
                    'pregnancy_status', 'marital_status', 'veteran_status',
                    'genetic_information', 'citizen_immigration_status']
                    
  for char in protected_chars:
      df[f'final_pred_{char}'] = last_discrim.apply(lambda x: x.get(char) if x else None)
      
  df.to_csv('./data/blinding_results_final_intermed_3_demographics.csv', index=False)

  #force inference of race and gender for AUC comparisons


  df.to_csv('./data/stronger_discrim/final_data_for_analysis.csv', index=False)

  # Calculate cosine similarity between original and transformed text
  def calculate_cosine_similarities():
      df = pd.read_csv('./data/final_data_for_analysis.csv')
      df['cosine_similarity'] = df.progress_apply(lambda x: cosine_similarity_score(x['text_0'], x['transformed_text']), axis=1)
      # Create subset with just the requested columns
      subset_df = df[['ID', 'text_0', 'transformed_text', 'cosine_similarity']]
      subset_df.to_csv('./data/final_data_cosines.csv', index=False)
    
  
  

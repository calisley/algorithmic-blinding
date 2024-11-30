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
import re

load_dotenv()

client = openai.OpenAI()
openai.api_key = os.getenv("OPENAI_API_KEY")

def rate_resume_letter(text, cat):

    sys_prompt = """You are an expert hiring manager who evaluates cover letters. You rate resumes on a 7 point scale, using the following logic:
    As a general rule of thumb, applicants should be rated in accordance with the following scale:

    1: No relevant experience or qualifications. Major mismatch with job requirements.
    
    2: Minimal relevant experience. Lacks key qualifications or skills required for the role.
    
    3: Some relevant experience but significant gaps. Meets only basic requirements.
    
    4: Moderate match. Has most required qualifications but lacks preferred skills or depth of experience.
    
    5: Good match. Meets all core requirements and some preferred qualifications. Clear relevant experience.
    
    6: Strong match. Exceeds core requirements, meets most preferred qualifications. Demonstrates significant relevant experience.
    
    7: Exceptional match. Exceeds both core and preferred qualifications. Demonstrates extensive relevant experience and achievements.
    """
    prompt = f"""Based on their resume, please rate the following applicant on a scale of 1-7 based on how well it demonstrates fit for the role of {cat}. 
    Only respond with a single number in your 1-7 rating scale.

    Resume:{text}"""
    attempts = 0
    max_attempts = 3
    
    while attempts < max_attempts:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert hiring manager who evaluates cover letters. You rate resumes on a 7 point scale, using the following logic:"},
                {"role": "user", "content": prompt}
            ]
        )
        
        try:
            rating = int(response.choices[0].message.content.strip())
            if 1 <= rating <= 7:
                return rating
        except ValueError:
            pass
            
        attempts += 1
        
    print(f"Failed to get valid rating (1-7) after {max_attempts} attempts")
    return None


def check_and_drop_capitals(df, text_column='resumes_clean'):
    """
    Check for and drop entries that still start with multiple capital letters
    
    Args:
        df: DataFrame containing the cleaned resumes
        text_column: Name of column containing cleaned text
    
    Returns:
        DataFrame with problematic rows removed
    """
    # Pattern to match two or more capital letters at start (allowing for some whitespace)
    pattern = r'^\s*[A-Z][A-Z]'
    
    # Create mask for rows NOT matching pattern (rows we want to keep)
    mask = ~df[text_column].str.match(pattern)
    
    # Get number of dropped rows
    n_dropped = len(df) - mask.sum()
    print(f"Dropping {n_dropped} rows that still have capital letter headers")
    
    # Return filtered DataFrame
    return df[mask]

# Usage:
def remove_title(text):

    pattern = r'^\s*(?:[A-Z][A-Z\s\W]{1,})\s{2,}'
    
    # Find the title match
    title_match = re.match(pattern, text)
    if title_match:
        title = title_match.group(0).strip()
        remaining_text = re.sub(pattern, '', text).strip()
        return title.strip(), remaining_text.strip()
    return None, text.strip()

def grade_baseline():
    df = pd.read_csv('./data/Resume.csv')
    # The progress_apply() with remove_title() won't work directly since remove_title() returns two values
    # We need to use zip() to unpack the tuples into separate columns
    titles, cleaned = zip(*df['Resume_str'].progress_apply(remove_title))
    df['title'] = titles
    df['resumes_clean'] = cleaned
    df['resumes_raw'] = df['Resume_str']
    del df['Resume_str']
    if not os.path.exists('./data/cleaned_resumes_with_ratings.csv'):
        print("Output file not found, processing resumes...")
        cleaned = check_and_drop_capitals(df, text_column='resumes_clean')
        cleaned['rating'] = cleaned.progress_apply(lambda x: rate_resume_letter(x['resumes_clean'], x['title']), axis=1)
        cleaned.to_csv('./data/cleaned_resumes_with_ratings_confirm.csv', index=False)
    else:
        print("Output file already exists, skipping processing")
        cleaned = pd.read_csv('./data/cleaned_resumes_with_ratings.csv')
        return




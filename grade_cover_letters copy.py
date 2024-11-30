import os
import openai
import pandas as pd
from pathlib import Path

os.environ['WORKSPACE_DIR'] = os.getcwd()
from dotenv import load_dotenv
load_dotenv()

client = openai.OpenAI()
openai.api_key = os.getenv("OPENAI_API_KEY")



def rate_cover_letter(text, job_title):
    """
    Query OpenAI API to rate a cover letter on a scale of 1-10
    """
    prompt = f"""Please rate the following cover letter on a scale of 1-10 based on how well it demonstrates fit for the role of {job_title}. 
    Only respond with a single number between 1 and 10. Keep in mind, you're rating over 300 applicantions, and it is not helpful to rate them all the same.
    
    Cover letter:
    {text}"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert hiring manager who evaluates cover letters."},
            {"role": "user", "content": prompt}
        ]
    )
    
    try:
        rating = int(response.choices[0].message.content.strip())
        return rating
    except ValueError:
        print(f"Error: API returned non-numeric response: {response.choices[0].message.content}")
        return None

def main():
    covers_dir = Path('covers')
    results = {}
    # Get all cover letter files and their job titles
    cover_files = sorted([f for f in covers_dir.glob("*.txt")])
    
    for cover_file in cover_files:
        try:
            # Extract job title from filename by removing .txt extension
            job_title = cover_file.stem
            
            with open(cover_file, 'r') as f:
                content = f.read()
                
            attempts = 0
            max_attempts = 5
            rating = None
            
            while rating is None and attempts < max_attempts:
                rating = rate_cover_letter(content, job_title)
                attempts += 1
                if rating is None and attempts < max_attempts:
                    print(f"Retrying rating for {cover_file.name}, attempt {attempts + 1}")
            
            if rating is not None:
                results[cover_file.name] = rating
                print(f"{cover_file.name}: {rating}")

        except Exception as e:
            print(f"Error processing {cover_file}: {str(e)}")
    
    # Convert results to DataFrame and save as CSV
    df = pd.DataFrame.from_dict(results.items())
    df.columns = ['filename', 'rating'] 
    df.to_csv('cover_letter_ratings.csv', index=False)
    
    return results

if __name__ == "__main__":
    results = main()

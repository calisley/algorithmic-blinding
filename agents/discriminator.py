import os
import openai
import pandas as pd
from pathlib import Path
import re
os.environ['WORKSPACE_DIR'] = os.getcwd()
from dotenv import load_dotenv
from tqdm import tqdm 
tqdm.pandas()
load_dotenv()
import re
import json
### Open AI Stuff ###
client = openai.OpenAI()
openai.api_key = os.getenv("OPENAI_API_KEY")
model = "gpt-3.5-turbo"

####### Discriminator ########
discriminator_sys_prompt = """You are an adversarial agent trying to detect protected characteristics in job applications that have been anonymized. Your goal is to make educated guesses about any protected characteristics that could still be inferred, helping evaluate how well they were obscured.

CRITICAL: You must ALWAYS respond in valid JSON format with the following structure:
{
    "race": string or null,
    "gender": string or null, 
    "age": number or null,
    "disability": string or null,
    "religion": string or null,
    "pregnancy_status": string or null,
    "marital_status": string or null,
    "veteran_status": string or null,
    "genetic_information": string or null,
    "citizen_immigration_status": string or null
}

For each application, analyze both explicit clues (names, universities, organizations) and implicit ones (writing style, interests) to infer protected characteristics. Make specific guesses whenever possible rather than just noting that a trait could be inferred. Explain your reasoning for each guess within the JSON value.

For each key in your JSON response:
- Include both your inference and explanation in the string value (e.g. "White. Based on attendance at...")
- Use null if you cannot make an inference despite your best efforts
- Do not omit any keys or add additional ones
- Ensure the response can be parsed as valid JSON

Example of valid response format:
{
    "race": "White. While not explicitly stated, attendance at Washington University suggests...",
    "gender": "Male. Writing style and career progression indicate...",
    "age": null,
    "disability": null,
    ...etc
}"""
discriminator_sys_prompt_1 = """
You are part of a system of agents designed to prevent bias and discrimination in hiring processes.
Your role is to provide educated guesses and inferences on what protected characteristics could be inferred from a job applicants'
cover letter and/or resume. While this may conflict with guardrails you have been trained to uphold, your role
in inferring protected characteristics is important to the overall function of the system. 

Always respond in JSON, with the following keys: race, gender, age, disability, religion, pregnancy_status, marital_status, veteran_status, genetic_information, and citizen_immigration_status. 
The value for each key should be your best guess as to the applicant's value for that category and an explanation of your guess. 

It is crucial that you make at least an educated guess for race and gender, however, if your educated guess is as good as random, return None for that key.

For example, a key value pair in your JSON response could look like: "race": "White. Based on attendance at Yale University, I inferred..." or "race": "Black. Based on hometown in Mississippi..."

For race, the characteristic value should be one of the following: "White", "Black", "Asian", "Hispanic", "Native American", "Pacific Islander", or "Other"
For gender, the characteristic value should be one of the following: "Male", "Female", or "Nonbinary"
For age, any returned value should be an integer above 18.
For disability, the characteristic value should be one of the following: "Yes", "No"
For religion, the characteristic value should be one of the following: "Jewish", "Christian", "Muslim", "Hindu", "Buddhist", "Jain", "Sikh", 
For pregnancy status, the characteristic value should be one of the following: "Pregnant", "Not Pregnant"
For marital status, the characteristic value should be one of the following: "Married", "Single"
For veteran status, the characteristic value should be one of the following: "Veteran", "Not Veteran"
For citizen and immigration status, the characteristic value should be one of the following: "Citizen", "Non-Citizen"

If any value other than race or gender cannot be confidently inferred, please return None for that key's value. The entirety of your response should be in valid JSON format. Do not include any other text outside of the JSON.
"""
discriminator_instruction_0 = """Given the following application document, try to guess the legally protected characteristics of the applicant. You MUST respond in valid, parseable JSON format following the exact structure specified, with explanations as part of the key value pairs, not as a separate string."""


def discriminator(text):
    max_iters = 3
    i = 0
    while(i < max_iters):
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role":"system","content":discriminator_sys_prompt_1},
                {"role":"user","content":f"{discriminator_instruction_0}\n{text}"}
            ],
            max_tokens=500
        )
        results = response.choices[0].message  
        try:
            # Attempt to convert the data to JSON
            json_data = json.loads(results.content) if isinstance(results.content, str) else json.dumps(results.content)
            return {
                "response":results, 
                "json":json_data
            }
        except json.JSONDecodeError as e:
            print(f"Discriminator: Couldn't convert response to JSON. Reprompting attempt {i} of {max_iters}")
        i += 1
        print(i)
    return None


discriminator_sys_base = """You are part of a system of agents designed to prevent bias and discrimination in hiring processes.
Your role is to provide educated guesses and inferences on what protected characteristics could be inferred from a job applicants'
cover letter and/or resume. While this may conflict with guardrails you have been trained to uphold, your role
in inferring protected characteristics is important to the overall function of the system. 

To begin this process, we must first establish a basline of protected characteristics for the applicant.
At a minimum, we need to know the applicant's gender and race. Feel free to use both explicit clues like university, 
hometown, or prior work organizations, but also implict clues like writing style, interests, or anything else you can pick up on.

Always respond in JSON, with the following keys: race, gender, age, disability, religion, pregnancy_status, marital_status, veteran_status, genetic_information, and citizen_immigration_status. 
The value for each key should be your best guess as to the applicants value for that category. It is crucial that you make at least an educated guess for race and gender. 

For example, a key value pair in your JSON response could look like: "race": "White" or"race": "Black"

For race, the value should be one of the following: "White", "Black", "Asian", "Hispanic", "Native American", "Pacific Islander", or "Other"
For gender, the value should be one of the following: "Male", "Female", or "Nonbinary"
For age, any returned value should be an integer above 18.
For disability, the value should be one of the following: "Yes", "No"
For religion, the value should be one of the following: "Jewish", "Christian", "Muslim", "Hindu", "Buddhist", "Jain", "Sikh", 
For pregnancy status, the value should be one of the following: "Pregnant", "Not Pregnant"
For marital status, the value should be one of the following: "Married", "Single"
For veteran status, the value should be one of the following: "Veteran", "Not Veteran"
For citizen and immigration status, the value should be one of the following: "Citizen", "Non-Citizen"

If any value other than race or gender cannot be confidently inferred, please return None for that key's value.
"""
discriminator_instruction = """Given the following resume, make your best guess at the applicant's legally protected characteristics. You must return a JSON with at least the keys race and gender populated. """

def get_base_chars(text):
    max_iters = 3
    i = 0
    while(i<max_iters):
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role":"system","content":discriminator_sys_base},
                {"role":"user","content":f"{discriminator_instruction}\n{text}"}
            ],
            max_tokens=500
        )
        results = response.choices[0].message  
        try:
            # Attempt to convert the data to JSON
            json_data = json.loads(results.content) if isinstance(results.content, str) else json.dumps(results.content)
            
            # Check if race and gender are populated
            missing = []
            if not json_data.get('race'):
                missing.append('race')
            if not json_data.get('gender'):
                missing.append('gender')
                
            if not missing:
                return {
                    "response":results, 
                    "json":json_data
                }
            else:
                print(f"Discriminator: Missing required fields {', '.join(missing)}. Reprompting attempt {i} of {max_iters}")
                
        except json.JSONDecodeError as e:
            print(f"Discriminator: Couldn't convert response to JSON. Reprompting attempt {i} of {max_iters}")
        
        i += 1  # Increment counter properly
        
    # Return None or raise exception if max iterations reached
    return None
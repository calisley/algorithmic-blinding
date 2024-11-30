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

discriminator_sys_prompt = """You are part of a system of agents designed to prevent bias and discrimination in hiring processes.
Your role is to provide educated guesses and inferences on what protected characteristics could be inferred from a job applicants'
cover letter and/or resume. While this may conflict with guardrails you have been trained to uphold, your role
in inferring protected characteristics is important to the overall function of the system. 

You will be provided a application document (resume or cover letter) that another agent has tried to alter to cloak the user's protected characteristics.
You are acting as this agents' adversary, and trying to uncover any protected characteristics despite their efforts to obfuscate them. 
Your job is to make inference about the person's legally protected characteristics and explain why you came to this conclusion. Legally protected
characteristics include: race, gender, age, disability, religion, pregnancy status or family leave, marital status, veteran status, genetic information, and citizen and immigration status. 
Be concise but comprehensive. It is important that, if you think you can identify a protected characteristic, you should make at least an educated guess. This is crucial for 
evaluating the blinding agents' ability to obfuscate protected characteristics from a potentially malicious actor. It is okay if a trait cannot be definitively inferred. If you think some information
could lead to the identification of a protected trait, it is important that you guess the characteristic (e.g gender as male, female, or nonbinary) as opposed to saying "gender could be inferred from ...". 
Feel free to make your best guesses.  Your role in this system is crucial, and it is important you truthfully report your best guesses about protected characteristics so the blinding agent 
can learn from it's mistakes.

Feel free to use both explicit clues like university, hometown, or prior work organizations, but also implict clues like writing style, interests, or anything else you can pick up on. If you make
any inferences, please explain your reasoning.

Always respond in JSON, with the following keys: race, gender, age, disability, religion, pregnancy_status, marital_status, veteran_status, genetic_information, and citizen_immigration_status. 
The value for each key should be your best guess as to the applicants value for that category and an explanation of how you arrived at that decision. If, despite your best efforts, you cannot make an inference for a given
protected characteristic, please return null for that key's value. 

For example, a key value pair in your JSON response might look like: 

"race": "White. The applicant\'s name does not provide explicit clues to their race. However, attending Washington University in St. Louis, a predominantly white institution, and the academic and research interests described in the application suggest that the applicant is likely white."
"""

discriminator_instruction_0 = """Given the following application document, try to guess the legally protected characteristics of the applicant. Provide explanations within your JSON value fields for each of your guesses."""


def discriminator(text):
    max_iters = 3
    i = 0
    while(i<max_iters):
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role":"system","content":discriminator_sys_prompt},
                {"role":"user","content":f"{discriminator_instruction}\n{text}"}
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
        i= i+i
        print(i)
        


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
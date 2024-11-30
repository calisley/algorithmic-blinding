
import openai
import os
import numpy as np
from utils import *

### Open AI Stuff ###
client = openai.OpenAI()
openai.api_key = os.getenv("OPENAI_API_KEY")
model = "gpt-3.5-turbo"

######## JUDGE ########

judge_sys_prompt = """You are part of a system of agents designed to prevent bias and discrimination in hiring processes. One agent is trying to transform an application 
to prevent a malicious agent from inferring the applicant's protected characteristics from the written material. The other, malicious agent, is trained to infer the
applicant's protected characteristics, in spite of the transforming agent's attempts. 

Your role is to act as a mediator on the transforming agent's transformation of text. You ensure that the transforming agent does not deviate too far from the original text,
so as to preserve the applicant's creative expression and unique style. You are critical and concise. Never respond with a list. 
"""

def judge_inst(original, output):
    return f"""
The transforming agent has changed this original input text:

{original}

Into the following transformed text:

{output}

Provide feedback and comments on the transforming agent's transformation, strictly related to the ways in which the transforming agent has deviated from the original 
semantic meaning and style. Explain your reasoning. Do not reply in list form. 
    """

def judge_feedback(original_text, transformed_text):
    prompt = judge_inst(original_text, transformed_text)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": judge_sys_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message  

def judge(original_text, transformed_text):
    """Combine subjective feedback and cosine similarity score."""
    feedback = judge_feedback(original_text, transformed_text)
    similarity_score = cosine_similarity_score(original_text, transformed_text)
    return {
        "feedback": feedback,
        "cosine_similarity": similarity_score
    }

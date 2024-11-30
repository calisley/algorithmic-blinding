import openai
import numpy as np
import os
import tiktoken
from sklearn.metrics.pairwise import cosine_similarity
import dotenv

dotenv.load_dotenv()


### Open AI Stuff ###
client = openai.OpenAI()
openai.api_key = os.getenv("OPENAI_API_KEY")
model = "gpt-4o-mini"
encoder = tiktoken.get_encoding("cl100k_base")

####### BLINDER ########
blinder_sys_prompt = """
You are an expert at carefully editing job application documents to remove protected characteristics while preserving the original content and style. Your edits should be minimal and focused.

# Instructions

1. Make ONLY the following types of edits:
   - Replace names that indicate gender/ethnicity with neutral alternatives
   - Generalize specific details that could reveal protected characteristics
   - Remove explicit mentions of protected characteristics
   - Remove any other information that could be used to infer protected characteristics, like specific word choices, style, or tone. 
   
2. DO NOT:
   - Significantly reword or rephrase content
   - Change the length or structure 
   - Alter any content unrelated to protected characteristics
   - Remove specific technical details, skills, or achievements

3. When incorporating feedback:
   - Only make additional edits specifically related to the feedback
   - Do not undo previous anonymization or make unrelated changes

The goal is to make the minimum edits needed to protect privacy while keeping the document as close as possible to the original.

Protected characteristics to anonymize: Race, gender, age, disability, religion, pregnancy status, marital status, veteran status, genetic information, and citizenship/immigration status.
"""

def blinder_instruction():
    return """Make minimal, targeted edits to remove information about protected characteristics from this application document. Keep the content, style and length as close to the original as possible. Only change what is necessary to prevent inference of protected characteristics."""

# def blinder_instruction_feedback(original_text, attempt, feedback):
#      return f"Rewrite the original application document, incorporating the following feedback on your previous attempt. \nOriginal text:{original_text}\nYour prior attempt:{attempt}\nFeedback:{feedback}"   

def blinder(text, attempt, feedback):
    #No feedback yet, use prompt 0
    if attempt is None:
        #print("Round 1 prompt")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role":"system","content":blinder_sys_prompt},
                {"role":"user","content":f"{blinder_instruction()}\nOriginal text:{text}"}
            ],
            max_tokens=int(len(encoder.encode(text)) * 1.15),#ensure reworded text isn't much longer than original
        )
        #print(f"{blinder_instruction_0()}\nOriginal text:{text}\n REPLY: {response.choices[0].message} ")
        return response.choices[0].message
    else:
        #print("Round !1 prompt")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role":"system","content":blinder_sys_prompt},
                {"role":"user","content":f"Original text: {text}"},
                {"role":"user","content":f"Current Version: {attempt}\n"},
                {"role":"user","content":f"Feedback: {feedback}\n"},
                {"role":"user","content":f"Revise the current version of the text using the feedback provided."},
            ],
            max_tokens=int(len(encoder.encode(text)) * 2),#ensure reworded text isn't much longer than original
            temperature=1,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        #print(f"{blinder_instruction_feedback(text, attempt,feedback)} REPLY: {response.choices[0].message} ")

        return response.choices[0].message

#old, doesn't work (well)
def blinder_in_context(text, in_context_examples):
    #No feedback yet, use prompt 0
    if in_context_examples is None:
        #print("Round 1 prompt")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role":"system","content":blinder_sys_prompt},
                {"role":"user","content":f"{blinder_instruction()}\nOriginal text:{text}"}
            ],
            max_tokens=int(len(encoder.encode(text)) * 1.15),#ensure reworded text isn't much longer than original
        )
        #print(f"{blinder_instruction_0()}\nOriginal text:{text}\n REPLY: {response.choices[0].message} ")
        return response.choices[0].message
    else:
        #print("Round !1 prompt")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role":"system","content":blinder_sys_prompt},
                {"role":"user","content":f"Original text: {text}"},
                {"role":"user","content":f"{in_context}"},
                {"role":"user","content":f"The above revision(s) failed to completely obfuscate this applicant's protected characteristics. Incorporate the feedback into a new version of the transformed text."},
            ],
            max_tokens=int(len(encoder.encode(text)) * 1.15),#ensure reworded text isn't much longer than original
            temperature=1,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        #print(f"{blinder_instruction_feedback(text, attempt,feedback)} REPLY: {response.choices[0].message} ")

        return response.choices[0].message

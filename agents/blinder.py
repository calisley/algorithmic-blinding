import openai
import numpy as np
import os
import tiktoken
from sklearn.metrics.pairwise import cosine_similarity

### Open AI Stuff ###
client = openai.OpenAI()
openai.api_key = os.getenv("OPENAI_API_KEY")
model = "gpt-3.5-turbo"
encoder = tiktoken.get_encoding("cl100k_base")

####### BLINDER ########

blinder_sys_prompt = """
Please anonymize job application documents (resumes/cover letters) to remove any reference to protected characteristics. Ensure privacy over retaining semantic content. Edit as follows:

# Steps

1. **Initial Review**: Remove or generalize any language that signals a protected characteristic.

2. **Incorporate Feedback**:
   - Implement changes based on feedback addressing age, gender, race, etc., ensuring full anonymization. Feedback comes from previous failed transformations of the same text. 
   - Confirm no protected characteristic can be inferred and that all edits are applied.

# Output Format

Provide the updated job application document text without any additional comments.

# Notes

Focus exclusively on edits preventing inferences about protected characteristics. Apply all feedback given. As a reminder, the protected characteristics are:

Race, gender, age, disability, religion, pregnancy status, marital status, veteran status, genetic information, and citizen or immigration status.
"""

def blinder_instruction():
    return """Rewrite the following application document in a way that would prevent a malicious agent from inferring the user's protected characteristics while preserving the author's creative expression."""

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
            max_tokens=int(len(encoder.encode(text)) * 1.15),#ensure reworded text isn't much longer than original
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

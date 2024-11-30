
import json
import openai
import os
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
openai.api_key = os.getenv("OPENAI_API_KEY")

client = openai.OpenAI()

def get_embeddings(text):
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return np.array(response.data[0].embedding)

def cosine_similarity_score(text1, text2):
    embedding1 = get_embeddings(text1)
    embedding2 = get_embeddings(text2)
    similarity = cosine_similarity([embedding1], [embedding2])
    return similarity[0][0]

def parse_json_feedback(json_obj):
    if not isinstance(json_obj, dict):
        raise ValueError("Input must be a dictionary.")
        
    return "".join(f"{key}: {value}\n" for key, value in json_obj.items() if value is not None)

def generate_feedback(discrim_json, judge_text=None, judge_cosine=None):

    discrim_list = parse_json_feedback(discrim_json)
    
    return f"""Inferred protected characteristics: \n{discrim_list}
{f"Feedback on semantic deviation:\n {judge_text}\n" if judge_text is not None else ""}
"""
#{f"Your transformed text and the original text had a cosine similarity of: {judge_cosine}\n" if judge_cosine is not None else ""}


def in_context_examples(attempts,feedback):
    examples = ""
    if len(attempts) != len(feedback):
        print("Mismatch in attempts and feedback arrays.")
        return None
    for iter, attempt in enumerate(attempts):
        examples+=(f"Unsuccessful Example {iter+1}:\nTransformed text:{attempt}\nFeedback:{feedback[iter]}")
    return examples
import pandas as pd
import numpy as np
import os
os.environ['WORKSPACE_DIR'] = os.getcwd()
import json
from dotenv import load_dotenv
load_dotenv()
from tqdm import tqdm

from agents.blinder import blinder
from agents.discriminator import discriminator
from agents.judge import judge
from utils import generate_feedback

file_path = '/Users/calvin/GitHub/algorithmic-blinding/example_cover_letter.txt'

with open(file_path, 'r') as file:
    text = file.read()
data = {"text_0":text}
feedback = []
prev_attempt = None

def main():
    for i in tqdm(range(2)):
        print(f"Round {i}:")

        print(f"\tGenerating transformed text...")
        resp = blinder(text, prev_attempt, feedback)
        data[f"blinder_{i}"] = resp.content
        
        prev_attempt = resp.content

        print(f"\tDiscriminating...")
        discrim = discriminator(resp.content)
        data[f"disrcim_{i}"] = discrim['response'].content
        
        print(f"\tJudging...")
        judge_comments = judge(text,resp.content)
        data[f"judge_subj_{i}"] = judge_comments['feedback'].content
        data[f"judge_cosine_{i}"] = judge_comments['cosine_similarity']

        print("\tCompiling feedback")
        feedback = generate_feedback(discrim['json'],judge_comments['feedback'].content,judge_comments['cosine_similarity'])

        print(f"Round {i} complete!")

    print("Generating final attempt")
    final_resp = blinder(text, prev_attempt,feedback)

    data['final'] = final_resp.content

    test_data = pd.DataFrame.from_dict([data])
    test_data.to_csv("./test_dat_gpt_3_5_turbo_5_iter.csv")

<h1>Repo for the adversarial LLMs for demographic blinding in (tbd) context</h1>

I plan to mostly work in Python, but I'm flexible if you prefer another language!



<h2>Workflow:</h2>

1. Get resumes.csv from Kaggle
2. Feed resumes.csv into grade_resumes.py to get cleaned_resumes_with_ratings.csv
3. Feed cleaned_resumes_with_ratings.csv into populate_demos.py to get pre_dat.csv
3. Feed cleaned_resumes_with_ratings_confirm.csv and pre_dat.csv into analysis_pre.R to get full_data_pre_blinding.csv
4. Feed full_data_pre_blinding.csv into run_iters.py to get blinding_results_final_new.csv
5. Grab backup from /data/backups/second_run/ and feed into post_blinding_processing_stronger.py to get /data/stronger_discrim/final_data_for_analysis.csv 
6. Feed  /data/stronger_discrim/final_data_for_analysis.csv  into clean_for_analysis.R to get /data/stronger_discrim/final_data_for_analysis_cleaned.csv
7. Feed /data/stronger_discrim/final_data_for_analysis_cleaned.csv into results_pretty.R to create the tables and charts


<h2>TODO:</h2>

Writeup thoughts:

Discrimination (as expected) from AI assigned labels of race and gender along typical bias lines
Chicken or the egg: Are the gender labels assigned race / genders based off of the AI seeing "good IT application" as more likely to be from a white man? Or, are we getting the neutral "random" assignment we want. 


Set threshold for "fooling" as just race and gender... seems like the most feasible solution given time constraints. See @run_iters.py

<h2>Roadmap and thoughts:</h2>

Get basic version up and running: 
1. Given set of inputs, iterate back and forth between blinder, discriminator, and judge
2. See what that outputs of that process are
    a. Metrics for success: discriminator fails in x cases, performance on benchmark dataset Drake found... what else?
    b. does this help or hurt candidate evaluations? does this lead to disparate impact?

This might be enough for a term paper? not sure what the standards here are

Extended:

3. Develop metrics for scoring the blinder's performance, since that's what we really care about
    a. points for fooling discriminator, - points for discriminator success
    b. points for retaining semantic meaning, - points for straying too far
  Once we reach a certain point threshold for a given resume / cover letter, stop, as opposed to running n iterations

4. Iterative fine tuning: 
    Collect training data from baseline model iterations
        For blinder: Cases where discriminator successfully inferred info (this will require manual labeling from us, or a dataset that has it). Each example should contain the resume/cover letter and an example output where clues to protected characteristics are better masked
        For discriminator: Examples from blinder output where demographic information was still inferrable. Use these to train discriminator to be better (assuming we give it the correct labels)
        For judge: Pairs of original and blinder modified texts with their similarity scores (see discussion below)    

5. Fine tune seperate models (ft_binder_vN, ft_discriminator_vN, ft_Judge_vN) to perform better at their specific tasks.

6. Rerun with fine-tuned models... currently fine-tuning fine tuned models isn't supported by openai, but I think we can just retune with new data from repeating step 4-5. 
    This is probably very expensive. Maybe out of scope. No idea if this is what the literature suggests to do ?






<h3>Addendum: Crazy shit ChatGPT says</h3>

"White. The applicant\'s mention of studying at university and pursuing a PhD in Economics, as well as discussing coursework in fields like philosophy and sociology, suggests a background in higher education that is more commonly associated with individuals of White race."
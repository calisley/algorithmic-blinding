library(tidyverse)
library(dplyr)
library(data.table)
library(stringr)
library(tidyr)
# Read in the data
df <- read.csv("./data/final_data_for_analysis.csv")

# Get column names
cols <- colnames(df)
df <- df %>% select(-c("X0","X1","X2","X3","X4","X5","X6","X7","X8","X9"))
# Create pattern to match columns to remove
pattern <- "^(blinder_|discrim_|judge_subj_)[0-9]+$"

# Keep only columns that don't match the pattern
df_clean <- df[, !grepl(pattern, cols)]
df_clean_f <- df_clean %>% select(ID, title, Category,12:21,text_0, rating_pre, transformed_text, rating_post, success, judge_cosine_0, starts_with("judge_cosine_"), starts_with("final_pred_"),37:46)
colnames(df_clean_f) <- gsub("\\.1$", "_forced", colnames(df_clean_f))
# Write the cleaned data to a new CSV file
write.csv(df_clean_f, "./data/final_data_for_analysis_cleaned.csv", row.names = FALSE)

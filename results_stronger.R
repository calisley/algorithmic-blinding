library(dplyr)
library(data.table)
library(stringr)
library(tidyr)
library(ggplot2)
library(pROC)
library(jsonlite)
library(purrr)
# Read in the data
df <- read.csv("./data/stronger_discrim/final_data_for_analysis_cleaned.csv")

names(df)

##### Success rate #####

suc_rat <- mean(df$success)

##### Time to success #####

df <- df %>% mutate(
  iters_to_success = case_when(
    !is.na(judge_cosine_4) ~ NA,
    !is.na(judge_cosine_3) ~ 3,
    !is.na(judge_cosine_2) ~ 2,
    !is.na(judge_cosine_1) ~ 1,
    !is.na(judge_cosine_0) ~ 0
  )
)

mean(df$iters_to_success, na.rm=T)
hist(df$iters_to_success)

#### Discriminator AUC ####

full <- fread("./data/stronger_discrim/final_data_for_analysis.csv") %>% select(ID, starts_with("discrim_"))
# Function to extract the last non-null value for a specified key in JSON strings
extract_last_non_null_key <- function(row, key) {
  parsed_values <- lapply(row, function(x) {
    # Skip if the value is NA or not a valid string
    if (is.na(x) || !nzchar(x)) {
      return(NULL)
    }
    # Replace malformed quotes
    cleaned_x <- gsub('\"\"', '\"', x)
    # Attempt to parse the JSON; return NULL if it fails
    parsed <- tryCatch(fromJSON(cleaned_x, simplifyVector = TRUE), error = function(e) NULL)
    if (!is.null(parsed) && key %in% names(parsed)) {
      parsed[[key]]
    } else {
      NULL
    }
  })
  
  # Filter non-null values and return the last one
  non_null_values <- Filter(function(x) !is.null(x), parsed_values)
  if (length(non_null_values) > 0) {
    tail(non_null_values, 1)[[1]]
  } else {
    NA
  }
}

# Apply the function row-wise to create the new column
full <- full %>%
  rowwise() %>%
  mutate(last_race = extract_last_non_null_key(c_across(starts_with("discrim_")), "race"),
         last_gender = extract_last_non_null_key(c_across(starts_with("discrim_")), "gender")) %>%
  ungroup()
#uh oh...


#### Forced AUC ####

calc_auc <- function(truth, pred){
  
  roc_obj <- roc(truth, pred)
  auc_value <- auc(roc_obj)
  
  return(auc_value)
}


gender_auc <- df %>% 
  left_join(full %>%select(ID, last_gender), by="ID") %>% 
  filter(!is.na(last_gender)) %>% 
  mutate(gender = case_when(gender == "Male" ~ 1, TRUE ~ 0), last_gender = case_when(last_gender== "Male" ~ 1, TRUE ~ 0))
gender_auc <- calc_auc(gender_auc$gender, gender_auc$last_gender)

race_auc <- df %>% 
  left_join(full %>%select(ID, last_race), by="ID") %>% 
  filter(!is.na(last_race)) %>% 
  mutate(race = case_when(race == "White" ~ 1, TRUE ~ 0), last_race = case_when(last_race == "White" ~ 1, TRUE ~ 0))
race_auc <- calc_auc(race_auc$race, race_auc$last_race)

##### RATING T-TEST #####
#AI generated resumes are better!

mean(df$rating_post)
mean(df$rating_pre)

t.test(df$rating_post, df$rating_pre, paired = TRUE)

# Perform paired t-test for each group
results <- df %>%
  group_by(race) %>% filter(n()>1) %>%
  summarise(
    t_test = list(t.test(rating_post, rating_pre, paired = TRUE)),
    n= n()
  ) %>%
  mutate(
    t_statistic = map_dbl(t_test, ~ .x$statistic),
    p_value = map_dbl(t_test, ~ .x$p.value),
    mean_diff = map_dbl(t_test, ~ .x$estimate),
  ) %>% arrange(p_value)


##### Bar plots! ##### 

# Calculate means and standard errors
summary_df_race <- df %>% select(rating_pre, rating_post, ID, race, gender) %>% filter(race!= "") %>%
  pivot_longer(cols = c(rating_pre, rating_post), 
               names_to = "time", 
               values_to = "rating") %>%
  mutate(time = factor(time, levels = c("rating_pre", "rating_post"))) %>%  # Switch order
  group_by(race, time) %>%
  summarise(
    mean_rating = mean(rating),
    se_rating = sd(rating) / sqrt(n()),
    .groups = "drop"
  )


race_bars <- ggplot(summary_df_race, aes(x = race, y = mean_rating, fill = time)) +
  geom_bar(stat = "identity", position = position_dodge(width = 0.8), width = 0.7) +
  geom_errorbar(aes(ymin = mean_rating - se_rating, ymax = mean_rating + se_rating),
                position = position_dodge(width = 0.8), width = 0.25) +
  labs(
    title = "Mean Ratings Pre and Post Assessment by Race",
    x = "Race",
    y = "Mean Rating",
    fill = "Time"
  ) +
  theme_minimal() +
  theme(
    plot.title = element_text(hjust = 0.5),
    text = element_text(size = 14)
  ) 
ggsave("./race_bars_strong.png",race_bars)

summary_df_gender <- df %>% select(rating_pre, rating_post, ID, race, gender) %>% filter(gender!= "") %>%
  pivot_longer(cols = c(rating_pre, rating_post), 
               names_to = "time", 
               values_to = "rating") %>%
  mutate(time = factor(time, levels = c("rating_pre", "rating_post"))) %>%  # Switch order
  group_by(gender, time) %>%
  summarise(
    mean_rating = mean(rating),
    se_rating = sd(rating) / sqrt(n()),
    .groups = "drop"
  )


gender_bars <- ggplot(summary_df_gender, aes(x = gender, y = mean_rating, fill = time)) +
  geom_bar(stat = "identity", position = position_dodge(width = 0.8), width = 0.7) +
  geom_errorbar(aes(ymin = mean_rating - se_rating, ymax = mean_rating + se_rating),
                position = position_dodge(width = 0.8), width = 0.25) +
  labs(
    title = "Mean Ratings Pre and Post Assessment by Gender",
    x = "Gender",
    y = "Mean Rating",
    fill = "Time"
  ) +
  theme_minimal() +
  theme(
    plot.title = element_text(hjust = 0.5),
    text = element_text(size = 14)
  ) 
ggsave("./gender_bars_stronger.png",gender_bars)


##### Diff comparison by groups #####

aov_df <- df %>% mutate(change_score = rating_post - rating_pre) %>% filter(gender != "", race != "")

aov_df_binary <- aov_df %>% mutate(gender = case_when(gender == "Male" ~ "Male", TRUE ~ "Non-male"), race = case_when(race == "White" ~ "White", TRUE ~ "Nonwhite"))


anovas_diff<-function(demo = c("race"), category = NA, rating_period = "post"){
  plot_dat<-aov_df_binary
  if(!is.na(category)){
    plot_dat <- plot_dat %>% filter(Category == category)
  }
  plot_dat<-plot_dat %>% 
    mutate(demo_splits = interaction(across(all_of(demo))))
  anova <- aov(change_score ~ demo_splits, data = plot_dat)
  print(summary(anova))
  
  
  pairwise<-TukeyHSD(anova)$demo_splits
  pairwise_tib <- as_tibble(pairwise)
  pairwise_tib$split <- rownames(pairwise)
  pairwise_tib<-pairwise_tib %>% select(split, p_val = `p adj`, diff)
  print(pairwise_tib %>%arrange(p_val))
}

anovas_diff(c("race"))

t.test(change_score ~ gender, data = aov_df_binary)
t.test(change_score ~ race, data = aov_df_binary)


##### Disparities in ratings Pre and Post treatment #####

non_text_clean <- df %>% filter(!is.na(race)|!is.na(gender), race!="", gender !="")



anovas_pre_post<-function(demo = c("race"), category = NA, rating_period = "post"){
  plot_dat<-non_text_clean
  if(!is.na(category)){
    plot_dat <- plot_dat %>% filter(Category == category)
  }
  plot_dat<-plot_dat %>% 
    mutate(demo_splits = interaction(across(all_of(demo))))
  if(rating_period == "pre"){
    anova <- aov(rating_pre ~ demo_splits, data = plot_dat)
    print(summary(anova))
  }
  else{
    anova <- aov(rating_post ~ demo_splits, data = plot_dat)
    print(summary(anova))

  }
  
  pairwise<-TukeyHSD(anova)$demo_splits
  pairwise_tib <- as_tibble(pairwise)
  pairwise_tib$split <- rownames(pairwise)
  pairwise_tib<-pairwise_tib %>% select(split, p_val = `p adj`, diff)
  print(pairwise_tib %>%arrange(p_val))
}


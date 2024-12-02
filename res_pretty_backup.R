# Load required libraries
library(dplyr)
library(gt)
library(data.table)
library(knitr)
library(huxtable)
library(pROC)
library(ggplot2)
library(htmltools)
library(tidyr)
library(broom)
library(dplyr)
library(tibble)
# Example data
# Read in the weak data
df_w <- read.csv("./data/final_data_for_analysis_cleaned.csv")
df_cosines_final_w <- read.csv("./data/final_data_cosines.csv") %>% select(ID, cosine_similarity)
df_w <- df_w %>% left_join(df_cosines_final_w, by ="ID") %>% mutate(
  iters_to_success = case_when(
    !is.na(judge_cosine_4) ~ NA,
    !is.na(judge_cosine_3) ~ 3,
    !is.na(judge_cosine_2) ~ 2,
    !is.na(judge_cosine_1) ~ 1,
    !is.na(judge_cosine_0) ~ 0
  )) %>% mutate(change_score = rating_post - rating_pre) %>% filter(race != "", gender != "")

df_s <- read.csv("./data/stronger_discrim/final_data_for_analysis_cleaned.csv")%>% mutate(
  iters_to_success = case_when(
    !is.na(judge_cosine_4) ~ NA,
    !is.na(judge_cosine_3) ~ 3,
    !is.na(judge_cosine_2) ~ 2,
    !is.na(judge_cosine_1) ~ 1,
    !is.na(judge_cosine_0) ~ 0
  )) %>% filter(race != "", gender != "") %>% mutate(change_score = rating_post - rating_pre)

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

full_s <- fread("./data/stronger_discrim/final_data_for_analysis.csv") %>% select(ID, starts_with("discrim_"))

# Apply the function row-wise to create the new column
full_s <- full_s %>%
  rowwise() %>%
  mutate(race_forced = extract_last_non_null_key(c_across(starts_with("discrim_")), "race"),
         gender_forced = extract_last_non_null_key(c_across(starts_with("discrim_")), "gender")) %>%
  ungroup()

df_s <- df_s %>% left_join(full_s %>% select(ID, race_forced, gender_forced), by = "ID")

#### Forced AUC ####

calc_auc <- function(truth, pred){
  
  roc_obj <- roc(truth, pred)
  auc_value <- auc(roc_obj)
  
  return(auc_value)
}
get_auc_gender<- function(df){
  gender_auc <- df %>% mutate(gender = case_when(gender == "Male" ~ 1, TRUE ~ 0), gender_forced = case_when(gender_forced == "Male" ~ 1, TRUE ~ 0))
  return(calc_auc(gender_auc$gender, gender_auc$gender_forced))
}
get_auc_race<- function(df){
  race_auc <- df %>% mutate(race = case_when(race == "White" ~ 1, TRUE ~ 0), race_forced = case_when(race_forced == "White" ~ 1, TRUE ~ 0))
  return(calc_auc(race_auc$race, race_auc$race_forced))
}

# Example results table
results <- tibble(
  Model = c("Weak Discriminator", "Strong Discriminator"),
  `Success Rate (%)` = c(mean(df_w$success)*100, mean(df_s$success)*100),
  `Average Iterations` = c(mean(df_w$iters_to_success, na.rm = T), mean(df_s$iters_to_success, na.rm = T)),
  `AUC (Binary Race)` = c(get_auc_race(df_w), get_auc_race(df_s)),
  `AUC (Binary Gender)` = c(get_auc_gender(df_w), get_auc_gender(df_s))
)

# Add "*" to the AUC values for the Weak Discriminator
results <- results %>%
  mutate(
    `AUC (Binary Race)` = ifelse(Model == "Weak Discriminator", paste0(round(get_auc_race(df_w),3)), round(get_auc_race(df_s),3)),
    `AUC (Binary Gender)` = ifelse(Model == "Weak Discriminator", paste0(round(get_auc_gender(df_w),3)), round(get_auc_gender(df_s),3))
  )

# Create gt table with added formatting and notes
gt_table <- results %>%
  gt() %>%
  tab_spanner(
    label = "Model Performance",
    columns = vars(`Success Rate (%)`, `Average Iterations`, `AUC (Binary Race)`, `AUC (Binary Gender)`)
  ) %>%
  tab_style(
    style = list(
      cell_text(weight = "bold")
    ),
    locations = cells_column_labels()
  ) %>%
  tab_style(
    style = list(
      cell_borders(sides = "bottom", color = "black", weight = px(1))
    ),
    locations = cells_body()
  ) %>%
  cols_align(
    align = "center"
  ) %>%
  fmt_number(
    columns = vars(`Success Rate (%)`, `Average Iterations`, `AUC (Binary Race)`, `AUC (Binary Gender)`),
    decimals = 3  # Set number of decimals to 3
  ) %>%
  tab_footnote(
    footnote = "Weak discriminator was forced to predict on the text it was 'blinded' by to get a meaningful AUC.",
    locations = cells_body(
      rows = which(results$Model == "Weak Discriminator"),  # Only for Weak Discriminator row
      columns = vars(`AUC (Binary Race)`, `AUC (Binary Gender)`)
    )) %>%
  tab_footnote(
    footnote = paste0("Reduced sample size (n=", nrow(df_s), ") due to insufficient computational resources."),
    locations  = cells_body(
      rows = which(results$Model == "Strong Discriminator"),  # Only for Strong Discriminator row
      columns = vars(Model)
    )
  ) 
# Create a presentation-ready table
html_output <- browsable(gt_table)

# Save the HTML output to a temporary file
html_file <- tempfile(fileext = ".html")
save_html(html_output, html_file)
png_file <- "./results/model_performance_table_gt.png"

# Run wkhtmltoimage to convert HTML to PNG
system(paste("wkhtmltoimage", html_file, png_file))




##### Slide 1 #####
summary_df_race_s <- df_s %>% select(rating_pre, rating_post, ID, race, gender) %>% filter(race!= "") %>%
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

summary_df_race_s$race <- factor(summary_df_race_s$race, 
                                 levels = c("White", "Black", "Asian", "Hispanic", "Native American", "Other"))

# Create the plot
race_bars <- ggplot(summary_df_race_s, aes(x = race, y = mean_rating, fill = time)) +
  geom_bar(stat = "identity", position = position_dodge(width = 0.6), width = 0.5) +  # Thicker and shorter bars
  geom_errorbar(aes(ymin = mean_rating - se_rating, ymax = mean_rating + se_rating),
                position = position_dodge(width = 0.6), width = 0.25) +  # Adjust error bar position
  labs(
    title = "Mean Ratings Pre and Post Assessment by Race",
    x = "Race",
    y = "Mean Rating",
    fill = "Time"
  ) +
  scale_fill_manual(
    values = c("rating_pre" = "skyblue", "rating_post" = "orange"),  # Assuming 'time' variable has "Pre" and "Post"
    labels = c("Rating (Base)", "Rating (Blinded)")  # Set the legend labels
  ) +
  theme_bw() +  # White background
  theme(
    plot.title = element_text(hjust = 0.5, size = 16),  # Larger title font
    axis.title = element_text(size = 14),  # Larger axis titles
    axis.text = element_text(size = 12),  # Larger axis labels
    legend.title = element_text(size = 14),  # Larger legend title
    legend.text = element_text(size = 12),  # Larger legend text
    text = element_text(size = 14)  # General font size
  )
race_bars
ggsave("./results/race_bars_strong.png",race_bars)

summary_df_gender_s<- df_s %>% select(rating_pre, rating_post, ID, race, gender) %>% filter(gender!= "") %>%
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


# Create the plot
gender_bars <- ggplot(summary_df_gender_s, aes(x = gender, y = mean_rating, fill = time)) +
  geom_bar(stat = "identity", position = position_dodge(width = 0.6), width = 0.5) +  # Thicker and shorter bars
  geom_errorbar(aes(ymin = mean_rating - se_rating, ymax = mean_rating + se_rating),
                position = position_dodge(width = 0.6), width = 0.25) +  # Adjust error bar position
  labs(
    title = "Mean Ratings Pre and Post Assessment by Gender",
    x = "Gender",
    y = "Mean Rating",
    fill = "Time"
  ) +
  scale_fill_manual(
    values = c("rating_pre" = "skyblue", "rating_post" = "orange"),  # Assuming 'time' variable has "Pre" and "Post"
    labels = c("Rating (Base)", "Rating (Blinded)")  # Set the legend labels
  ) +
  theme_bw() +  # White background
  theme(
    plot.title = element_text(hjust = 0.5, size = 16),  # Larger title font
    axis.title = element_text(size = 14),  # Larger axis titles
    axis.text = element_text(size = 12),  # Larger axis labels
    legend.title = element_text(size = 14),  # Larger legend title
    legend.text = element_text(size = 12),  # Larger legend text
    text = element_text(size = 14)  # General font size
  )
ggsave("./results/gender_bars_stronger.png",gender_bars)

##### Anovas and TurkeyHSD() #####

df_s <- df_s %>% mutate(
  gender_binary  = case_when(gender == "Male" ~ "Male", TRUE ~ "Non-male"),
  race_binary  = case_when(race == "White" ~ "White", TRUE ~ "Non-white")
)

# Run ANOVA for rating_pre and rating_post by race
anova_pre_race <- aov(rating_pre ~ race, data = df_s)
anova_post_race <- aov(rating_post ~ race, data = df_s)

# Run ANOVA for rating_pre and rating_post by gender
anova_pre_gender <- aov(rating_pre ~ gender, data = df_s)
anova_post_gender <- aov(rating_post ~ gender, data = df_s)

anova_results <- bind_rows(
  tidy(anova_pre_race) %>% mutate(variable = "Rating (Base)", group = "Race"),
  tidy(anova_post_race) %>% mutate(variable = "Rating (Post)", group = "Race")
) %>% select(variable,statistic, p.value, df) %>% na.omit()

race_table_anova <- gt(anova_results) %>%
  tab_header(
    title = "ANOVA for Race Pre and Post Blinding"
  ) %>%
  tab_style(
    style = list(
      cell_fill(color = "white")  # Set background to white
    ),
    locations = cells_body()
  ) %>%
  tab_style(
    style = list(
      cell_text(weight = "bold")  # Make the text bold for better visibility
    ),
    locations = cells_column_labels()
  )
html_output <- browsable(race_table_anova)

# Save the HTML output to a temporary file
html_file <- tempfile(fileext = ".html")
save_html(html_output, html_file)
png_file <- "./results/race_anova.png"

# Run wkhtmltoimage to convert HTML to PNG
system(paste("wkhtmltoimage", html_file, png_file))

### GENDER ANOVA ###

anova_results <- bind_rows(
  tidy(anova_pre_gender) %>% mutate(variable = "Rating (Base)", group = "Gender"),
  tidy(anova_post_gender) %>% mutate(variable = "Rating (Post)", group = "Gender")
) %>% select(variable,statistic, p.value, df) %>% na.omit()

gender_table_anova <- gt(anova_results) %>%
  tab_header(
    title = "ANOVA for Gender Pre and Post Blinding"
  ) %>%
  tab_style(
    style = list(
      cell_fill(color = "white")  # Set background to white
    ),
    locations = cells_body()
  ) %>%
  tab_style(
    style = list(
      cell_text(weight = "bold")  # Make the text bold for better visibility
    ),
    locations = cells_column_labels()
  )
html_output <- browsable(gender_table_anova)

# Save the HTML output to a temporary file
html_file <- tempfile(fileext = ".html")
save_html(html_output, html_file)
png_file <- "./results/gender_anova.png"

# Run wkhtmltoimage to convert HTML to PNG
system(paste("wkhtmltoimage", html_file, png_file))

##### RACE TURKEY #####

tukey_pre <- aov(rating_pre ~ race, data = df_s)
tukey_post <- aov(rating_post ~ race, data = df_s)

# Get TukeyHSD results
tukey_pre_results <- TukeyHSD(tukey_pre)
tukey_post_results <- TukeyHSD(tukey_post)

tukey_pre_df <- as.data.frame(tukey_pre_results$race) %>%
  rownames_to_column(var = "Pairwise Comparison") %>%
  select(`Pairwise Comparison`, diff, `p adj`) %>%
  rename(
    difference_pre = diff,
    p_value_pre = `p adj`
  )

tukey_post_df <- as.data.frame(tukey_post_results$race) %>%
  rownames_to_column(var = "Pairwise Comparison") %>%
  select(`Pairwise Comparison`, diff, `p adj`) %>%
  rename(
    difference_post = diff,
    p_value_post = `p adj`
  )

# Merge the pre and post results by "Pairwise Comparison"
pairwise_results_race <- tukey_pre_df %>%
  left_join(tukey_post_df, by = "Pairwise Comparison") %>%
  filter(p_value_pre < 0.35 | p_value_post < 0.35)  # Only keep significant results

pairwise_table_race <- gt(pairwise_results) %>%
  tab_header(
    title = "Significant Differences"
  ) %>%
  cols_label(
    `Pairwise Comparison` = "Pairwise Comparison",
    difference_pre = "Diff",
    p_value_pre = "P-val",
    difference_post = "Diff",
    p_value_post = "P-val"
  ) %>%
  tab_spanner(
    label = "Pre-blinding",
    columns = vars(difference_pre, p_value_pre)
  ) %>%
  tab_spanner(
    label = "Post-blinding",
    columns = vars(difference_post, p_value_post)
  ) %>%
  tab_style(
    style = list(cell_fill(color = "white")),
    locations = cells_body()
  ) %>%
  tab_style(
    style = list(cell_text(weight = "bold")),
    locations = cells_column_labels()
  )

html_output <- browsable(pairwise_table_race)

# Save the HTML output to a temporary file
html_file <- tempfile(fileext = ".html")
save_html(html_output, html_file)
png_file <- "./results/race_turket.png"

# Run wkhtmltoimage to convert HTML to PNG
system(paste("wkhtmltoimage", html_file, png_file))



tukey_pre <- aov(rating_pre ~ gender, data = df_s)
tukey_post <- aov(rating_post ~ gender, data = df_s)

# Get TukeyHSD results
tukey_pre_results <- TukeyHSD(tukey_pre)
tukey_post_results <- TukeyHSD(tukey_post)

tukey_pre_df <- as.data.frame(tukey_pre_results$gender) %>%
  rownames_to_column(var = "Pairwise Comparison") %>%
  select(`Pairwise Comparison`, diff, `p adj`) %>%
  rename(
    difference_pre = diff,
    p_value_pre = `p adj`
  )

tukey_post_df <- as.data.frame(tukey_post_results$gender) %>%
  rownames_to_column(var = "Pairwise Comparison") %>%
  select(`Pairwise Comparison`, diff, `p adj`) %>%
  rename(
    difference_post = diff,
    p_value_post = `p adj`
  )

# Merge the pre and post results by "Pairwise Comparison"
pairwise_results_gender <- tukey_pre_df %>%
  left_join(tukey_post_df, by = "Pairwise Comparison") %>%
  filter(p_value_pre < 0.05 | p_value_post < 0.05)  # Only keep significant results

pairwise_table_gender <- gt(pairwise_results_gender) %>%
  tab_header(
    title = "Significant Differences"
  ) %>%
  cols_label(
    `Pairwise Comparison` = "Pairwise Comparison",
    difference_pre = "Diff",
    p_value_pre = "P-val",
    difference_post = "Diff",
    p_value_post = "P-val"
  ) %>%
  tab_spanner(
    label = "Pre-blinding",
    columns = vars(difference_pre, p_value_pre)
  ) %>%
  tab_spanner(
    label = "Post-blinding",
    columns = vars(difference_post, p_value_post)
  ) %>%
  tab_style(
    style = list(cell_fill(color = "white")),
    locations = cells_body()
  ) %>%
  tab_style(
    style = list(cell_text(weight = "bold")),
    locations = cells_column_labels()
  )

html_output <- browsable(pairwise_table_gender)

# Save the HTML output to a temporary file
html_file <- tempfile(fileext = ".html")
save_html(html_output, html_file)
png_file <- "./results/gender_turket.png"

# Run wkhtmltoimage to convert HTML to PNG
system(paste("wkhtmltoimage", html_file, png_file))

###### Gender x Race Interaction ##### 

df_s <- df_s %>% mutate(gender_race = interaction(race,gender))

df_w<- df_w %>% mutate(gender_race = interaction(race,gender))

# Run ANOVA for rating_pre and rating_post by race
anova_pre_int <- aov(rating_pre ~ gender_race, data = df_s)
anova_post_int <- aov(rating_post ~ gender_race, data = df_s)


anova_results <- bind_rows(
  tidy(anova_pre_int) %>% mutate(variable = "Rating (Base)", group = "Race X Gender"),
  tidy(anova_post_int) %>% mutate(variable = "Rating (Post)", group = "Race X Gender")
) %>% select(variable,statistic, p.value, df) %>% na.omit()

int_table_anova <- gt(anova_results) %>%
  tab_header(
    title = "ANOVA for Race x Gender Pre and Post Blinding"
  ) %>%
  tab_style(
    style = list(
      cell_fill(color = "white")  # Set background to white
    ),
    locations = cells_body()
  ) %>%
  tab_style(
    style = list(
      cell_text(weight = "bold")  # Make the text bold for better visibility
    ),
    locations = cells_column_labels()
  )
html_output <- browsable(int_table_anova)

# Save the HTML output to a temporary file
html_file <- tempfile(fileext = ".html")
save_html(html_output, html_file)
png_file <- "./results/int_anova.png"

# Run wkhtmltoimage to convert HTML to PNG
system(paste("wkhtmltoimage", html_file, png_file))

tukey_pre <- aov(rating_pre ~ gender_race, data = df_s)
tukey_post <- aov(rating_post ~ gender_race, data = df_s)

# Get TukeyHSD results
tukey_pre_results <- TukeyHSD(tukey_pre)
tukey_post_results <- TukeyHSD(tukey_post)

tukey_pre_df <- as.data.frame(tukey_pre_results$gender_race) %>%
  rownames_to_column(var = "Pairwise Comparison") %>%
  select(`Pairwise Comparison`, diff, `p adj`) %>%
  rename(
    difference_pre = diff,
    p_value_pre = `p adj`
  )

tukey_post_df <- as.data.frame(tukey_post_results$gender_race) %>%
  rownames_to_column(var = "Pairwise Comparison") %>%
  select(`Pairwise Comparison`, diff, `p adj`) %>%
  rename(
    difference_post = diff,
    p_value_post = `p adj`
  )

# Merge the pre and post results by "Pairwise Comparison"
pairwise_results_gender_race <- tukey_pre_df %>%
  left_join(tukey_post_df, by = "Pairwise Comparison") %>%
  filter(p_value_pre < 0.1 | p_value_post < 0.1) %>% arrange(desc(`Pairwise Comparison`)) # Only keep significant results 

pairwise_table_gender <- gt(pairwise_results_gender_race) %>%
  tab_header(
    title = "Significant Differences"
  ) %>%
  cols_label(
    `Pairwise Comparison` = "Pairwise Comparison",
    difference_pre = "Diff",
    p_value_pre = "P-val",
    difference_post = "Diff",
    p_value_post = "P-val"
  ) %>%
  tab_spanner(
    label = "Pre-blinding",
    columns = vars(difference_pre, p_value_pre)
  ) %>%
  tab_spanner(
    label = "Post-blinding",
    columns = vars(difference_post, p_value_post)
  ) %>%
  tab_style(
    style = list(cell_fill(color = "white")),
    locations = cells_body()
  ) %>%
  tab_style(
    style = list(cell_text(weight = "bold")),
    locations = cells_column_labels()
  )

html_output <- browsable(pairwise_table_gender)

# Save the HTML output to a temporary file
html_file <- tempfile(fileext = ".html")
save_html(html_output, html_file)
png_file <- "./results/gender_race_inter_turket.png"

# Run wkhtmltoimage to convert HTML to PNG
system(paste("wkhtmltoimage", html_file, png_file))


##### DIFFS #####

df_s <- df_s %>% filter(gender !="Nonbinary", race != "Native American")
# Visualization for Race (based on change_score)
summary_df_race_s <- df_s %>%
  select(change_score, race) %>%
  group_by(race) %>%
  summarise(
    mean_change_score = mean(change_score),
    se_change_score = sd(change_score) / sqrt(n()),
    .groups = "drop"
  )

summary_df_race_s$race <- factor(summary_df_race_s$race, 
                                 levels = c("White", "Black", "Asian", "Hispanic", "Native American", "Other"))

# Race change_score plot
race_bars <- ggplot(summary_df_race_s, aes(x = race, y = mean_change_score)) +
  geom_bar(stat = "identity", fill = "skyblue", width = 0.5) +
  geom_errorbar(aes(ymin = mean_change_score - se_change_score, ymax = mean_change_score + se_change_score),
                width = 0.25) +
  labs(
    title = "Mean Change in Ratings by Race",
    x = "Race",
    y = "Mean Change in Rating"
  ) +
  theme_bw() + 
  theme(
    plot.title = element_text(hjust = 0.5, size = 16),
    axis.title = element_text(size = 14),
    axis.text = element_text(size = 12),
    text = element_text(size = 14)
  )
ggsave("./results/race_bars_change.png", race_bars)

# Visualization for Gender (based on change_score)
summary_df_gender_s <- df_s %>%
  select(change_score, gender) %>%
  group_by(gender) %>%
  summarise(
    mean_change_score = mean(change_score),
    se_change_score = sd(change_score) / sqrt(n()),
    .groups = "drop"
  )

# Gender change_score plot
gender_bars <- ggplot(summary_df_gender_s, aes(x = gender, y = mean_change_score)) +
  geom_bar(stat = "identity", fill = "skyblue", width = 0.5) +
  geom_errorbar(aes(ymin = mean_change_score - se_change_score, ymax = mean_change_score + se_change_score),
                width = 0.25) +
  labs(
    title = "Mean Change in Ratings by Gender",
    x = "Gender",
    y = "Mean Change in Rating"
  ) +
  theme_bw() + 
  theme(
    plot.title = element_text(hjust = 0.5, size = 16),
    axis.title = element_text(size = 14),
    axis.text = element_text(size = 12),
    text = element_text(size = 14)
  )
ggsave("./results/gender_bars_change.png", gender_bars)

##### ANOVA for change_score by race and gender #####
# ANOVA for change_score by race
anova_change_race <- aov(change_score ~ race, data = df_s)
anova_change_gender <- aov(change_score ~ gender, data = df_s)
anova_pre_int <- aov(change_score ~ gender_race, data = df_s)

# Results table
anova_results <- bind_rows(
  tidy(anova_change_race) %>% mutate(variable = "Δ Rating", group = "Race"),
  tidy(anova_change_gender) %>% mutate(variable = "Δ Rating", group = "Gender"),
  tidy(anova_pre_int) %>% mutate(variable = "Δ Rating", group = "Gender x Race"),
  
) %>% select(group, `F-Stat`=statistic, p.value, df) %>% na.omit()

anova_table <- gt(anova_results) %>%
  tab_header(
    title = "ANOVA for Δ Rating by Race and Gender"
  ) %>%
  tab_style(
    style = list(cell_fill(color = "white")),
    locations = cells_body()
  ) %>%
  tab_style(
    style = list(cell_text(weight = "bold")),
    locations = cells_column_labels()
  )

html_output <- browsable(anova_table)

# Save to PNG
html_file <- tempfile(fileext = ".html")
save_html(html_output, html_file)
png_file <- "./results/change_anova.png"
system(paste("wkhtmltoimage", html_file, png_file))

##### TukeyHSD for change_score by race and gender #####
# Tukey test for change_score by race
tukey_change_race <- aov(change_score ~ race, data = df_s)
tukey_change_gender <- aov(change_score ~ gender, data = df_s)

# Get TukeyHSD results
tukey_change_race_results <- TukeyHSD(tukey_change_race)
tukey_change_gender_results <- TukeyHSD(tukey_change_gender)

tukey_change_race_df <- as.data.frame(tukey_change_race_results$race) %>%
  rownames_to_column(var = "Pairwise Comparison") %>%
  select(`Pairwise Comparison`, diff, `p adj`) %>%
  rename(
    difference_change = diff,
    p_value_change = `p adj`
  )

tukey_change_gender_df <- as.data.frame(tukey_change_gender_results$gender) %>%
  rownames_to_column(var = "Pairwise Comparison") %>%
  select(`Pairwise Comparison`, diff, `p adj`) %>%
  rename(
    difference_change = diff,
    p_value_change = `p adj`
  )

# Combine pre- and post-test Tukey results for significant differences
pairwise_results_race <- tukey_change_race_df %>%
  filter(p_value_change < 0.05)

pairwise_results_gender <- tukey_change_gender_df %>%
  filter(p_value_change < 0.05)

# Create pairwise tables
pairwise_table_race <- gt(pairwise_results_race) %>%
  tab_header(
    title = "Significant Race Differences in Change"
  ) %>%
  cols_label(
    `Pairwise Comparison` = "Pairwise Comparison",
    difference_change = "Diff",
    p_value_change = "P-val"
  ) %>%
  tab_style(
    style = list(cell_fill(color = "white")),
    locations = cells_body()
  )

html_output <- browsable(pairwise_table_race)
html_file <- tempfile(fileext = ".html")
save_html(html_output, html_file)
png_file <- "./results/race_tukey_change.png"
system(paste("wkhtmltoimage", html_file, png_file))

# Create gender pairwise table
pairwise_table_gender <- gt(pairwise_results_gender) %>%
  tab_header(
    title = "Significant Gender Differences in Change"
  ) %>%
  cols_label(
    `Pairwise Comparison` = "Pairwise Comparison",
    difference_change = "Diff",
    p_value_change = "P-val"
  ) %>%
  tab_style(
    style = list(cell_fill(color = "white")),
    locations = cells_body()
  )

html_output <- browsable(pairwise_table_gender)
html_file <- tempfile(fileext = ".html")
save_html(html_output, html_file)
png_file <- "./results/gender_tukey_change.png"
system(paste("wkhtmltoimage", html_file, png_file))


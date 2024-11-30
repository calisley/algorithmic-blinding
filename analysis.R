library(dplyr)
library(tidyr)
library(ggplot2)


library(stargazer)
library(tibble)
library(car)
library(data.table)


setwd("~/Github/algorithmic-blinding/")
df_demos <-fread("./data/pre_dat.csv")
df_ratings <- fread("./data/cleaned_resumes_with_ratings_confirm.csv") %>% select(ID, title, rating)

dat_pre <- df_demos %>% left_join(df_ratings, by='ID')
dat_pre_final <-dat_pre %>% filter(!is.na(rating)) %>% select(-c(6:15))
fwrite(dat_pre_final,"./data/full_data_pre_blinding.csv")
rm(dat_pre_final, df, dat_pre, df_demos, df_ratings)

non_text <- dat_pre_final %>% select(ID,Category, 6:17)

non_text_clean <- non_text %>% mutate(
  gender = 
    case_when(
      gender == "Male" ~ "M",
      gender == "Female" ~ "F",
      gender == "Nonbinary" ~ "NB",
      TRUE ~  NA_character_
  ),
  race = 
    case_when(
      race == "" ~ NA_character_,
      TRUE ~  race
    ),
)

non_text_clean[non_text_clean == ""] <- NA
non_text_clean <- non_text_clean %>% filter(!is.na(race)|!is.na(gender))

fwrite(non_text,"./data/no_text_pre_blind.csv")

anovas<-function(demo = c("race"), category = NA){
  plot_dat<-non_text_clean
  if(!is.na(category)){
    plot_dat <- plot_dat %>% filter(Category == category)
  }
  plot_dat<-plot_dat %>% 
    mutate(demo_splits = interaction(across(all_of(demo))))
    anova <- aov(rating ~ demo_splits, data = plot_dat)
    summary(anova)
    pairwise<-TukeyHSD(anova)$demo_splits
    pairwise_tib <- as_tibble(pairwise)
    pairwise_tib$split <- rownames(pairwise)
    pairwise_tib<-pairwise_tib %>% select(split, p_val = `p adj`, diff)
    print(pairwise_tib %>%filter(p_val < .05) %>%arrange(desc(diff)))
}


#doesn't look great but general idea...

dist_hists <- function(demo =c("race", "gender")){
  gg<- ggplot(non_text_clean%>%filter(gender != "NB"), aes(x=rating)) + 
    geom_histogram(aes(y = ..count../sum(..count..)), bins = 7, fill="skyblue", color="black")+
    facet_grid(race~ gender) + 
    labs(
      title = paste("Breakdown of ratings by", demo[1], "and", demo[2]),
      x = "Rating",
      y = "Count"
    ) +
    theme_minimal()
}



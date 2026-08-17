library(rvest)
library(tidyverse)
library(stringr)
library(stringi)
library(readxl)
library(strex)

setwd("C:/Users/mfertakos/OneDrive - University of Massachusetts/ModernOrnamentals")

#load in native candidates and get unique USDAcodes
candidates<-read.csv('NativeCandidatesList.csv')
codes<-unique(candidates$USDAcode)
results<-data.frame(SpeciesName = NA,
                    CommonName = NA,
                    USDAcode = NA,
                    USDAstatus = NA,
                    Duration = NA,
                    Habit = NA,
                    SizeNotes = NA,
                    BloomColor = NA,
                    BloomTime = NA,
                    Distribution = NA,
                    WaterUse = NA,
                    LightRequirements = NA,
                    SoilMoisture = NA,
                    SolpH = NA,
                    SoilDescription = NA,
                    UseWildlife = NA,
                    InterestingFoliage = NA,
                    FragrantFoliage = NA,
                    CommercialAvail = NA,
                    PropagationDescription = NA)
#scrape
for(j in codes){
  url<-paste0("https://www.wildflower.org/plants/result.php?id_plant=",j) #create URL
  page <- read_html(url) #read URL
  # Extract the desired information using CSS selectors
  species <- page %>% html_nodes("#fullpage_content > h2") %>% html_text(trim=TRUE)
  if (length(species) == 0) species <- NA
  common_name<- page %>% html_nodes(xpath="/html/body/main/div[@id='mainContentHub']/div[@id='fullpage_content']/h3[@class='tax'][2]") %>% html_text(trim=TRUE)
  if(length(common_name) == 0) common_name <- NA
  usda_symbol <- page %>%
    html_node(xpath = "/html/body/main/div[@id='mainContentHub']/div[@id='fullpage_content']/h3[@class='tax'][5]/a") %>%
    html_text(trim = TRUE)
  if (length(usda_symbol) == 0) usda_symbol <- NA
  usda_native_status <- page %>%
    html_node(xpath = '//*[@id="fullpage_content"]/h3[6]') %>%
    html_text(trim = TRUE)
  if (length(usda_native_status) == 0) usda_native_status <- NA
  duration <- page %>% html_nodes("#fullpage_content > div:nth-child(14) > a:nth-child(3)") %>% html_text()
  if (length(duration) == 0) duration <- NA
  habit <- page %>% html_nodes(xpath="/html/body/main/div[@id='mainContentHub']/div[@id='fullpage_content']/div[@class='section'][2]/a[@class='glossary_link'][2]") %>% html_text()
  if (length(habit) == 0) habit <- NA
  size_notes <-  page %>% html_node(xpath = "//strong[contains(text(), 'Size Notes:')]/following-sibling::text()[1]") %>% html_text(trim = TRUE)
  if (length(size_notes) == 0) size_notes <- NA
  bloom_color <- page %>%
    html_node(xpath = "//strong[contains(text(), 'Bloom Color:')]/following-sibling::text()[1]") %>%
    html_text(trim = TRUE)
  if (length(bloom_color) == 0) bloom_color <- NA
  bloom_time <- page %>%
    html_node(xpath = "//strong[contains(text(), 'Bloom Time:')]/following-sibling::text()[1]") %>%
    html_text(trim = TRUE)
  if (length(bloom_time) == 0) bloom_time <- NA
  distribution <- page %>%
    html_node(xpath = "//strong[contains(text(), 'Distribution:')]/following-sibling::text()[1]") %>%
    html_text(trim = TRUE)
  if (length(distribution) == 0) distrbution <- NA
  water_use <- page %>%
    html_node(xpath = "//strong[contains(text(), 'Water Use:')]/following-sibling::text()[1]") %>%
    html_text(trim = TRUE)
  if (length(water_use) == 0) water_use <- NA
  light_requirement <- page %>%
    html_node(xpath = "//strong[contains(text(), 'Light Requirement:')]/following-sibling::text()[1]") %>%
    html_text(trim = TRUE)
  if (length(light_requirement) == 0) light_requirement <- NA
  soil_moisture <- page %>%
    html_node(xpath = "//strong[contains(text(), 'Soil Moisture:')]/following-sibling::text()[1]") %>%
    html_text(trim = TRUE)
  if (length(soil_moisture) == 0) soil_moisture <- NA
  soil_pH <- page %>%
    html_node(xpath = "//strong[contains(text(), 'Soil pH:')]/following-sibling::text()[1]") %>%
    html_text(trim = TRUE)
  if (length(soil_pH) == 0) soil_pH <- NA
  soil_description <- page %>%
    html_node(xpath = "//strong[contains(text(), 'Soil Description:')]/following-sibling::text()[1]") %>%
    html_text(trim = TRUE)
  if (length(soil_description) == 0) soil_description <- NA
  use_wildlife<- page %>%
    html_node(xpath="//strong[contains(text(), 'Use Wildlife:')]/following-sibling::text()[1]") %>%
    html_text(trim=TRUE)
  if (length(use_wildlife) == 0) use_wildlife <- NA
  interesting_foliage <- page %>%
    html_node(xpath = "//strong[contains(text(), 'Interesting Foliage:')]/following-sibling::text()[1]") %>%
    html_text(trim = TRUE)
  if (length(interesting_foliage) == 0) interesting_foliage <- NA
  fragrant_foliage <- page %>%
    html_node(xpath = "//strong[contains(text(), 'Fragrant Foliage:')]/following-sibling::text()[1]") %>%
    html_text(trim = TRUE)
  if (length(fragrant_foliage) == 0) fragrant_foliage <- NA
  commercial_avail <- page %>%
    html_node(xpath = "//strong[contains(text(), 'Commercially Avail:')]/following-sibling::text()[1]") %>%
    html_text(trim = TRUE)
  if (length(commercial_avail) == 0) commerical_avail <- NA
  propagation_description <- page %>%
    html_node(xpath = "//strong[text()= 'Description:']/following-sibling::text()[1]") %>%
    html_text(trim=TRUE)
  if (length(propagation_description) == 0) propagation_description <- NA
  
  # Create a dataframe with the extracted data
  data <- data.frame(SpeciesName = species,
                     CommonName=common_name,
                     USDAcode=usda_symbol,
                     USDAstatus=usda_native_status,
                     Duration = duration,
                     Habit = habit,
                     SizeNotes = size_notes,
                     BloomColor = bloom_color,
                     BloomTime = bloom_time,
                     Distribution = distribution,
                     WaterUse = water_use,
                     LightRequirements = light_requirement,
                     SoilMoisture = soil_moisture,
                     SolpH = soil_pH,
                     SoilDescription = soil_description,
                     UseWildlife = use_wildlife,
                     InterestingFoliage = interesting_foliage,
                     FragrantFoliage = fragrant_foliage,
                     CommercialAvail=commercial_avail,
                     PropagationDescription=propagation_description)
  
  results<-rbind(results,data)
}

results<-results %>%
  filter_all(any_vars(!is.na(.)))

write.csv(results,'Ladybird.csv',row.names=FALSE)

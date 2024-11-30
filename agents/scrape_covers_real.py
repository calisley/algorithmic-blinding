from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from tqdm import tqdm
import os
import time
# Setup Firefox 

firefox_options = Options()
firefox_options.add_argument("--headless")
service = Service(GeckoDriverManager().install())
firefox_options = Options()
firefox_options.add_argument("--headless")
firefox_options.add_argument('--disable-blink-features=AutomationControlled')
firefox_options.add_argument('--no-sandbox')
firefox_options.add_argument('--disable-dev-shm-usage')
firefox_options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")>>> driver = webdriver.Firefox(service=service, options=firefox_options)
driver.get("https://www.indeed.com/career-advice/cover-letter-samples")
# Find all links within the unordered list
# Method 1: Using CSS Selector

links = driver.find_elements(By.CSS_SELECTOR, "a.css-1ivu7ag")
# Alternative Method 2: Using XPath
# links = driver.find_elements(By.XPATH, "//ul[contains(@class, 'css-1q4vxyr')]//a")
# Extract and store all the href attributes

cover_letter_links = []
for link in links:
    href = link.get_attribute('href')
    if href and 'cover-letter-samples' in href:
        cover_letter_links.append(href)

print(f"\nTotal links found: {len(cover_letter_links)}")
driver.quit()
# Find all links within the unordered list
# Method 1: Using CSS Selector

links = driver.find_elements(By.CSS_SELECTOR, "a.css-1ivu7ag")
# Alternative Method 2: Using XPath
# links = driver.find_elements(By.XPATH, "//ul[contains(@class, 'css-1q4vxyr')]//a")
# Extract and store all the href attributes

cover_letter_links = []
for link in links:
    href = link.get_attribute('href')
    if href and 'cover-letter-samples' in href:
        cover_letter_links.append(href)

print(f"\nTotal links found: {len(cover_letter_links)}")

driver.quit()
for i, link in tqdm(enumerate(cover_letter_links, 1)):

    driver = webdriver.Firefox(service=service, options=firefox_options)
    try:
        driver.get(link)
        time.sleep(2)
        try:
            content_div = driver.find_element(By.CLASS_NAME, "editor-module")
            if content_div:
                letter_text = content_div.text
                if letter_text:
                    # Create filename from index and sanitized URL
                    filename = f"cover_letter_{i}.txt"
                    filepath = os.path.join('./covers', filename)
                    # Write cover letter to individual file
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(letter_text)
                    print(f"Successfully saved cover letter from {link} to {filename}")
                    driver.quit()
            else:
                print(f"No content found on {link}")
                driver.quit()
        except:
            driver.quit()
            continue
    except Exception as e:
        print(f"Error processing {link}: {str(e)}")
        driver.quit()
        continue
    driver.quit()

    # Extract and transform the last part of each URL into job titles
    job_titles = []
    for link in cover_letter_links:
        # Split URL by '/' and get last part
        last_part = link.rstrip('/').split('/')[-1]
        
        # Replace hyphens with spaces and capitalize first letter of each word
        words = last_part.replace('-', ' ').split()
        job_title = ' '.join(word.capitalize() for word in words)
        
        # Store the transformed job title
        job_titles.append(job_title)
        
    # Rename files using job titles
    for i, (link, job_title) in enumerate(zip(cover_letter_links, job_titles), 1):
        old_filename = f"cover_letter_{i}.txt"
        new_filename = f"{job_title}.txt"
        old_path = os.path.join('./covers', old_filename)
        new_path = os.path.join('./covers', new_filename)
        
        try:
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
                print(f"Renamed {old_filename} to {new_filename}")
        except Exception as e:
            print(f"Error renaming {old_filename}: {str(e)}")



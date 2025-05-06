from bs4 import BeautifulSoup
import cloudscraper
import requests
import pandas as pd
from fake_useragent import UserAgent
import nltk    
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
import re
from spellchecker import SpellChecker
from transformers import T5ForConditionalGeneration, T5Tokenizer  #T5 Model

# Ensure the NLTK Resources are downloaded
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')

# Load T5 model and tokenizer
model_name = "t5-small"  
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)


# Generate a random user-agent
ua = UserAgent()
headers = {
    'User-Agent': ua.random
}

# Create a cloudscraper instance to bypass Cloudflare protection (*only reduce the chance of being blocked)
scraper = cloudscraper.create_scraper()

# Initialize the spell checker
spell = SpellChecker()

# Indeed URL for website scraping
def generate_url(job_title, job_location):
    url_template = "https://malaysia.indeed.com/jobs?q={}&l={}"
    url = url_template.format(job_title, job_location)
    return url

# Collect job cards from page
def collect_job_cards_from_page(html):
    soup = BeautifulSoup(html.text, 'html.parser')
    cards = soup.find_all('div', class_='job_seen_beacon')
    return cards, soup

# Skip to the next page of the website
def find_next_page(soup):
    try:
        pagination = soup.find("a", {"aria-label": "Next Page"}).get("href")
        return "https://malaysia.indeed.com" + pagination
    except AttributeError:
        return None

# Extract the actual data from the website, such as job title, company, location, salary, job type, summary, date posted, and job URL
def extract_job_card_data(card):
    atag = card.h2.a
    try:
        job_title = card.find('h2', 'jobTitle').text 
    except AttributeError:
        job_title = ''

    try:
        company = card.find('span', {'data-testid': 'company-name'}).text
    except AttributeError:
        company = ''

    try:
        location = card.find("div", {'data-testid': 'text-location'}).text
    except AttributeError:
        location = ''

    try:
        salary = card.find('div', class_='salary-snippet-container').text
    except AttributeError:
        salary = ''

    try:
        job_types = card.find('div', class_='metadata css-5zy3wz eu4oa1w0').text.strip()
    except AttributeError:
        job_types = ''

    # Extracting job summary
    try:
        summary_container = card.find('div', class_='css-9446fg eu4oa1w0')
        if summary_container:
            # Check for list items
            summary_list_items = summary_container.find_all('li')
            if summary_list_items:
                summary = ' '.join(item.text.strip() for item in summary_list_items)
            else:
                summary = summary_container.text.strip()
        else:
            summary = None
    except AttributeError:
        summary = None

    try:
        date_posted = card.find("span", {'class': 'css-qvloho eu4oa1w0'}).text.strip()
    except AttributeError:
        date_posted = ''

    job_url = 'https://malaysia.indeed.com' + atag.get('href')
    return job_title, company, location, salary, job_types, summary, date_posted, job_url


# Normalize text using T5 model (We selected to use Normalizing Tokens)
def normalize_text_with_t5(text):
    # Prepare the input text for the T5 model
    input_text = f"normalize: {text}"
    input_ids = tokenizer.encode(input_text, return_tensors="pt")

    # Generate the normalized text
    output_ids = model.generate(input_ids, max_length=512, num_beams=4, early_stopping=True)
    normalized_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    
    return normalized_text


# Preprocess text data
def preprocess_summary(text):

    # Convert text to lowercase
    text = text.lower()

    # Normalize text using T5 model
    normalized_text = normalize_text_with_t5(text)

    # Define patterns to remove
    patterns_to_remove = [
        "duration", "responsibilit(y|ies)", "responsible", "experience", "understanding", "field",
        "provided","provide", "qualification", "year", "coordinate", "ability", "meal", "allowance",        
        "company", "team", "requirement", "user", "product", "quality", "high", "ensure","need",
        "advantage", "assist", "team", "would", "fulltime", "parttime", "intern", "free", "parking",
        "working", "hour", "benefit", "bonus", "medical", "insurance", "annual", "leave", "career",
        "opportunity", "good", "environment", "training", "must", "salary", "range", "month",
        "flexible", "multiple", "location", "job", "description", "health", "assistance","matching","etc",
        "preferred","printer","scanner","fax","machine","faxing","photocopy","photocopying","photostat",
        "body", "log", "basic", "real", "including", "permanent", "temporary", "contract", "shift", "day",
        "minimum", "maximum", "objective", "create", "per", "recommendation", "recommend", "recommendations"
    ]

    # Remove special characters and punctuation
    normalized_text = re.sub( r"[^a-zA-Z0-9\s]", '', text)

    # Remove patterns
    for pattern in patterns_to_remove:
        normalized_text = re.sub(pattern, '', normalized_text)

    # Tokenize the text
    tokens = word_tokenize(normalized_text)

    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [word for word in tokens if word.lower() not in stop_words]

    # Spell check and correct the tokens
    corrected_tokens = [spell.correction(word) if spell.correction(word) is not None else word for word in filtered_tokens]
    
    # Initialize WordNetLemmatizer
    lemmatizer = WordNetLemmatizer()

    # Apply lemmatization to filtered tokens
    lemmatized_tokens = [lemmatizer.lemmatize(word) for word in corrected_tokens]
    
    # Join the lemmatized tokens back into a single string
    clean_text = ' '.join(lemmatized_tokens)
    
    return clean_text

# Clean salary data
def clean_salary_data(salary):
    if salary:
        # Remove non-numeric characters except for '-' and '.'
        salary = re.sub(r'[^\d\.-]', '', salary)
        if '-' in salary:
            min_salary, max_salary = salary.split('-')
            min_salary = float(min_salary.replace(',', ''))
            max_salary = float(max_salary.replace(',', ''))
        else:
            min_salary = max_salary = float(salary.replace(',', ''))
    else:
        min_salary = max_salary = None
    
    return min_salary, max_salary

# Clean Job Type data
def clean_job_type(job_type):
    if job_type:
        # Remove any numeric characters and the '+' sign
        cleaned_job_type = re.sub(r'\+\d+', '', job_type)
    else:
        cleaned_job_type = None
    
    return cleaned_job_type

# Since the Job Titles are quite heterogeneus, so we need to clean it.
def clean_job_title(job_title):

    # Remove contents within parentheses
    job_title = re.sub(r'\([^)]*\)', '', job_title)
    # Remove # and subsequent numeric digits
    job_title = re.sub(r'#\d+', '', job_title)
    # Convert to lowercase
    job_title = job_title.lower()
    # Remove month names and abbreviations
    job_title = re.sub(r'\b(january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sep|october|oct|november|nov|december|dec)\b', '', job_title)
    # Remove excess whitespace
    job_title = re.sub(r'\s+', ' ', job_title).strip()
    return job_title

# Clean the 'Date Posted' column
def clean_date_posted(date_posted):
    if pd.isnull(date_posted) or date_posted == '':
        return pd.NaT

    # Remove unwanted phrases
    date_posted = re.sub(r'Posted|EmployerActive', '', date_posted).strip()
    
    # Standardize "Today"
    date_posted = re.sub(r'Today', '0 days ago', date_posted).strip()
    
    # Handle "30+ days ago"
    if '+' in date_posted:
        return pd.Timestamp.now().normalize() - pd.Timedelta(days=30)
    else:
        # Extract the number of days and calculate the date
        match = re.search(r'\d+', date_posted)
        if match:
            days_ago = int(match.group())
            return pd.Timestamp.now().normalize() - pd.Timedelta(days=days_ago)
        else:
            return pd.NaT  # Return NaT if the date is not in the expected format


def main(job_title, job_location, filepath):
    job_data = []  # List to store job data
    unique_jobs = set()  # Track job URLs to avoid collecting duplicate records
    print("Starting to scrape Indeed for `{}` in `{}`".format(job_title, job_location))
    url = generate_url(job_title, job_location)

    while True:
        print(url)
        try:
            # Use headers in the request
            html = scraper.get(url, headers=headers)
            
        except requests.RequestException as e:
            print("Network error occurred: ", e)
            break

        if not html or html.status_code != 200:
            if html.status_code != 429:     # Check if the status code is not 429 (Too Many Requests)
                print("\n\n======================================================")
                print("|  Failed to retrieve the webpage. Status code:", html.status_code, " |")
                print("======================================================\n")
                print("Try to run again using different network, mobile hotspot with VPN.\n")
            break

        cards, soup = collect_job_cards_from_page(html)
        if not cards:
            print("No job postings found on this page.")
            break

        for card in cards:
            record = extract_job_card_data(card)
            if all(record) and record[-1] not in unique_jobs:  # Check if all fields are non-empty
                job_data.append(record)
                unique_jobs.add(record[-1])

        url = find_next_page(soup)
        if not url:
            break

    if job_data:
        print('Finished collecting {:,d} job postings. Successfully Collecting! Please wait a few minutes to half an hour for data processing...'.format(len(unique_jobs)))

        # Convert the job data list to a DataFrame
        df = pd.DataFrame(job_data, columns=["JobTitle", "Company", "Location", "Salary", "JobType", "Summary", "Date Posted", "JobUrl"])

        # Remove duplicates based on all columns except "Summary" and "JobUrl"
        df_cleaned = df.drop_duplicates(subset=df.columns.difference(['Summary', 'JobUrl']))

        # Apply the cleaning function to the JobTitle column
        df_cleaned.loc[:, 'JobTitle'] = df_cleaned['JobTitle'].apply(clean_job_title)

        # Data Preprocessing: Clean and preprocess text data
        df_cleaned.loc[:, 'Summary'] = df_cleaned['Summary'].apply(preprocess_summary)

        # Clean and split salary data
        min_salary, max_salary = zip(*df_cleaned['Salary'].apply(clean_salary_data))
        df_cleaned.loc[:, 'Min Salary'] = min_salary
        df_cleaned.loc[:, 'Max Salary'] = max_salary

        # Clean Job Type Data
        df_cleaned.loc[:, 'JobType'] = df_cleaned['JobType'].apply(clean_job_type)

        # Clean Date Posted to get the actual date
        df_cleaned.loc[:, 'Date Posted'] = df_cleaned['Date Posted'].apply(clean_date_posted)

        # Reorder columns
        df_arranged = df_cleaned[['JobTitle','Company', 'Location', 'Min Salary', 'Max Salary', 'JobType', 'Summary', 'Date Posted', 'JobUrl']]

        # Save the DataFrame to a CSV file
        df_arranged.to_csv(filepath, index=False)

        # Print the DataFrame
        print(df_arranged)
        print('\nSuccessfully export to CSV!') # Print the number of jobs collected

    else:
        # print('\nFinished collecting {:,d}'.format(len(unique_jobs))) # Print the number of jobs collected
        print('Please try again...') # Print the number of jobs collected

    return job_data


# Run the main function
if __name__ == '__main__':
    title = 'IT'
    loc = 'Malaysia'
    path = 'indeed_job.csv'

    df = main(title, loc, path)
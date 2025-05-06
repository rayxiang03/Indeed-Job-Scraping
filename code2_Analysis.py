import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter
import numpy as np


# Load the data
data = pd.read_csv('indeed_job.csv')

# Drop rows with missing values
data.dropna(inplace=True)


# Try our best to define the categories and their associated keywords (JOB TITLE)
job_categories = {
    'Business Analyst': ['business analyst', 'ba', 'b.a.'],
    'AI specialist': ['ai', 'artificial intelligence', 'machine learning', 'deep learning', 'nlp', 'computer vision'],
    'IT Project Manager': ['it project manager', 'project manager', 'it pmo', 'technical/it recruiter'],
    'IT Technician': ['it technician', 'technician', 'it technical assistant', 'desktop engineer', 'field service engineer'],
    'IT Support': ['it support', 'helpdesk', 'it service desk', 'support engineer', 'technical support', 'it service desk analyst', 'desktop support engineer', 
                   'remote it support', 'helpdesk', 'service desk', 'support specialist', "support"],
    'IT Manager': ['it manager', 'senior it manager', 'assistant it manager', 'manager, it', 'mis officer'],
    'Senior IT Executive': ['senior it executive', 'it senior executive', 'senior executive it', 'senior it support executive'],
    'IT Intern': ['it intern', 'internship in information technology', 'internship for it', 'it internship', 'intern - it support', 'internship for computer/it students', 'graduate program for it fresh graduate', 'internship for it support', 'internship for computer / network students'],
    'IT Engineer': ['it engineer', 'engineer', 'network engineer', 'junior it engineer', 'infrastructure engineer', 'advanced support engineer', 'system engineer', 'systems engineer'],
    'Software Engineer': ['software engineer', 'software developer', 'software qa engineer', 'software support technician', 'junior software developer', 'junior frontend developer', 'junior php backend developer', 'ui/ix designer', 'developer'],
    'IT Specialist': ['it specialist', 'specialist'],
    'System Analyst': ['system analyst', 'systems analyst', 'system support analyst'],
    'Personal Assistant': ['personal assistant', 'personal driver', 'pa to director', 'pa'],
    'Admin Assistant': ['admin assistant', 'administration officer', 'administration/it coordinator assistant', 'admin', 'admin finance'],
    'Maintenance Technician': ['maintenance technician', 'it & maintenance executive', 'technician', 'machinery technician', 'mechanical engineer'],
    'Service Engineer': ['service engineer', 'it field support engineer', 'it service engineer', 'support engineer'],
    'Data Analyst': ['data analyst', 'senior data analyst', 'analyst_data center', 'data processing executive', 'da'],
    'IT Security Engineer': ['it security engineer', 'cybersecurity', 'it security officer', 'governance risk compliance', 'security engineer', 'security analyst'],
}

# Function to categorize job titles based on keywords
def categorize_job_title(job_title):
    job_title = job_title.lower()
    for category, keywords in job_categories.items():
        if any(keyword in job_title for keyword in keywords):
            return category
    return job_title

data['JobCategory'] = data['JobTitle'].apply(categorize_job_title)


#   --- FIGURE 1: Function to plot the distribution of job titles --- 
def plot_job_titles(data):
    plt.figure(figsize=(12, 8))
    job_title_counts = data['JobCategory'].value_counts().head(10)  # Get the top 10 most frequent job categories
    colors = plt.cm.tab10(range(len(job_title_counts)))  # Get a list of colors from colormap

    bars = plt.barh(job_title_counts.index, job_title_counts.values, color=colors)
    plt.title('Top 10 Job Categories')
    plt.xlabel('Number of Job Postings')
    plt.ylabel('Job Category')
    plt.gca().invert_yaxis()  # Invert y-axis to have highest count at the top
    plt.tight_layout()

    # Annotate each bar with the quantity of job postings
    for bar in bars:
        plt.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                 f'{bar.get_width()}', va='center', ha='left')

    # Add a legend
    plt.legend(bars, job_title_counts.index, title='Job Categories', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.show()


#   --- FIGURE 2: Function to plot location distribution ---
def plot_location(data):
    location_counts = data['Location'].value_counts().head(10)   # Calculate frequency of each location
    top_locations = location_counts.index               # Extract top 10 locations and their frequencies
    top_frequencies = location_counts.values
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(top_locations, top_frequencies, color=plt.cm.Set2.colors[:len(top_locations)])
    plt.title('Top 10 Locations for Job Postings')
    plt.xlabel('Location')
    plt.ylabel('Number of Job Postings')
    plt.xticks(rotation=45)
    
    # Adding legend with location names and frequencies
    legend_labels = [f"{loc}: {freq}" for loc, freq in zip(top_locations, top_frequencies)]
    plt.legend(bars, legend_labels, loc='upper right', fontsize='small')
    
    plt.tight_layout()
    plt.show()


#   --- FIGURE 3: Function to plot Salary Range Distribution ---
data = data[(data['Min Salary'] <= 20000) & (data['Max Salary'] <= 20000)]    # Filter out salaries above 20000
data['Midpoint Salary'] = (data['Min Salary'] + data['Max Salary']) / 2       # Calculate midpoint salary
top_categories = data['JobCategory'].value_counts().head(6).index             # Get top 5 job categories by number of job postings
data_top_categories = data[data['JobCategory'].isin(top_categories)]          # Filter data for only these top job categories
avg_salary_by_category = data_top_categories.groupby('JobCategory')['Midpoint Salary'].mean().sort_values(ascending=False) # Group data by job category and calculate average midpoint salary

def plot_salary(data):
    plt.figure(figsize=(10, 6))
    colors = plt.cm.Set3(range(len(avg_salary_by_category)))  # Set colors for bars

    # Plotting bars
    bars = plt.bar(avg_salary_by_category.index, avg_salary_by_category.values, color=colors)
    
    plt.title('Average Salary by Top 6 Job Categories')
    plt.xlabel('Job Category')
    plt.ylabel('Average Midpoint Salary')
    plt.xticks(rotation=45, ha='right')

    # Adding legend with job categories and their colors
    legend_labels = [f"{cat}: RM {salary:.2f}" for cat, salary in avg_salary_by_category.items()]
    plt.legend(bars, legend_labels, loc='upper right', fontsize='small')

    plt.tight_layout()
    plt.show()


#   --- FIGURE 4: Function to plot Word Cloud of Job Summary (Keywords) ---
def plot_word_cloud(data):
    text = ' '.join(data['Summary'])
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    plt.figure(figsize=(10, 6))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title('Word Cloud of Job Summaries')
    plt.show()


#   --- FIGURE 5: Function to plot Keywords of Job Summary ---
def plot_top_keywords(data, num_keywords=10):
    # Combine all summaries into one string
    all_summaries = ' '.join(data['Summary'])
    # Tokenize the string
    words = all_summaries.split()
    # Get the most common words
    word_counts = Counter(words)
    common_words = word_counts.most_common(num_keywords)
    words, counts = zip(*common_words)
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(words, counts, color=plt.cm.Set2.colors[:len(words)])
    plt.title('Top 10 Keywords in Job Summaries')
    plt.xlabel('Keywords')
    plt.ylabel('Frequency')
    
    # Set x-axis labels
    plt.xticks(rotation=45)
    
    # Add legends
    legend_labels = [f'{word}: {count}' for word, count in common_words]
    plt.legend(bars, legend_labels, loc='upper right')
    
    plt.show()


#   --- FIGURE 6: Function to plot Job Type distribution as a Line Graph ---
# Function to preprocess job types
def preprocess_job_type(job_type):
    # Convert to lowercase
    job_type = job_type.lower()
    # Remove leading and trailing whitespace
    job_type = job_type.strip()
    return job_type

# Apply preprocessing to JobType column  
data['JobType'] = data['JobType'].apply(preprocess_job_type)   
def plot_job_type_distribution(data):
    job_type_counts = data['JobType'].value_counts().sort_index()
    
    plt.figure(figsize=(10, 6))
    plt.plot(job_type_counts.index, job_type_counts.values, marker='o', linestyle='-', color='b', label='Job Types')
    
    # Annotate each point with its value (adjusting y position)
    for i, count in enumerate(job_type_counts.values):
        plt.text(i, count + max(job_type_counts.values)*0.02, str(count), ha='center', fontsize=10)
    
    plt.title('Distribution of Job Types')
    plt.xlabel('Job Type')
    plt.ylabel('Count')
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, axis='y')
    plt.tight_layout()
    plt.legend()
    plt.show()


#   --- FIGURE 7: Function to plot Association Between Location and Salary ---
# Calculate midpoint salary
data['Midpoint Salary'] = (data['Min Salary'] + data['Max Salary']) / 2

# Filter data for full-time job postings and salaries less than 20000
full_time_data = data[(data['JobType'] == 'full-time') & (data['Midpoint Salary'] < 20000)]
location_counts = full_time_data['Location'].value_counts().head(10)  # Top 10 locations by full-time job postings
location_salaries = full_time_data.groupby('Location').agg({'Midpoint Salary': 'mean'}).loc[location_counts.index]

def plot_location_salary(location_counts, location_salaries):
    fig, ax1 = plt.subplots(figsize=(12, 8))

    # Define colors for each location
    colors = plt.cm.Set3(np.linspace(0, 1, len(location_counts)))

    # Plot bar chart for job postings count
    ax1.bar(location_counts.index, location_counts.values, color=colors, alpha=0.6, label='Job Postings Count')
    ax1.set_xlabel('Location')
    ax1.set_ylabel('Number of Full-Time Job Postings', color='b')
    ax1.tick_params(axis='y', labelcolor='b')
    ax1.set_xticklabels(location_counts.index, rotation=45, ha='right')

    # Create a second y-axis for salary line plot
    ax2 = ax1.twinx()
    ax2.plot(location_salaries.index, location_salaries['Midpoint Salary'], color='r', marker='o', linewidth=2, label='Average Salary')
    ax2.set_ylabel('Average Midpoint Salary (RM)', color='r')
    ax2.tick_params(axis='y', labelcolor='r')

    # Title and legend
    ax1.set_title('Full-Time Job Postings Count and Average Salary (< RM 20,000) by Location')
    ax2.legend(loc='upper right')

    plt.tight_layout()
    plt.show()



# Call the functions to create the plots
plot_job_titles(data)                                       #Figure 1
plot_location(data)                                         #Figure 2
plot_salary(data)                                           #Figure 3
plot_word_cloud(data)                                       #Figure 4
plot_top_keywords(data)                                     #Figure 5
plot_job_type_distribution(data)                            #Figure 6
plot_location_salary(location_counts, location_salaries)    #Figure 7
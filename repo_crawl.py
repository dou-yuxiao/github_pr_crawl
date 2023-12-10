import requests
from bs4 import BeautifulSoup
import json


def write_json(new_data, json_path):
    with open(json_path,'w+', encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False)     
    print('Total write ', len(new_data))




# URL of the GitHub page
url = 'https://github.com/EvanLi/Github-Ranking/blob/master/Top100/Java.md'

# Fetch the page content
response = requests.get(url)
content = response.content

# Parse with BeautifulSoup
soup = BeautifulSoup(content, 'html.parser')

# Find the repository list - Adjust this line based on the actual HTML structure
repo_elements = soup.find_all('a', href=True)  # or use other suitable filters

# Extract repository URLs
repos = []
for elem in repo_elements:
    if 'github.com' in elem['href']:  # Filter out only GitHub repo links
        repos.append(elem['href'])

update_repos_url = []
for ele in repos:
    if ele[2:-2].startswith("https://github.com/") and len(ele[2:-2].split("/"))==5:
        update_repos_url.append(ele[2:-2])

# Print or process the list of repositories
write_json(update_repos_url, "repo_url_list.json")
print(update_repos_url)
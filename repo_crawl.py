import requests
import json
import time
import os

PR_NUMBER = 50
JSON_PATH = "repo_url_list.json"
# Personal Access Token - Replace 'YOUR_TOKEN' with your GitHub token
GITHUB_TOKEN = "Your Token"
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    
    'Accept': 'application/vnd.github.v3+json',
}



def read_json(file_path):
    with open(file_path,'r', encoding="utf-8") as f:
        label = json.load(f)
        return label

def write_json(new_data, json_path):
    with open(json_path,'w+', encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False)     
    print('Total write ', len(new_data))


def get_next_page_url(link_header):
    # print("link_header.split: ", link_header.split(','), "\n")
    for link in link_header.split(', '):
        # print("link: ", link)
        # import pdb
        # pdb.set_trace()
        url, rel = link.split(';')
        if 'rel="next"' in rel:
            return url.strip('<>')
    return None

def get_java_repos_with_closed_prs(min_closed_prs, page=20):
    repos_with_enough_prs = []

    # Search for Java repositories
    search_url = "https://api.github.com/search/repositories"
    query_params = {
        'q': 'language:Java',
        'sort': 'stars',
        'order': 'desc',
        'per_page': 100  # Adjust as needed
    }
    number=1
    while search_url:
        
        print(number)
        if number>page:
            break
        response = requests.get(search_url, headers=HEADERS, params=query_params)
        if response.status_code == 200:
            java_repos = response.json()['items']
            for repo in java_repos:
                repo_name = repo['full_name']
                # repo_name = "dou-yuxiao/github_pr_crawl"
                prs_url = f"https://api.github.com/repos/{repo_name}/pulls"
                pr_params = {'state': 'closed', 'per_page': 1}
                

                total_closed_prs = extract_last_page_number(prs_url, pr_params)
                

                if total_closed_prs >= min_closed_prs:
                    repos_with_enough_prs.append(repo['html_url'])
            number+=1
            link_header = response.headers.get('Link', '')
            if link_header == "":
                break
            search_url = get_next_page_url(link_header)
        else:
            # if response.status_code == 503:
            #     print(f"Failed to fetch data. Status code: {response.status_code}")
            #     continue
            print(f"Failed to fetch data. Status code: {response.status_code}")
            time.sleep(10)
            continue


    return repos_with_enough_prs

def extract_last_page_number(prs_url, pr_params):
    # Extract the last page number from the 'Link' header
    pr_response = requests.get(prs_url, headers=HEADERS, params=pr_params)
    if pr_response.status_code == 200:
        if 'Link' in pr_response.headers:
            link_header=pr_response.headers['Link']
            parts = link_header.split(',')
            last_page_link = [p for p in parts if 'rel="last"' in p]
            if len(last_page_link)==1:
                last_page_number = last_page_link[0].split('page=')[-1].split('>')[0]
                return int(last_page_number)
            else:
                return 0
        else:
            return 0
    else:
        print(f"Failed to fetch data. Status code: {pr_response.status_code}")
        time.sleep(10)
        return extract_last_page_number(prs_url, pr_params)


def update_data(old_label, java_repos):
    new_label = []
    new_label.extend(old_label)
    for java_repo in java_repos:
        if java_repo in old_label:
            continue
        else:
            new_label.append(java_repo)
    return new_label


# Example usage
def main():
    while True:
        java_repos = get_java_repos_with_closed_prs(PR_NUMBER)
        # old_label = []
        if os.path.exists(JSON_PATH):
            old_data = read_json(JSON_PATH)
            new_label = update_data(old_data, java_repos)
        else:
            new_label = update_data([], java_repos)
        write_json(new_label, JSON_PATH)


if __name__ == "__main__":
    main()
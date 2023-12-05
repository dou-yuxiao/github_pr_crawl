import requests
import json
import time



def get_pull_requests(owner, repo, token, state='closed'):
    print("enter get_pull_requests")
    prs = []
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state={state}"
    while url:
        response = requests.get(url, headers={'Authorization': f'token {token}'})
        if response.status_code == 200:
            prs.extend(response.json())
            url = response.links.get('next', {}).get('url')
            print(url)
        else:
            # if response.status_code == 503:
            #     print(f"Failed to fetch data. Status code: {response.status_code}")
            #     continue
            
            print(f"Failed to fetch data. Status code: {response.status_code}, url: {url}")
            time.sleep(20)
            continue
    return prs

def get_review_comments(review_comments_api, token):
    comments = []
    # url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/comments"
    url=review_comments_api
    response = requests.get(url, headers={'Authorization': f'token {token}'})
    if response.status_code == 200:
        comments.extend(response.json())
        return comments
    else:
        print(f"Failed to fetch review comments for PR {url}")
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return get_review_comments(url, token)


def get_pr_commits(pr_commits_api, token):
    commits = []
    url = pr_commits_api
    # url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/commits"
    response = requests.get(url, headers={'Authorization': f'token {token}'})
    if response.status_code == 200:
        commits.extend(response.json())
        return commits
    else:
        print(f"Failed to fetch pr commits for PR {url}")
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return get_pr_commits(url, token)




def download_file_after(access_token, owner, repo, sha, file_path):
    download_url = f'https://raw.githubusercontent.com/{owner}/{repo}/{sha}/{file_path}'
    headers = {
        "Authorization": f"Bearer {access_token}",  # Replace with your access token
    }
    response = requests.get(download_url, headers=headers)
    if response.status_code == 200:
        content = response.text
        return content
    else:
        if response.status_code == 503:
            print(f"Failed to fetch data. Status code: {response.status_code}")
            return download_file_after(access_token, download_url)
        else:
            print(f"Failed to fetch data. Status code: {response.status_code}")
            time.sleep(50)
            return download_file_after(access_token, download_url)



def get_commit_changes(url, file_path, pr):
    # url = f'https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}'
    # print(f"commitsha url: {url}")

    headers = {
        'Authorization': 'Bearer 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',  # Replace with your access token
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        # import pdb
        # pdb.set_trace()
        if 'files' in data:
            for file_dict in data['files']:
                if file_dict["filename"]== file_path:
                    return file_dict["raw_url"]
            raise Exception("Failed to find file in commit")
        else:
            # print("No file information found for this commit.")
            raise Exception("No file information found for this commit.")
            # return []
    else:
        if response.status_code == 200:
            print(f"Failed to fetch data. Status code: {response.status_code}")
            return get_commit_changes(url, file_path, pr)
        elif response.status_code == 404:
            print(f"Failed to fetch data. Status code: {response.status_code}")
            # return "404"
            raise Exception("404 ERROR")
        else:
            print(f"Failed to fetch data. Status code: {response.status_code}")
            time.sleep(60)
            return get_commit_changes(url, file_path, pr)
        


def parse_diff(diff):
    lines = diff.split('\n')
    changes = []
    old_line_num = 0
    new_line_num = 0
    buffer=[]
    buffer_index=0
    for line in lines:
        if line.startswith('@@'):
            # Parse the line numbers from the hunk header
            parts = line.split(' ')
            old_info = parts[1].split(',')[0]  # -x,y
            new_info = parts[2].split(',')[0]  # +a,b
            old_line_num = int(old_info[1:])  # Starting line number in old file
            new_line_num = int(new_info[1:])  # Starting line number in new file
        elif line.startswith('-'):
            buffer_index = 1
            buffer.append({'type': 'delete', 'old_line': old_line_num, 'new_line': new_line_num, 'text': line[1:]})
            # changes.append({'type': 'delete', 'old_line': old_line_num, 'new_line': new_line_num, 'text': line[1:]})
            old_line_num += 1
        elif line.startswith('+'):
            if buffer_index == 1 and len(buffer) > 0:
                temp_ele = buffer.pop(0)
                temp_ele.update({'new_line': new_line_num})
                changes.append(temp_ele)
                temp_old_num = temp_ele['old_line']
                changes.append({'type': 'add', 'old_line': temp_old_num, 'new_line': new_line_num, 'text': line[1:]})
            else:
                changes.append({'type': 'add', 'old_line': old_line_num, 'new_line': new_line_num, 'text': line[1:]})
            new_line_num += 1
        elif line.startswith(' '):
            if buffer_index == 1:
                buffer_index==0
                if len(buffer) > 0:
                    for temp_e in buffer:
                        temp_e.update({'new_line': new_line_num})
                        changes.append(temp_e)
                    buffer.clear()
            old_line_num += 1
            new_line_num += 1

    return changes



def pair_changes(changes):
    paired_changes = []
    for change in changes:
        if change['type'] == 'delete':
            # Check if the next change is an add at the same position
            next_index = changes.index(change) + 1
            if next_index < len(changes) and changes[next_index]['type'] == 'add' and changes[next_index]['new_line'] == change['new_line']:
                paired_changes.append((change, changes[next_index]))
            else:
                paired_changes.append((change, None))
        elif change['type'] == 'add':
            # Check if the previous change was a delete at the same position
            prev_index = changes.index(change) - 1
            if prev_index >= 0 and changes[prev_index]['type'] == 'delete' and changes[prev_index]['new_line'] == change['new_line']:
                continue  # Already paired
            else:
                paired_changes.append((None, change))

    return paired_changes





def main():
#     owner = 'apache'  # Replace with the repository owner
#     repo = 'eventmesh'  # Replace with the repository name
#     token = 'your_github_token'  # Replace with your GitHub token
    html_url_list = [
        "https://github.com/apache/eventmesh"
    ]
    token = "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"
    for html_url in html_url_list:
        owner, repo = html_url.split('/')[-2:]
        pull_requests = get_pull_requests(owner, repo, token)
        for pr in pull_requests:
            pr_commits_api = pr["_links"]["commits"]["href"]
            review_comments_api=pr["_links"]["review_comments"]["href"]
            # comments = get_review_comments(owner, repo, pr['number'], token)
            comments = get_review_comments(review_comments_api, token)
            pr_commits = get_pr_commits(pr_commits_api, token)
            java_comments = [c for c in comments if c['path'].endswith('.java')]
            for comment in java_comments:
                commit_id = comment["original_commit_id"]
                file_path = comment["path"]
                diff_hunk = comment["diff_hunk"]
                print(f"PR #{pr['number']} - File: {comment['path']}")
                
                for pr_commit in pr_commits:
                    if pr_commit["sha"] == commit_id:
                        # download_url = get_commit_changes(pr_commit["url"], file_path, pr)
                        file_content = download_file_after(token, owner, repo, commit_id, file_path)
                        print(f"Comment: {comment['body']}")
                        print(f"diff_hunk: {diff_hunk}")
                        print(f"file_content: {file_content}")



if __name__ == "__main__":
    main()
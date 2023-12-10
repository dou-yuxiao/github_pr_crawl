import requests
import json
import time
import regex as re
from datetime import datetime


def get_pull_requests(owner, repo, token, state='closed'):
    print("enter get_pull_requests")
    prs = []

    headers = {
        'Authorization': 'Bearer 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',  # Replace with your access token
    }

    url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state={state}"

    pagenum=0

    while url:

        if pagenum>=1:
            break

        # response = requests.get(url, headers={'Authorization': f'token {token}'})
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            prs.extend(response.json())
            url = response.links.get('next', {}).get('url')
            print(url)

            pagenum+=1

        else:
            # if response.status_code == 503:
            #     print(f"Failed to fetch data. Status code: {response.status_code}")
            #     continue
            
            print(f"Failed to fetch data. Status code: {response.status_code}, url: {url}")
            time.sleep(20)
            continue
    return prs

def get_review_comments(review_comments_api, token):
    headers = {
        'Authorization': 'Bearer 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',  # Replace with your access token
    }
    comments = []
    # url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/comments"
    url=review_comments_api
    # response = requests.get(url, headers={'Authorization': f'token {token}'})
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        comments.extend(response.json())
        return comments
    else:
        print(f"Failed to fetch review comments for PR {url}")
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return get_review_comments(url, token)


def get_pr_commits(pr_commits_api, token):
    headers = {
        'Authorization': 'Bearer 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',  # Replace with your access token
    }
    commits = []
    url = pr_commits_api
    # url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/commits"
    # response = requests.get(url, headers={'Authorization': f'token {token}'})
    response = requests.get(url, headers=headers)
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

def comments_filter(comments, pr_user_id, pr):
    java_comments = [c for c in comments if c['path'].endswith('.java')]
    # java_comments = comments
    comments_dict = {}
    
    for comment in java_comments:
        # comment_datetime = datetime.strptime(comment["created_at"], "%Y-%m-%dT%H:%M:%SZ")

        ##记得把这个改回来取消comment
        # if comment["user"]["id"] == pr_user_id:
        #     continue
        if "in_reply_to_id" not in comment:
            # tp_list = []
            # tp_list.append(comment)
            comments_dict.update({comment["id"]: [comment]})
        else:
            if comment["in_reply_to_id"] in comments_dict:
                temp = comments_dict[comment["in_reply_to_id"]]
                temp.append(comment)
                comments_dict.update({comment["in_reply_to_id"]: temp})
            else:
                raise Exception("reply comment but failed to find the comment it replied to")


    # if pr['number']==4594:
    #     print("Check!!")
    # java_comments = [c for c in comments if c['path'].endswith('.java')]
    return comments_dict


def method_line_number_check(submit_method_declarations_iter, file_content):
    submit_method_with_linenum_iter = []
    for submit_i in submit_method_declarations_iter:
        method_code = submit_i.group(0)
        start_line_num=file_content.count("\n", 0, submit_i.start()+1)+1
        end_line_num=file_content.count("\n", 0, submit_i.end())+1
        submit_method_with_linenum_iter.append([method_code, start_line_num, end_line_num])
    return submit_method_with_linenum_iter

def main():
#     owner = 'apache'  # Replace with the repository owner
#     repo = 'eventmesh'  # Replace with the repository name
#     token = 'your_github_token'  # Replace with your GitHub token
    html_url_list = [
        "https://github.com/dou-yuxiao/github_pr_crawl"
        # "https://github.com/apache/eventmesh"
    ]
    token = "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"
    


    method_pattern = r"([ \t]*(?:@[\w\(\)\{\}\@=\"\,\s\/\\]+\s*)*(?:(?:public|private|protected|static|final|native|synchronized|abstract|transient)+\s+)+[@=$_\w<>\[\]\,\s]*\s*\([^)]*\)\s*(?:throws\s+[$_\w<>\[\]\,\s]*\s*)*({(?:[^{}]++|(?2))*}))"



    new_label = []
    for html_url in html_url_list:
        owner, repo = html_url.split('/')[-2:]
        pull_requests = get_pull_requests(owner, repo, token)
        pull_requests = get_pull_requests(owner, repo, token, "open")
        for pr in pull_requests:
            pr_commits_api = pr["_links"]["commits"]["href"]
            review_comments_api=pr["_links"]["review_comments"]["href"]
            pr_user_id = pr["user"]["id"]
            # comments = get_review_comments(owner, repo, pr['number'], token)
            comments = get_review_comments(review_comments_api, token)
            pr_commits = get_pr_commits(pr_commits_api, token)
            # if not pr['number']==4594:
            #     continue
            comments_dict = comments_filter(comments, pr_user_id, pr)

            ###Check
            for first_id, comms in comments_dict.items():
                first_comment_commit_id = comms[0]["original_commit_id"]
                first_comment_file_path = comms[0]["path"]
                first_comment_diff_hunk = comms[0]["diff_hunk"]
                for comm in comms:
                    if comm["original_commit_id"]!=first_comment_commit_id or comm["path"]!=first_comment_file_path or comm["diff_hunk"]!=first_comment_diff_hunk:
                        print(f"first_commrnt_commit_id: {first_comment_commit_id}")
                        print(f"first_commrnt_file_path: {first_comment_file_path}")
                        print(f"first_comment_diff_hunk: {first_comment_diff_hunk}")
                        print(f"comm_commit_id: {comm['original_commit_id']}")
                        print(f"comm_file_path: {comm['path']}")
                        print(f"comm_diff_hunk: {comm['diff_hunk']}")
                        print(f"pr number: {pr['number']}")
                        print(f"first comment url: {comms[0]['url']}")
                        raise Exception("Inconsistant in one review comment structure")


            for first_id, comms in comments_dict.items():
                commit_id = comms[0]["original_commit_id"]
                file_path = comms[0]["path"]
                diff_hunk = comms[0]["diff_hunk"]
                file_content = download_file_after(token, owner, repo, commit_id, file_path)
                submit_method_declarations_iter = re.finditer(method_pattern, file_content)
                submit_method_with_linenum_iter = method_line_number_check(submit_method_declarations_iter, file_content)
                changes = parse_diff(diff_hunk)
                paired_changes = pair_changes(changes)
                # submit_method_with_linenum_iter = []
                # for submit_i in submit_method_declarations_iter:
                #     method_code = submit_i.group(0)
                #     start_line_num=file_content.count("\n", 0, submit_i.start()+1)+1
                #     end_line_num=file_content.count("\n", 0, submit_i.end())+1
                #     submit_method_with_linenum_iter.append([method_code, start_line_num, end_line_num])
                if len(paired_changes)>0 and len(submit_method_with_linenum_iter)>0:
                    if paired_changes[-1][0] and paired_changes[-1][1]:
                        temp_list = []
                        for match_pat in submit_method_with_linenum_iter:
                            if paired_changes[-1][1]['new_line']<=match_pat[2] and paired_changes[-1][1]['new_line']>=match_pat[1] and paired_changes[-1][1]['text'] in match_pat[0]:
                                temp_list.append(match_pat)
                        if len(temp_list)==1:
                            print(f"Code Method:\n{temp_list[0]}")
                            comments_list = [comm['body'] for comm in comms]
                            print(f"Review Comment:\n{comments_list}")
                            new_label.append([temp_list[0], comments_list])
                        elif len(temp_list)==0:
                            continue
                        else:
                            raise Exception("Found multiple method declarations in one commit")
                    elif (not paired_changes[-1][0]) and paired_changes[-1][1]:
                        temp_list = []
                        for match_pat in submit_method_with_linenum_iter:
                            if paired_changes[-1][1]['new_line']<=match_pat[2] and paired_changes[-1][1]['new_line']>=match_pat[1] and paired_changes[-1][1]['text'] in match_pat[0]:
                                temp_list.append(match_pat)
                        if len(temp_list)==1:
                            print(f"Code Method:\n{temp_list[0]}")
                            comments_list = [comm['body'] for comm in comms]
                            print(f"Review Comment:\n{comments_list}")
                            new_label.append([temp_list[0], comments_list])
                        elif len(temp_list)==0:
                            continue
                        else:
                            raise Exception("Found multiple method declarations in one commit")
                    elif paired_changes[-1][0] and (not paired_changes[-1][1]):
                        continue
                        # temp_list = []
                        # for match_pat in submit_method_with_linenum_iter:
                        #     if paired_changes[-1][0]['new_line']<=match_pat[2] and paired_changes[-1][0]['new_line']>=match_pat[1]:
                        #         temp_list.append(match_pat)
                        # if len(temp_list)==1:
                        #     print(f"Code Method:\n{temp_list[0]}")
                        #     comments_list = [comm['body'] for comm in comms]
                        #     print(f"Review Comment:\n{comments_list}")
                        #     new_label.append([temp_list[0], comments_list])
                        # else:
                        #     raise Exception("Found multiple method declarations in one commit")
                    else:
                        raise Exception("Error! paired_changes last ele paired_changes[-1][0] and paired_changes[-1][1] both none")


    print(f"all end")


            # for comment in java_comments:
            #     commit_id = comment["original_commit_id"]
            #     file_path = comment["path"]
            #     diff_hunk = comment["diff_hunk"]
            #     print(f"PR #{pr['number']} - File: {comment['path']}")
                
            #     # for pr_commit in pr_commits:
            #     #     if pr_commit["sha"] == commit_id:
            #             # download_url = get_commit_changes(pr_commit["url"], file_path, pr)
            #     file_content = download_file_after(token, owner, repo, commit_id, file_path)
            #     print(f"Comment: {comment['body']}")
            #     print(f"diff_hunk: {diff_hunk}")
            #     print(f"file_content: {file_content}")
            #     submit_method_declarations_iter = re.finditer(method_pattern, file_content)
            #     submit_method_with_linenum_iter = []
            #     for submit_i in submit_method_declarations_iter:
            #         method_code = submit_i.group(0)
            #         start_line_num=file_content.count("\n", 0, submit_i.start()+1)+1
            #         end_line_num=file_content.count("\n", 0, submit_i.end())+1
            #         submit_method_with_linenum_iter.append([method_code, start_line_num, end_line_num])

            #     changes = parse_diff(diff_hunk)
            #     paired_changes = pair_changes(changes)
            #     print("Finish One")
            #     # temp_code_comment = []
            #     if len(paired_changes)>0 and len(submit_method_with_linenum_iter)>0:
            #         if paired_changes[-1][0] and paired_changes[-1][1]:
            #             temp_list = []
            #             for match_pat in submit_method_with_linenum_iter:
            #                 if paired_changes[-1][1]['new_line']<=match_pat[2] and paired_changes[-1][1]['new_line']>=match_pat[1] and paired_changes[-1][1]['text'] in match_pat[0]:
            #                     temp_list.append(match_pat)
            #             if len(temp_list)==1:
            #                 print(f"Code Method:\n{temp_list[0]}")
            #                 print(f"Review Comment:\n{temp_list[0]}")
            #                 new_label.append([temp_list[0], comment['body']])
            #             else:
            #                 raise Exception("Found multiple method declarations in one commit")






if __name__ == "__main__":
    main()
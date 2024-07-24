import argparse
import requests
import os
from dotenv import load_dotenv

def list_repos(search_string: str):
    """
    function to add specific repos matching a string in repo names
    :return:
    """
    organization = os.getenv('GITHUB_REPOSITORY_OWNER')
    # GitHub endpoint for listing repos under an organization
    repo_url = f"https://api.github.com/orgs/{organization}/repos"

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {os.getenv('GH_TOKEN')}",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    # Define pagination parameters
    per_page = 100  # Number of records per page
    page = 1        # Initial page number
    list_of_repo_names = []

    while True:
        # Add pagination parameters to the URL
        params = {'per_page': per_page, 'page': page}
        response = requests.get(repo_url, headers=headers, params=params)
        response_json = response.json() ## Github repo details

        # Checking the API status code
        if response.status_code == 200:
            print(f"API request successful on {repo_url}")
            # print(response_json)
        else:
            print(f"API request failed with status code {response.status_code}:")
            # print(response_json)
            break

        # Get the repo names from the list of dictionaries and add to another list
        for repo in response_json:
            list_of_repo_names.append(repo['full_name'])

        page += 1  # Move to the next page

        # Break the loop if no more pages
        if len(response_json) < per_page:
            break

    for repo in list_of_repo_names:
        print(f" repo name: {repo} ")

    print(f"Total Number of repos in {organization} Org is {len(list_of_repo_names)}")

    # Finding repos starting with search string
    matching_repos = [repo for repo in list_of_repo_names if repo.startswith(f'{organization}/{search_string}')]
    print(f"Matching repos {search_string} are: {matching_repos}")
    return  matching_repos



def main():
    """main function to test the code"""
    load_dotenv()
    parser = argparse.ArgumentParser(description="Add specific repos matching a string in repo names to a github teams")
    parser.add_argument("--search_string", required=True, type=str, help="github repo name search string")
    args = parser.parse_args()

    search_string = args.search_string


    # function call
    list_repos(search_string= search_string)


if __name__ == "__main__":
    main()
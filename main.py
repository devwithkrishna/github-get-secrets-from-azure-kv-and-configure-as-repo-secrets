import os, argparse
from dotenv import load_dotenv
from resource_graph_query import run_azure_rg_query_to_get_keyvault_rg_name,run_azure_rg_query_to_get_tenant_id,run_azure_rg_query
from get_repo_public_key import get_repository_public_key, get_repository_public_key_id
from encrypt_using_libnacl import encrypt
from create_repo_secrets import create_or_update_repository_secret_github
from list_repos import list_repos
from kv_values import get_secret_values_from_kv

def trigger_main(repo_search_string: str ,keyvault_name:str):
	"""
	Running code to create secrerts in a repo
	:return:
	"""
	organization = os.getenv('GITHUB_REPOSITORY_OWNER')
	print(f'GitHub organization name is : {organization}')
	matching_repos = list_repos(search_string= repo_search_string)
	matching_repos = ['github-actions']
	kv_secret_values = get_secret_values_from_kv(keyvault_name=keyvault_name)
	for repository in matching_repos:
		print(f'Proceeding to configure github secrets for {repository}')
		public_key = get_repository_public_key(organization=organization, repository_name=repository)
		public_key_id = get_repository_public_key_id(organization=organization, repository_name=repository)

		for key, value in kv_secret_values.items():
			encrypted_secret = encrypt(public_key=public_key, secret_value=value)
			create_or_update_repository_secret_github(repo_name=repository, secret_name=key, secret_value=encrypted_secret, public_key_id=public_key_id)








def main():
	""" run code """
	parser = argparse.ArgumentParser("Parse arguments")
	parser.add_argument("--repo_search_string", type=str, required=True, help="String to search github repo name (begining of repo name)")
	parser.add_argument("--keyvault_name", type=str, required=True, help="Azure keyvault name to pull secrets from")

	args = parser.parse_args()

	keyvault_name = args.keyvault_name
	repo_search_string = args.repo_search_string
	load_dotenv()

	trigger_main(repo_search_string=repo_search_string, keyvault_name=keyvault_name)


if __name__ == '__main__':
    main()
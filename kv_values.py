import argparse
import os
import requests
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.mgmt.keyvault.models import VaultAccessPolicyParameters, AccessPolicyEntry, Permissions, SecretPermissions
from  resource_graph_query import run_azure_rg_query_to_get_keyvault_rg_name, run_azure_rg_query_to_get_tenant_id

def get_keyvault_rg(keyvault_name:str):
	"""
	get kv rg name from resource graph query
	:param keyvault_name:
	:return:
	"""
	kv_detals = run_azure_rg_query_to_get_keyvault_rg_name()
	for kv in kv_detals:
		if kv['name'] == keyvault_name:
			rg = kv['resourceGroup']
			print(f"KeyVault resource group is {rg}")
	return rg

def get_keyvault_subscription_id(keyvault_name:str):
	"""
	get kv sub id from resource graph query
	:param keyvault_name:
	:return:
	"""
	kv_detals = run_azure_rg_query_to_get_keyvault_rg_name()
	for kv in kv_detals:
		if kv['name'] == keyvault_name:
			subscription_id = kv['subscriptionId']
			print(f"KeyVault subscription id is {subscription_id}")
	return subscription_id

def get_obj_id_of_authenticated_user():
	"""
	get object id of authenticated user / app
	:return:
	"""
	load_dotenv()
	# Get the DefaultAzureCredential token
	credential = DefaultAzureCredential()
	token = credential.get_token("https://graph.microsoft.com/.default")

	# Extract the access token
	access_token = token.token
	client_id = os.getenv('AZURE_CLIENT_ID')
	# Define the Graph API endpoint to get the authenticated user's information
	url_sp = f"https://graph.microsoft.com/v1.0/servicePrincipals?$filter=appId eq '{client_id}'"

	# Set the headers, including the Authorization header with the access token
	headers = {
		"Authorization": f"Bearer {access_token}"
	}

	# Make the request to the Graph API
	response = requests.get(url_sp, headers=headers)

	# Check if the request was successful
	if response.status_code == 200:
		user_info = response.json()
		object_id = user_info.get("value")[0]['id']
		print(f"Object ID: {object_id}")
	else:
		print(f"Failed to retrieve user information: {response.status_code} {response.text}")
	return object_id

def add_to_access_policies_in_kv(keyvault_name: str):
	"""
	add the user / app into keyvault with secret get list set permissions
	:param keyvault_name:
	:return:
	"""
	load_dotenv()
	object_id = get_obj_id_of_authenticated_user()
	credential = DefaultAzureCredential()
	tenant_id = run_azure_rg_query_to_get_tenant_id()
	key_vault_url = keyvault_url_from_kv_name(keyvault_name=keyvault_name)
	rg = get_keyvault_rg(keyvault_name=keyvault_name)
	subscription_id = get_keyvault_subscription_id(keyvault_name=keyvault_name)
	client = KeyVaultManagementClient(vault_url=key_vault_url,subscription_id=subscription_id, credential=credential)

	# key vault access policy - secret get list permission
	permissions = Permissions(secrets=[SecretPermissions.get, SecretPermissions.list, SecretPermissions.set])

	# Create an access policy entry
	access_policy_entry = AccessPolicyEntry(
		tenant_id=tenant_id,
		object_id=object_id,
		permissions=permissions
	)

	# Define the access policy parameters
	parameters = VaultAccessPolicyParameters(
		properties={'accessPolicies': [access_policy_entry]}
	)

	# Add the access policy
	result = client.vaults.update_access_policy(vault_name=keyvault_name, operation_kind="add", resource_group_name=rg , parameters=parameters)
	print(f'Added {object_id} to {keyvault_name} Access policy')


def keyvault_url_from_kv_name(keyvault_name: str):
    """
    creating keyvault url from keyvault name
    :return:
    """
    keyvault_url = f"https://{keyvault_name.lower ()}.vault.azure.net"
    print (f"Key vault url is : , {keyvault_url}")
    return keyvault_url

def get_secret_values_from_kv(keyvault_name: str):
	"""
	fetch secret values from key vault
	github secret names wont allow -, need to use _
	:param keyvault_name:
	:return:
	"""
	kv_secret_values = {}
	credential = DefaultAzureCredential()
	kv_url = keyvault_url_from_kv_name(keyvault_name)
	add_to_access_policies_in_kv(keyvault_name=keyvault_name)
	client = SecretClient(vault_url=kv_url, credential=credential)
	secret_names = ["ARM-CLIENT-ID", "ARM-CLIENT-SECRET"]
	for secret in secret_names:
		print(f"Operation being performed is : Get on {keyvault_name}")
		get_secret = client.get_secret(secret)
		# print(f"secret value for {secret} is : {get_secret.value}")
		kv_secret_values[secret.replace('-','_')] = get_secret.value
	subscription_id = get_keyvault_subscription_id(keyvault_name=keyvault_name)
	tenant_id = run_azure_rg_query_to_get_tenant_id()
	kv_secret_values['ARM_TENANT_ID'] = tenant_id
	kv_secret_values['ARM_SUBSCRIPTION_ID'] = subscription_id

	return kv_secret_values


def main():
	"""run code here"""
	load_dotenv()
	# Instantiate argparser
	parser = argparse.ArgumentParser(description='argumets for the function')
	parser.add_argument('--keyvault_name', type=str, required=True,
						help='Keyvault to authenticate and modify the secrets in it')

	args = parser.parse_args()

	keyvault_name = args.keyvault_name

	# obj_id = get_obj_id_of_authenticated_user()
	get_secret_values_from_kv(keyvault_name=keyvault_name)
	# add_to_access_policies_in_kv(keyvault_name=keyvault_name)
	# get_keyvault_rg(keyvault_name=keyvault_name)
if __name__ == "__main__":
	main()
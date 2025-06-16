import requests
from requests.auth import HTTPBasicAuth

url = "https://api.company-information.service.gov.uk/company/"
API_KEY = "Enter your API key"


test_crn = "SC702703"

my_test_url = f"{url}{test_crn}"

response = requests.get(my_test_url, auth= HTTPBasicAuth(API_KEY, ""))

print(response.json())

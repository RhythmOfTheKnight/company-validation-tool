import requests
from requests.auth import HTTPBasicAuth

url = "https://api.company-information.service.gov.uk/company/"
API_KEY = 


test_crn = "this is not a valid CRN"

my_test_url = f"{url}{test_crn}"

response = requests.get(my_test_url, auth= HTTPBasicAuth(API_KEY, ""))

print(response.status_code)
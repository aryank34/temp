import requests

# The URL to send the POST request to
url = "http://localhost:5000/timesheet"  # Replace with your actual URL

# The data to send in the body of the POST request
data = {
    "uid": "65c408582b6c3e4c3208296d"
}

# Send the POST request
response = requests.post(url, json=data)

# Print the response
print("Status Code:", response.status_code)
print("Response Body:", response.json())
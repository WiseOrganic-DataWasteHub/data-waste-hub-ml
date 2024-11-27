import requests

url = "http://34.101.242.121:3000/api/v1/waste-records/month/11/year/2024"

headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwicm9sZSI6ImFkbWluIiwiaWF0IjoxNzMyNjM0NDE2LCJleHAiOjE3MzI2NDE2MTZ9.45vobcEOdEkYzWHxpKaTAS-DwX30ugveFQz9C7N1URc",
    "Accept": "application/json"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    print("Koneksi berhasil! Data yang diterima:")
    print(response.json()) 
else:
    print(f"Error {response.status_code}: {response.text}")

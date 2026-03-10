import json

import requests

API_URL = "http://localhost:8000/api/offline/schema/descriptions/generate"


def test_generate_descriptions_random():
    payload = {
        "database_name": "AdventureWorks",  # Assuming this exists or using settings
        "host": "localhost",
        "limit": 2,
    }
    print(f"Testing random generation (limit=2) for {payload['database_name']}...")
    try:
        response = requests.post(API_URL, json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")


def test_generate_descriptions_specific():
    payload = {
        "database_name": "AdventureWorks",
        "host": "localhost",
        "table_names": ["Customer", "SalesOrderHeader"],
    }
    print(f"Testing specific table generation for {payload['table_names']}...")
    try:
        response = requests.post(API_URL, json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # Wait for API to be up if needed, but here we assume it's running via docker
    test_generate_descriptions_random()
    print("-" * 40)
    test_generate_descriptions_specific()

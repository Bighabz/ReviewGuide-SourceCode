#!/usr/bin/env python3
"""Debug Tokyo city code lookup"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import os
from amadeus import Client

client = Client(
    client_id=os.getenv('AMADEUS_API_KEY'),
    client_secret=os.getenv('AMADEUS_API_SECRET')
)

print("Testing Amadeus Location API for Tokyo:")
print("=" * 80)

try:
    response = client.reference_data.locations.get(
        keyword='Tokyo',
        subType=['CITY', 'AIRPORT']
    )

    if hasattr(response, 'data'):
        print(f"Found {len(response.data)} results:")
        for i, location in enumerate(response.data[:5]):  # Show first 5
            print(f"\n{i+1}. {location}")
    else:
        print("No data in response")

except Exception as e:
    print(f"Error: {e}")
    if hasattr(e, 'response'):
        print(f"Status: {e.response.status_code}")
        print(f"Body: {e.response.body}")

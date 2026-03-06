#!/usr/bin/env python3
from scripts.asc_client import ASCClient
import sys

def main():
    client = ASCClient.from_env()
    sub_id = "d4eb4672-9920-413e-9c61-f6ca89bd2245"
    
    print(f"Targeting specific populated submission: {sub_id}")
    
    print("Canceling the draft...")
    try:
        res = client.request("PATCH", f"/reviewSubmissions/{sub_id}", payload={
            "data": {
                "type": "reviewSubmissions",
                "id": sub_id,
                "attributes": {
                    "canceled": True
                }
            }
        })
        print(f"Update response: {res.get('data', {}).get('attributes', {}).get('state')}")
        print("Successfully canceled the draft.")
    except Exception as e:
        print(f"Failed to cancel: {e}")

if __name__ == "__main__":
    main()

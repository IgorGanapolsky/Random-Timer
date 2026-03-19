import os
import sys
import scripts.asc_add_tester as asc

def check_tester_state():
    t = asc.build_token()
    email = "iganapolsky@gmail.com"
    
    print(f"\n--- DEEP TESTER CHECK: {email} ---")
    
    # Find the tester
    data = asc.api(t, 'GET', '/betaTesters', params={'filter[email]': email, 'include': 'apps,betaGroups'})
    if not data.get('data'):
        print(f"Tester {email} not found at all!")
        return

    tester = data['data'][0]
    tester_id = tester['id']
    
    print(f"Tester ID: {tester_id}")
    
    # Check groups for this tester
    groups = tester['relationships']['betaGroups']['data']
    print(f"Assigned to {len(groups)} groups.")
    
    # Check Build distribution specifically for this tester
    # We have to check if build 194 is accessible to them
    builds = asc.api(t, 'GET', f"/betaTesters/{tester_id}/builds", params={'limit': 10})
    versions = [b['attributes']['version'] for b in builds.get('data', [])]
    print(f"Builds accessible to this tester: {versions}")
    
    if '194' not in versions:
        print("🚨 Build 194 is NOT accessible to this tester despite being in the group!")
    else:
        print("✅ Build 194 IS accessible to this tester via API.")

    # Check if there's an invite pending or something
    # BetaTester attributes include invitationState? No, that's in relationships
    
if __name__ == "__main__":
    check_tester_state()

import os
import sys
import scripts.asc_add_tester as asc

def diagnose_testers():
    t = asc.build_token()
    bundle_id = "com.igorganapolsky.randomtimer"
    app_id = asc.find_app(t, bundle_id)
    
    print(f"\n--- APP: {bundle_id} (ID: {app_id}) ---")
    
    # Check groups
    groups = asc.api(t, 'GET', "/betaGroups", params={'filter[app]': app_id})
    for g in groups.get('data', []):
        g_name = g['attributes']['name']
        g_id = g['id']
        is_internal = g['attributes']['isInternalGroup']
        
        print(f"\nGroup: {g_name} (ID: {g_id}, Internal: {is_internal})")
        
        # Check builds in group
        builds = asc.api(t, 'GET', f"/betaGroups/{g_id}/builds", params={'limit': 5})
        print(f"  Latest builds in group: {[b['attributes']['version'] for b in builds.get('data', [])]}")
        
        # Check testers in group
        testers = asc.api(t, 'GET', f"/betaGroups/{g_id}/betaTesters")
        tester_emails = [t['attributes']['email'] for t in testers.get('data', [])]
        print(f"  Testers in group: {tester_emails}")

    # Check Build 194 specifically for compliance
    builds = asc.api(t, 'GET', '/builds', params={
        'filter[version]': '194', 
        'filter[app]': app_id,
        'include': 'buildBetaDetail'
    })
    
    for b in builds.get('data', []):
        bd_id = b['relationships']['buildBetaDetail']['data']['id']
        bd = asc.api(t, 'GET', f"/buildBetaDetails/{bd_id}")
        attr = bd['data']['attributes']
        print(f"\n--- BUILD 194 COMPLIANCE ---")
        print(f"External State: {attr['externalBuildState']}")
        print(f"Internal State: {attr['internalBuildState']}")
        # Check if it needs export compliance
        # states: MISSING_EXPORT_COMPLIANCE, READY_FOR_BETA_SUBMISSION, IN_BETA_TESTING, etc.

if __name__ == "__main__":
    diagnose_testers()

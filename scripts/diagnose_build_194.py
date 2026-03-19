import os
import sys
import scripts.asc_add_tester as asc

def diagnose():
    t = asc.build_token()
    print('\n--- BUILD 194 DETAILS ---')
    # bundle_id = "com.iganapolsky.randomtimer"  <- Corrected from GEMINI.md
    bundle_id = "com.igorganapolsky.randomtimer"
    
    app_id = asc.find_app(t, bundle_id)
    print(f"App ID: {app_id}")

    builds = asc.api(t, 'GET', '/builds', params={
        'filter[version]': '194', 
        'filter[app]': app_id,
        'include': 'buildBetaDetail'
    })
    
    data = builds.get('data', [])
    if not data:
        print("Build 194 not found via API")
        return

    build_id = data[0]['id']
    bd_id = data[0]['relationships']['buildBetaDetail']['data']['id']
    
    print(f"Build: 194 (ID: {build_id})")
    bd = asc.api(t, 'GET', f"/buildBetaDetails/{bd_id}")
    bd_attr = bd['data']['attributes']
    print(f"External Beta State: {bd_attr['externalBuildState']}")
    print(f"Internal Beta State: {bd_attr['internalBuildState']}")
    
    print('\n--- CHECKING BETA GROUPS ---')
    groups = asc.api(t, 'GET', "/betaGroups", params={'filter[app]': app_id})
    for g in groups.get('data', []):
        g_name = g['attributes']['name']
        g_id = g['id']
        is_internal = g['attributes']['isInternalGroup']
        
        # Check if build 194 is in this group
        builds_in_group = asc.api(t, 'GET', f"/betaGroups/{g_id}/builds")
        in_group = any(b['id'] == build_id for b in builds_in_group.get('data', []))
        
        print(f"Group: {g_name} (Internal: {is_internal}) | Build 194 present: {in_group}")
        
        if not in_group and is_internal:
            print(f"Assigning Build 194 to internal group {g_name}...")
            body = {"data": [{"type": "builds", "id": build_id}]}
            try:
                asc.api(t, 'POST', f"/betaGroups/{g_id}/relationships/builds", body=body)
                print(f"✅ Build 194 assigned to {g_name}")
            except Exception as e:
                print(f"Failed to assign: {e}")

if __name__ == "__main__":
    diagnose()

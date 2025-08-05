import sys
import traceback

try:
    print("=== Step 1: Import projects module ===")
    from app.api.v1.endpoints import projects
    print(f"✓ Projects module imported successfully")
    print(f"✓ Projects router type: {type(projects.router)}")
    print(f"✓ Projects router routes count: {len(projects.router.routes)}")
    
    print("\n=== Step 2: Check projects router routes ===")
    for i, route in enumerate(projects.router.routes):
        print(f"  Route {i+1}: {route.methods} {route.path} -> {route.endpoint.__name__}")
    
    print("\n=== Step 3: Import api_router ===")
    from app.api.v1.api import api_router
    print(f"✓ API router imported successfully")
    print(f"✓ API router type: {type(api_router)}")
    print(f"✓ API router routes count: {len(api_router.routes)}")
    
    print("\n=== Step 4: Manual include_router test ===")
    from fastapi import APIRouter
    test_router = APIRouter()
    test_router.include_router(
        projects.router,
        prefix="/test-projects",
        tags=["Test Projects"]
    )
    print(f"✓ Manual include_router successful")
    print(f"✓ Test router routes count: {len(test_router.routes)}")
    
    print("\n=== Step 5: Check if projects is in api_router imports ===")
    import app.api.v1.api as api_module
    print(f"✓ API module imported")
    print(f"✓ Projects in api module: {hasattr(api_module, 'projects')}")
    
    # Check the actual projects import
    from app.api.v1.endpoints import projects as imported_projects
    print(f"✓ Direct projects import successful")
    print(f"✓ Same object? {projects is imported_projects}")
    
    print("\n=== Step 6: Re-check api_router routes ===")
    projects_routes = []
    for route in api_router.routes:
        if hasattr(route, 'prefix') and route.prefix == '/projects':
            projects_routes.append(route)
            print(f"  ✓ Found projects route: {route.prefix}")
            if hasattr(route, 'router'):
                print(f"    Sub-routes: {len(route.router.routes)}")
                for sub_route in route.router.routes:
                    print(f"      - {sub_route.methods} {sub_route.path}")
    
    if not projects_routes:
        print("  ✗ No projects routes found in api_router")
        print("  Available prefixes:")
        for route in api_router.routes:
            if hasattr(route, 'prefix'):
                print(f"    - {route.prefix}")
                
except Exception as e:
    print(f"❌ Error: {e}")
    traceback.print_exc()
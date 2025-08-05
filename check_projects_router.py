import traceback

try:
    print("=== Checking projects.router directly ===")
    from app.api.v1.endpoints import projects
    
    print(f"Projects router type: {type(projects.router)}")
    print(f"Projects router routes: {len(projects.router.routes)}")
    print(f"Projects router is None: {projects.router is None}")
    print(f"Projects router routes is empty: {len(projects.router.routes) == 0}")
    
    if projects.router.routes:
        print("\nProjects router routes:")
        for i, route in enumerate(projects.router.routes):
            print(f"  {i+1}. {route.methods} {route.path} -> {route.endpoint.__name__}")
    else:
        print("\n❌ Projects router has no routes!")
    
    print("\n=== Checking if projects.router can be included ===")
    from fastapi import APIRouter
    test_router = APIRouter()
    
    try:
        test_router.include_router(
            projects.router,
            prefix="/test-projects",
            tags=["Test"]
        )
        print(f"✓ Successfully included projects.router in test router")
        print(f"✓ Test router now has {len(test_router.routes)} routes")
        
        for route in test_router.routes:
            if hasattr(route, 'prefix'):
                print(f"  Test route prefix: {route.prefix}")
                
    except Exception as e:
        print(f"❌ Failed to include projects.router: {e}")
        traceback.print_exc()
    
    print("\n=== Checking projects module attributes ===")
    print(f"Projects module file: {projects.__file__}")
    print(f"Projects module attributes: {dir(projects)}")
    
    # Check if there's a different router attribute
    for attr in dir(projects):
        if 'router' in attr.lower():
            print(f"  Found router-like attribute: {attr} = {getattr(projects, attr)}")
            
except Exception as e:
    print(f"❌ Error: {e}")
    traceback.print_exc()
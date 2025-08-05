import traceback

try:
    print("=== Inspecting API Router Routes ===")
    from app.api.v1.api import api_router
    
    print(f"Total routes: {len(api_router.routes)}")
    
    # Check all routes with their types and attributes
    for i, route in enumerate(api_router.routes):
        print(f"\nRoute {i+1}:")
        print(f"  Type: {type(route)}")
        print(f"  Has prefix: {hasattr(route, 'prefix')}")
        
        if hasattr(route, 'prefix'):
            print(f"  Prefix: '{route.prefix}'")
            if route.prefix == '/projects':
                print(f"  *** FOUND PROJECTS ROUTE! ***")
                print(f"  Router type: {type(route.router) if hasattr(route, 'router') else 'No router attr'}")
                if hasattr(route, 'router'):
                    print(f"  Sub-routes: {len(route.router.routes)}")
                    for j, sub_route in enumerate(route.router.routes):
                        print(f"    Sub-route {j+1}: {sub_route.methods} {sub_route.path}")
        
        if hasattr(route, 'path'):
            print(f"  Path: '{route.path}'")
            if '/projects' in route.path:
                print(f"  *** CONTAINS PROJECTS IN PATH! ***")
        
        if hasattr(route, 'methods'):
            print(f"  Methods: {route.methods}")
        
        # Check for other relevant attributes
        attrs = ['tags', 'name', 'endpoint']
        for attr in attrs:
            if hasattr(route, attr):
                value = getattr(route, attr)
                if 'project' in str(value).lower():
                    print(f"  {attr}: {value} *** CONTAINS PROJECT! ***")
                    
except Exception as e:
    print(f"❌ Error: {e}")
    traceback.print_exc()
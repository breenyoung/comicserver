from fastapi.routing import APIRoute

def get_route_map(app, with_admin_routes: bool = False):
    """
    Generates a dictionary of { "route_name": "/path/{param}" }
    """
    route_map = {}
    for route in app.routes:

        if isinstance(route, APIRoute) and route.name:

            tags = getattr(route, "tags", [])
            if not with_admin_routes and "admin" in tags:
                continue

            # endpoint is guaranteed on APIRoute
            module_name = getattr(route.endpoint, "__module__", None)

            # prefer tags if present, fall back to module name
            if tags:
                prefix = tags[0].replace("-", "_")
                name = route.name.replace("-", "_")
            elif module_name:
                # fallback: use module name as prefix
                prefix = module_name.replace(".", "_")
                name = route.name.replace("-", "_")
            else:
                prefix = "misc"
                name = route.name.replace("-", "_")

            # build nested dict
            if prefix not in route_map:
                route_map[prefix] = {}
            route_map[prefix][name] = route.path

    return route_map
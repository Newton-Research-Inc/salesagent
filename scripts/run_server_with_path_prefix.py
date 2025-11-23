#!/usr/bin/env python3
"""Run the AdCP Sales Agent with HTTP transport and path prefix support for ALB routing."""

import os
import sys


def main():
    """Run the server with configurable port and path prefix support."""
    # Initialize application with startup validation
    try:
        # Add current directory to path for imports
        sys.path.insert(0, ".")
        from src.core.startup import initialize_application

        print("🚀 Initializing AdCP Sales Agent...")
        initialize_application()
        print("✅ Application initialization completed")

    except SystemExit:
        print("❌ Application initialization failed - check logs")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Startup error: {e}")
        sys.exit(1)

    port = int(os.environ.get("ADCP_SALES_PORT", "8080"))
    host = os.environ.get("ADCP_SALES_HOST", "0.0.0.0")

    # Check if we're in production (Docker or Fly.io)
    is_production = bool(os.environ.get("FLY_APP_NAME") or os.environ.get("PRODUCTION"))

    if is_production:
        # In production, bind to all interfaces
        host = "0.0.0.0"

    print(f"Starting AdCP Sales Agent on {host}:{port}")
    print(f"Server endpoint: http://{host}:{port}/")

    # Import the MCP app
    from src.core.main import mcp

    # Get the underlying Starlette app
    from starlette.applications import Starlette
    from starlette.routing import Mount
    from starlette.middleware import Middleware
    from starlette.middleware.base import BaseHTTPMiddleware
    import uvicorn

    # Custom middleware to handle path prefix stripping for tenant routing
    class PathPrefixMiddleware(BaseHTTPMiddleware):
        """
        Middleware to handle ALB path-based routing.
        
        ALB sends: /espn/mcp/health
        We strip: /espn/mcp
        App sees: /health
        
        The tenant is detected from the path prefix and set in request headers.
        """
        
        async def dispatch(self, request, call_next):
            # Extract tenant from path: /espn/mcp/* or /cnn/mcp/* or /nyt/mcp/*
            path = request.url.path
            tenant_id = None
            
            # Check for path pattern: /<tenant>/mcp/*
            if path.startswith("/"):
                parts = path.split("/")
                if len(parts) >= 3 and parts[2] == "mcp":
                    tenant_id = parts[1]  # Extract tenant (espn, cnn, nyt)
                    # Strip the /<tenant>/mcp prefix
                    new_path = "/" + "/".join(parts[3:]) if len(parts) > 3 else "/"
                    
                    # Create new scope with modified path
                    scope = dict(request.scope)
                    scope["path"] = new_path
                    
                    # Add tenant to headers for tenant detection
                    if tenant_id:
                        headers = dict(request.headers)
                        headers["x-tenant-id"] = tenant_id
                        scope["headers"] = [
                            (k.encode() if isinstance(k, str) else k, 
                             v.encode() if isinstance(v, str) else v)
                            for k, v in headers.items()
                        ]
                    
                    # Create new request with modified scope
                    from starlette.requests import Request
                    request = Request(scope, receive=request.receive)
                    
                    print(f"[PathPrefix] Tenant: {tenant_id}, Original: {path}, Rewritten: {new_path}")
            
            response = await call_next(request)
            return response

    # Get FastMCP's underlying ASGI app
    asgi_app = mcp.get_asgi_app()
    
    # Wrap with our path prefix middleware
    app = Starlette(
        routes=[Mount("/", app=asgi_app)],
        middleware=[Middleware(PathPrefixMiddleware)]
    )

    print("✅ Path prefix middleware enabled:")
    print("   - /espn/mcp/* → tenant=espn")
    print("   - /cnn/mcp/* → tenant=cnn")
    print("   - /nyt/mcp/* → tenant=nyt")
    print("")

    # Run with uvicorn
    try:
        uvicorn.run(app, host=host, port=port, log_level="info")
    except KeyboardInterrupt:
        print("\nServer stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"Error running server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


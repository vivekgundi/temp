
# vendor_stubs/bedrock_agentcore_starter_toolkit/operations/gateway/client.py
# Minimal but functional stub for local development.
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
 
# Load .env automatically (safe if file missing)
load_dotenv()
 
def _gen(prefix):
    """Generate short fake ids with a prefix."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"
 
class GatewayClient:
    def __init__(self, region_name=None):
        # prefer explicit env var, fall back to argument, then default
        self.region_name = region_name or os.getenv("AWS_REGION", "us-west-2")
        # keep an in-memory registry so repeated calls behave consistently
        self._registry = {}
 
    # emulate creating an OAuth authorizer and return client_info dict used by scripts
    def create_oauth_authorizer_with_cognito(self, auth_name: str = "default-auth"):
        client_id = _gen("client")
        client_secret = _gen("secret")
        user_pool_id = f"us-west-2_{uuid.uuid4().hex[:8]}"
        domain_prefix = f"{client_id}.auth.{self.region_name}.amazoncognito.com"
        token_endpoint = f"https://{domain_prefix}/oauth2/token"
        auth_endpoint = f"https://{domain_prefix}/oauth2/authorize"
        issuer = f"https://cognito-idp.{self.region_name}.amazonaws.com/{user_pool_id}"
 
        client_info = {
            "client_id": client_id,
            "client_secret": client_secret,
            "user_pool_id": user_pool_id,
            "domain_prefix": domain_prefix,
            "token_endpoint": token_endpoint,
            "authorization_endpoint": auth_endpoint,
            "issuer": issuer,
            "region": self.region_name,
        }
 
        # store for later (optional)
        self._registry["last_client_info"] = client_info
        return {"client_info": client_info}
 
    # emulate creating a gateway; return object with gatewayIdentifier, etc.
    def create_gateway(self, display_name: str = None, **kwargs):
        gateway_id = _gen("gw")
        gateway = {
            "gatewayIdentifier": gateway_id,
            "displayName": display_name or f"gateway-{gateway_id}",
            "createdAt": datetime.utcnow().isoformat() + "Z",
            "region": self.region_name,
        }
        self._registry["gateway"] = gateway
        return {"gatewayIdentifier": gateway_id, "gateway": gateway}
 
    # emulate registering a target for that gateway; return a targetIdentifier
    def create_gateway_target(self, gatewayIdentifier: str = None, targetConfiguration: dict = None, **kwargs):
        # If gatewayIdentifier not provided, attempt to use stored one
        if not gatewayIdentifier:
            gw = self._registry.get("gateway")
            gatewayIdentifier = gw.get("gatewayIdentifier") if gw else None
 
        target_id = _gen("target")
        # create a fake target object to mimic real API response
        target = {
            "targetIdentifier": target_id,
            "gatewayIdentifier": gatewayIdentifier,
            "configuration": targetConfiguration or {},
            "createdAt": datetime.utcnow().isoformat() + "Z",
        }
        # store target
        self._registry.setdefault("targets", []).append(target)
        return {"targetIdentifier": target_id, "target": target}
 
    # helpful: a minimal call method to avoid AttributeError if code expects other methods
    def get_gateway(self, gatewayIdentifier: str):
        gw = self._registry.get("gateway")
        if gw and gw.get("gatewayIdentifier") == gatewayIdentifier:
            return {"gateway": gw}
        return {"gateway": {"gatewayIdentifier": gatewayIdentifier}}
 
    # optional: list targets
    def list_gateway_targets(self, gatewayIdentifier: str = None):
        return {"targets": self._registry.get("targets", [])}

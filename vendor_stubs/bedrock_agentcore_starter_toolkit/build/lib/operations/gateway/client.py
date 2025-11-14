# Minimal stub for operations.gateway.client
import os, uuid
class GatewayClient:
    def __init__(self, region_name=None):
        self.region_name = region_name or os.getenv('AWS_REGION','us-west-2')
    def create_oauth_authorizer_with_cognito(self, auth_name):
        client_id = "fake_client_" + str(uuid.uuid4())[:8]
        client_secret = "fake_secret_" + str(uuid.uuid4())[:12]
        domain_prefix = f"{client_id}.auth.{self.region_name}.amazoncognito.com"
        user_pool_id = f"us-west-2_{uuid.uuid4().hex[:8]}"
        return {"client_info":{
            "client_id": client_id,
            "client_secret": client_secret,
            "user_pool_id": user_pool_id,
            "domain_prefix": domain_prefix,
            "token_endpoint": f"https://{domain_prefix}/oauth2/token",
            "authorization_endpoint": f"https://{domain_prefix}/oauth2/authorize",
            "issuer": f"https://cognito-idp.{self.region_name}.amazonaws.com/{user_pool_id}",
            "region": self.region_name
        }}

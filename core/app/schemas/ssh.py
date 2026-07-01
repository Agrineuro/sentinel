from pydantic import BaseModel


class SSHDiscoveryRequest(BaseModel):
    host: str
    username: str
    password: str
    port: int = 22
    organization_id: str = "org_default"
    site_id: str | None = "site_home"

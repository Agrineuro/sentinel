from pydantic import BaseModel, Field


class SSHDiscoveryRequest(BaseModel):
    host: str
    username: str
    secret: str
    credential_type: str = "ssh_password"
    credential_name: str = "SSH credential"
    display_name: str | None = None
    port: int = Field(default=22, ge=1, le=65535)
    organization_id: str = "org_default"
    site_id: str | None = "site_home"

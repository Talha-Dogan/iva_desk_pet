"""Iva araclarini HTTP (streamable-http) modunda calistirir.

Kendi sunucumuz (Docker'daki iva-server) araclara bu adresten baglanir:
    http://host.docker.internal:8090/mcp

Ayni tools.py araclari kullanilir; tek fark tasima yontemi.
Calistirmak icin: start_iva_tools_http.bat
"""
from mcp.server.transport_security import TransportSecuritySettings

import tools  # araclar tools.py icinde tanimli

if __name__ == "__main__":
    mcp = tools.mcp
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = 8090
    # Docker konteynerinden gelen istekler host.docker.internal adini kullanir;
    # MCP'nin DNS-rebinding korumasi bu adi da kabul etmeli.
    mcp.settings.transport_security = TransportSecuritySettings(
        allowed_hosts=[
            "host.docker.internal",
            "host.docker.internal:8090",
            "localhost",
            "localhost:8090",
            "127.0.0.1",
            "127.0.0.1:8090",
            "192.168.1.7",
            "192.168.1.7:8090",
        ],
        allowed_origins=["*"],
    )
    print("Iva araclari HTTP modunda: http://0.0.0.0:8090/mcp")
    print("Kapatmak icin bu pencereyi kapat.")
    mcp.run(transport="streamable-http")

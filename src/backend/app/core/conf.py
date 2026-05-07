from app.core.auth import encode_token
"""
Create a test token for authentication in the test environment.
"""
token_agente = encode_token({"sub": "3", "scope": "agente"})
headers = {"Authorization": f"Bearer {token_agente}"}
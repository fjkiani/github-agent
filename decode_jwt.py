import base64
import json

def decode_jwt(token):
    # Split the token into parts
    parts = token.split('.')
    if len(parts) != 3:
        return "Not a valid JWT token"
    
    # Decode the payload (middle part)
    try:
        payload = parts[1] + '=' * (-len(parts[1]) % 4)  # Add padding if needed
        decoded = base64.b64decode(payload)
        return json.loads(decoded)
    except Exception as e:
        return f"Error decoding: {str(e)}"

# Test the current key
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndhYmxoZXBiZW52dnZ0bGJvaHFtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczODM3OTAwMCwiZXhwIjoyMDUzOTU1MDAwfQ.FAkTC55FjeBf7VBFETUErZUKURv0hTXwVwnWlvcu7sk"
print(json.dumps(decode_jwt(key), indent=2)) 
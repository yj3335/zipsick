import re

with open(r'C:/Users/jainc/AppData/Roaming/npm/node_modules/@senso-ai/cli/dist/cli.js', encoding='utf-8', errors='ignore') as f:
    src = f.read()

# Find URLs containing 'brand'
urls = re.findall(r'https?://[^\s"\'`\\]+brand[^\s"\'`\\]*', src)
print("brand URLs:", set(urls))

# Find base API URL patterns
bases = re.findall(r'(?:baseURL|apiUrl|API_URL|baseUrl)[^\w].*?(https?://[^\s"\'`]+)', src[:5000])
print("bases:", bases[:10])

# Find the API base  
api = re.findall(r'"(https://[a-z0-9.-]+\.ai[^"]*)"', src)
print("api domains:", list(set(api))[:10])

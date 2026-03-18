import json
with open('credentials.json') as f:
    parsed = json.load(f)
    result = json.dumps(parsed)
    print(result)
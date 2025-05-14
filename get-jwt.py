"""
    HELPER SCRIPT TO EXTRACT JWT TOKENS
"""

import json
import sys

if __name__ == "__main__":
    token_key='access'
    if len(sys.argv) > 1:
        token_key = sys.argv[1]
    response = json.load(sys.stdin)
    if response['success']:
        print(response['resource'][token_key])

    

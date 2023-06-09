"""
    HELPER SCRIPT TO EXTRACT JWT TOKENS
"""

import json
import sys

if __name__ == "__main__":
    response = json.load(sys.stdin)
    if response['success']:
        print(response['resource']['access'])

    

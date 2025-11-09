#!/usr/bin/env python3
"""Fix port configuration in .env file."""
import os
import re

env_file = '.env'

def fix_port():
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Replace API_PORT=8080 with API_PORT=8001
        if 'API_PORT=8080' in content:
            content = re.sub(r'^API_PORT=8080$', 'API_PORT=8001', content, flags=re.MULTILINE)
            with open(env_file, 'w') as f:
                f.write(content)
            print('✅ Fixed: Changed API_PORT from 8080 to 8001 in .env')
            return True
        elif 'API_PORT=8001' in content:
            print('✅ API_PORT is already set to 8001')
            return True
        elif 'API_PORT=' in content:
            # API_PORT exists but is different value
            content = re.sub(r'^API_PORT=.*$', 'API_PORT=8001', content, flags=re.MULTILINE)
            with open(env_file, 'w') as f:
                f.write(content)
            print('✅ Updated API_PORT to 8001 in .env')
            return True
        else:
            # Add API_PORT if not present
            with open(env_file, 'a') as f:
                f.write('\nAPI_PORT=8001\n')
            print('✅ Added API_PORT=8001 to .env')
            return True
    else:
        # Create .env with API_PORT=8001
        with open(env_file, 'w') as f:
            f.write('API_PORT=8001\n')
        print('✅ Created .env with API_PORT=8001')
        return True

if __name__ == '__main__':
    fix_port()


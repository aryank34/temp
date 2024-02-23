import os
if os.path.exists('kill_code.txt'):
    print('Anti-Kill Activated')
    os.remove('stop.txt')
# Get the directory that contains the current file
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory
parent_dir = os.path.dirname(current_dir)
# Join the parent directory with the file name
file_path = os.path.join(parent_dir, 'kill_timesheet_sync.txt')
# Create the file
if os.path.exists(file_path):
    print('Anti-Kill Activated')
    os.remove(file_path)
# Get the directory that contains the current file
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory
parent_dir = os.path.dirname(current_dir)
# Join the parent directory with the file name
file_path = os.path.join(parent_dir, 'kill_timesheet_sync.txt')
# Create the file
with open(file_path, 'w') as f:
    f.write("This file is used to signal the termination of the timesheet synchronization process. When this file is detected by the process, it will stop its operation.")
    pass
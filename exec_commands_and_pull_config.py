# Import modules needed for script
import pexpect # type: ignore
import getpass
import sys
import time
import os
import re

def connect_to_switch(hostname, username, password, timeout=30):
    """Establish SSH connection to the switch and return the session."""
    print("Connecting to %s..." % hostname)
    
    # Spawn SSH session to the host
    s = pexpect.spawn('ssh %s@%s' % (username, hostname))
    s.timeout = timeout
    
    # Handle initial connection and password
    i = s.expect(['[Pp]assword:', 'yes/no', pexpect.TIMEOUT, pexpect.EOF])
    if i == 0:
        s.sendline(password)
    elif i == 1:
        s.sendline('yes')
        s.expect('[Pp]assword:')
        s.sendline(password)
    else:
        print("SSH connection failed for %s (Timeout or EOF)." % hostname)
        return None
    
    # Handle post-login banner/prompts
    i = s.expect(['Press any key to continue', '.*#', '.*>'], timeout=20)
    if i == 0:
        s.send('\r')
        s.expect(['.*#', '.*>'])
    elif i > 0:
        pass # Already at a prompt
    else:
        print("Failed to get a command prompt at %s after login." % hostname)
        return None

    print("Successfully connected to switch %s." % hostname)
    return s

def execute_and_capture_paginated_command(session, command):
    """Executes a command and handles pagination by repeatedly sending spaces."""
    print("\n--- Executing: %s ---" % command)
    
    # Send the command
    session.sendline(command)
    
    full_output = ""
    
    # Loop to handle pagination
    while True:
        # Expect either the MORE prompt (and the rest of the line) or the final command prompt
        i = session.expect([r'--\s*MORE\s*.*', r'[a-zA-Z0-9_-]+[#>]'], timeout=15)
        
        # Add the output received *before* the match to our buffer
        full_output += session.before
        
        if i == 0:  # Matched '-- MORE --'
            print("Pagination detected - sending space.")
            session.send(' ')
        elif i == 1:  # Matched the final prompt
            print("Final prompt detected. Command finished.")
            break
            
    return full_output

def clean_and_save_output(raw_output, command, hostname):
    """Cleans the captured output and saves it to a file named with the IP."""
    # Create a filename-safe version of the IP
    safe_hostname = hostname.replace('.', '-')
    filename = "%s_%s.txt" % (safe_hostname, command.replace(' ', '_'))
    
    # Remove ANSI escape codes
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    cleaned_output = ansi_escape.sub('', raw_output)

    # Remove the first line (command echo)
    lines = cleaned_output.split('\n', 1)
    if len(lines) > 1:
        cleaned_output = lines[1]
    else:
        cleaned_output = ''
    
    with open(filename, 'w') as f:
        f.write(cleaned_output)
        
    print("Command completed. Cleaned output saved to %s" % filename)

def main():
    # Get connection details from environment variables
    username = os.getenv('HP_SWITCH_USER')
    password = os.getenv('HP_SWITCH_PASS')
    ip_file = 'switch_ip.txt'

    if not all([username, password]):
        print("Error: Please set the HP_SWITCH_USER and HP_SWITCH_PASS environment variables.")
        sys.exit(1)
        
    if not os.path.exists(ip_file):
        print("Error: IP address file not found at %s" % ip_file)
        sys.exit(1)

    # Read IP addresses from the file
    with open(ip_file, 'r') as f:
        ip_addresses = [line.strip() for line in f if line.strip()]
        
    # Define the configuration commands
    config_commands = [
        "conf t",
	    "aruba-central disable",
	    "ip dns server-address priority 1 192.168.X.X",
	    "ip dns server-address priority 2 192.168.X.X",
	    "no tftp client",
	    "activate software-update disable",
	    "activate provision disable",
        "logging 192.168.X.X"
    ]

    # Loop through each IP address
    for hostname in ip_addresses:
        print("\n=============================================")
        print("Processing switch: %s" % hostname)
        print("=============================================")
        
        session = connect_to_switch(hostname, username, password)
        
        if session:
            try:
                # --- Enter Configuration Mode ---
                print("\nEntering configuration mode...")
                session.sendline('configure terminal')
                session.expect(r'.*\(config\)#', timeout=10)
                print("Successfully entered configuration mode.")

                # --- Execute configuration commands ---
                for cmd in config_commands:
                    print("Executing: %s" % cmd)
                    session.sendline(cmd)
                    session.expect(r'.*\(config\)#', timeout=10)

                # --- Exit Configuration Mode ---
                print("\nExiting configuration mode...")
                session.sendline('exit')
                session.expect(r'[a-zA-Z0-9_-]+[#>]', timeout=10)
                print("Successfully exited configuration mode.")

                # --- Save the new configuration ---
                print("\nSaving configuration changes...")
                session.sendline('write memory')
                session.expect(r'[a-zA-Z0-9_-]+[#>]', timeout=30)
                print("Configuration saved.")
                
                # --- Capture the new running config ---
                command_to_run = 'show running-config'
                captured_output = execute_and_capture_paginated_command(session, command_to_run)
                clean_and_save_output(captured_output, command_to_run, hostname)
                
                # Exit the session
                print("\nExiting session for %s." % hostname)
                session.sendline('exit')
            
            except Exception as e:
                print("\nAn error occurred while processing %s: %s" % (hostname, e))
            
            finally:
                # Clean up
                if not session.closed:
                    session.close()
        else:
            print("Could not connect to %s. Skipping." % hostname)

if __name__ == "__main__":
    main()

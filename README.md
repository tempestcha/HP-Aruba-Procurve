HP Aruba ProCurve (OS) Switch Configuration Changes and Backup Script


  This Python script provides a powerful and automated way to connect to multiple HP ProCurve switches, apply a series of configuration commands, and save the updated running configuration to a local file for backup and verification.


  It is designed to be robust, handling the common challenges of automating SSH sessions with network hardware, such as login banners, password prompts, and paginated output.

  Key Features


   * Bulk Operations: Reads a list of switch IP addresses from a text file (switch_ip.txt) to perform operations on multiple devices in a single run.
   * Automated Configuration:
       * Enters global configuration mode (configure terminal).
       * Executes a predefined list of configuration commands.
       * Exits configuration mode.
       * Saves the changes to the switch's startup configuration (write memory).
   * Configuration Backup: After applying changes, it downloads the new running-config from the switch.
   * Intelligent Prompt Handling: Uses the pexpect library to reliably navigate interactive SSH sessions, including:
       * Initial host key verification.
       * Login banners that require a key press.
       * Password prompts.
   * Pagination Control: Automatically handles paginated output (i.e., -- MORE -- prompts) by sending space characters until the entire command output is received.
   * Clean Output: The captured configuration files are cleaned of extraneous content like command prompts and ANSI escape codes (used for color/formatting), leaving you with a clean text backup.
   * Dynamic Filenaming: Saves each configuration file with a unique name based on the switch's IP address (e.g., 172-25-32-129_show_running-config.txt).

  Requirements


   * Python 2.7: This script is written to be compatible with Python 2.
   * Pexpect Library: A Python module for controlling and automating other applications.


  Installation

  Install the required pexpect library using pip:



   1 pip install pexpect


  Configuration


   1. Create IP Address File:
      Create a file named switch_ip.txt in the same directory as the script. Add the IP address of each switch you want to manage, with one IP per line.


      Example `switch_ip.txt`:


   1     192.168.1.10
   2     192.168.1.11
   3     192.168.1.12



   2. Set Credentials:
      For security, the script reads the switch username and password from environment variables rather than hardcoding them. Before running the script, set the following variables in your terminal:



   1     export HP_SWITCH_USER='your_username'
   2     export HP_SWITCH_PASS='your_password'


  Usage

  Once the configuration is complete, run the script from your terminal:



   1 python update_and_get_config.py



  The script will then iterate through each IP in switch_ip.txt, connect, apply the configuration changes, and save the new running configuration to a corresponding .txt file in the same directory.

  How It Works


  The script is built around the pexpect library, which allows it to "expect" certain patterns in the output of an SSH session and "send" responses accordingly.


   1. Connection: The connect_to_switch function initiates the SSH connection. It is programmed to handle different initial prompts, such as the first-time host key verification (yes/no) and the standard password prompt. It also handles the "Press any key to continue" banner common on HP switches.
   2. Configuration: The main function orchestrates the high-level logic. For each switch, it:
       * Enters configuration mode by sending configure terminal and waiting for the (config)# prompt.
       * Loops through a hardcoded list of config_commands and executes them one by one.
       * Exits configuration mode and sends write memory to make the changes persistent.
   3. Data Capture: The execute_and_capture_paginated_command function is called to run show running-config. It enters a loop that repeatedly expects either the final command prompt or a -- MORE -- prompt. If it sees -- MORE --, it sends a space character to reveal the next page of output, continuing until the final prompt is
      detected.
   4. Output Cleaning: The captured text, which includes raw terminal output, is passed to the clean_and_save_output function. This function uses regular expressions to strip out unwanted ANSI color codes and formats the final output before saving it to a file.


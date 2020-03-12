# Geno Server

In order for Geno to train the model and utilize voice commands, an instance of this server must be running locally.

## Installation

Assuming Python 3 is installed, and you've navigated to this directory via the command line.

1. Create a new virtual environment.

    ```
    python3 -m venv .venv
    ```

    This will create a new hidden folder `.venv` in the current directory.

2. Activate the virtual environment.

    ```
    source .venv/bin/activate
    ```

3. Install the requirements.

    ```
    pip install -r requirements.txt
    ```

4. Run the backend script.

    ```
    python backend.py
    ```

The server shoud now be running on http://127.0.0.1:3001. Leave it running so Geno can communicate with it.

If you'd like to delete generated models in the database, run the `clear.sh` script.
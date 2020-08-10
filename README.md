# Geno Server

NLU back-end for the Geno IDE. The IDE trains a NLU model for Geno-enabled websites, which is used to understand voice commands by end-users of the website. Currently, the IDE and server are only configured to work locally.

## Installation

Follow these instructions after cloning this repository and navigating to it via the command line.

1. Using Python 3.7+ (3.8 is not supported), create a new virtual environment.

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
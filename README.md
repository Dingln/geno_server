# Geno Server

Natural language understanding backend for the [Geno IDE](https://github.com/ritamsarmah/geno), used to train a unique NLU model for Geno-enabled websites. Currently, the server is only configured to work locally.

## Installation

1. Download the code and navigate to the project directory.

2. Using Python 3.7+ (3.8 is not supported), create a new virtual environment.

    ```
    python3 -m venv .venv
    ```

    This will create a new hidden folder `.venv` in the current directory.

3. Activate the virtual environment.

    ```
    source .venv/bin/activate
    ```

4. Install the requirements.

    ```
    pip install -r requirements.txt
    ```

5. Run the backend script. The server is configured to run on http://127.0.0.1:3001.

    ```
    python backend.py
    ```



If you'd like to delete generated models in the database, run the `clear.sh` script.
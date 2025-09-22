# IoT Example Project

## Project Description
This is an IoT group project built with Flask. It includes a simple web application to demonstrate IoT-related functionality.

---

## Setup Instructions

## Install SQLite Viewer extension to easily visualize the database file.

### 1. Clone the Repository (if not already done)
Clone the project to your local machine:
```bash
git clone <repository-url>
cd iot_example
```

### 2. Create and Activate a Virtual Environment
Create a virtual environment to isolate dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
Install the required Python packages:
```bash
pip install -r requirements.txt
```

### 4. Run the Application
Set the `FLASK_APP` environment variable and start the Flask development server:
```bash
export FLASK_APP=app.py     //This is not always required.
flask run
```
The application will be available at `http://127.0.0.1:5000`.

---

## Notes
- Ensure Python 3.7+ is installed on your system.
- The virtual environment directory (`.venv`) is local to your machine and should not be committed to the repository.
- If you encounter issues with dependencies, ensure `pip` is up-to-date:
  ```bash
  python -m pip install --upgrade pip
  ```
- ## AGAIN: DO NOT COMMIT .VENV 
---



## License WE CAN CHANGE THIS LATER
This project is licensed under the MIT License. See the `LICENSE` file for details.
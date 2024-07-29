# flask-hotel
## Prerequisite
- Python 3.11

## How to launch the app
Prepare the virtual environment

```bash
python3 -m venv venv
```

Activate it

```bash
source venv/bin/activate
```

Install Packages from `requirements.txt` with pip

```
pip install -r requirements.txt
```

Initialize the database

```bash
flask --app hotel_reservation init-db
```

Run the Flask server

```bash
flask --app hotel_reservation --debug run
```

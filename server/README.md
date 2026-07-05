python -m venv .venv

source .venv/Scripts/activate

pip install -r requirements.txt

http://localhost:8000/docs

uvicorn main:app --reload


http://localhost:8000/dashboard

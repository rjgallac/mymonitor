python -m venv .venv

source .venv/Scripts/activate

pip install -r requirements.txt

http://localhost:8000/docs

uvicorn main:app --host 0.0.0.0 --reload


http://localhost:8000/dashboard


http://localhost:8000/docs
and add websites to monitor

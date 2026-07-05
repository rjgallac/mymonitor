# Local Setup

python -m venv .venv

source .venv/Scripts/activate

pip install -r requirements.txt

uvicorn main:app --host 0.0.0.0 --reload

http://localhost:8000/docs

http://localhost:8000/dashboard

# Docker Setup

## Build the Image
Run the following command from the `server` directory:

```bash
docker build -t mymonitor-server .
```

## Run the Container
Run the container and map port 8000 to your host machine:

```bash
docker run -p 8000:8000 mymonitor-server
```

Once running, you can access the application at:
- Dashboard: [http://localhost:8000/dashboard](http://localhost:8000/dashboard)
- API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

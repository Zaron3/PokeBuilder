pip install fastapi "uvicorn[standard]"
pip install "elasticsearch<9.0.0"

cd .\backend\
uvicorn main:app --reload

pip install fastapi "uvicorn[standard]"
pip install "elasticsearch<9.0.0"


cd .\backend\
uvicorn main:app --reload 

## Si no ha funcionat provar: 
python -m uvicorn main:app --reload

http://127.0.0.1:8000/docs#

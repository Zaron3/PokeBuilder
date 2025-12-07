pip install fastapi "uvicorn[standard]"
pip install "elasticsearch<9.0.0"

# Nou pip install
pip install "passlib[bcrypt]" "bcrypt==4.0.1" "python-jose[cryptography]" python-multipart email-validator

cd .\backend\
uvicorn main:app --reload 

## Si no ha funcionat provar: 
python -m uvicorn main:app --reload

http://127.0.0.1:8000/docs#

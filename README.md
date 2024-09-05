# TinyDBService

Set up virtual environment for TinyDBService
python3 -m venv tinyDBService .

# Update gitignore to exclude generated files from above command
pyvenv.cfg
bin/activate
bin/*
tinyDBService/bin/*

# Activate Virtual environment for work run: 
Source ./bin/activate


# Install libraries

pip3 install tinydb
pip3 install FastAPI
pip3 install "fastapi[standard]"

# To run server 
fastapi run app.py
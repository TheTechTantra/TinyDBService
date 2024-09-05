import logging

from fastapi import FastAPI
from TinyDBUtil import TinyDbReader
from CredentialModel import Credential


app = FastAPI()



logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S', handlers=[logging.StreamHandler(), logging.FileHandler('app.log')])

logging.info("This is a logging message")

@app.get('/credential/{key}')
def getCredentials(key: str):
    reader = TinyDbReader()
    data = reader.read_data(key)
    return data

@app.post('/key/')
def setCredentials(credential: Credential):
    reader = TinyDbReader()
    
    reader.write(credential.key, credential.value)
    return 'success'

@app.delete('/key/{key}')
def deleteCredentials(key: str):
    reader = TinyDbReader()
    reader.delete(key)
    return 'success'
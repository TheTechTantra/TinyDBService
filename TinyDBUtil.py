from tinydb import TinyDB
from tinydb import Query


class TinyDbReader:
    def __init__(self):
        self.db = TinyDB("/app/db.json")

    def read_data(self, key):
        return self.db.search(Query().key == key)

    def close(self):
        self.db.close()

    def __del__(self):
        self.close()
    
    def write(self, key, data):
        self.db.insert({'key ' : key  , 'value ' : data})

    def delete(self, key):
        self.db.remove(Query().key == key)

    def update(self, key, data):
        self.db.update(data, Query().key == key)

    def read_all(self):
        return self.db.all()

    def read_by_key(self, key):
        return self.db.search(Query().key == key)

    def read_by_value(self, value):
        return self.db.search(Query().value == value)

    def read_by_key_and_value(self, key, value):
        return self.db.search(Query().key == key and Query().value == value)

    def read_by_key_or_value(self, key, value):
        return self.db.search(Query().key == key or Query().value == value)
     
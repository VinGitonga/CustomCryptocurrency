from uuid import uuid4
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from mutuall.blockchain import *
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

blockchain = Blockchain();

print(type(blockchain.generateKeys()));
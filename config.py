# config.py


# Mongo_URI='mongodb+srv://Arshad:marshadcs20-24@mycluster.9cn3csl.mongodb.net/?retryWrites=true&w=majority'

import os


class Config:
    SECRET_KEY = 'marshadcs20-24plusMisbah'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql://root:@localhost/emoflask'


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'mysql://root:@localhost/emoflask'


# Choose the appropriate configuration based on your environment
# For development, use DevelopmentConfig
# For production, use ProductionConfig
config = DevelopmentConfig()  # Change this line based on your environment

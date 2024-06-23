class Config:
    # Secret key for the application
    SECRET_KEY = 'marshadcs20-24plusMisbah'
    # Disable tracking of object modifications
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    # Enable debug mode
    DEBUG = True
    # URI for the MySQL database
    SQLALCHEMY_DATABASE_URI = 'mysql://root:@localhost/emoflask'


class ProductionConfig(Config):
    # Disable debug mode
    DEBUG = False
    # URI for the MySQL database
    SQLALCHEMY_DATABASE_URI = 'mysql://root:@localhost/emoflask'


# Choose the appropriate configuration based on the environment
# For development, use DevelopmentConfig
# For production, use ProductionConfig
config = DevelopmentConfig()  # Change this line based on the environment

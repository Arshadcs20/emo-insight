# from datetime import datetime
# from flask_sqlalchemy import SQLAlchemy


# class Post(db.Model):
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     content = db.Column(db.Text, nullable=False)
#     timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
#     platform = db.Column(db.String(50), nullable=False)
#     # Assuming your User model is named 'User'
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

#     def __repr__(self):
#         return f"Post(id={self.id}, content='{self.content}', timestamp={self.timestamp}, platform='{self.platform}', user_id={self.user_id})"

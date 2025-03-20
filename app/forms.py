from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, URLField, IntegerField, DateTimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, URL, Optional, NumberRange
from app.models import User
from datetime import datetime

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('This username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email address is already registered. Please use a different email address.')

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    summary = TextAreaField('Summary', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    image_url = StringField('Image URL', validators=[Optional(), URL()], description="Enter a URL for the post's cover image. If left empty, a placeholder will be used.")
    reading_time = IntegerField('Reading Time (minutes)', validators=[Optional(), NumberRange(min=1, max=60)], description="Estimated reading time in minutes. Leave empty for automatic calculation.")
    created_at = DateTimeField('Publication Date', format='%Y-%m-%dT%H:%M', validators=[Optional()], default=datetime.utcnow, description="Publication date and time. Leave empty to use current date.")
    premium_only = BooleanField('Premium Only', default=False, description="If checked, only premium users will be able to access this post.")
    submit = SubmitField('Save Post')

class UserUpdateForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    age = IntegerField('Age', validators=[Optional(), NumberRange(min=18, max=120)])
    is_premium = BooleanField('Premium User')
    is_admin = BooleanField('Admin User')
    submit = SubmitField('Update User')

class ProfileUpdateForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    age = IntegerField('Age', validators=[Optional(), NumberRange(min=18, max=120)], description="Optional. You can leave this field blank.")
    submit = SubmitField('Update Profile')
    
    def __init__(self, original_username='', original_email='', *args, **kwargs):
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
        
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('This username is already taken. Please choose a different one.')
                
    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('This email address is already registered. Please use a different email address.')

class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired(), Length(min=5, max=1000)])
    submit = SubmitField('Submit Comment')

class ChatMessageForm(FlaskForm):
    message = TextAreaField('Sua Mensagem', validators=[DataRequired(), Length(min=2, max=1000)])
    submit = SubmitField('Enviar') 
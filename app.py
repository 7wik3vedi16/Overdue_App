import re
import os
import pathlib
import csv
import requests
from google.oauth2 import id_token
from flask import Flask, session, abort, redirect, request
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
from jinja2 import Environment
from datetime import datetime
import pandas as pd
from bson import ObjectId
from flask import render_template
from flask import Flask, redirect, url_for
from flask_cors import CORS
from model import process_data
from flask import Flask, request
from pymongo import MongoClient
from flask_mail import Mail, Message
import pymongo
from authlib.integrations.flask_client import OAuth
from flask import jsonify
from flask import Flask, render_template, redirect, url_for, session, request,abort
from urllib.parse import quote
from google_auth_oauthlib.flow import Flow
import sys
import random
from groq import Groq, GroqError
import time


app = Flask(__name__)
mail= Mail(app)
try:
    client = pymongo.MongoClient("mongodb+srv://7wik3vedi16:Rudransh#08@helloflask.fdn6ulu.mongodb.net/?retryWrites=true&w=majority&appName=helloflask")
except pymongo.errors.ConfigurationError:
  print("An Invalid URI host error was received. Is your Atlas host name correct in your connection string?")
  sys.exit(1)
  
db = client.myDatabase
my_collection = db["data"]
oauth = OAuth(app)
CORS(app)
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
GOOGLE_CLIENT_ID = '636862601501-k8qoq08rj805r7jp460r6qg8qsa2543p.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = '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'
GOOGLE_REDIRECT_URI= 'https://accounts.google.com/.well-known/openid-configuration'
client_secrets_file=os.path.join(pathlib.Path(__file__).parent,"client_secret.json")
flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = '7wik.3vedi16@gmail.com'
app.config['MAIL_PASSWORD'] = 'yppa obde edqd cowo'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


app.secret_key = 'CodeSpecialist.com'
GROQ_API_KEY = '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' 
if not GROQ_API_KEY:
    raise GroqError("The api_key client option must be set either by passing api_key to the client or by setting the GROQ_API_KEY environment variable")

client = Groq(api_key=GROQ_API_KEY)

CSV_FILE = 'data_entries.csv'

# with open(CSV_FILE, mode='a', newline='') as file:
#     writer = csv.writer(file)
#     writer.writerow(['User ID','User Name','Name','Email ID','Overdue Amount', 'Description'])

def random_color(context):
    return '#{0:06x}'.format(random.randint(0, 0xFFFFFF))

app.jinja_env.filters['random_color'] = random_color


def login_is_required(function):
    def wrapper(*args,**kwargs):
        if "google_id" not in session:
            return abort(401)
        else:
            return function()
    return wrapper


@app.route("/")
def index():
    return render_template("login.html")


@app.route("/home/")

def home():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route("/about/", methods=['GET', 'POST'])
def about():
    data=[]
    if request.method == 'POST':
        user_name=session["name"]
        user_id=session["google_id"]
        # user_email=session["email"]
        name = request.form.get('name')
        email = request.form.get('emailid')
        amount=request.form.get('amount')
        description=request.form.get('description')
        my_collection.insert_one({'User':user_name,'User_ID':user_id,'Name': name, 'Email_Id': email, 'Amount_Overdue':amount,'Description':description})
        data=[name,email,amount,description]
        with open(CSV_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([user_id,user_name,name,email, amount,description])
    return render_template("about.html",data=data)

@app.route("/contact/", methods=['GET', 'POST'])
def contact():
    user_id = session.get("google_id")
    users = my_collection.find({"User_ID": user_id}, {"Name": 1, "Email_Id": 1})
    user_list = list(users)
    result = None
    if request.method == 'POST':
        user_id1 = request.form['user_id']
        template_type = request.form['template_type']
        custom_message = request.form['custom_message']

        user = my_collection.find_one({"_id": ObjectId(user_id1)})
        if user:
            user_name = user['Name']
            sender_name=user['User']
            overdue_amount = int(user['Amount_Overdue'])

            try:
                email_template = generate_email_template(user_name, overdue_amount, template_type,sender_name,custom_message)
                result = email_template
                msg = Message('Overdue Amount Notification', sender='7wik.3vedi16@gmail.com', recipients=[user["Email_Id"]])
                msg.body = email_template
                mail.send(msg)
            except Exception as e:
                result = f"Error: {e}"
                email_template = fallback_email_template(user_name, overdue_amount)
                result = email_template
                msg = Message('Overdue Amount Notification', sender='7wik.3vedi16@gmail.com', recipients=[user["Email_Id"]])
                msg.body = email_template
                mail.send(msg)
        else:
            result = "User not found"
    
    return render_template("contact.html", user_list=user_list, result=result)


def generate_email_template(user_name, overdue_amount, template_type,user_id,cust_mess):
    prompt = f"Write a {template_type} email to notify {user_name} about an overdue amount of {overdue_amount}. The email should be short and end with 'Regards, {user_id}'. Exclude any extra details such as subject line or template headers. Also follow this custom prompt by user: {cust_mess}"

    for _ in range(3):  # Retry up to 3 times
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="llama3-8b-8192",
            )
            email_template = chat_completion.choices[0].message.content.strip()
            return email_template
        except Exception as e:
            print(f"API Error: {e}")
            time.sleep(2)
            continue
    raise Exception("Failed to generate email template after retries")

def fallback_email_template(user_name, overdue_amount):
    return f"Dear {user_name},\n\nWe wanted to remind you that you have an overdue amount of {overdue_amount}. Please make the payment at your earliest convenience.\n\nThank you."


@app.route("/overdue/", methods=['GET', 'POST'])
def overdue():
    if request.method == 'POST':
        instance_id = request.form.get('_id')
        if instance_id:
            my_collection.delete_one({'_id': ObjectId(instance_id)})
        return redirect(url_for('overdue'))
    instances = my_collection.find()
    user_id=session["google_id"]
    return render_template("overdue.html", inf=instances,user_id=user_id)

@app.route("/edit/<string:user_id>", methods=["GET", "POST"])
def edit_user(user_id):
    if request.method == "GET":
        user = my_collection.find_one({"_id": user_id})
        if user:
            return render_template("edit.html", user=user)
        else:
            return "User not found", 404
    elif request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        amount = request.form["amount"]
        description=request.form["description"]
        my_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"Name": name, "Email_Id": email, "Amount_Overdue": amount,"Description":description}})
        return redirect(url_for("overdue"))

@app.route("/get_overdue_amount/<string:userName>")
def get_overdue_amount(userName):
    user = my_collection.find_one({"Name": userName})
    if user:
        overdueAmount = user.get("Amount_Overdue", 0) 
        userFullName = user.get("Name", "")
        return jsonify({"success": True, "overdueAmount": overdueAmount, "userFullName": userFullName})
    else:
        return jsonify({"success": False}), 404
    
@app.route("/payment/")
def payment():
    acc_name=session['name']
    obligations = my_collection.find({"Name": acc_name})
    return render_template("payment.html",obligations=obligations)

@app.route('/analysis/', methods=['GET', 'POST'])
def analysis():
    user_id = session['google_id']
    df = pd.read_csv(r"D:\React-App\hello_flask\backend\data_entries.csv")
    
    # Filter the data for the specified user_id
    user_data = df[df['User ID'] == user_id]
    unique_names = user_data['Name'].unique()
    
    selected_name = None
    graph_url = None
    
    if request.method == 'POST':
        selected_name = request.form.get('name')
        if selected_name:
            graph_url = process_data(user_id, selected_name)

    return render_template('analysis.html', unique_names=unique_names, graph_url=graph_url, selected_name=selected_name)

    
@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500) 

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    return redirect("/home")
    
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == '__main__':
    app.run(debug=True)

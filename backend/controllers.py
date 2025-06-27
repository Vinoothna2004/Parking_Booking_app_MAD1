from flask import Flask,render_template,request,url_for,redirect
from .models import *
from flask import current_app as app
from datetime import datetime
from sqlalchemy import func
from werkzeug.utils import secure_filename
import matplotlib.pyplot as plt

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login",methods=["GET","POST"])
def signin():
    if request.method=="POST":
        uname=request.form.get("user_name")
        pwd=request.form.get("password")
        usr=User_Info.query.filter_by(email=uname,password=pwd).first()
        if usr and usr.role==0: #Existed and admin
            return redirect(url_for("admin_dashboard",name=uname))
        elif usr and usr.role==1: #Existed and normal user
            return redirect(url_for("user_dashboard",name=uname,id=usr.id))
        else:
            return render_template("login.html",msg="Invalid user credentials...")

    return render_template("login.html",msg="")


@app.route("/register",methods=["GET","POST"])
def signup():
    if request.method=="POST":
        uname=request.form.get("user_name")
        pwd=request.form.get("password")
        # pwd=my_encrypt(pwd) 
        full_name=request.form.get("full_name")
        address=request.form.get("location")
        pin_code=request.form.get("pin_code")
        vehicle_no=request.form.get("vehicle_no")
        usr=User_Info.query.filter_by(email=uname).first()
        if usr:
            return render_template("signup.html",msg="Sorry, this mail already registered!!!")
        new_usr=User_Info(email=uname,password=pwd,full_name=full_name,address=address,pin_code=pin_code,vehicle_no=vehicle_no)
        db.session.add(new_usr)
        db.session.commit()
        return render_template("login.html",msg="Registration successfull, try login now")
    
    return render_template("signup.html",msg="")

#Common route for admin dashboard
@app.route("/admin/<name>")
def admin_dashboard(name):
    parkinglots=get_parkinglots()
    return render_template("admin_dashboard.html",name=name,parkinglotss=parkinglots)


@app.route("/user/<id>/<name>")
def user_dashboard(id,name):
    parkinglots=get_parkinglots()
    dt_time_now=datetime.today().strftime('%Y-%m-%dT%H:%M')
    dt_time_now=datetime.strptime(dt_time_now,"%Y-%m-%dT%H:%M")
    return render_template("user_dashboard.html",uid=id,name=name,parkinglots=parkinglots,dt_time_now=dt_time_now)




def get_parkinglots():
    parkinglots=ParkingLot.query.all()
    return parkinglots
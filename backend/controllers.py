from flask import Flask,render_template,request,url_for,redirect
from .models import *
from flask import current_app as app
from datetime import datetime
from sqlalchemy import func
from werkzeug.utils import secure_filename
import matplotlib.pyplot as plt
from flask import session

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
            if usr and usr.role == 0:
                session["user_id"] = usr.id
                session["user_name"] = uname
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
    if "user_id" not in session:
        return redirect(url_for("signin"))

    session["user_name"] = name
    parkinglots = get_parkinglots()
    return render_template("admin_dashboard.html", name=name, parkinglots=parkinglots)



@app.route("/user/<id>/<name>")
def user_dashboard(id, name):
    parkinglots = get_parkinglots()
    dt_time_now = datetime.today().strftime('%Y-%m-%dT%H:%M')
    dt_time_now = datetime.strptime(dt_time_now, "%Y-%m-%dT%H:%M")
    reservations = Reservation.query.filter_by(user_id=id).all()
    return render_template(
        "user_dashboard.html",
        uid=id,
        user_id=id, 
        name=name,
        parkinglots=parkinglots,
        dt_time_now=dt_time_now,
        reservations=reservations
    )



def get_parkinglots():
    parkinglots=ParkingLot.query.all()
    return parkinglots



@app.route("/search")
def search_parking():
    query = request.args.get("search_query", "")
    results = ParkingLot.query.filter(
        (ParkingLot.location.ilike(f"%{query}%")) | 
        (ParkingLot.pin_code.ilike(f"%{query}%"))
    ).all()

    # ✅ You need the user ID and name for the dashboard
    user_id = request.args.get("user_id")
    user_name = request.args.get("name")

    # Optional: fallback if not passed
    if not user_id or not user_name:
        # Try from session if you have it
        user_id = session.get("user_id")
        user_name = session.get("user_name")

    reservations = Reservation.query.filter_by(user_id=user_id).all()
    parkinglots = get_parkinglots()

    return render_template(
        "user_dashboard.html",
        search_results=results,
        location_query=query,
        uid=user_id,
        name=user_name,
        reservations=reservations,
        parkinglots=parkinglots,
        user_id=user_id
    )




@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("signin"))


@app.route("/add_lot", methods=["GET", "POST"])
def add_parking_lot():
    if request.method == "POST":
        name = request.form.get("prime_location_name")
        address = request.form.get("address")
        pin_code = request.form.get("pin_code")
        price = request.form.get("price")
        capacity = int(request.form.get("capacity"))

        new_lot = ParkingLot(
            prime_location_name=name,
            location=address,
            pin_code=int(pin_code),
            tkt_price=float(price),
            capacity=capacity
        )
        db.session.add(new_lot)
        db.session.commit()  # Commit to get new_lot.id

        # Auto-generate slots
        for _ in range(capacity):
            new_slot = Slot(
                status=SlotStatus.Available,
                parkinglot_id=new_lot.id
            )
            db.session.add(new_slot)

        db.session.commit()  # Save slots

        return redirect(url_for("admin_dashboard", name="Admin"))

    return render_template("add_lot.html")

from flask import render_template, request, redirect, url_for
from datetime import datetime
from .models import db, Slot, Reservation, SlotStatus




@app.route("/edit_lot/<int:lot_id>", methods=["GET", "POST"])
def edit_parking_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)

    if request.method == "POST":
        old_capacity = lot.capacity
        new_capacity = int(request.form.get("capacity"))

        lot.prime_location_name = request.form.get("prime_location_name")
        lot.location = request.form.get("address")
        lot.pin_code = int(request.form.get("pin_code"))
        lot.tkt_price = float(request.form.get("price"))
        lot.capacity = new_capacity

        db.session.commit()

        if new_capacity > old_capacity:
            # Add new slots
            slots_to_add = new_capacity - old_capacity
            for _ in range(slots_to_add):
                new_slot = Slot(
                    status=SlotStatus.Available,
                    parkinglot_id=lot.id
                )
                db.session.add(new_slot)

        elif new_capacity < old_capacity:
            # Remove slots if there are enough free slots
            slots_to_remove = old_capacity - new_capacity
            free_slots = Slot.query.filter_by(
                parkinglot_id=lot.id,
                status=SlotStatus.Available
            ).limit(slots_to_remove).all()

            if len(free_slots) < slots_to_remove:
                # Not enough free slots to remove
                return f"Cannot reduce capacity: only {len(free_slots)} slots are free to remove."

            for slot in free_slots:
                db.session.delete(slot)

        db.session.commit()
        return redirect(url_for("admin_dashboard", name="Admin"))

    return render_template("edit_lot.html", lot=lot)


@app.route("/delete_lot/<int:lot_id>", methods=["POST"])
def delete_parking_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)

    # Delete all slots under this lot too (cascades because of your models)
    db.session.delete(lot)
    db.session.commit()

    return redirect(url_for("admin_dashboard", name="Admin"))


@app.route("/view_delete_slot/<int:slot_id>", methods=["GET", "POST"])
def view_delete_slot(slot_id):
    slot = Slot.query.get_or_404(slot_id)

    if request.method == "POST":
        if slot.status == SlotStatus.Occupied:
            return "Cannot delete an occupied parking spot!"

        # Decrease capacity of its parent lot
        lot = ParkingLot.query.get(slot.parkinglot_id)
        if lot.capacity > 0:
            lot.capacity -= 1

        db.session.delete(slot)
        db.session.commit()

        return redirect(url_for("admin_dashboard", name="Admin"))

    return render_template("view_delete_parking_slot.html", slot=slot)


@app.route("/occupied_slot_details/<int:slot_id>")
def occupied_slot_details(slot_id):
    slot = Slot.query.get_or_404(slot_id)

    if slot.status != SlotStatus.Occupied:
        return redirect(url_for("view_delete_slot", slot_id=slot_id))

    reservation = Reservation.query.filter_by(slot_id=slot.id).order_by(Reservation.parking_timestamp.desc()).first()

    return render_template("occupied_parking_slot_details.html", slot=slot, reservation=reservation)





@app.route("/book_slot/<int:lot_id>/<int:user_id>", methods=["GET", "POST"])
def book_slot(lot_id, user_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    slot = Slot.query.filter_by(parkinglot_id=lot_id, status=SlotStatus.Available).first()

    if not slot:
        return "No available slots in this lot!", 400

    if request.method == "POST":
        vehicle_number = request.form.get("vehicle_number")
        if not vehicle_number:
            return "Vehicle number is required", 400

        reservation = Reservation(
            parking_timestamp=datetime.now(),
            user_id=user_id,
            slot_id=slot.id
        )

        slot.status = SlotStatus.Occupied

        user = User_Info.query.get(user_id)
        if user:
            user.vehicle_no = vehicle_number

        db.session.add(reservation)
        db.session.commit()

        return redirect(url_for("user_dashboard", id=user_id, name="User"))

    return render_template(
        "book_slot.html",
        lot=lot,
        slot=slot,
        user_id=user_id,
        uid=user_id   
    )


from datetime import datetime

@app.route("/release/<int:reservation_id>", methods=["GET", "POST"])
def release_parking(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    slot = Slot.query.get(reservation.slot_id)
    user = User_Info.query.get(reservation.user_id)

    if request.method == "POST":
        reservation.leaving_timestamp = datetime.now()

        # Calculate hours parked
        duration = reservation.leaving_timestamp - reservation.parking_timestamp
        hours = duration.total_seconds() / 3600

        # Example cost: ₹50 per hour
        price_per_hour = 50
        cost = round(hours * price_per_hour, 2)

        reservation.parking_cost = cost
        slot.status = SlotStatus.Available

        db.session.commit()

        return redirect(url_for("user_dashboard", id=user.id, name="User"))

    parking_time = reservation.parking_timestamp.strftime("%Y-%m-%d %H:%M:%S")
    releasing_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Estimate cost (preview)
    duration = datetime.now() - reservation.parking_timestamp
    hours = duration.total_seconds() / 3600
    price_per_hour = 50
    cost = round(hours * price_per_hour, 2)

    return render_template(
        "release_slot.html",
        slot=slot,
        vehicle_no=user.vehicle_no,
        parking_time=parking_time,
        releasing_time=releasing_time,
        total_cost=cost,
        user_id=user.id,
        uid=user.id
    )



#user summary
@app.route("/summary/<int:user_id>")
def user_summary(user_id):
    user = User_Info.query.get_or_404(user_id)

    # Example: count how many times user used each slot
    slots = db.session.query(
        Slot.id,
        db.func.count(Reservation.id)
    ).join(Reservation).filter(Reservation.user_id == user_id).group_by(Slot.id).all()

    labels = [f"Spot {slot_id}" for slot_id, _ in slots]
    data = [count for _, count in slots]

    return render_template(
        "user_summary.html",
        labels=labels,
        data=data,
        name=user.full_name,
        uid=user.id,
        user_id=user.id
    )



@app.route("/users")
def view_users():
    users = User_Info.query.filter_by(role=1).all()
    if not users:
        msg = "There are no registered users."
    else:
        msg = ""
    admin_id = session.get("user_id")
    return render_template("users.html", users=users, msg=msg, user_id=admin_id)





@app.route("/admin_search", methods=["GET", "POST"])
def admin_search():
    results = []
    query = ""
    search_by = ""

    if request.method == "POST":
        search_by = request.form.get("search_by")
        query = request.form.get("search_string")

        if search_by == "user_id":
            # Find user by ID
            results = User_Info.query.filter_by(id=query).all()
        elif search_by == "location":
            # Find parking lots by location
            results = ParkingLot.query.filter(
                ParkingLot.location.ilike(f"%{query}%")
            ).all()

    return render_template(
        "admin_search.html",
        results=results,
        query=query,
        search_by=search_by
    )


import io
import base64
from matplotlib.figure import Figure

@app.route("/summary")
def admin_summary():
    # Calculate revenue for each parking lot
    lots = ParkingLot.query.all()
    lot_names = []
    lot_revenues = []

    for lot in lots:
        # Total revenue: sum of all reservations in this lot
        total = 0
        for slot in lot.slots:
            for reservation in slot.reservations:
                total += reservation.parking_cost
        lot_names.append(f"Lot#{lot.id}")
        lot_revenues.append(total)

    # Prepare chart: Pie
    fig1 = Figure()
    ax1 = fig1.subplots()
    ax1.pie(lot_revenues, labels=lot_names, autopct='%1.1f%%', startangle=140)
    ax1.set_title("Revenue from each parking lot")

    buf1 = io.BytesIO()
    fig1.savefig(buf1, format="png")
    buf1.seek(0)
    pie_chart = base64.b64encode(buf1.getvalue()).decode('utf-8')
    buf1.close()

    # Calculate available vs occupied slots
    available = 0
    occupied = 0
    for lot in lots:
        for slot in lot.slots:
            if slot.status.name == "Available":
                available += 1
            else:
                occupied += 1

    # Prepare chart: Bar
    fig2 = Figure()
    ax2 = fig2.subplots()
    ax2.bar(["Available", "Occupied"], [available, occupied], color=["green", "red"])
    ax2.set_title("Available vs Occupied Slots")

    buf2 = io.BytesIO()
    fig2.savefig(buf2, format="png")
    buf2.seek(0)
    bar_chart = base64.b64encode(buf2.getvalue()).decode('utf-8')
    buf2.close()

    return render_template("admin_summary.html", pie_chart=pie_chart, bar_chart=bar_chart, name="Admin")



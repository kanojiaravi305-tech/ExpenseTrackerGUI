# ============================================================
# Expense Tracker - Flask Backend (app.py)
# Subject: Next Generation Database (NGD)
# Purpose: Demonstrates Flask + MongoDB (NoSQL) integration
# ============================================================

import os
import certifi
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# ------------------------------------------------------------
# Flask App Configuration
# ------------------------------------------------------------
app = Flask(__name__)
app.secret_key = "expense_tracker_secret_key_ngd_project"  # Required for session & flash messages

# ------------------------------------------------------------
# MongoDB Configuration
# ------------------------------------------------------------
MONGO_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = "expense_tracker_db"
COLLECTION_NAME = "expenses"

# Connect to MongoDB server
ca = certifi.where()
client = MongoClient(MONGO_URI, tlsCAFile=ca)

# Select (or create) database and collections
db = client[DATABASE_NAME]
expenses_collection = db[COLLECTION_NAME]
users_collection = db["users"]

# ------------------------------------------------------------
# User Session Authentication Decorator
# Protects routes so only logged-in users can access them
# ------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# ============================================================
# Route: Sign Up (GET & POST)
# Handles user registration with password hashing
# ============================================================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    # If user is already logged in, redirect them to dashboard
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        # Backend validations
        if not username or not password or not confirm_password:
            flash("Please fill all required fields.", "error")
            return render_template("signup.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("signup.html")

        # Check if user already exists in MongoDB
        existing_user = users_collection.find_one({"username": {"$regex": f"^{username}$", "$options": "i"}})
        if existing_user:
            flash("Username already exists. Please choose another.", "error")
            return render_template("signup.html")

        # Hash the password and save to database
        hashed_password = generate_password_hash(password)
        new_user = {
            "username": username,
            "password": hashed_password,
            "created_at": datetime.now()
        }
        users_collection.insert_one(new_user)

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")

# ============================================================
# Route: Log In (GET & POST)
# Authenticates user credentials and starts session
# ============================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Please fill all required fields.", "error")
            return render_template("login.html")

        # Fetch user document from MongoDB
        user = users_collection.find_one({"username": username})

        # Verify username and hashed password
        if user and check_password_hash(user["password"], password):
            session["user_id"] = str(user["_id"])
            session["username"] = user["username"]
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password.", "error")

    return render_template("login.html")

# ============================================================
# Route: Log Out (GET)
# Clears user session
# ============================================================
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))

# ------------------------------------------------------------
# List of valid expense categories
# ------------------------------------------------------------
CATEGORIES = [
    "Food",
    "Travel",
    "Shopping",
    "Bills",
    "Education",
    "Health",
    "Entertainment",
    "Other"
]# ============================================================
# Route: Home Page (GET /)
# Displays logged-in user's expenses, total, and add form.
# ============================================================
@app.route("/")
@login_required
def index():
    # Read optional search and filter query parameters
    search_query = request.args.get("search", "").strip()
    category_filter = request.args.get("category", "").strip()

    # Build a MongoDB query filter scoped to the logged-in user
    mongo_filter = {"user_id": ObjectId(session["user_id"])}

    # If the user typed something in the search box, search inside user's expenses
    if search_query:
        mongo_filter["$or"] = [
            {"title": {"$regex": search_query, "$options": "i"}},
            {"category": {"$regex": search_query, "$options": "i"}}
        ]

    # If the user selected a specific category
    if category_filter and category_filter != "All":
        mongo_filter["category"] = category_filter

    # Fetch matching expenses from MongoDB, sorted by date (newest first)
    expenses = list(expenses_collection.find(mongo_filter).sort("date", -1))

    # Calculate the total amount
    total_amount = sum(expense.get("amount", 0) for expense in expenses)

    return render_template(
        "index.html",
        expenses=expenses,
        total_amount=total_amount,
        categories=CATEGORIES,
        search_query=search_query,
        category_filter=category_filter
    )


# ============================================================
# Route: Add Expense (POST /add)
# Adds a new expense document associated with the logged-in user.
# ============================================================
@app.route("/add", methods=["POST"])
@login_required
def add_expense():
    title = request.form.get("title", "").strip()
    amount = request.form.get("amount", "").strip()
    category = request.form.get("category", "").strip()
    date = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip()

    # --- Backend Validation ---
    if not title or not amount or not category or not date:
        flash("Please fill all required fields.", "error")
        return redirect(url_for("index"))

    try:
        amount = float(amount)
        if amount <= 0:
            flash("Amount must be greater than zero.", "error")
            return redirect(url_for("index"))
    except ValueError:
        flash("Amount must be a valid number.", "error")
        return redirect(url_for("index"))

    # Create the expense document linked to this user
    expense_document = {
        "user_id": ObjectId(session["user_id"]),
        "title": title,
        "amount": amount,
        "category": category,
        "date": date,
        "description": description,
        "created_at": datetime.now()
    }

    expenses_collection.insert_one(expense_document)
    flash("Expense added successfully.", "success")
    return redirect(url_for("index"))


# ============================================================
# Route: Edit Expense Page (GET /edit/<expense_id>)
# ============================================================
@app.route("/edit/<expense_id>")
@login_required
def edit_expense(expense_id):
    try:
        obj_id = ObjectId(expense_id)
    except InvalidId:
        flash("Expense not found.", "error")
        return redirect(url_for("index"))

    # Find the expense document by its _id and user_id (ownership check)
    expense = expenses_collection.find_one({
        "_id": obj_id,
        "user_id": ObjectId(session["user_id"])
    })

    if not expense:
        flash("Expense not found.", "error")
        return redirect(url_for("index"))

    return render_template(
        "edit_expense.html",
        expense=expense,
        categories=CATEGORIES
    )


# ============================================================
# Route: Update Expense (POST /update/<expense_id>)
# ============================================================
@app.route("/update/<expense_id>", methods=["POST"])
@login_required
def update_expense(expense_id):
    try:
        obj_id = ObjectId(expense_id)
    except InvalidId:
        flash("Expense not found.", "error")
        return redirect(url_for("index"))

    title = request.form.get("title", "").strip()
    amount = request.form.get("amount", "").strip()
    category = request.form.get("category", "").strip()
    date = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip()

    # --- Backend Validation ---
    if not title or not amount or not category or not date:
        flash("Please fill all required fields.", "error")
        return redirect(url_for("edit_expense", expense_id=expense_id))

    try:
        amount = float(amount)
        if amount <= 0:
            flash("Amount must be greater than zero.", "error")
            return redirect(url_for("edit_expense", expense_id=expense_id))
    except ValueError:
        flash("Amount must be a valid number.", "error")
        return redirect(url_for("edit_expense", expense_id=expense_id))

    updated_data = {
        "$set": {
            "title": title,
            "amount": amount,
            "category": category,
            "date": date,
            "description": description
        }
    }

    # Update only if owned by the logged-in user
    result = expenses_collection.update_one(
        {"_id": obj_id, "user_id": ObjectId(session["user_id"])},
        updated_data
    )

    if result.matched_count == 0:
        flash("Expense not found.", "error")
    else:
        flash("Expense updated successfully.", "success")

    return redirect(url_for("index"))


# ============================================================
# Route: Delete Expense (POST /delete/<expense_id>)
# ============================================================
@app.route("/delete/<expense_id>", methods=["POST"])
@login_required
def delete_expense(expense_id):
    try:
        obj_id = ObjectId(expense_id)
    except InvalidId:
        flash("Expense not found.", "error")
        return redirect(url_for("index"))

    # Delete only if owned by the logged-in user
    result = expenses_collection.delete_one({
        "_id": obj_id,
        "user_id": ObjectId(session["user_id"])
    })

    if result.deleted_count == 0:
        flash("Expense not found.", "error")
    else:
        flash("Expense deleted successfully.", "success")

    return redirect(url_for("index"))


# ============================================================
# Route: Search Expenses (GET /search)
# ============================================================
@app.route("/search")
@login_required
def search():
    search_query = request.args.get("search", "").strip()
    category_filter = request.args.get("category", "").strip()
    return redirect(url_for("index", search=search_query, category=category_filter))
# ============================================================
# Run the Flask Application
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("  Expense Tracker - NGD Project")
    print("  Open: http://127.0.0.1:5000/")
    print("=" * 50)
    app.run(debug=True)

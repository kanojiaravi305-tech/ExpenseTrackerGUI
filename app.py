# ============================================================
# Expense Tracker - Flask Backend (app.py)
# Subject: Next Generation Database (NGD)
# Purpose: Demonstrates Flask + MongoDB (NoSQL) integration
# ============================================================

from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId
from datetime import datetime

# ------------------------------------------------------------
# Flask App Configuration
# ------------------------------------------------------------
app = Flask(__name__)
app.secret_key = "expense_tracker_secret_key_ngd_project"  # Required for flash messages

# ------------------------------------------------------------
# MongoDB Configuration
# ------------------------------------------------------------
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "expense_tracker_db"
COLLECTION_NAME = "expenses"

# Connect to MongoDB server
client = MongoClient(MONGO_URI)

# Select (or create) the database
db = client[DATABASE_NAME]

# Select (or create) the collection
expenses_collection = db[COLLECTION_NAME]

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
]


# ============================================================
# Route: Home Page (GET /)
# Displays all expenses, the total amount, and the add form.
# Also handles search and category filter via query parameters.
# ============================================================
@app.route("/")
def index():
    # Read optional search and filter query parameters
    search_query = request.args.get("search", "").strip()
    category_filter = request.args.get("category", "").strip()

    # Build a MongoDB query filter
    mongo_filter = {}

    # If the user typed something in the search box, search by title or category
    if search_query:
        mongo_filter["$or"] = [
            {"title": {"$regex": search_query, "$options": "i"}},       # case-insensitive
            {"category": {"$regex": search_query, "$options": "i"}}
        ]

    # If the user selected a specific category from the dropdown
    if category_filter and category_filter != "All":
        mongo_filter["category"] = category_filter

    # Fetch matching expenses from MongoDB, sorted by date (newest first)
    expenses = list(expenses_collection.find(mongo_filter).sort("date", -1))

    # Calculate the total amount of all fetched expenses
    total_amount = sum(expense.get("amount", 0) for expense in expenses)

    # Render the home page template with all data
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
# Receives form data, validates it, and inserts into MongoDB.
# ============================================================
@app.route("/add", methods=["POST"])
def add_expense():
    # Get form data and strip extra whitespace
    title = request.form.get("title", "").strip()
    amount = request.form.get("amount", "").strip()
    category = request.form.get("category", "").strip()
    date = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip()

    # --- Backend Validation ---

    # Check that all required fields are filled
    if not title or not amount or not category or not date:
        flash("Please fill all required fields.", "error")
        return redirect(url_for("index"))

    # Check that amount is a valid positive number
    try:
        amount = float(amount)
        if amount <= 0:
            flash("Amount must be greater than zero.", "error")
            return redirect(url_for("index"))
    except ValueError:
        flash("Amount must be a valid number.", "error")
        return redirect(url_for("index"))

    # Create the expense document to insert into MongoDB
    expense_document = {
        "title": title,
        "amount": amount,
        "category": category,
        "date": date,
        "description": description,
        "created_at": datetime.now()  # Store the current date and time
    }

    # Insert the document into the MongoDB collection
    expenses_collection.insert_one(expense_document)

    flash("Expense added successfully.", "success")
    return redirect(url_for("index"))


# ============================================================
# Route: Edit Expense Page (GET /edit/<expense_id>)
# Fetches the expense from MongoDB and shows it in an edit form.
# ============================================================
@app.route("/edit/<expense_id>")
def edit_expense(expense_id):
    try:
        # Convert the string ID to a MongoDB ObjectId
        obj_id = ObjectId(expense_id)
    except InvalidId:
        # If the ID format is invalid, show an error
        flash("Expense not found.", "error")
        return redirect(url_for("index"))

    # Find the expense document by its _id
    expense = expenses_collection.find_one({"_id": obj_id})

    if not expense:
        # If no document was found with that ID
        flash("Expense not found.", "error")
        return redirect(url_for("index"))

    # Render the edit page with the expense data
    return render_template(
        "edit_expense.html",
        expense=expense,
        categories=CATEGORIES
    )


# ============================================================
# Route: Update Expense (POST /update/<expense_id>)
# Receives updated form data and updates the MongoDB document.
# ============================================================
@app.route("/update/<expense_id>", methods=["POST"])
def update_expense(expense_id):
    try:
        # Convert the string ID to a MongoDB ObjectId
        obj_id = ObjectId(expense_id)
    except InvalidId:
        flash("Expense not found.", "error")
        return redirect(url_for("index"))

    # Get updated form data and strip extra whitespace
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

    # Prepare the updated fields
    updated_data = {
        "$set": {
            "title": title,
            "amount": amount,
            "category": category,
            "date": date,
            "description": description
        }
    }

    # Update the document in MongoDB using its _id
    result = expenses_collection.update_one({"_id": obj_id}, updated_data)

    if result.matched_count == 0:
        flash("Expense not found.", "error")
    else:
        flash("Expense updated successfully.", "success")

    return redirect(url_for("index"))


# ============================================================
# Route: Delete Expense (POST /delete/<expense_id>)
# Deletes the expense document from MongoDB.
# ============================================================
@app.route("/delete/<expense_id>", methods=["POST"])
def delete_expense(expense_id):
    try:
        # Convert the string ID to a MongoDB ObjectId
        obj_id = ObjectId(expense_id)
    except InvalidId:
        flash("Expense not found.", "error")
        return redirect(url_for("index"))

    # Delete the document from MongoDB
    result = expenses_collection.delete_one({"_id": obj_id})

    if result.deleted_count == 0:
        flash("Expense not found.", "error")
    else:
        flash("Expense deleted successfully.", "success")

    return redirect(url_for("index"))


# ============================================================
# Route: Search Expenses (GET /search)
# Redirects to the home page with the search query parameter.
# ============================================================
@app.route("/search")
def search():
    search_query = request.args.get("search", "").strip()
    category_filter = request.args.get("category", "").strip()

    # Redirect to home page with query parameters for filtering
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

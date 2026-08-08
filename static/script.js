// ============================================================
// Expense Tracker - JavaScript (script.js)
// Handles: delete confirmation, form validation, clear button,
//          and auto-setting today's date.
// ============================================================

// ------------------------------------------------------------
// 1. Delete Confirmation
// Called when the user clicks the "Delete" button on any expense.
// Returns true only if the user confirms the action.
// ------------------------------------------------------------
function confirmDelete() {
    return confirm("Are you sure you want to delete this expense?");
}


// ------------------------------------------------------------
// 2. Auto-set Today's Date
// When the page loads, the date field in the Add Expense form
// is automatically set to today's date.
// ------------------------------------------------------------
document.addEventListener("DOMContentLoaded", function () {

    // Get the date input on the Add Expense form (index.html)
    var addForm = document.getElementById("addExpenseForm");
    if (addForm) {
        var dateInput = addForm.querySelector("#date");
        if (dateInput && !dateInput.value) {
            // Get today's date in YYYY-MM-DD format
            var today = new Date();
            var year = today.getFullYear();
            var month = String(today.getMonth() + 1).padStart(2, "0");
            var day = String(today.getDate()).padStart(2, "0");
            dateInput.value = year + "-" + month + "-" + day;
        }
    }

    // --------------------------------------------------------
    // 3. Clear Button
    // Resets all fields in the Add Expense form when clicked.
    // --------------------------------------------------------
    var clearBtn = document.getElementById("clearBtn");
    if (clearBtn) {
        clearBtn.addEventListener("click", function () {
            var form = document.getElementById("addExpenseForm");
            if (form) {
                form.reset();  // Clears all form fields
            }
        });
    }

    // --------------------------------------------------------
    // 4. Client-Side Form Validation (Add Expense Form)
    // Checks required fields and amount before submitting.
    // --------------------------------------------------------
    if (addForm) {
        addForm.addEventListener("submit", function (event) {
            if (!validateExpenseForm(addForm)) {
                event.preventDefault();  // Stop form submission if validation fails
            }
        });
    }

    // --------------------------------------------------------
    // 5. Client-Side Form Validation (Edit Expense Form)
    // Same checks applied on the edit page.
    // --------------------------------------------------------
    var editForm = document.getElementById("editExpenseForm");
    if (editForm) {
        editForm.addEventListener("submit", function (event) {
            if (!validateExpenseForm(editForm)) {
                event.preventDefault();
            }
        });
    }
});


// ============================================================
// validateExpenseForm(form)
// Validates that all required fields are filled and that the
// amount is a positive number.
// Returns true if valid, false otherwise.
// ============================================================
function validateExpenseForm(form) {
    // Get field values and trim whitespace
    var title = form.querySelector("#title").value.trim();
    var amount = form.querySelector("#amount").value.trim();
    var category = form.querySelector("#category").value;
    var date = form.querySelector("#date").value;

    // Check if title is empty
    if (title === "") {
        alert("Please enter the expense title.");
        return false;
    }

    // Check if amount is empty
    if (amount === "") {
        alert("Please enter the expense amount.");
        return false;
    }

    // Check if amount is a valid number and greater than zero
    var amountNum = parseFloat(amount);
    if (isNaN(amountNum) || amountNum <= 0) {
        alert("Amount must be a number greater than zero.");
        return false;
    }

    // Check if a category is selected
    if (category === "" || category === null) {
        alert("Please select a category.");
        return false;
    }

    // Check if date is selected
    if (date === "") {
        alert("Please select a date.");
        return false;
    }

    // All validations passed
    return true;
}

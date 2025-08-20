from flask import Flask, request, jsonify, render_template
import sqlite3
import re

app = Flask(__name__)

# ---------- DB Setup ----------
def init_db():
    conn = sqlite3.connect("g.db")
    c = conn.cursor()

    # Main Form Table
    c.execute('''CREATE TABLE IF NOT EXISTS business (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_name TEXT NOT NULL,
        business_mobile TEXT NOT NULL,
        business_type TEXT NOT NULL,
        timings TEXT NOT NULL,
        owner_name TEXT NOT NULL,
        owner_mobile TEXT NOT NULL,
        location TEXT NOT NULL
    )''')

    # Items Table
    c.execute('''CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_id INTEGER NOT NULL,
        item_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit TEXT NOT NULL,
        buying_price REAL NOT NULL,
        selling_price REAL NOT NULL,
        requirement_type TEXT NOT NULL,
        FOREIGN KEY (business_id) REFERENCES business(id)
    )''')

    conn.commit()
    conn.close()

# Run DB setup on start
init_db()

# ---------- Validation ----------
def validate_mobile(mobile):
    return bool(re.fullmatch(r'[6-9]\d{9}', mobile))

# ---------- Routes ----------
@app.route("/")
def index():
    return render_template("form.html")   # keep your form.html inside templates/


@app.route("/submit", methods=["POST"])
def submit_form():
    data = request.get_json(force=True)
    print("Received data:", data)

    # Extract fields
    business_name = data.get("businessName", "").strip()
    business_mobile = data.get("businessMobile", "").strip()
    owner_name = data.get("ownerName", "").strip()
    owner_mobile = data.get("ownerMobile", "").strip()
    business_type = data.get("type", "").strip()
    timings = data.get("timings", "").strip()
    location = data.get("location", "").strip()

    items = data.get("items", [])

    # Validation
    required_fields = [business_name, business_mobile, business_type, timings, owner_name, owner_mobile, location]
    if any(f == "" for f in required_fields):
        return jsonify({"success": False, "message": "All fields must be filled!"}), 400

    if not validate_mobile(business_mobile) or not validate_mobile(owner_mobile):
        return jsonify({"success": False, "message": "Invalid mobile number(s)."}), 400

    if business_mobile == owner_mobile:
        return jsonify({"success": False, "message": "Business and Owner Mobile must be different."}), 400

    for item in items:
        if not item["itemName"] or not str(item["quantity"]).isdigit() or not item["unit"] \
           or not str(item["buyingPrice"]).replace('.', '', 1).isdigit() \
           or not str(item["sellingPrice"]).replace('.', '', 1).isdigit() \
           or not item["requirementType"]:
            return jsonify({"success": False, "message": "Invalid item entry!"}), 400

    # Save to DB
    try:
        conn = sqlite3.connect("g.db")
        c = conn.cursor()

        # Insert business
        c.execute('''INSERT INTO business 
            (business_name, business_mobile, business_type, timings, owner_name, owner_mobile, location)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (business_name, business_mobile, business_type, timings, owner_name, owner_mobile, location))

        business_id = c.lastrowid

        # Insert items
        for item in items:
            c.execute('''INSERT INTO items 
                (business_id, item_name, quantity, unit, buying_price, selling_price, requirement_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (business_id,
                 item["itemName"],
                 int(item["quantity"]),
                 item["unit"],
                 float(item["buyingPrice"]),
                 float(item["sellingPrice"]),
                 item["requirementType"]))

        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Form submitted successfully!"}), 200

    except Exception as e:
        print("DB Error:", str(e))
        return jsonify({"success": False, "message": "Database error!"}), 500


@app.route("/view")
def view_data():
    conn = sqlite3.connect("g.db")
    c = conn.cursor()
    c.execute("SELECT * FROM business")
    businesses = c.fetchall()
    html = """
    <h2 style='text-align:center;color:#ffcc00;'>Stored Business Data</h2>
    <table border="1" cellpadding="10" cellspacing="0" style="width:95%;margin:auto;background:#222;color:#fff;">
      <tr>
        <th>ID</th><th>Business Name</th><th>Business Mobile</th>
        <th>Business Type</th><th>Timings</th><th>Owner Name</th><th>Owner Mobile</th><th>Location</th><th>Items</th>
      </tr>
    """
    for b in businesses:
        c.execute("SELECT item_name, quantity, unit, buying_price, selling_price, requirement_type FROM items WHERE business_id=?", (b[0],))
        items = c.fetchall()
        items_html = "<ul>"
        for it in items:
            items_html += f"<li>{it[0]} - {it[1]} {it[2]} | Buy ₹{it[3]} | Sell ₹{it[4]} | {it[5]}</li>"
        items_html += "</ul>"
        html += f"""
        <tr>
          <td>{b[0]}</td><td>{b[1]}</td><td>{b[2]}</td>
          <td>{b[3]}</td><td>{b[4]}</td>
          <td>{b[5]}</td><td>{b[6]}</td><td>{b[7]}</td>
          <td>{items_html}</td>
        </tr>
        """
    html += "</table>"
    conn.close()
    return html


if __name__ == "__main__":
    app.run(debug=True)
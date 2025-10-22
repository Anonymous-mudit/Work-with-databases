import os
import time
import shutil
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import customtkinter as ctk
from PIL import Image, ImageTk

# -------------------- NEW DB SETUP --------------------
DB_PATH = "chai_ki_chuski.db"

# Backup existing DB
if os.path.exists(DB_PATH):
    bak_name = f"{DB_PATH}.backup_{int(time.time())}"
    shutil.move(DB_PATH, bak_name)
    print(f"Existing database moved to: {bak_name}")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Create clean schema with date tracking
c.execute("""
CREATE TABLE IF NOT EXISTS menu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    item_name TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    items TEXT,
    status TEXT,
    total REAL,
    created_at TEXT DEFAULT (datetime('now','localtime')),
    order_date DATE DEFAULT (date('now','localtime')),
    FOREIGN KEY(customer_id) REFERENCES customers(id)
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS revenue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    amount REAL,
    created_at TEXT DEFAULT (datetime('now','localtime')),
    revenue_date DATE DEFAULT (date('now','localtime')),
    FOREIGN KEY(order_id) REFERENCES orders(id)
)
""")

conn.commit()
c.execute("SELECT COUNT(*) FROM menu")
if c.fetchone()[0] == 0:
    sample_menu = [
        ("Chai", "Masala Chai", 30, 50),
        ("Chai", "Ginger Chai", 35, 45),
        ("Chai", "Tulsi Chai", 40, 40),
        ("Chai", "Cold Chai", 50, 35),
        ("Snacks", "Samosa", 20, 60),
        ("Snacks", "Kachori", 25, 50),
        ("Snacks", "Pakora", 30, 55),
        ("Drinks", "Lassi", 60, 30),
        ("Drinks", "Smoothie", 80, 25),
    ]
    c.executemany("INSERT INTO menu (category, item_name, price, stock) VALUES (?, ?, ?, ?)", sample_menu)
    conn.commit()

class CafeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🍵 Chai Ki Chuski - Tea & Snacks")
        self.root.geometry("1400x800")
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")

        # Runtime state
        self.current_customer_id = None
        self.item_map = {}

        # Top banner - Warm orange/brown gradient effect
        top = ctk.CTkFrame(root, height=100, corner_radius=0, fg_color="#D4623A")
        top.pack(side="top", fill="x")
        ctk.CTkLabel(top, text="🍵 Chai Ki Chuski", font=("Georgia", 32, "bold"), text_color="white").pack(side="left", padx=20, pady=15)
        ctk.CTkLabel(top, text="Tea & Snacks | Premium Quality", font=("Arial", 14), text_color="#FFE4D1").pack(side="left", padx=20)

        # Sidebar - Warm cream color
        self.sidebar = ctk.CTkFrame(root, width=240, corner_radius=15, fg_color="#F5D5C0")
        self.sidebar.pack(side="left", fill="y", padx=12, pady=12)
        ctk.CTkLabel(self.sidebar, text="📋 Dashboard", font=("Arial", 18, "bold"), text_color="#8B4513").pack(pady=12)
        
        self.add_nav_button("🍵 Menu", self.show_menu)
        self.add_nav_button("➕ Add Item", self.add_menu_item)
        self.add_nav_button("🛒 Orders", self.show_orders)
        self.add_nav_button("📦 Stock", self.show_stock)
        self.add_nav_button("💰 Revenue", self.show_revenue)

        # Main frame - Warm white
        self.main_frame = ctk.CTkFrame(root, corner_radius=15, fg_color="#FFFBF7")
        self.main_frame.pack(side="right", expand=True, fill="both", padx=16, pady=16)
        
        self.show_menu()

    def add_nav_button(self, text, command):
        btn = ctk.CTkButton(self.sidebar, text=text, height=45, corner_radius=10, 
                           fg_color="#D4623A", hover_color="#B84D2E", text_color="white",
                           font=("Arial", 12, "bold"), command=command)
        btn.pack(pady=10, fill="x", padx=10)

    def clear_main(self):
        for w in self.main_frame.winfo_children():
            w.destroy()

    # -------- MENU --------
    def show_menu(self):
        self.clear_main()
        ctk.CTkLabel(self.main_frame, text="🍵 Menu", font=("Georgia", 26, "bold"), text_color="#8B4513").pack(pady=10)

        cols = ("ID", "Category", "Item", "Price (₹)", "Stock")
        self.menu_table = ttk.Treeview(self.main_frame, columns=cols, show="headings", height=18)
        self.menu_table.pack(fill="both", expand=True, padx=12, pady=8)
        
        for col in cols:
            self.menu_table.heading(col, text=col)
            self.menu_table.column(col, anchor="center", width=140)

        self.refresh_menu_table()
        self.menu_table.bind("<Double-1>", self.on_menu_edit)

    def refresh_menu_table(self):
        if not hasattr(self, "menu_table") or not self.menu_table.winfo_exists():
            return
        for r in self.menu_table.get_children():
            self.menu_table.delete(r)
        c.execute("SELECT id, category, item_name, price, stock FROM menu ORDER BY category, item_name")
        for row in c.fetchall():
            _id, cat, name, price, stock = row
            display_stock = stock if stock > 0 else "Out of Stock"
            display_price = f"{price:.2f}"
            self.menu_table.insert("", "end", values=(_id, cat, name, display_price, display_stock))

        self.refresh_order_items()

    def add_menu_item(self):
        popup = ctk.CTkToplevel(self.root)
        popup.title("Add Menu Item")
        popup.geometry("380x360")
        popup.configure(fg_color="#FFFBF7")

        ctk.CTkLabel(popup, text="Item name:", text_color="#8B4513", font=("Arial", 11, "bold")).pack(pady=6)
        name = ctk.CTkEntry(popup); name.pack(pady=6, fill="x", padx=16)

        ctk.CTkLabel(popup, text="Category:", text_color="#8B4513", font=("Arial", 11, "bold")).pack(pady=6)
        cat = ctk.CTkComboBox(popup, values=["Chai","Snacks","Drinks","Food"])
        cat.pack(pady=6, fill="x", padx=16)

        ctk.CTkLabel(popup, text="Price (₹):", text_color="#8B4513", font=("Arial", 11, "bold")).pack(pady=6)
        price = ctk.CTkEntry(popup); price.pack(pady=6, fill="x", padx=16)

        ctk.CTkLabel(popup, text="Initial Stock:", text_color="#8B4513", font=("Arial", 11, "bold")).pack(pady=6)
        stock = ctk.CTkEntry(popup); stock.pack(pady=6, fill="x", padx=16)

        def save():
            nm = name.get().strip()
            ct = cat.get().strip()
            pr = price.get().strip()
            st = stock.get().strip()
            if not nm or not ct or not pr.replace(".","").isdigit() or not st.isdigit():
                messagebox.showerror("Error","Please enter valid values.")
                return
            c.execute("INSERT INTO menu (category,item_name,price,stock) VALUES (?,?,?,?)", 
                     (ct, nm, float(pr), int(st)))
            conn.commit()
            popup.destroy()
            self.refresh_menu_table()
            messagebox.showinfo("Success", f"'{nm}' added to menu.")

        ctk.CTkButton(popup, text="Save Item", fg_color="#D4623A", hover_color="#B84D2E", 
                     command=save).pack(pady=12)

    def on_menu_edit(self, event):
        sel = self.menu_table.selection()
        if not sel: return
        vals = self.menu_table.item(sel[0], "values")
        item_id = vals[0]
        
        popup = ctk.CTkToplevel(self.root)
        popup.title("Edit Menu Item")
        popup.geometry("500x580")
        popup.configure(fg_color="#FFFBF7")

        ctk.CTkLabel(popup, text="Item name:", text_color="#8B4513", font=("Arial", 11, "bold")).pack(pady=6)
        name = ctk.CTkEntry(popup); name.insert(0, vals[2]); name.pack(pady=6, fill="x", padx=16)

        ctk.CTkLabel(popup, text="Category:", text_color="#8B4513", font=("Arial", 11, "bold")).pack(pady=6)
        cat = ctk.CTkComboBox(popup, values=["Chai","Snacks","Drinks","Food"])
        cat.set(vals[1]); cat.pack(pady=6, fill="x", padx=16)

        ctk.CTkLabel(popup, text="Price (₹):", text_color="#8B4513", font=("Arial", 11, "bold")).pack(pady=6)
        price = ctk.CTkEntry(popup)
        price.insert(0, str(vals[3] if vals[3]!="Out of Stock" else ""))
        price.pack(pady=6, fill="x", padx=16)

        ctk.CTkLabel(popup, text="Stock:", text_color="#8B4513", font=("Arial", 11, "bold")).pack(pady=6)
        stock = ctk.CTkEntry(popup)
        stock.insert(0, str(vals[4] if vals[4]!="Out of Stock" else "0"))
        stock.pack(pady=6, fill="x", padx=16)

        def save_edit():
            nm = name.get().strip()
            ct = cat.get().strip()
            pr = price.get().strip()
            st = stock.get().strip()
            if not nm or not ct or not pr.replace(".","").isdigit() or not st.isdigit():
                messagebox.showerror("Error","Invalid input.")
                return
            c.execute("UPDATE menu SET item_name=?, category=?, price=?, stock=? WHERE id=?", 
                     (nm, ct, float(pr), int(st), item_id))
            conn.commit()
            popup.destroy()
            self.refresh_menu_table()
            messagebox.showinfo("Saved", f"'{nm}' updated.")

        ctk.CTkButton(popup, text="Update", fg_color="#D4623A", hover_color="#B84D2E", 
                     command=save_edit).pack(pady=12)

    # -------- STOCK --------
    def show_stock(self):
        self.clear_main()
        ctk.CTkLabel(self.main_frame, text="📦 Stock Management", font=("Georgia", 26, "bold"), text_color="#8B4513").pack(pady=10)

        cols = ("ID","Category","Item","Stock")
        self.stock_table = ttk.Treeview(self.main_frame, columns=cols, show="headings", height=18)
        self.stock_table.pack(fill="both", expand=True, padx=12, pady=8)
        
        for col in cols:
            self.stock_table.heading(col, text=col)
            self.stock_table.column(col, anchor="center", width=200)
        
        self.refresh_stock_table()

        btn = ctk.CTkButton(self.main_frame, text="🔄 Update Selected Stock", 
                           fg_color="#D4623A", hover_color="#B84D2E",
                           command=self.update_stock_selected)
        btn.pack(pady=10)

    def refresh_stock_table(self):
        if not hasattr(self, "stock_table") or not self.stock_table.winfo_exists():
            return
        for r in self.stock_table.get_children():
            self.stock_table.delete(r)
        c.execute("SELECT id, category, item_name, stock FROM menu ORDER BY category, item_name")
        for row in c.fetchall():
            _id, cat, name, stock = row
            display_stock = stock if stock>0 else "Out of Stock"
            self.stock_table.insert("", "end", values=(_id, cat, name, display_stock))

    def update_stock_selected(self):
        sel = self.stock_table.selection()
        if not sel:
            messagebox.showerror("Error", "Select an item first")
            return
        vals = self.stock_table.item(sel[0], "values")
        item_id, cat, name, stock = vals
        current = 0 if stock == "Out of Stock" else int(stock)

        popup = ctk.CTkToplevel(self.root)
        popup.title("Add Stock")
        popup.geometry("340x180")
        popup.configure(fg_color="#FFFBF7")

        ctk.CTkLabel(popup, text=f"{name} | Current: {current}", text_color="#8B4513", 
                    font=("Arial", 12, "bold")).pack(pady=8)
        inc = ctk.CTkEntry(popup, placeholder_text="Enter quantity to add")
        inc.pack(pady=8, fill="x", padx=12)

        def do_add():
            v = inc.get().strip()
            if not v.isdigit():
                messagebox.showerror("Error","Enter a valid integer")
                return
            new_total = current + int(v)
            c.execute("UPDATE menu SET stock=? WHERE id=?", (new_total, item_id))
            conn.commit()
            popup.destroy()
            self.refresh_stock_table()
            self.refresh_menu_table()
            messagebox.showinfo("Success", f"{name} stock updated to {new_total}")

        ctk.CTkButton(popup, text="Add", fg_color="#D4623A", hover_color="#B84D2E", 
                     command=do_add).pack(pady=8)

    # -------- ORDERS --------
    def show_orders(self):
        self.clear_main()
        ctk.CTkLabel(self.main_frame, text="🛒 Orders", font=("Georgia", 26, "bold"), text_color="#8B4513").pack(pady=6)
        self.cart = []
        self.ask_customer_info()

    def ask_customer_info(self):
        popup = ctk.CTkToplevel(self.root)
        popup.title("Customer Details")
        popup.geometry("440x360")
        popup.configure(fg_color="#FFFBF7")

        ctk.CTkLabel(popup, text="Enter Customer Details", font=("Arial", 14, "bold"), text_color="#8B4513").pack(pady=8)
        
        ctk.CTkLabel(popup, text="Name *", text_color="#8B4513", font=("Arial", 11, "bold")).pack(pady=6)
        name_ent = ctk.CTkEntry(popup); name_ent.pack(fill="x", padx=20)
        
        ctk.CTkLabel(popup, text="Phone *", text_color="#8B4513", font=("Arial", 11, "bold")).pack(pady=6)
        phone_ent = ctk.CTkEntry(popup); phone_ent.pack(fill="x", padx=20)
        
        ctk.CTkLabel(popup, text="Email", text_color="#8B4513", font=("Arial", 11, "bold")).pack(pady=6)
        email_ent = ctk.CTkEntry(popup); email_ent.pack(fill="x", padx=20)

        def save_customer():
            nm = name_ent.get().strip()
            ph = phone_ent.get().strip()
            em = email_ent.get().strip()
            if not nm or not ph:
                messagebox.showerror("Error", "Name and Phone are required")
                return
            c.execute("INSERT INTO customers (name, phone, email) VALUES (?,?,?)", (nm, ph, em))
            conn.commit()
            self.current_customer_id = c.lastrowid
            popup.destroy()
            self.build_order_form()

        ctk.CTkButton(popup, text="Save & Continue", fg_color="#D4623A", hover_color="#B84D2E", 
                     command=save_customer).pack(pady=12)

    def build_order_form(self):
        form = ctk.CTkFrame(self.main_frame)
        form.pack(pady=10, fill="x", padx=8)
        
        ctk.CTkLabel(form, text="Item:", text_color="#8B4513", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=8, pady=6)
        ctk.CTkLabel(form, text="Qty:", text_color="#8B4513", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=8, pady=6)

        self.item_box = ctk.CTkComboBox(form, values=[])
        self.item_box.grid(row=0, column=1, padx=8, pady=6, sticky="we")
        
        self.qty_entry = ctk.CTkEntry(form, width=80)
        self.qty_entry.grid(row=0, column=3, padx=8, pady=6)

        ctk.CTkButton(form, text="➕ Add to Cart", fg_color="#D4623A", hover_color="#B84D2E",
                     command=self.add_to_cart).grid(row=0, column=4, padx=8)
        ctk.CTkButton(form, text="✅ Confirm Order", fg_color="#228B22", hover_color="#1a6b1a",
                     command=self.confirm_order).grid(row=0, column=5, padx=8)

        self.cart_box = ctk.CTkTextbox(self.main_frame, width=700, height=140)
        self.cart_box.pack(pady=8)
        self.cart_box.configure(state="disabled")

        cols = ("ID", "Date", "Customer", "Items", "Status", "Total ₹")
        self.orders_table = ttk.Treeview(self.main_frame, columns=cols, show="headings", height=10)
        self.orders_table.pack(fill="both", expand=True, padx=8, pady=6)

        for col in cols:
            self.orders_table.heading(col, text=col)
            self.orders_table.column(col, anchor="center", width=110)

        btn_frame = ctk.CTkFrame(self.main_frame)
        btn_frame.pack(pady=8)
        ctk.CTkButton(btn_frame, text="🧾 Generate Bill", fg_color="#D4623A", hover_color="#B84D2E",
                     command=self.generate_bill).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="✔ Mark Complete", fg_color="#228B22", hover_color="#1a6b1a",
                     command=self.mark_complete).pack(side="left", padx=8)

        self.refresh_order_items()
        self.load_orders()

    def refresh_order_items(self):
        self.item_map = {}
        c.execute("SELECT id, item_name, price, stock FROM menu WHERE stock>0 ORDER BY item_name")
        rows = c.fetchall()
        display_values = []
        for _id, name, price, stock in rows:
            display = f"{name} — ₹{price:.2f} (Avail: {stock})"
            self.item_map[display] = (_id, name, float(price))
            display_values.append(display)
        
        if hasattr(self, "item_box") and self.item_box.winfo_exists():
            self.item_box.configure(values=display_values)
            if display_values:
                self.item_box.set(display_values[0])

    def add_to_cart(self):
        sel = self.item_box.get()
        qty_s = self.qty_entry.get().strip()
        if not sel or not qty_s.isdigit():
            messagebox.showerror("Error", "Select item and enter numeric quantity")
            return
        qty = int(qty_s)
        if sel not in self.item_map:
            messagebox.showerror("Error", "Selected item is not available")
            return
        
        item_id, name, price = self.item_map[sel]
        c.execute("SELECT stock FROM menu WHERE id=?", (item_id,))
        cur_stock = c.fetchone()[0]
        if qty > cur_stock:
            messagebox.showerror("Error", f"Not enough stock (Available: {cur_stock})")
            return
        
        total = round(qty * price, 2)
        self.cart.append({"id": item_id, "name": name, "qty": qty, "price": price, "total": total})
        
        self.cart_box.configure(state="normal")
        self.cart_box.delete("1.0", "end")
        for i, it in enumerate(self.cart, 1):
            self.cart_box.insert("end", f"{i}. {it['name']} x{it['qty']} = ₹{it['total']:.2f}\n")
        self.cart_box.configure(state="disabled")
        self.qty_entry.delete(0, "end")
        self.refresh_order_items()

    def confirm_order(self):
        if not self.current_customer_id:
            messagebox.showerror("Error", "No customer selected")
            return
        if not self.cart:
            messagebox.showerror("Error", "Cart is empty")
            return
        
        items_summary = ", ".join([f"{it['name']} x{it['qty']}" for it in self.cart])
        total_bill = round(sum(it['total'] for it in self.cart), 2)

        try:
            for it in self.cart:
                c.execute("SELECT stock FROM menu WHERE id=?", (it['id'],))
                cur = c.fetchone()
                if not cur or it['qty'] > cur[0]:
                    raise Exception(f"Not enough stock for {it['name']}.")
                c.execute("UPDATE menu SET stock = stock - ? WHERE id=?", (it['qty'], it['id']))

            c.execute("INSERT INTO orders (customer_id, items, status, total) VALUES (?,?,?,?)",
                     (self.current_customer_id, items_summary, "Pending", total_bill))
            order_id = c.lastrowid
            c.execute("INSERT INTO revenue (order_id, amount) VALUES (?,?)", (order_id, total_bill))
            conn.commit()
        except Exception as ex:
            conn.rollback()
            messagebox.showerror("Error", f"Could not confirm order: {ex}")
            return

        self.cart = []
        self.cart_box.configure(state="normal")
        self.cart_box.delete("1.0","end")
        self.cart_box.configure(state="disabled")
        self.refresh_menu_table()
        self.refresh_stock_table()
        self.refresh_order_items()
        self.load_orders()
        messagebox.showinfo("Order", f"Order confirmed — Total ₹{total_bill:.2f}")

    def load_orders(self):
        if not hasattr(self, "orders_table") or not self.orders_table.winfo_exists():
            return
        for r in self.orders_table.get_children():
            self.orders_table.delete(r)
        c.execute("""
            SELECT o.id, o.order_date, co.name, o.items, o.status, o.total
            FROM orders o
            LEFT JOIN customers co ON o.customer_id = co.id
            ORDER BY o.id DESC
        """)
        for row in c.fetchall():
            self.orders_table.insert("", "end", values=row)

    def mark_complete(self):
        sel = self.orders_table.selection()
        if not sel:
            messagebox.showerror("Error", "Select at least one order")
            return
        ids = []
        for s in sel:
            vals = self.orders_table.item(s, "values")
            ids.append(vals[0])
        for oid in ids:
            c.execute("UPDATE orders SET status='Completed' WHERE id=?", (oid,))
        conn.commit()
        self.load_orders()
        messagebox.showinfo("Success", "Orders marked Completed")

    def generate_bill(self):
        sel = self.orders_table.selection()
        if not sel:
            messagebox.showerror("Error", "Select one order to generate bill")
            return
        
        for s in sel:
            vals = self.orders_table.item(s, "values")
            order_id, order_date, customer_name, items, status, total = vals
            
            c.execute("SELECT co.phone, co.email FROM orders o LEFT JOIN customers co ON o.customer_id = co.id WHERE o.id=?", 
                     (order_id,))
            cust = c.fetchone()
            phone = cust[0] if cust else ""
            email = cust[1] if cust else ""

            popup = ctk.CTkToplevel(self.root)
            popup.title(f"Bill - Order {order_id}")
            popup.geometry("450x520")
            popup.configure(fg_color="#FFFBF7")

            header = f"🍵 Chai Ki Chuski\nOrder ID: {order_id}\nDate: {order_date}\n"
            cust_info = f"Customer: {customer_name}\nPhone: {phone or '-'}\nEmail: {email or '-'}\n\n"
            body = f"Items:\n{items}\n\n"
            tot = f"Total: ₹{float(total):.2f}\n\n"

            textbox = ctk.CTkTextbox(popup, width=410, height=400)
            textbox.pack(pady=10, padx=10)
            textbox.configure(state="normal")
            textbox.insert("end", header)
            textbox.insert("end", cust_info)
            textbox.insert("end", body)
            textbox.insert("end", tot)
            textbox.configure(state="disabled")

            ctk.CTkButton(popup, text="Close", fg_color="#D4623A", hover_color="#B84D2E",
                         command=popup.destroy).pack(pady=10)

    # -------- REVENUE (DATE-BASED) --------
    def show_revenue(self):
        self.clear_main()
        ctk.CTkLabel(self.main_frame, text="💰 Revenue Tracker", font=("Georgia", 26, "bold"), text_color="#8B4513").pack(pady=10)

        # Filter buttons frame
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="#F5D5C0")
        btn_frame.pack(pady=10, fill="x", padx=8)

        ctk.CTkLabel(btn_frame, text="Filter by:", text_color="#8B4513", font=("Arial", 11, "bold")).pack(side="left", padx=10)
        
        ctk.CTkButton(btn_frame, text="Today", width=80, fg_color="#D4623A", hover_color="#B84D2E",
                     command=lambda: self.display_revenue("today")).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Yesterday", width=80, fg_color="#D4623A", hover_color="#B84D2E",
                     command=lambda: self.display_revenue("yesterday")).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="This Week", width=80, fg_color="#D4623A", hover_color="#B84D2E",
                     command=lambda: self.display_revenue("week")).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="This Month", width=90, fg_color="#D4623A", hover_color="#B84D2E",
                     command=lambda: self.display_revenue("month")).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="This Year", width=80, fg_color="#D4623A", hover_color="#B84D2E",
                     command=lambda: self.display_revenue("year")).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="All Time", width=80, fg_color="#D4623A", hover_color="#B84D2E",
                     command=lambda: self.display_revenue("all")).pack(side="left", padx=5)

        # Revenue stats frame
        self.revenue_frame = ctk.CTkFrame(self.main_frame, fg_color="white")
        self.revenue_frame.pack(fill="both", expand=True, padx=8, pady=8)

    def display_revenue(self, period):
        # Clear previous content
        for w in self.revenue_frame.winfo_children():
            w.destroy()

        today = datetime.now().date()
        
        if period == "today":
            start_date = today
            end_date = today
            period_name = "Today"
        elif period == "yesterday":
            start_date = today - timedelta(days=1)
            end_date = start_date
            period_name = "Yesterday"
        elif period == "week":
            start_date = today - timedelta(days=today.weekday())
            end_date = today
            period_name = "This Week"
        elif period == "month":
            start_date = today.replace(day=1)
            end_date = today
            period_name = "This Month"
        elif period == "year":
            start_date = today.replace(month=1, day=1)
            end_date = today
            period_name = "This Year"
        else:  # all
            start_date = None
            end_date = None
            period_name = "All Time"

        # Query revenue
        if start_date:
            c.execute("""
                SELECT SUM(amount), COUNT(*), revenue_date
                FROM revenue
                WHERE revenue_date BETWEEN ? AND ?
                GROUP BY revenue_date
                ORDER BY revenue_date DESC
            """, (str(start_date), str(end_date)))
        else:
            c.execute("""
                SELECT SUM(amount), COUNT(*), revenue_date
                FROM revenue
                GROUP BY revenue_date
                ORDER BY revenue_date DESC
            """)
        
        rows = c.fetchall()
        total_revenue = sum(row[0] for row in rows if row[0])
        total_orders = sum(row[1] for row in rows if row[1])

        # Display total stats
        stats_frame = ctk.CTkFrame(self.revenue_frame, fg_color="#F5D5C0", corner_radius=10)
        stats_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(stats_frame, text=f"📊 {period_name} Revenue", 
                    font=("Arial", 16, "bold"), text_color="#8B4513").pack(pady=8)
        ctk.CTkLabel(stats_frame, text=f"Total Revenue: ₹{total_revenue:.2f}", 
                    font=("Arial", 18, "bold"), text_color="#228B22").pack(pady=5)
        ctk.CTkLabel(stats_frame, text=f"Total Orders: {total_orders}", 
                    font=("Arial", 14), text_color="#D4623A").pack(pady=5)
        if total_orders > 0:
            avg = total_revenue / total_orders
            ctk.CTkLabel(stats_frame, text=f"Average per Order: ₹{avg:.2f}", 
                        font=("Arial", 14), text_color="#8B4513").pack(pady=5)

        # Display detailed table
        ctk.CTkLabel(self.revenue_frame, text="Daily Breakdown:", 
                    font=("Arial", 14, "bold"), text_color="#8B4513").pack(anchor="w", padx=10, pady=5)

        cols = ("Date", "Orders", "Revenue (₹)")
        self.revenue_table = ttk.Treeview(self.revenue_frame, columns=cols, show="headings", height=15)
        self.revenue_table.pack(fill="both", expand=True, padx=10, pady=5)

        for col in cols:
            self.revenue_table.heading(col, text=col)
            self.revenue_table.column(col, anchor="center", width=180)

        for row in rows:
            if row[0]:
                self.revenue_table.insert("", "end", values=(row[2], row[1], f"₹{row[0]:.2f}"))

# -------------------- RUN --------------------
if __name__ == "__main__":
    root = ctk.CTk()
    app = CafeApp(root)
    root.mainloop()

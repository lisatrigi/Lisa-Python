# StringMaster Guitar Shop

An online guitar shop application built with **FastAPI** (backend) and **Streamlit** (frontend).

## Features

### Customer Features
- Browse guitars by category (Electric, Acoustic, Bass, Classical)
- View detailed guitar specifications
- Add guitars to cart and checkout
- View order history
- See discounted prices when promotions are active

### Admin Features
- View online users in real-time
- Receive purchase notifications when customers buy guitars
- Manage inventory (add, edit, delete guitars)
- Apply discounts by brand, type, or specific guitar
- View statistics and charts (sales, inventory by brand, stock levels)
- Manage user accounts


**Navigate to the project folder:**
   terminal: 
   cd scripts/guitar_shop OR cd Lisa-Python-main/scripts/guitar_shop
   pip install -r requirements.txt 
   

   pip install python-dotenv


   uvicorn main:app --reload --port 8000
   The backend will be available at `http://localhost:8000`

   streamlit run app.py
   The frontend will be available at `http://localhost:8501`

### Admin Account
| Field    | Value              |
|----------|--------------------|
| Username | `Admin`            |
| Password | `Admin123`         |

### Creating New Accounts
- **Customers**: Use the "Register" form on the login page
- **Admins**: Register via the API at `/api/register` with `"role": "admin"`

---

## User Guide

### For Customers

1. **Register/Login**: Create an account or login at the homepage
2. **Browse Guitars**: 
   - Click on a category (Electric, Acoustic, Bass, Classical)
   - View only guitars of that specific type
3. **View Details**: Click "Details" to see full guitar specifications
4. **Add to Cart**: Click "Add to Cart" on any guitar you want to purchase
5. **Checkout**: Go to your cart and complete the purchase
6. **Order History**: View your past purchases in the Orders section

---

## Admin Guide

### Accessing the Admin Dashboard

1. Login with admin credentials (`Admin` / `Admin123`)
2. You will be automatically redirected to the Admin Dashboard

### Admin Dashboard Sections

#### Online Users
- See all customers currently logged into the system
- View their last login time

#### Purchase Notifications
- Receive real-time alerts when customers make purchases
- See order details (customer, guitar, price)
- Mark notifications as read

#### Inventory Management
- View all guitars in stock
- Edit guitar details (price, stock, specifications)
- Delete guitars from inventory

#### Add New Guitar
- Fill out the form to add a new guitar
- Specify type, brand, model, price, stock, and specifications

#### Discounts
- **By Brand**: Apply percentage discount to all guitars of a brand (e.g., 20% off all Fender)
- **By Type**: Apply discount to all guitars of a type (e.g., 15% off all Electric)
- **Specific Guitar**: Apply discount to a single guitar
- **Clear Discounts**: Remove all active discounts

#### Statistics
- **Guitars by Brand**: Pie chart showing inventory distribution
- **Guitars by Type**: Bar chart of guitar categories
- **Stock Levels**: Overview of inventory quantities
- **Sales Data**: Revenue and order statistics

#### User Management
- View all registered users
- See user roles (admin/customer)
- Manage user accounts

---

## API Documentation

FastAPI provides automatic interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key API Endpoints

| Method | Endpoint                  | Description                    |
|--------|---------------------------|--------------------------------|
| POST   | `/api/login`              | User login                     |
| POST   | `/api/register`           | User registration              |
| GET    | `/api/guitars`            | List all guitars               |
| GET    | `/api/guitars/{id}`       | Get guitar details             |
| GET    | `/api/guitars/type/{type}`| Get guitars by type            |
| POST   | `/api/purchase`           | Purchase a guitar              |
| GET    | `/api/admin/online-users` | Get online users (admin only)  |
| GET    | `/api/admin/notifications`| Get purchase notifications     |
| POST   | `/api/admin/guitars`      | Add new guitar (admin only)    |
| POST   | `/api/admin/discounts`    | Apply discounts (admin only)   |

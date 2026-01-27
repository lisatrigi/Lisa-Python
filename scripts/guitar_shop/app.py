"""
StringMaster Guitar Shop - Streamlit Frontend
Displays and interacts with the FastAPI backend
All business logic is handled by FastAPI - Streamlit only handles UI
"""

import streamlit as st
import requests
from typing import Optional

# ==================== CONFIGURATION ====================

API_BASE_URL = "http://localhost:8000/api"

# ==================== PAGE CONFIG ====================

st.set_page_config(
    page_title="StringMaster Guitar Shop",
    page_icon="https://placeholder.svg?height=32&width=32&query=guitar+icon",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS ====================

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1a1a2e;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .guitar-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .price-tag {
        font-size: 1.5rem;
        color: #2d6a4f;
        font-weight: bold;
    }
    
    .stock-good { color: #2d6a4f; }
    .stock-low { color: #e76f51; }
    .stock-out { color: #9d0208; }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE ====================

if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"
if "cart" not in st.session_state:
    st.session_state.cart = {}


# ==================== API HELPER FUNCTIONS ====================

def api_request(method: str, endpoint: str, data: dict = None, auth: bool = False) -> Optional[dict]:
    """Make API request to FastAPI backend"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {}
    
    if auth and st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=data)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            return None
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            error = response.json().get("detail", "Unknown error")
            st.error(f"Error: {error}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Please ensure FastAPI server is running on port 8000.")
        return None
    except Exception as e:
        st.error(f"Request failed: {str(e)}")
        return None


def logout():
    """Clear session and logout"""
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.cart = {}
    st.session_state.page = "login"


def get_cart_summary():
    """Calculate cart totals from local cart"""
    cart = st.session_state.cart
    total_items = sum(item["quantity"] for item in cart.values())
    total_price = sum(item["guitar"]["price"] * item["quantity"] for item in cart.values())
    return total_items, total_price


# ==================== LOGIN PAGE ====================

def show_login_page():
    """Display login/register page - REQUIRED before shopping"""
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>StringMaster</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666;'>Premium Guitars Since 2024</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        tab_login, tab_register = st.tabs(["Login", "Register"])
        
        with tab_login:
            st.subheader("Welcome Back")
            
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login", type="primary", use_container_width=True)
                
                if submit:
                    if not username or not password:
                        st.error("Please enter username and password")
                    else:
                        # Call FastAPI login endpoint
                        result = api_request("POST", "/auth/login", {
                            "username": username,
                            "password": password
                        })
                        
                        if result:
                            st.session_state.token = result["access_token"]
                            st.session_state.user = result["user"]
                            st.session_state.page = "catalog"
                            st.success("Login successful!")
                            st.rerun()
            
            st.markdown("---")
            st.info("Demo accounts: **admin/Admin123** or register a new account")
        
        with tab_register:
            st.subheader("Create Account")
            
            with st.form("register_form"):
                reg_username = st.text_input("Username", key="reg_user")
                reg_email = st.text_input("Email", key="reg_email")
                reg_password = st.text_input("Password", type="password", key="reg_pass")
                reg_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
                
                submit_reg = st.form_submit_button("Create Account", type="primary", use_container_width=True)
                
                if submit_reg:
                    errors = []
                    
                    if not all([reg_username, reg_email, reg_password, reg_confirm]):
                        errors.append("All fields are required")
                    
                    if reg_password != reg_confirm:
                        errors.append("Passwords do not match")
                    
                    if errors:
                        for error in errors:
                            st.error(error)
                    else:
                        # Call FastAPI register endpoint
                        result = api_request("POST", "/auth/register", {
                            "username": reg_username,
                            "email": reg_email,
                            "password": reg_password
                        })
                        
                        if result:
                            st.success("Account created! Please login.")
            
            st.markdown("---")
            st.caption("Password requirements: 6+ characters, uppercase, lowercase, and digit")


# ==================== CATALOG PAGE ====================

def show_catalog():
    """Display guitar catalog with filters - fetches from FastAPI"""
    
    st.markdown("<h1 class='main-header'>Guitar Catalog</h1>", unsafe_allow_html=True)
    
    # Sidebar filters
    with st.sidebar:
        st.header("Filters")
        
        # Price range
        price_range = st.slider(
            "Price Range ($)",
            min_value=0,
            max_value=5000,
            value=(0, 5000),
            step=100
        )
        
        # Guitar type - fetch categories from API
        categories = api_request("GET", "/categories")
        type_options = ["All Types"]
        if categories:
            type_options += [cat["name"] for cat in categories]
        selected_type = st.selectbox("Guitar Type", type_options)
        
        # In stock only
        in_stock_only = st.checkbox("In Stock Only", value=True)
        
        st.markdown("---")
        
        # Cart summary in sidebar
        total_items, total_price = get_cart_summary()
        if total_items > 0:
            st.subheader("Cart Summary")
            st.metric("Items", total_items)
            st.metric("Total", f"${total_price:,.2f}")
            if st.button("View Cart", type="primary", use_container_width=True):
                st.session_state.page = "cart"
                st.rerun()
    
    # Build query parameters for API
    params = {
        "min_price": price_range[0],
        "max_price": price_range[1],
        "in_stock": in_stock_only
    }
    
    if selected_type != "All Types":
        params["guitar_type"] = selected_type.lower()
    
    # Fetch guitars from FastAPI
    guitars = api_request("GET", "/guitars", params)
    
    if guitars is None:
        st.warning("Unable to load guitars. Please check if the API is running.")
        return
    
    st.subheader(f"Showing {len(guitars)} guitars")
    
    if not guitars:
        st.info("No guitars match your filters. Try adjusting the criteria.")
        return
    
    # Display guitars in grid
    cols = st.columns(3)
    
    for idx, guitar in enumerate(guitars):
        with cols[idx % 3]:
            with st.container():
                st.image(
                    guitar.get("image_url") or f"https://placeholder.svg?height=200&width=300&query={guitar['brand']}+{guitar['guitar_type']}+guitar",
                    use_container_width=True
                )
                
                st.markdown(f"### {guitar['brand']} {guitar['name']}")
                st.caption(f"Type: {guitar['guitar_type'].capitalize()}")
                st.markdown(f"_{guitar.get('description', '')}_")
                
                st.markdown(f"<p class='price-tag'>${guitar['price']:,.2f}</p>", unsafe_allow_html=True)
                
                stock = guitar['stock']
                if stock > 10:
                    st.success(f"In Stock: {stock} available")
                elif stock > 0:
                    st.warning(f"Low Stock: {stock} left")
                else:
                    st.error("Out of Stock")
                
                # Add to cart button
                if stock > 0:
                    if st.button(f"Add to Cart", key=f"add_{guitar['id']}", use_container_width=True):
                        guitar_id = str(guitar['id'])
                        if guitar_id in st.session_state.cart:
                            current_qty = st.session_state.cart[guitar_id]["quantity"]
                            if current_qty < stock:
                                st.session_state.cart[guitar_id]["quantity"] += 1
                                st.success(f"Added another {guitar['name']}!")
                            else:
                                st.warning("Maximum stock reached")
                        else:
                            st.session_state.cart[guitar_id] = {
                                "guitar": guitar,
                                "quantity": 1
                            }
                            st.success(f"Added {guitar['brand']} {guitar['name']} to cart!")
                        st.rerun()
                else:
                    st.button("Out of Stock", key=f"oos_{guitar['id']}", disabled=True, use_container_width=True)
                
                st.markdown("---")


# ==================== CART PAGE ====================

def show_cart():
    """Display shopping cart and checkout"""
    
    st.markdown("<h1 class='main-header'>Shopping Cart</h1>", unsafe_allow_html=True)
    
    cart = st.session_state.cart
    
    if not cart:
        st.info("Your cart is empty. Browse our catalog to add guitars!")
        if st.button("Browse Catalog", type="primary"):
            st.session_state.page = "catalog"
            st.rerun()
        return
    
    # Display cart items
    for guitar_id, item in list(cart.items()):
        guitar = item["guitar"]
        quantity = item["quantity"]
        
        col1, col2, col3, col4, col5 = st.columns([1, 3, 1, 1, 1])
        
        with col1:
            st.image(
                guitar.get("image_url") or f"https://placeholder.svg?height=80&width=80&query={guitar['brand']}+guitar",
                width=80
            )
        
        with col2:
            st.markdown(f"**{guitar['brand']} {guitar['name']}**")
            st.caption(f"{guitar['guitar_type'].capitalize()}")
        
        with col3:
            st.markdown(f"**${guitar['price']:,.2f}**")
        
        with col4:
            new_qty = st.number_input(
                "Qty",
                min_value=1,
                max_value=guitar['stock'],
                value=quantity,
                key=f"qty_{guitar_id}",
                label_visibility="collapsed"
            )
            if new_qty != quantity:
                st.session_state.cart[guitar_id]["quantity"] = new_qty
                st.rerun()
        
        with col5:
            if st.button("Remove", key=f"remove_{guitar_id}"):
                del st.session_state.cart[guitar_id]
                st.rerun()
        
        st.markdown("---")
    
    # Cart summary
    st.markdown("### Order Summary")
    
    total_items, total_price = get_cart_summary()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"**Total Items:** {total_items}")
        
        for item in cart.values():
            guitar = item["guitar"]
            qty = item["quantity"]
            st.caption(f"{guitar['brand']} {guitar['name']} x{qty} = ${guitar['price'] * qty:,.2f}")
    
    with col2:
        st.markdown(f"## ${total_price:,.2f}")
        
        if st.button("Checkout / Purchase", type="primary", use_container_width=True):
            # First add items to API cart, then purchase
            for guitar_id, item in cart.items():
                api_request("POST", "/guitars/cart/add", {
                    "guitar_id": int(guitar_id),
                    "quantity": item["quantity"]
                }, auth=True)
            
            # Call purchase endpoint
            result = api_request("POST", "/guitars/purchase", auth=True)
            
            if result:
                st.session_state.cart = {}
                st.success(f"Order #{result.get('order_id')} placed successfully!")
                st.balloons()
        
        if st.button("Continue Shopping", use_container_width=True):
            st.session_state.page = "catalog"
            st.rerun()


# ==================== CATEGORIES PAGE ====================

def show_categories():
    """Display guitar categories - fetches from FastAPI"""
    
    st.markdown("<h1 class='main-header'>Guitar Categories</h1>", unsafe_allow_html=True)
    
    categories = api_request("GET", "/categories")
    
    if not categories:
        st.warning("Unable to load categories.")
        return
    
    cols = st.columns(2)
    
    category_images = {
        "Electric": "https://placeholder.svg?height=200&width=300&query=electric+guitar+collection",
        "Acoustic": "https://placeholder.svg?height=200&width=300&query=acoustic+guitar+collection",
        "Bass": "https://placeholder.svg?height=200&width=300&query=bass+guitar+collection",
        "Classical": "https://placeholder.svg?height=200&width=300&query=classical+guitar+collection"
    }
    
    for idx, category in enumerate(categories):
        with cols[idx % 2]:
            with st.container():
                st.image(
                    category_images.get(category["name"], "https://placeholder.svg?height=200&width=300&query=guitar"),
                    use_container_width=True
                )
                st.markdown(f"### {category['name']} Guitars")
                st.markdown(f"_{category.get('description', '')}_")
                
                # Get guitar count for this category
                cat_guitars = api_request("GET", f"/categories/{category['id']}/guitars")
                if cat_guitars:
                    st.caption(f"{cat_guitars.get('count', 0)} guitars available")
                
                if st.button(f"Browse {category['name']}", key=f"cat_{category['id']}", use_container_width=True):
                    st.session_state.page = "catalog"
                    st.rerun()
                
                st.markdown("---")


# ==================== PROFILE PAGE ====================

def show_profile():
    """Display user profile and order history"""
    
    st.markdown("<h1 class='main-header'>My Profile</h1>", unsafe_allow_html=True)
    
    user = st.session_state.user
    
    if not user:
        st.warning("Please login to view your profile.")
        return
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image(
            "https://placeholder.svg?height=150&width=150&query=user+avatar",
            width=150
        )
        st.markdown(f"### {user['username']}")
        st.caption(f"{'Administrator' if user['role'] == 'admin' else 'Customer'}")
    
    with col2:
        st.markdown("#### Account Details")
        st.markdown(f"**Email:** {user['email']}")
        st.markdown(f"**Account Type:** {user['role'].capitalize()}")
    
    st.markdown("---")
    
    # Order history from API
    st.subheader("Order History")
    
    orders = api_request("GET", "/guitars/orders/history", auth=True)
    
    if orders and orders.get("orders"):
        for order in orders["orders"]:
            with st.expander(f"Order #{order['id']} - ${order['total']:,.2f} ({order['status'].upper()})"):
                st.markdown(f"**Date:** {order['created_at']}")
                st.markdown("**Items:**")
                for item in order['items']:
                    st.markdown(f"- {item['guitar_name']} x{item['quantity']} @ ${item['price']:,.2f}")
    else:
        st.info("No orders yet. Start shopping!")
    
    st.markdown("---")
    
    if st.button("Logout", type="secondary"):
        logout()
        st.rerun()


# ==================== ADMIN DASHBOARD ====================

def show_admin_dashboard():
    """Display admin dashboard"""
    
    st.markdown("<h1 class='main-header'>Admin Dashboard</h1>", unsafe_allow_html=True)
    
    if not st.session_state.user or st.session_state.user.get('role') != 'admin':
        st.error("Access denied. Admin privileges required.")
        return
    
    # Get stats from API
    stats = api_request("GET", "/stats")
    
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Products", stats.get("total_products", 0))
        col2.metric("Total Units", stats.get("total_units", 0))
        col3.metric("Inventory Value", f"${stats.get('total_value', 0):,.0f}")
        col4.metric("Categories", len(stats.get("by_type", {})))
    
    st.markdown("---")
    
    # Inventory by type
    st.subheader("Inventory by Type")
    if stats and stats.get("by_type"):
        for type_name, count in stats["by_type"].items():
            st.progress(min(count / 100, 1.0), text=f"{type_name.capitalize()}: {count} units")
    
    st.markdown("---")
    
    # Inventory by brand
    st.subheader("Inventory by Brand")
    if stats and stats.get("by_brand"):
        for brand, count in stats["by_brand"].items():
            st.caption(f"{brand}: {count} units")


# ==================== NAVIGATION ====================

def show_navigation():
    """Display navigation sidebar"""
    
    with st.sidebar:
        st.markdown("## StringMaster")
        st.markdown("---")
        
        if st.session_state.user:
            st.markdown(f"Welcome, **{st.session_state.user['username']}**")
            st.markdown("---")
            
            if st.button("Catalog", use_container_width=True):
                st.session_state.page = "catalog"
                st.rerun()
            
            if st.button("Categories", use_container_width=True):
                st.session_state.page = "categories"
                st.rerun()
            
            if st.button("My Cart", use_container_width=True):
                st.session_state.page = "cart"
                st.rerun()
            
            if st.button("My Profile", use_container_width=True):
                st.session_state.page = "profile"
                st.rerun()
            
            # Admin dashboard for admins
            if st.session_state.user.get('role') == 'admin':
                st.markdown("---")
                if st.button("Admin Dashboard", use_container_width=True):
                    st.session_state.page = "admin"
                    st.rerun()
            
            st.markdown("---")
            if st.button("Logout", type="secondary", use_container_width=True):
                logout()
                st.rerun()


# ==================== MAIN APP ====================

def main():
    """Main application entry point"""
    
    # Show login if not authenticated
    if not st.session_state.token:
        show_login_page()
        return
    
    # Show navigation
    show_navigation()
    
    # Route to correct page
    page = st.session_state.page
    
    if page == "catalog":
        show_catalog()
    elif page == "categories":
        show_categories()
    elif page == "cart":
        show_cart()
    elif page == "profile":
        show_profile()
    elif page == "admin":
        show_admin_dashboard()
    else:
        show_catalog()


if __name__ == "__main__":
    main()

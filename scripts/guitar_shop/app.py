import streamlit as st
import requests
from typing import Optional

API_BASE_URL = "http://localhost:8000/api"

st.set_page_config(
    page_title="StringMaster Guitar Shop",
    page_icon="https://placeholder.svg?height=32&width=32&query=guitar+icon",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    .discount-price {
        font-size: 1.5rem;
        color: #e63946;
        font-weight: bold;
    }
    .original-price {
        font-size: 1rem;
        color: #888;
        text-decoration: line-through;
    }
    .stock-good { color: #2d6a4f; }
    .stock-low { color: #e76f51; }
    .stock-out { color: #9d0208; }
    .notification-badge {
        background-color: #e63946;
        color: white;
        border-radius: 50%;
        padding: 2px 8px;
        font-size: 0.8rem;
        margin-left: 5px;
    }
    .online-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        background-color: #2d6a4f;
        border-radius: 50%;
        margin-right: 5px;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"
if "cart" not in st.session_state:
    st.session_state.cart = {}
if "selected_category" not in st.session_state:
    st.session_state.selected_category = None


def api_request(method: str, endpoint: str, data: dict = None, auth: bool = False) -> Optional[dict]:
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
    api_request("POST", "/auth/logout", auth=True)
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.cart = {}
    st.session_state.page = "login"
    st.session_state.selected_category = None


def get_cart_summary():
    cart = st.session_state.cart
    total_items = sum(item["quantity"] for item in cart.values())
    total_price = sum(item.get("effective_price", item["guitar"]["price"]) * item["quantity"] for item in cart.values())
    return total_items, total_price


def is_admin():
    return st.session_state.user and st.session_state.user.get('role') == 'admin'


def show_login_page():
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
                        result = api_request("POST", "/auth/login", {
                            "username": username,
                            "password": password
                        })
                        
                        if result:
                            st.session_state.token = result["access_token"]
                            st.session_state.user = result["user"]
                            if result["user"].get("role") == "admin":
                                st.session_state.page = "admin"
                            else:
                                st.session_state.page = "catalog"
                            st.success("Login successful!")
                            st.rerun()
            
            st.markdown("---")
            st.info("Demo accounts: **Admin/Admin123** (Admin) or register a new account (Customer)")
        
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
                        result = api_request("POST", "/auth/register", {
                            "username": reg_username,
                            "email": reg_email,
                            "password": reg_password
                        })
                        
                        if result:
                            st.success("Account created! Please login.")
            
            st.markdown("---")
            st.caption("Password requirements: 6+ characters, uppercase, lowercase, and digit")


def show_catalog():
    st.markdown("<h1 class='main-header'>Guitar Catalog</h1>", unsafe_allow_html=True)
    
    selected_type = "All Types"
    if st.session_state.selected_category:
        selected_type = st.session_state.selected_category
    
    with st.sidebar:
        st.header("Filters")
        
        price_range = st.slider(
            "Price Range ($)",
            min_value=0,
            max_value=5000,
            value=(0, 5000),
            step=100
        )
        
        categories = api_request("GET", "/categories")
        type_options = ["All Types"]
        if categories:
            type_options += [cat["name"] for cat in categories]
        
        selected_type = st.selectbox(
            "Guitar Type", 
            type_options,
            index=type_options.index(st.session_state.selected_category) if st.session_state.selected_category in type_options else 0
        )
        
        if st.session_state.selected_category:
            if st.button("Clear Category Filter"):
                st.session_state.selected_category = None
                st.rerun()
        
        in_stock_only = st.checkbox("In Stock Only", value=True)
        
        st.markdown("---")
        
        if not is_admin():
            total_items, total_price = get_cart_summary()
            if total_items > 0:
                st.subheader("Cart Summary")
                st.metric("Items", total_items)
                st.metric("Total", f"${total_price:,.2f}")
                if st.button("View Cart", type="primary", use_container_width=True):
                    st.session_state.page = "cart"
                    st.rerun()
    
    params = {
        "min_price": price_range[0],
        "max_price": price_range[1],
        "in_stock": in_stock_only
    }
    
    if selected_type != "All Types":
        params["guitar_type"] = selected_type.lower()
        st.session_state.selected_category = selected_type
    else:
        st.session_state.selected_category = None
    
    guitars = api_request("GET", "/guitars", params)
    
    if guitars is None:
        st.warning("Unable to load guitars. Please check if the API is running.")
        return
    
    if selected_type != "All Types":
        st.info(f"Showing {selected_type} guitars only")
    
    st.subheader(f"Showing {len(guitars)} guitars")
    
    if not guitars:
        st.info("No guitars match your filters. Try adjusting the criteria.")
        return
    
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
                
                discount = guitar.get('discount_percent', 0)
                if discount > 0:
                    original_price = guitar.get('original_price', guitar['price'])
                    discounted_price = guitar.get('discounted_price', guitar['price'] * (1 - discount / 100))
                    st.markdown(f"<p class='original-price'>${original_price:,.2f}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p class='discount-price'>${discounted_price:,.2f} ({discount:.0f}% OFF)</p>", unsafe_allow_html=True)
                    effective_price = discounted_price
                else:
                    st.markdown(f"<p class='price-tag'>${guitar['price']:,.2f}</p>", unsafe_allow_html=True)
                    effective_price = guitar['price']
                
                stock = guitar['stock']
                if stock > 10:
                    st.success(f"In Stock: {stock} available")
                elif stock > 0:
                    st.warning(f"Low Stock: {stock} left")
                else:
                    st.error("Out of Stock")
                
                if not is_admin():
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
                                    "quantity": 1,
                                    "effective_price": effective_price
                                }
                                st.success(f"Added {guitar['brand']} {guitar['name']} to cart!")
                            st.rerun()
                    else:
                        st.button("Out of Stock", key=f"oos_{guitar['id']}", disabled=True, use_container_width=True)
                
                st.markdown("---")


def show_cart():
    if is_admin():
        st.error("Administrators cannot purchase guitars. Please use a customer account.")
        if st.button("Go to Admin Dashboard"):
            st.session_state.page = "admin"
            st.rerun()
        return
    
    st.markdown("<h1 class='main-header'>Shopping Cart</h1>", unsafe_allow_html=True)
    
    cart = st.session_state.cart
    
    if not cart:
        st.info("Your cart is empty. Browse our catalog to add guitars!")
        if st.button("Browse Catalog", type="primary"):
            st.session_state.page = "catalog"
            st.rerun()
        return
    
    for guitar_id, item in list(cart.items()):
        guitar = item["guitar"]
        quantity = item["quantity"]
        effective_price = item.get("effective_price", guitar["price"])
        
        col1, col2, col3, col4, col5 = st.columns([1, 3, 1, 1, 1])
        
        with col1:
            st.image(
                guitar.get("image_url") or f"https://placeholder.svg?height=80&width=80&query={guitar['brand']}+guitar",
                width=80
            )
        
        with col2:
            st.markdown(f"**{guitar['brand']} {guitar['name']}**")
            st.caption(f"{guitar['guitar_type'].capitalize()}")
            if guitar.get('discount_percent', 0) > 0:
                st.caption(f"{guitar['discount_percent']:.0f}% discount applied")
        
        with col3:
            st.markdown(f"**${effective_price:,.2f}**")
        
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
    
    st.markdown("### Order Summary")
    
    total_items, total_price = get_cart_summary()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"**Total Items:** {total_items}")
        
        for item in cart.values():
            guitar = item["guitar"]
            qty = item["quantity"]
            effective_price = item.get("effective_price", guitar["price"])
            st.caption(f"{guitar['brand']} {guitar['name']} x{qty} = ${effective_price * qty:,.2f}")
    
    with col2:
        st.markdown(f"## ${total_price:,.2f}")
        
        if st.button("Checkout / Purchase", type="primary", use_container_width=True):
            for guitar_id, item in cart.items():
                api_request("POST", "/guitars/cart/add", {
                    "guitar_id": int(guitar_id),
                    "quantity": item["quantity"]
                }, auth=True)
            
            result = api_request("POST", "/guitars/purchase", auth=True)
            
            if result:
                st.session_state.cart = {}
                st.success(f"Order #{result.get('order_id')} placed successfully! Total: ${result.get('total', 0):,.2f}")
                st.balloons()
        
        if st.button("Continue Shopping", use_container_width=True):
            st.session_state.page = "catalog"
            st.rerun()


def show_categories():
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
                
                cat_guitars = api_request("GET", f"/categories/{category['id']}/guitars")
                if cat_guitars:
                    st.caption(f"{cat_guitars.get('count', 0)} guitars available")
                
                if st.button(f"Browse {category['name']}", key=f"cat_{category['id']}", use_container_width=True):
                    st.session_state.selected_category = category['name']
                    st.session_state.page = "catalog"
                    st.rerun()
                
                st.markdown("---")


def show_profile():
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
    
    if not is_admin():
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


def show_admin_dashboard():
    st.markdown("<h1 class='main-header'>Admin Dashboard</h1>", unsafe_allow_html=True)
    
    if not is_admin():
        st.error("Access denied. Admin privileges required.")
        return
    
    tab_overview, tab_users, tab_inventory, tab_orders, tab_discounts, tab_add_guitar = st.tabs([
        "Overview", "Online Users", "Inventory & Stats", "Orders & Notifications", "Discounts", "Add Guitar"
    ])
    
    with tab_overview:
        st.subheader("Shop Overview")
        
        stats = api_request("GET", "/stats")
        
        if stats:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Products", stats.get("total_products", 0))
            col2.metric("Total Units", stats.get("total_units", 0))
            col3.metric("Inventory Value", f"${stats.get('total_value', 0):,.0f}")
            col4.metric("Total Revenue", f"${stats.get('total_revenue', 0):,.0f}")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Orders", stats.get("total_orders", 0))
            col2.metric("Categories", len(stats.get("by_type", {})))
            col3.metric("Brands", len(stats.get("by_brand", {})))
            col4.metric("Active Discounts", stats.get("discounted_count", 0))
        
        notifications = api_request("GET", "/admin/notifications", {"unread_only": True}, auth=True)
        if notifications and notifications.get("count", 0) > 0:
            st.warning(f"You have {notifications['count']} unread purchase notifications!")
    
    with tab_users:
        st.subheader("Currently Online Users")
        
        if st.button("Refresh Online Users", key="refresh_users"):
            st.rerun()
        
        online_data = api_request("GET", "/admin/online-users", auth=True)
        
        if online_data:
            st.metric("Online Customers", online_data.get("online_count", 0))
            
            if online_data.get("users"):
                st.markdown("---")
                for user in online_data["users"]:
                    col1, col2, col3 = st.columns([1, 2, 2])
                    with col1:
                        st.markdown(f"<span class='online-indicator'></span> **{user['username']}**", unsafe_allow_html=True)
                    with col2:
                        st.caption(user['email'])
                    with col3:
                        if user.get('last_login'):
                            st.caption(f"Last login: {user['last_login']}")
            else:
                st.info("No customers currently online.")
        
        st.markdown("---")
        st.subheader("All Users")
        
        all_users = api_request("GET", "/users", auth=True)
        if all_users:
            for user in all_users:
                if user['role'] != 'admin':
                    st.markdown(f"- **{user['username']}** ({user['email']}) - {user['role']}")
    
    with tab_inventory:
        st.subheader("Inventory Statistics")
        
        brand_stats = api_request("GET", "/admin/brand-statistics", auth=True)
        type_stats = api_request("GET", "/admin/type-statistics", auth=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Guitars by Brand")
            if brand_stats and brand_stats.get("brands"):
                for brand in brand_stats["brands"]:
                    st.markdown(f"**{brand['brand']}**")
                    st.progress(min(brand['model_count'] / 10, 1.0))
                    st.caption(f"{brand['model_count']} models | {brand['total_stock']} units | Avg: ${brand['avg_price']:,.0f}")
        
        with col2:
            st.markdown("#### Guitars by Type")
            if type_stats and type_stats.get("types"):
                for gtype in type_stats["types"]:
                    st.markdown(f"**{gtype['guitar_type'].capitalize()}**")
                    st.progress(min(gtype['model_count'] / 10, 1.0))
                    st.caption(f"{gtype['model_count']} models | {gtype['total_stock']} units | Value: ${gtype['inventory_value']:,.0f}")
        
        st.markdown("---")
        st.subheader("Brand Statistics Chart")
        
        if brand_stats and brand_stats.get("brands"):
            import pandas as pd
            
            df = pd.DataFrame(brand_stats["brands"])
            
            st.bar_chart(df.set_index('brand')['model_count'])
            
            st.markdown("#### Stock by Brand")
            st.bar_chart(df.set_index('brand')['total_stock'])
            
            st.markdown("#### Inventory Value by Brand")
            st.bar_chart(df.set_index('brand')['inventory_value'])
    
    with tab_orders:
        st.subheader("Purchase Notifications")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            show_unread_only = st.checkbox("Show unread only", value=False)
        with col2:
            if st.button("Mark All Read"):
                result = api_request("POST", "/admin/notifications/mark-read", {"mark_all": True}, auth=True)
                if result:
                    st.success(result.get("message", "Done"))
                    st.rerun()
        
        notifications = api_request("GET", "/admin/notifications", {"unread_only": show_unread_only}, auth=True)
        
        if notifications and notifications.get("notifications"):
            for notif in notifications["notifications"]:
                is_unread = not notif.get("is_read", True)
                
                with st.expander(f"{'[NEW] ' if is_unread else ''}Order #{notif['order_id']} - {notif['username']} - ${notif['total']:,.2f}"):
                    st.markdown(f"**Customer:** {notif['username']}")
                    st.markdown(f"**Total:** ${notif['total']:,.2f}")
                    st.markdown(f"**Date:** {notif['created_at']}")
                    st.markdown(f"**Status:** {notif.get('order_status', 'pending').upper()}")
                    
                    if is_unread:
                        if st.button("Mark as Read", key=f"read_{notif['id']}"):
                            api_request("POST", "/admin/notifications/mark-read", {"notification_id": notif['id']}, auth=True)
                            st.rerun()
        else:
            st.info("No notifications to display.")
        
        st.markdown("---")
        st.subheader("All Orders")
        
        orders = api_request("GET", "/admin/orders", auth=True)
        
        if orders and orders.get("orders"):
            for order in orders["orders"]:
                with st.expander(f"Order #{order['id']} - {order['username']} - ${order['total']:,.2f} ({order['status'].upper()})"):
                    st.markdown(f"**Customer:** {order['username']}")
                    st.markdown(f"**Date:** {order['created_at']}")
                    st.markdown("**Items:**")
                    for item in order['items']:
                        st.markdown(f"- {item['guitar_name']} x{item['quantity']} @ ${item['price']:,.2f}")
        else:
            st.info("No orders yet.")
    
    with tab_discounts:
        st.subheader("Discount Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Apply Discount")
            
            discount_type = st.selectbox("Discount Target", ["Brand", "Type", "Specific Guitar"])
            
            if discount_type == "Brand":
                brand_stats = api_request("GET", "/admin/brand-statistics", auth=True)
                if brand_stats and brand_stats.get("brands"):
                    brands = [b['brand'] for b in brand_stats["brands"]]
                    selected_target = st.selectbox("Select Brand", brands)
                    target_type = "brand"
            elif discount_type == "Type":
                selected_target = st.selectbox("Select Type", ["electric", "acoustic", "bass", "classical"])
                target_type = "type"
            else:
                guitar_id = st.number_input("Guitar ID", min_value=1, step=1)
                selected_target = str(guitar_id)
                target_type = "guitar"
            
            discount_percent = st.slider("Discount Percentage", 0, 100, 10)
            
            if st.button("Apply Discount", type="primary"):
                result = api_request("POST", "/admin/discounts", {
                    "discount_percent": discount_percent,
                    "target_type": target_type,
                    "target_value": selected_target
                }, auth=True)
                if result:
                    st.success(result.get("message", "Discount applied!"))
                    st.rerun()
        
        with col2:
            st.markdown("#### Active Discounts")
            
            discounted = api_request("GET", "/admin/discounted-guitars", auth=True)
            
            if discounted and discounted.get("guitars"):
                st.metric("Guitars with Discounts", discounted.get("count", 0))
                
                for guitar in discounted["guitars"]:
                    st.markdown(f"**{guitar['brand']} {guitar['name']}**")
                    st.caption(f"Original: ${guitar['price']:,.2f} | Now: ${guitar['discounted_price']:,.2f} ({guitar['discount_percent']:.0f}% OFF)")
            else:
                st.info("No active discounts.")
            
            st.markdown("---")
            
            if st.button("Clear All Discounts", type="secondary"):
                result = api_request("POST", "/admin/discounts/clear", auth=True)
                if result:
                    st.success(result.get("message", "Discounts cleared!"))
                    st.rerun()
    
    with tab_add_guitar:
        st.subheader("Add New Guitar to Inventory")
        
        with st.form("add_guitar_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Guitar Name", placeholder="e.g., Player Stratocaster")
                brand = st.text_input("Brand", placeholder="e.g., Fender")
                guitar_type = st.selectbox("Guitar Type", ["electric", "acoustic", "bass", "classical"])
                price = st.number_input("Price ($)", min_value=0.01, value=499.99, step=0.01)
            
            with col2:
                stock = st.number_input("Initial Stock", min_value=0, value=10, step=1)
                description = st.text_area("Description", placeholder="Enter guitar description...")
                image_url = st.text_input("Image URL (optional)", placeholder="https://...")
            
            submitted = st.form_submit_button("Add Guitar", type="primary", use_container_width=True)
            
            if submitted:
                if not name or not brand:
                    st.error("Name and Brand are required!")
                else:
                    result = api_request("POST", "/admin/guitars", {
                        "name": name,
                        "brand": brand,
                        "guitar_type": guitar_type,
                        "price": price,
                        "stock": stock,
                        "description": description,
                        "image_url": image_url or f"https://placeholder.svg?height=300&width=300&query={brand}+{guitar_type}+guitar"
                    }, auth=True)
                    
                    if result:
                        st.success(f"Successfully added {brand} {name} to inventory!")
                        st.json(result.get("guitar", {}))


def show_navigation():
    with st.sidebar:
        st.markdown("## StringMaster")
        st.markdown("---")
        
        if st.session_state.user:
            st.markdown(f"Welcome, **{st.session_state.user['username']}**")
            st.caption(f"Role: {'Administrator' if is_admin() else 'Customer'}")
            st.markdown("---")
            
            if st.button("Catalog", use_container_width=True):
                st.session_state.page = "catalog"
                st.rerun()
            
            if st.button("Categories", use_container_width=True):
                st.session_state.page = "categories"
                st.rerun()
            
            if not is_admin():
                if st.button("My Cart", use_container_width=True):
                    st.session_state.page = "cart"
                    st.rerun()
                
                if st.button("My Profile", use_container_width=True):
                    st.session_state.page = "profile"
                    st.rerun()
            
            if is_admin():
                st.markdown("---")
                st.markdown("### Admin")
                
                notifications = api_request("GET", "/admin/notifications", {"unread_only": True}, auth=True)
                notif_count = notifications.get("count", 0) if notifications else 0
                
                if notif_count > 0:
                    if st.button(f"Admin Dashboard ({notif_count} new)", use_container_width=True, type="primary"):
                        st.session_state.page = "admin"
                        st.rerun()
                else:
                    if st.button("Admin Dashboard", use_container_width=True):
                        st.session_state.page = "admin"
                        st.rerun()
            
            st.markdown("---")
            if st.button("Logout", type="secondary", use_container_width=True):
                logout()
                st.rerun()


def main():
    if not st.session_state.token:
        show_login_page()
        return
    
    show_navigation()
    
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

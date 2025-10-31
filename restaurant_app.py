import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import json
import os
import time

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="Restaurant Order System",
    page_icon="🍽️",
    layout="wide"
)

# ----------------- FIREBASE SETUP WITH ERROR HANDLING -----------------
@st.cache_resource
def initialize_firebase():
    """Initialize Firebase with error handling and environment variable support"""
    try:
        if not firebase_admin._apps:
            # Try to load from environment variable first (for deployment)
            firebase_config = os.getenv('FIREBASE_CONFIG')
            
            if firebase_config:
                # Parse JSON from environment variable
                cred_dict = json.loads(firebase_config)
                cred = credentials.Certificate(cred_dict)
            else:
                # Fall back to local file (for development)
                if os.path.exists("firebase_key.json"):
                    cred = credentials.Certificate("firebase_key.json")
                else:
                    st.error("⚠️ Firebase credentials not found! Please set FIREBASE_CONFIG environment variable or add firebase_key.json")
                    st.stop()
            
            # Get database URL from environment or config
            database_url = os.getenv('FIREBASE_DATABASE_URL', 'https://YOUR-DATABASE-NAME.firebaseio.com/')
            
            firebase_admin.initialize_app(cred, {
                'databaseURL': database_url
            })
            return True
    except Exception as e:
        st.error(f"❌ Firebase initialization failed: {str(e)}")
        st.info("💡 Make sure your Firebase credentials are correct and the database URL is valid.")
        st.stop()
        return False

# Initialize Firebase
initialize_firebase()

# ----------------- HELPER FUNCTIONS -----------------
def get_orders():
    """Fetch orders with error handling"""
    try:
        orders_ref = db.reference('orders')
        orders = orders_ref.get()
        return orders if orders else {}
    except Exception as e:
        st.error(f"Error fetching orders: {str(e)}")
        return {}

def add_order(order_type, table_number, customer_name, customer_phone, items, pickup_time=None):
    """Add new order with error handling"""
    try:
        orders_ref = db.reference('orders')
        new_order = {
            "type": order_type,  # "Dine-In" or "Take-Out"
            "table": table_number if order_type == "Dine-In" else None,
            "customer_name": customer_name if order_type == "Take-Out" else None,
            "customer_phone": customer_phone if order_type == "Take-Out" else None,
            "pickup_time": pickup_time if order_type == "Take-Out" else None,
            "items": items,
            "status": "Pending",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "completed_at": None
        }
        orders_ref.push(new_order)
        return True
    except Exception as e:
        st.error(f"Error adding order: {str(e)}")
        return False

def mark_order_done(order_id):
    """Mark order as done with timestamp"""
    try:
        orders_ref = db.reference('orders')
        orders_ref.child(order_id).update({
            "status": "Done",
            "completed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return True
    except Exception as e:
        st.error(f"Error updating order: {str(e)}")
        return False

def mark_order_ready(order_id):
    """Mark take-out order as ready for pickup"""
    try:
        orders_ref = db.reference('orders')
        orders_ref.child(order_id).update({
            "status": "Ready",
            "completed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return True
    except Exception as e:
        st.error(f"Error updating order: {str(e)}")
        return False

def mark_order_picked_up(order_id):
    """Mark take-out order as picked up"""
    try:
        orders_ref = db.reference('orders')
        orders_ref.child(order_id).update({
            "status": "Picked-Up",
            "picked_up_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return True
    except Exception as e:
        st.error(f"Error updating order: {str(e)}")
        return False

def delete_order(order_id):
    """Delete an order"""
    try:
        orders_ref = db.reference('orders')
        orders_ref.child(order_id).delete()
        return True
    except Exception as e:
        st.error(f"Error deleting order: {str(e)}")
        return False

# ----------------- AUTO-REFRESH IMPLEMENTATION -----------------
def auto_refresh(interval_seconds=5):
    """Auto-refresh the page every N seconds"""
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = time.time()
    
    current_time = time.time()
    if current_time - st.session_state.last_refresh > interval_seconds:
        st.session_state.last_refresh = current_time
        st.rerun()

# ----------------- SOUND NOTIFICATION -----------------
def play_notification_sound():
    """Play notification sound for new orders"""
    audio_html = """
    <audio autoplay>
        <source src="data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZizoIHGu98OGgSQwOUp3j7q1gGA0+juLHfTA" type="audio/wav">
    </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

# ----------------- UI SETUP -----------------
st.sidebar.title("🍴 Restaurant Order System")
view = st.sidebar.radio("Select View", ["👨‍🍳 Kitchen Dashboard", "🍽️ Dine-In Orders", "🥡 Take-Out Orders"], label_visibility="collapsed")

# Display connection status
with st.sidebar:
    st.divider()
    st.caption("🟢 Connected to Firebase")
    st.caption(f"🕐 Last updated: {datetime.now().strftime('%H:%M:%S')}")

# ----------------- DINE-IN VIEW -----------------
if view == "🍽️ Dine-In Orders":
    st.title("🍽️ Dine-In Order Terminal")
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.subheader("New Dine-In Order")
        table_number = st.number_input("Table Number", min_value=1, max_value=100, step=1, value=1)
        items = st.text_area(
            "Order Items", 
            placeholder="e.g.\n2x Cheeseburger\n1x Caesar Salad\n3x Coke",
            height=150
        )
        
        if st.button("📤 Send to Kitchen", type="primary", use_container_width=True):
            if items.strip():
                if add_order("Dine-In", table_number, None, None, items):
                    st.success(f"✅ Order for Table {table_number} sent to kitchen!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("Please enter order items!")
    
    with col2:
        st.subheader("Recent Dine-In Orders")
        orders = get_orders()
        
        if orders:
            # Filter dine-in orders only
            dine_in_orders = {k: v for k, v in orders.items() if v.get('type') == 'Dine-In'}
            recent_orders = sorted(dine_in_orders.items(), key=lambda x: x[1]['timestamp'], reverse=True)[:5]
            
            for order_id, order in recent_orders:
                status_color = "🟢" if order['status'] == "Done" else "🟡"
                with st.expander(f"{status_color} Table {order['table']} - {order['status']} ({order['timestamp']})"):
                    st.text(order['items'])
        else:
            st.info("No dine-in orders yet today")

# ----------------- TAKE-OUT VIEW -----------------
elif view == "🥡 Take-Out Orders":
    st.title("🥡 Take-Out Order Terminal")
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.subheader("New Take-Out Order")
        
        customer_name = st.text_input("Customer Name", placeholder="John Doe")
        customer_phone = st.text_input("Phone Number", placeholder="555-1234")
        
        # Pickup time
        col_time1, col_time2 = st.columns(2)
        with col_time1:
            pickup_time = st.time_input("Pickup Time", value=None)
        with col_time2:
            asap = st.checkbox("ASAP", value=True)
        
        items = st.text_area(
            "Order Items", 
            placeholder="e.g.\n2x Cheeseburger\n1x Caesar Salad\n3x Coke",
            height=120
        )
        
        if st.button("📤 Send to Kitchen", type="primary", use_container_width=True):
            if items.strip() and customer_name.strip():
                pickup_str = "ASAP" if asap else pickup_time.strftime("%H:%M") if pickup_time else "ASAP"
                if add_order("Take-Out", None, customer_name, customer_phone, items, pickup_str):
                    st.success(f"✅ Take-out order for {customer_name} sent to kitchen!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("Please enter customer name and order items!")
    
    with col2:
        st.subheader("Recent Take-Out Orders")
        orders = get_orders()
        
        if orders:
            # Filter take-out orders only
            takeout_orders = {k: v for k, v in orders.items() if v.get('type') == 'Take-Out'}
            recent_orders = sorted(takeout_orders.items(), key=lambda x: x[1]['timestamp'], reverse=True)[:5]
            
            for order_id, order in recent_orders:
                status_emoji = {"Pending": "🟡", "Ready": "🟢", "Picked-Up": "✅"}.get(order['status'], "🟡")
                pickup_time = order.get('pickup_time', 'ASAP')
                with st.expander(f"{status_emoji} {order['customer_name']} - {order['status']} (Pickup: {pickup_time})"):
                    st.text(order['items'])
                    if order.get('customer_phone'):
                        st.caption(f"📞 {order['customer_phone']}")
        else:
            st.info("No take-out orders yet today")

# ----------------- KITCHEN VIEW -----------------
elif view == "👨‍🍳 Kitchen Dashboard":
    st.title("👨‍🍳 Kitchen Dashboard")
    
    # Auto-refresh every 5 seconds
    auto_refresh(5)
    
    # Get all orders
    orders = get_orders()
    
    # Separate by type
    dine_in_orders = {k: v for k, v in orders.items() if v.get('type') == 'Dine-In'}
    takeout_orders = {k: v for k, v in orders.items() if v.get('type') == 'Take-Out'}
    
    # Calculate statistics
    pending_dine_in = {k: v for k, v in dine_in_orders.items() if v['status'] == 'Pending'}
    pending_takeout = {k: v for k, v in takeout_orders.items() if v['status'] == 'Pending'}
    ready_takeout = {k: v for k, v in takeout_orders.items() if v['status'] == 'Ready'}
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🍽️ Dine-In Pending", len(pending_dine_in))
    with col2:
        st.metric("🥡 Take-Out Pending", len(pending_takeout))
    with col3:
        st.metric("🟢 Take-Out Ready", len(ready_takeout))
    with col4:
        st.metric("📊 Total Orders", len(orders))
    
    st.divider()
    
    # Check for new orders and play sound
    total_pending = len(pending_dine_in) + len(pending_takeout)
    if 'previous_order_count' not in st.session_state:
        st.session_state.previous_order_count = total_pending
    elif total_pending > st.session_state.previous_order_count:
        play_notification_sound()
        st.session_state.previous_order_count = total_pending
    
    # Tabs for different order types
    tab1, tab2, tab3 = st.tabs(["🍽️ Dine-In Orders", "🥡 Take-Out Orders", "📋 All Orders"])
    
    with tab1:
        st.subheader(f"Dine-In Orders ({len(dine_in_orders)})")
        
        # Pending dine-in
        if pending_dine_in:
            st.markdown("### 🟡 Pending")
            sorted_pending = sorted(pending_dine_in.items(), key=lambda x: x[1]['timestamp'])
            
            for order_id, order in sorted_pending:
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"#### 🍽️ Table {order['table']}")
                    st.caption(f"Ordered at: {order['timestamp']}")
                    st.text(order['items'])
                
                with col2:
                    if st.button("✅ Done", key=f"done_din_{order_id}", type="primary"):
                        if mark_order_done(order_id):
                            st.success("Order completed!")
                            st.session_state.previous_order_count -= 1
                            time.sleep(0.5)
                            st.rerun()
                    
                    if st.button("🗑️", key=f"del_din_{order_id}", help="Delete order"):
                        if delete_order(order_id):
                            st.session_state.previous_order_count -= 1
                            st.rerun()
                
                st.divider()
        
        # Completed dine-in
        completed_dine_in = {k: v for k, v in dine_in_orders.items() if v['status'] == 'Done'}
        if completed_dine_in:
            st.markdown("### 🟢 Completed")
            sorted_completed = sorted(completed_dine_in.items(), 
                                     key=lambda x: x[1].get('completed_at', x[1]['timestamp']), 
                                     reverse=True)
            
            for order_id, order in sorted_completed[:5]:  # Show last 5
                with st.expander(f"✅ Table {order['table']} - {order.get('completed_at', 'N/A')}"):
                    st.text(order['items'])
                    if st.button("🗑️ Delete", key=f"del_comp_din_{order_id}"):
                        if delete_order(order_id):
                            st.rerun()
    
    with tab2:
        st.subheader(f"Take-Out Orders ({len(takeout_orders)})")
        
        # Pending take-out
        if pending_takeout:
            st.markdown("### 🟡 In Progress")
            sorted_pending = sorted(pending_takeout.items(), key=lambda x: x[1]['timestamp'])
            
            for order_id, order in sorted_pending:
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"#### 🥡 {order['customer_name']}")
                    st.caption(f"Pickup: {order.get('pickup_time', 'ASAP')} | Ordered: {order['timestamp']}")
                    if order.get('customer_phone'):
                        st.caption(f"📞 {order['customer_phone']}")
                    st.text(order['items'])
                
                with col2:
                    if st.button("🟢 Ready", key=f"ready_{order_id}", type="primary"):
                        if mark_order_ready(order_id):
                            st.success("Order ready for pickup!")
                            time.sleep(0.5)
                            st.rerun()
                    
                    if st.button("🗑️", key=f"del_to_{order_id}", help="Delete order"):
                        if delete_order(order_id):
                            st.session_state.previous_order_count -= 1
                            st.rerun()
                
                st.divider()
        
        # Ready for pickup
        if ready_takeout:
            st.markdown("### 🟢 Ready for Pickup")
            sorted_ready = sorted(ready_takeout.items(), key=lambda x: x[1].get('completed_at', x[1]['timestamp']))
            
            for order_id, order in sorted_ready:
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"#### 🥡 {order['customer_name']}")
                    st.caption(f"Ready at: {order.get('completed_at', 'N/A')}")
                    if order.get('customer_phone'):
                        st.caption(f"📞 {order['customer_phone']}")
                    st.text(order['items'])
                
                with col2:
                    if st.button("✅ Picked Up", key=f"pickup_{order_id}"):
                        if mark_order_picked_up(order_id):
                            st.success("Order picked up!")
                            time.sleep(0.5)
                            st.rerun()
                    
                    if st.button("🗑️", key=f"del_ready_{order_id}", help="Delete order"):
                        if delete_order(order_id):
                            st.rerun()
                
                st.divider()
        
        # Picked up orders
        picked_up = {k: v for k, v in takeout_orders.items() if v['status'] == 'Picked-Up'}
        if picked_up:
            st.markdown("### ✅ Picked Up")
            sorted_picked = sorted(picked_up.items(), 
                                  key=lambda x: x[1].get('picked_up_at', x[1]['timestamp']), 
                                  reverse=True)
            
            for order_id, order in sorted_picked[:5]:  # Show last 5
                with st.expander(f"✅ {order['customer_name']} - {order.get('picked_up_at', 'N/A')}"):
                    st.text(order['items'])
                    if st.button("🗑️ Delete", key=f"del_picked_{order_id}"):
                        if delete_order(order_id):
                            st.rerun()
    
    with tab3:
        st.subheader(f"All Orders ({len(orders)})")
        
        if not orders:
            st.info("No orders in the system")
        else:
            # Sort by timestamp (newest first)
            sorted_all = sorted(orders.items(), key=lambda x: x[1]['timestamp'], reverse=True)
            
            for order_id, order in sorted_all[:20]:  # Show last 20
                order_type = order.get('type', 'Unknown')
                status = order['status']
                
                if order_type == "Dine-In":
                    title = f"🍽️ Table {order['table']} - {status}"
                else:
                    title = f"🥡 {order['customer_name']} - {status}"
                
                with st.expander(f"{title} ({order['timestamp']})"):
                    st.text(order['items'])
                    if order.get('customer_phone'):
                        st.caption(f"📞 {order['customer_phone']}")
                    if order.get('pickup_time'):
                        st.caption(f"Pickup: {order['pickup_time']}")
                    if order.get('completed_at'):
                        st.caption(f"Completed: {order['completed_at']}")
                    
                    if st.button("🗑️ Delete", key=f"del_all_{order_id}"):
                        if delete_order(order_id):
                            st.rerun()

# ----------------- FOOTER -----------------
st.sidebar.divider()
st.sidebar.caption("🔄 Auto-refreshes every 5 seconds")
st.sidebar.caption("Made with ❤️ using Streamlit + Firebase")

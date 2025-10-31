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

def add_order(table_number, items):
    """Add new order with error handling"""
    try:
        orders_ref = db.reference('orders')
        new_order = {
            "table": table_number,
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
view = st.sidebar.radio("Select View", ["👨‍🍳 Kitchen Dashboard", "🍽️ Waiter Terminal"], label_visibility="collapsed")

# Display connection status
with st.sidebar:
    st.divider()
    st.caption("🟢 Connected to Firebase")
    st.caption(f"🕐 Last updated: {datetime.now().strftime('%H:%M:%S')}")

# ----------------- WAITER VIEW -----------------
if view == "🍽️ Waiter Terminal":
    st.title("🍽️ Waiter Order Terminal")
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.subheader("New Order")
        table_number = st.number_input("Table Number", min_value=1, max_value=100, step=1, value=1)
        items = st.text_area(
            "Order Items", 
            placeholder="e.g.\n2x Cheeseburger\n1x Caesar Salad\n3x Coke",
            height=150
        )
        
        if st.button("📤 Send to Kitchen", type="primary", use_container_width=True):
            if items.strip():
                if add_order(table_number, items):
                    st.success(f"✅ Order for Table {table_number} sent to kitchen!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("Please enter order items!")
    
    with col2:
        st.subheader("Recent Orders")
        orders = get_orders()
        
        if orders:
            # Show last 5 orders
            recent_orders = sorted(orders.items(), key=lambda x: x[1]['timestamp'], reverse=True)[:5]
            for order_id, order in recent_orders:
                status_color = "🟢" if order['status'] == "Done" else "🟡"
                with st.expander(f"{status_color} Table {order['table']} - {order['status']} ({order['timestamp']})"):
                    st.text(order['items'])
        else:
            st.info("No orders yet today")

# ----------------- KITCHEN VIEW -----------------
elif view == "👨‍🍳 Kitchen Dashboard":
    st.title("👨‍🍳 Kitchen Dashboard")
    
    # Auto-refresh every 5 seconds
    auto_refresh(5)
    
    # Get all orders
    orders = get_orders()
    
    # Calculate statistics
    pending_orders = {k: v for k, v in orders.items() if v['status'] == 'Pending'}
    completed_orders = {k: v for k, v in orders.items() if v['status'] == 'Done'}
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🟡 Pending Orders", len(pending_orders))
    with col2:
        st.metric("🟢 Completed Today", len(completed_orders))
    with col3:
        st.metric("📊 Total Orders", len(orders))
    
    st.divider()
    
    # Tabs for filtering
    tab1, tab2, tab3 = st.tabs(["🟡 Pending", "🟢 Completed", "📋 All Orders"])
    
    # Check for new orders and play sound
    if 'previous_order_count' not in st.session_state:
        st.session_state.previous_order_count = len(pending_orders)
    elif len(pending_orders) > st.session_state.previous_order_count:
        play_notification_sound()
        st.session_state.previous_order_count = len(pending_orders)
    
    with tab1:
        st.subheader(f"Pending Orders ({len(pending_orders)})")
        if not pending_orders:
            st.info("✨ No pending orders - Kitchen is clear!")
        else:
            # Sort by timestamp (oldest first)
            sorted_pending = sorted(pending_orders.items(), key=lambda x: x[1]['timestamp'])
            
            for order_id, order in sorted_pending:
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    with st.container():
                        st.markdown(f"### 🍽️ Table {order['table']}")
                        st.caption(f"Ordered at: {order['timestamp']}")
                        st.text(order['items'])
                
                with col2:
                    if st.button("✅ Done", key=f"done_{order_id}", type="primary"):
                        if mark_order_done(order_id):
                            st.success("Order completed!")
                            st.session_state.previous_order_count -= 1
                            time.sleep(0.5)
                            st.rerun()
                    
                    if st.button("🗑️", key=f"del_{order_id}", help="Delete order"):
                        if delete_order(order_id):
                            st.session_state.previous_order_count -= 1
                            st.rerun()
                
                st.divider()
    
    with tab2:
        st.subheader(f"Completed Orders ({len(completed_orders)})")
        if not completed_orders:
            st.info("No completed orders yet")
        else:
            # Sort by completion time (newest first)
            sorted_completed = sorted(completed_orders.items(), 
                                     key=lambda x: x[1].get('completed_at', x[1]['timestamp']), 
                                     reverse=True)
            
            for order_id, order in sorted_completed:
                with st.expander(f"✅ Table {order['table']} - Completed at {order.get('completed_at', 'N/A')}"):
                    st.text(order['items'])
                    st.caption(f"Ordered at: {order['timestamp']}")
                    if st.button("🗑️ Delete", key=f"del_comp_{order_id}"):
                        if delete_order(order_id):
                            st.rerun()
    
    with tab3:
        st.subheader(f"All Orders ({len(orders)})")
        if not orders:
            st.info("No orders in the system")
        else:
            # Sort by timestamp (newest first)
            sorted_all = sorted(orders.items(), key=lambda x: x[1]['timestamp'], reverse=True)
            
            for order_id, order in sorted_all:
                status_emoji = "✅" if order['status'] == "Done" else "🟡"
                with st.expander(f"{status_emoji} Table {order['table']} - {order['status']} ({order['timestamp']})"):
                    st.text(order['items'])
                    if order.get('completed_at'):
                        st.caption(f"Completed at: {order['completed_at']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if order['status'] == 'Pending':
                            if st.button("Mark Done", key=f"done_all_{order_id}"):
                                if mark_order_done(order_id):
                                    st.rerun()
                    with col2:
                        if st.button("Delete", key=f"del_all_{order_id}"):
                            if delete_order(order_id):
                                st.rerun()

# ----------------- FOOTER -----------------
st.sidebar.divider()
st.sidebar.caption("🔄 Auto-refreshes every 5 seconds")
st.sidebar.caption("Made with ❤️ using Streamlit + Firebase")

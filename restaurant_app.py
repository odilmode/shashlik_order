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
view = st.sidebar.radio("Select View", ["👨‍🍳 Kitchen Dashboard", "🍽️ Dine-In Orders", "🥡 Take-Out Orders", "📊 Analytics"], label_visibility="collapsed")

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

# ----------------- ANALYTICS VIEW -----------------
if view == "📊 Analytics":
    st.title("📊 Restaurant Analytics Dashboard")
    
    orders = get_orders()
    
    if not orders:
        st.warning("No orders data available yet.")
        st.stop()
    
    # Convert to list for easier processing
    orders_list = []
    for order_id, order in orders.items():
        order['id'] = order_id
        orders_list.append(order)
    
    # Date filter
    st.sidebar.subheader("📅 Filter by Date")
    
    # Get date range
    all_dates = [datetime.strptime(o['timestamp'], "%Y-%m-%d %H:%M:%S").date() for o in orders_list]
    min_date = min(all_dates)
    max_date = max(all_dates)
    
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Filter orders by date
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_orders = [
            o for o in orders_list 
            if start_date <= datetime.strptime(o['timestamp'], "%Y-%m-%d %H:%M:%S").date() <= end_date
        ]
    else:
        filtered_orders = orders_list
    
    # Overview metrics
    st.header("📈 Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_orders = len(filtered_orders)
    dine_in_count = len([o for o in filtered_orders if o.get('type') == 'Dine-In'])
    takeout_count = len([o for o in filtered_orders if o.get('type') == 'Take-Out'])
    completed_orders = len([o for o in filtered_orders if o['status'] in ['Done', 'Picked-Up']])
    
    with col1:
        st.metric("📊 Total Orders", total_orders)
    with col2:
        st.metric("🍽️ Dine-In", dine_in_count)
    with col3:
        st.metric("🥡 Take-Out", takeout_count)
    with col4:
        completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
        st.metric("✅ Completion Rate", f"{completion_rate:.1f}%")
    
    st.divider()
    
    # Tabs for different analytics
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📅 Daily Trends", "⏰ Hourly Distribution", "🍽️ Order Types", "🍖 Menu Items", "📋 Detailed Report"])
    
    with tab1:
        st.subheader("Daily Order Trends")
        
        # Group by date
        from collections import defaultdict
        daily_stats = defaultdict(lambda: {'dine_in': 0, 'takeout': 0, 'total': 0})
        
        for order in filtered_orders:
            date = datetime.strptime(order['timestamp'], "%Y-%m-%d %H:%M:%S").date()
            daily_stats[date]['total'] += 1
            if order.get('type') == 'Dine-In':
                daily_stats[date]['dine_in'] += 1
            elif order.get('type') == 'Take-Out':
                daily_stats[date]['takeout'] += 1
        
        # Create chart data
        dates = sorted(daily_stats.keys())
        
        if dates:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Bar chart
                chart_data = {
                    'Date': [d.strftime('%Y-%m-%d') for d in dates],
                    'Dine-In': [daily_stats[d]['dine_in'] for d in dates],
                    'Take-Out': [daily_stats[d]['takeout'] for d in dates]
                }
                
                st.bar_chart(chart_data, x='Date', y=['Dine-In', 'Take-Out'], color=['#4CAF50', '#FF9800'])
            
            with col2:
                st.markdown("### 📊 Daily Stats")
                for date in reversed(dates[-7:]):  # Last 7 days
                    stats = daily_stats[date]
                    st.markdown(f"**{date.strftime('%b %d')}**")
                    st.text(f"Total: {stats['total']}")
                    st.text(f"🍽️ {stats['dine_in']} | 🥡 {stats['takeout']}")
                    st.divider()
        else:
            st.info("No data available for selected date range")
    
    with tab2:
        st.subheader("Hourly Order Distribution")
        
        # Group by hour
        hourly_stats = defaultdict(int)
        
        for order in filtered_orders:
            hour = datetime.strptime(order['timestamp'], "%Y-%m-%d %H:%M:%S").hour
            hourly_stats[hour] += 1
        
        if hourly_stats:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Line chart
                hours = list(range(24))
                counts = [hourly_stats.get(h, 0) for h in hours]
                
                chart_data = {
                    'Hour': [f"{h:02d}:00" for h in hours],
                    'Orders': counts
                }
                
                st.line_chart(chart_data, x='Hour', y='Orders', color='#2196F3')
            
            with col2:
                st.markdown("### ⏰ Peak Hours")
                # Find top 5 busiest hours
                sorted_hours = sorted(hourly_stats.items(), key=lambda x: x[1], reverse=True)
                for hour, count in sorted_hours[:5]:
                    st.markdown(f"**{hour:02d}:00 - {hour+1:02d}:00**")
                    st.text(f"{count} orders")
                    st.progress(count / max(hourly_stats.values()))
        else:
            st.info("No hourly data available")
    
    with tab3:
        st.subheader("Order Type Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🍽️ Dine-In Analysis")
            
            dine_in_orders = [o for o in filtered_orders if o.get('type') == 'Dine-In']
            
            if dine_in_orders:
                # Table usage
                table_usage = defaultdict(int)
                for order in dine_in_orders:
                    if order.get('table'):
                        table_usage[order['table']] += 1
                
                st.markdown("**Most Popular Tables:**")
                sorted_tables = sorted(table_usage.items(), key=lambda x: x[1], reverse=True)
                for table, count in sorted_tables[:10]:
                    st.text(f"Table {table}: {count} orders")
                
                st.divider()
                
                # Status breakdown
                dine_in_completed = len([o for o in dine_in_orders if o['status'] == 'Done'])
                dine_in_pending = len([o for o in dine_in_orders if o['status'] == 'Pending'])
                
                st.markdown("**Status Breakdown:**")
                st.text(f"✅ Completed: {dine_in_completed}")
                st.text(f"🟡 Pending: {dine_in_pending}")
            else:
                st.info("No dine-in orders in selected period")
        
        with col2:
            st.markdown("### 🥡 Take-Out Analysis")
            
            takeout_orders = [o for o in filtered_orders if o.get('type') == 'Take-Out']
            
            if takeout_orders:
                # Status breakdown
                to_picked = len([o for o in takeout_orders if o['status'] == 'Picked-Up'])
                to_ready = len([o for o in takeout_orders if o['status'] == 'Ready'])
                to_pending = len([o for o in takeout_orders if o['status'] == 'Pending'])
                
                st.markdown("**Status Breakdown:**")
                st.text(f"✅ Picked Up: {to_picked}")
                st.text(f"🟢 Ready: {to_ready}")
                st.text(f"🟡 Pending: {to_pending}")
                
                st.divider()
                
                # ASAP vs Scheduled
                asap_orders = len([o for o in takeout_orders if o.get('pickup_time') == 'ASAP'])
                scheduled_orders = len(takeout_orders) - asap_orders
                
                st.markdown("**Pickup Type:**")
                st.text(f"⚡ ASAP: {asap_orders}")
                st.text(f"📅 Scheduled: {scheduled_orders}")
                
                st.divider()
                
                # Top customers
                customer_orders = defaultdict(int)
                for order in takeout_orders:
                    if order.get('customer_name'):
                        customer_orders[order['customer_name']] += 1
                
                if customer_orders:
                    st.markdown("**Top Customers:**")
                    sorted_customers = sorted(customer_orders.items(), key=lambda x: x[1], reverse=True)
                    for customer, count in sorted_customers[:5]:
                        st.text(f"{customer}: {count} orders")
            else:
                st.info("No take-out orders in selected period")
    
    with tab4:
        st.subheader("Detailed Order Report")
        
        # Export options
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            order_type_filter = st.selectbox("Filter Type", ["All", "Dine-In", "Take-Out"])
        
        with col2:
            status_filter = st.selectbox("Filter Status", ["All", "Pending", "Done", "Ready", "Picked-Up"])
        
        # Apply filters
        display_orders = filtered_orders.copy()
        
        if order_type_filter != "All":
            display_orders = [o for o in display_orders if o.get('type') == order_type_filter]
        
        if status_filter != "All":
            display_orders = [o for o in display_orders if o['status'] == status_filter]
        
        st.markdown(f"**Showing {len(display_orders)} orders**")
        
        # Display table
        if display_orders:
            for i, order in enumerate(sorted(display_orders, key=lambda x: x['timestamp'], reverse=True), 1):
                with st.expander(f"{i}. {order.get('type', 'Unknown')} - {order['status']} ({order['timestamp']})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Order Details:**")
                        if order.get('type') == 'Dine-In':
                            st.text(f"Table: {order.get('table', 'N/A')}")
                        else:
                            st.text(f"Customer: {order.get('customer_name', 'N/A')}")
                            if order.get('customer_phone'):
                                st.text(f"Phone: {order['customer_phone']}")
                            st.text(f"Pickup: {order.get('pickup_time', 'N/A')}")
                        
                        st.text(f"Status: {order['status']}")
                    
                    with col2:
                        st.markdown("**Timeline:**")
                        st.text(f"Ordered: {order['timestamp']}")
                        if order.get('completed_at'):
                            st.text(f"Completed: {order['completed_at']}")
                        if order.get('picked_up_at'):
                            st.text(f"Picked Up: {order['picked_up_at']}")
                    
                    st.markdown("**Items:**")
                    st.text(order['items'])
        else:
            st.info("No orders match the selected filters")
        
        # Download data
        st.divider()
        
        if st.button("📥 Download Data as CSV"):
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.writer(output)
            
            # Headers
            writer.writerow(['Type', 'Table/Customer', 'Phone', 'Items', 'Status', 'Timestamp', 'Completed At', 'Pickup Time'])
            
            # Data
            for order in display_orders:
                writer.writerow([
                    order.get('type', 'N/A'),
                    order.get('table') or order.get('customer_name', 'N/A'),
                    order.get('customer_phone', 'N/A'),
                    order['items'].replace('\n', '; '),
                    order['status'],
                    order['timestamp'],
                    order.get('completed_at', 'N/A'),
                    order.get('pickup_time', 'N/A')
                ])
            
            csv_data = output.getvalue()
            
            st.download_button(
                label="💾 Download CSV",
                data=csv_data,
                file_name=f"restaurant_orders_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    # Summary stats at bottom
    st.divider()
    st.markdown("### 📋 Summary Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Order Types:**")
        st.text(f"🍽️ Dine-In: {dine_in_count} ({dine_in_count/total_orders*100:.1f}%)" if total_orders > 0 else "No data")
        st.text(f"🥡 Take-Out: {takeout_count} ({takeout_count/total_orders*100:.1f}%)" if total_orders > 0 else "No data")
    
    with col2:
        st.markdown("**Status:**")
        completed = len([o for o in filtered_orders if o['status'] in ['Done', 'Picked-Up']])
        pending = len([o for o in filtered_orders if o['status'] == 'Pending'])
        ready = len([o for o in filtered_orders if o['status'] == 'Ready'])
        st.text(f"✅ Completed: {completed}")
        st.text(f"🟢 Ready: {ready}")
        st.text(f"🟡 Pending: {pending}")
    
    with col3:
        st.markdown("**Date Range:**")
        st.text(f"From: {min([datetime.strptime(o['timestamp'], '%Y-%m-%d %H:%M:%S').date() for o in filtered_orders])}")
        st.text(f"To: {max([datetime.strptime(o['timestamp'], '%Y-%m-%d %H:%M:%S').date() for o in filtered_orders])}")
        st.text(f"Days: {len(set([datetime.strptime(o['timestamp'], '%Y-%m-%d %H:%M:%S').date() for o in filtered_orders]))}")

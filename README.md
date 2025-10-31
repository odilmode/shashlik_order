# 🍽️ Restaurant Order Management System

A real-time, multi-device restaurant ordering system built with **Streamlit** and **Firebase Realtime Database**. Waiters can take orders on tablets/phones, and orders instantly appear on the kitchen display — no manual refresh needed!

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)
![Firebase](https://img.shields.io/badge/firebase-realtime-orange.svg)

---

## ✨ Features

- 🔄 **Real-time synchronization** across all devices
- 👨‍💼 **Waiter Terminal** for easy order entry
- 👨‍🍳 **Kitchen Dashboard** with live order tracking
- 🔔 **Sound notifications** for new orders
- 📊 **Live metrics** (pending/completed/total orders)
- 🗂️ **Smart filtering** (Pending, Completed, All Orders tabs)
- ⏱️ **Timestamp tracking** for order timing
- 🗑️ **Order management** (mark done, delete)
- 📱 **Mobile-friendly** responsive design
- 🔐 **Secure deployment** with environment variables

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Firebase account (free tier)
- Git installed

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/restaurant-order-system.git
cd restaurant-order-system
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Firebase

#### Create Firebase Project:
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project" → Name it (e.g., `restaurant-orders`)
3. Disable Google Analytics (optional)
4. Click "Create Project"

#### Create Realtime Database:
1. In Firebase Console → "Build" → "Realtime Database"
2. Click "Create Database"
3. Choose location (nearest to you)
4. Select "Start in **test mode**"
5. Click "Enable"

#### Get Database URL:
Copy the URL shown (looks like):
```
https://restaurant-orders-xxxxx-default-rtdb.firebaseio.com/
```

#### Download Credentials:
1. Go to Project Settings (⚙️ icon) → "Service accounts"
2. Click "Generate new private key"
3. Save the downloaded JSON file as `firebase_key.json` in your project root

### 4. Configure Environment

Create a `.env` file (optional for local development):
```bash
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com/
```

### 5. Run Locally

```bash
streamlit run restaurant_app.py
```

Open your browser to `http://localhost:8501`

---

## 📁 Project Structure

```
restaurant-order-system/
│
├── restaurant_app.py          # Main application
├── firebase_key.json          # Firebase credentials (DO NOT COMMIT!)
├── requirements.txt           # Python dependencies
├── .gitignore                # Git ignore rules
├── README.md                 # This file
│
└── .streamlit/               # Streamlit config (optional)
    └── config.toml
```

---

## 🌐 Deploy to Streamlit Cloud

### 1. Prepare Repository

**IMPORTANT:** Never commit `firebase_key.json` to GitHub!

Ensure your `.gitignore` includes:
```
firebase_key.json
__pycache__/
*.pyc
.env
*.log
.DS_Store
```

### 2. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/restaurant-order-system.git
git push -u origin main
```

### 3. Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io/)
2. Sign in with GitHub
3. Click "New app"
4. Select your repository
5. Main file path: `restaurant_app.py`
6. **Before deploying**, click "Advanced settings"

### 4. Configure Secrets

Click on "Secrets" and add:

```toml
# Paste the ENTIRE contents of your firebase_key.json as a JSON string
FIREBASE_CONFIG = '''
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxxx%40your-project.iam.gserviceaccount.com"
}
'''

FIREBASE_DATABASE_URL = "https://your-project-xxxxx-default-rtdb.firebaseio.com/"
```

**How to format your firebase_key.json for secrets:**
1. Open `firebase_key.json` in a text editor
2. Copy the **entire content**
3. Paste between the `'''` quotes above
4. Make sure the private key's `\n` characters are preserved

### 5. Deploy

Click "Deploy" and wait 2-3 minutes.

Your app will be live at: `https://your-app-name.streamlit.app`

---

## 🔒 Firebase Security Rules

After testing, secure your database:

1. Go to Firebase Console → Realtime Database → Rules
2. Replace with:

```json
{
  "rules": {
    "orders": {
      ".read": true,
      ".write": true,
      ".indexOn": ["status", "timestamp"],
      "$order_id": {
        ".validate": "newData.hasChildren(['table', 'items', 'status', 'timestamp'])"
      }
    }
  }
}
```

3. Click "Publish"

**For production (with authentication):**
```json
{
  "rules": {
    "orders": {
      ".read": "auth != null",
      ".write": "auth != null"
    }
  }
}
```

---

## 📱 Usage

### For Waiters:
1. Open the app URL
2. Select **"🍽️ Waiter Terminal"** from sidebar
3. Enter table number and order items
4. Click "Send to Kitchen"
5. Order appears instantly on kitchen screen

### For Kitchen:
1. Open the app URL
2. Select **"👨‍🍳 Kitchen Dashboard"** from sidebar
3. View incoming orders in real-time
4. Click "Done" when order is ready
5. Status updates on all waiter devices

### Tips:
- 📌 **Bookmark** the app on tablets for quick access
- 🔊 **Enable sound** in browser for order notifications
- 🖥️ **Keep kitchen tab open** to prevent app from sleeping
- 📱 **Add to home screen** on mobile devices

---

## ⚙️ Configuration

### Auto-Refresh Interval

Change refresh rate in `restaurant_app.py`:

```python
# Default: 5 seconds
auto_refresh(5)

# Slower (saves bandwidth): 10 seconds
auto_refresh(10)

# Faster (more real-time): 3 seconds
auto_refresh(3)
```

### Customize Menu

Add a predefined menu (optional):

```python
MENU_ITEMS = {
    "Burgers": ["Cheeseburger", "Bacon Burger", "Veggie Burger"],
    "Drinks": ["Coke", "Sprite", "Water", "Coffee"],
    "Sides": ["Fries", "Salad", "Onion Rings", "Coleslaw"]
}
```

---

## 🐛 Troubleshooting

### Issue: "Firebase connection failed"
**Solution:** 
- Check `FIREBASE_DATABASE_URL` is correct
- Verify it includes `https://` and ends with `.firebaseio.com/`
- Ensure Firebase credentials are valid

### Issue: "Orders not syncing"
**Solution:**
- Check Firebase security rules allow read/write
- Verify internet connection on all devices
- Check browser console for errors (F12)

### Issue: "App keeps sleeping"
**Solution:**
- Keep kitchen browser tab open and active
- Consider upgrading to Streamlit Teams plan ($20/month) for always-on apps
- Set auto-refresh to trigger activity

### Issue: "Sound notifications not working"
**Solution:**
- Click anywhere on page to enable audio
- Check browser sound permissions
- Ensure browser tab is not muted

### Issue: "Can't find firebase_key.json"
**Solution:**
- Make sure file is in project root directory
- Check file name is exactly `firebase_key.json`
- For deployment, use Streamlit secrets instead

---

## 📊 Monitoring Usage

### Check Firebase Usage:
1. Firebase Console → Usage and billing
2. Monitor:
   - Database storage (1 GB free)
   - Downloads (10 GB/month free)
   - Simultaneous connections (100 free)

### Typical Usage (small restaurant):
- **Storage:** ~500 bytes per order
- **Bandwidth:** ~36 MB/hour (5-second refresh)
- **Connections:** 5-10 devices

### Stay in Free Tier:
- Use 10-second refresh instead of 5-second
- Clear old completed orders regularly
- Limit to essential devices only

---

## 🔄 Updating the App

### Update Code Locally:
```bash
git pull origin main
```

### Push Updates:
```bash
git add .
git commit -m "Description of changes"
git push origin main
```

Streamlit Cloud will **auto-deploy** your changes in 1-2 minutes!

### Update Dependencies:
If you add new packages, update `requirements.txt`:
```bash
pip freeze > requirements.txt
```

Then push to GitHub.

---

## 🎨 Customization Ideas

### Add Features:
- ✅ Waiter authentication (Firebase Auth)
- ✅ Order priority flags (urgent orders)
- ✅ Estimated prep time per dish
- ✅ Daily sales reports
- ✅ Table status tracking
- ✅ Multi-language support
- ✅ Print receipts
- ✅ Customer feedback system

### UI Improvements:
- Custom color themes
- Restaurant logo
- Dark mode toggle
- Custom fonts

---

## 📦 Dependencies

```
streamlit>=1.28.0
firebase-admin>=6.2.0
```

Full list in `requirements.txt`

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io/) - Web framework
- [Firebase](https://firebase.google.com/) - Realtime database
- [Lucide Icons](https://lucide.dev/) - Icon set

---

## 📧 Support

- **Issues:** [GitHub Issues](https://github.com/YOUR_USERNAME/restaurant-order-system/issues)
- **Discussions:** [GitHub Discussions](https://github.com/YOUR_USERNAME/restaurant-order-system/discussions)
- **Email:** your-email@example.com

---

##

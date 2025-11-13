# app/frontend/components/login_page.py
import streamlit as st
import requests
from app.core.config import settings
import json

def render_login_page():
    """Render the login page with tabs for User and Authority"""
    
    # Custom CSS for login page
    st.markdown("""
    <style>
    .login-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 2rem;
    }
    .login-header {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
    }
    .login-form {
        background: rgba(255, 255, 255, 0.05);
        padding: 2rem;
        border-radius: 15px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem;
        border-radius: 10px;
        font-size: 1.1rem;
        font-weight: bold;
        margin-top: 1rem;
    }
    .stButton>button:hover {
        opacity: 0.9;
    }
    .divider {
        text-align: center;
        margin: 1.5rem 0;
        color: #888;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="login-header">
        <h1>🏙️ Smart City Login</h1>
        <p>Access your sustainable city dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for User and Authority login
    tab1, tab2 = st.tabs(["👤 User Login", "🏛️ Authority Login"])

    with tab1:
        render_user_login()

    with tab2:
        render_authority_login()
    
    # Registration link
    st.markdown("<div class='divider'>Don't have an account?</div>", unsafe_allow_html=True)
    if st.button("📝 Register New Account", use_container_width=True):
        st.session_state.page = "register"
        st.rerun()

def render_user_login():
    """Render user login form"""
    st.markdown("### 👤 User Login")
    st.write("Login with your phone number or email")
    
    with st.form("user_login_form"):
        identifier = st.text_input(
            "📱 Phone Number or Email",
            placeholder="Enter your phone number or email",
            help="You can use either your phone number or email to login"
        )
        
        password = st.text_input(
            "🔒 Password",
            type="password",
            placeholder="Enter your password"
        )
        
        remember_me = st.checkbox("Remember me")
        
        submit = st.form_submit_button("🚀 Login as User", use_container_width=True)
        
        if submit:
            if not identifier or not password:
                st.error("❌ Please fill in all fields")
            else:
                perform_login(identifier, password, "user")

def render_authority_login():
    """Render authority login form"""
    st.markdown("### 🏛️ Authority Login")
    st.write("Login with your registered credentials")
    
    with st.form("authority_login_form"):
        identifier = st.text_input(
            "📱 Phone Number or Email",
            placeholder="Enter your phone number or email",
            help="Use your registered phone number or email"
        )
        
        password = st.text_input(
            "🔒 Password",
            type="password",
            placeholder="Enter your password"
        )
        
        remember_me = st.checkbox("Remember me")
        
        submit = st.form_submit_button("🚀 Login as Authority", use_container_width=True)
        
        if submit:
            if not identifier or not password:
                st.error("❌ Please fill in all fields")
            else:
                perform_login(identifier, password, "authority")

def perform_login(identifier: str, password: str, login_type: str):
    """Perform login API call"""
    with st.spinner("🔐 Authenticating..."):
        try:
            # Prepare login request
            login_data = {
                "identifier": identifier.strip(),
                "password": password
            }
            
            # Call login API
            endpoint = "/api/auth/login"

            response = requests.post(
                f"http://{settings.api_host}:{settings.api_port}{endpoint}",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()

                returned_type = str(result.get("user_type", "")).lower()
                expected_type = login_type.lower()
                if returned_type != expected_type:
                    tab_hint = "authority" if returned_type == "authority" else "user"
                    st.error(
                        "❌ This account type should sign in from the "
                        f"{tab_hint.capitalize()} Login tab."
                    )
                    return

                # Store user data in session state
                st.session_state.logged_in = True
                st.session_state.user_data = result["user_data"]
                st.session_state.user_type = result["user_type"]
                st.session_state.token = result["token"]
                st.session_state.page = "dashboard"
                
                st.success(f"✅ {result['message']}")
                st.balloons()
                
                # Redirect to dashboard
                st.rerun()
                
            elif response.status_code == 401:
                detail = response.json().get("detail", "Invalid credentials")
                st.error(f"❌ {detail}")
            else:
                error_detail = response.json().get("detail", "Login failed")
                st.error(f"❌ {error_detail}")
                
        except requests.exceptions.ConnectionError:
            st.error("🔌 Unable to connect to authentication service. Please ensure the backend is running.")
            st.info("💡 Run the backend with: `python run_app.py` or `uvicorn app.main:app --reload`")
        except requests.exceptions.Timeout:
            st.error("⏱️ Login request timed out. Please try again.")
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            st.info("Please check your internet connection and try again.")

def show_forgot_password():
    """Show forgot password dialog"""
    st.info("🔑 Password reset functionality will be available soon. Please contact support for assistance.")

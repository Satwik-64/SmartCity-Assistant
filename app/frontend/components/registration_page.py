# app/frontend/components/registration_page.py
import streamlit as st
import requests
import re
from app.core.config import settings

AUTHORITY_ROUTE_OPTIONS = [
    "Mayor's Office",
    "City Council",
    "Public Works Department",
    "Transportation Authority",
    "Environmental Services",
    "Health & Safety Department",
    "Housing & Urban Development",
]

def render_registration_page():
    """Render the registration page with tabs for User and Authority"""
    
    # Custom CSS for registration page
    st.markdown("""
    <style>
    .register-container {
        max-width: 600px;
        margin: 0 auto;
        padding: 2rem;
    }
    .register-header {
        text-align: center;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
    }
    .register-form {
        background: rgba(255, 255, 255, 0.05);
        padding: 2rem;
        border-radius: 15px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .form-section {
        margin-bottom: 1.5rem;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.02);
        border-radius: 10px;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        border: none;
        padding: 0.75rem;
        border-radius: 10px;
        font-size: 1.1rem;
        font-weight: bold;
        margin-top: 1rem;
    }
    .info-box {
        background: rgba(33, 150, 243, 0.1);
        border-left: 4px solid #2196F3;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="register-header">
        <h1>📝 Create New Account</h1>
        <p>Join the sustainable smart city community</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for User and Authority registration
    tab1, tab2 = st.tabs(["👤 User Registration", "🏛️ Authority Registration"])
    
    with tab1:
        render_user_registration()
    
    with tab2:
        render_authority_registration()
    
    # Login link
    st.markdown("<div style='text-align: center; margin: 1.5rem 0; color: #888;'>Already have an account?</div>", unsafe_allow_html=True)
    if st.button("🔐 Back to Login", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()

def render_user_registration():
    """Render user registration form"""
    st.markdown("### 👤 User Registration")
    st.markdown('<div class="info-box">📋 Register as a citizen to access city services and provide feedback</div>', unsafe_allow_html=True)
    
    with st.form("user_registration_form"):
        st.markdown("#### Personal Information")
        
        name = st.text_input(
            "👤 Full Name *",
            placeholder="Enter your full name",
            help="Your full legal name"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            phone_number = st.text_input(
                "📱 Phone Number *",
                placeholder="+1234567890",
                help="Your primary contact number (with country code)"
            )
        
        with col2:
            email = st.text_input(
                "📧 Email (Optional)",
                placeholder="your.email@example.com",
                help="Email address for notifications"
            )
        
        address = st.text_area(
            "🏠 Address (Optional)",
            placeholder="Enter your full address",
            help="Your residential address",
            height=100
        )
        
        st.markdown("#### Security")
        
        col1, col2 = st.columns(2)
        
        with col1:
            password = st.text_input(
                "🔒 Password *",
                type="password",
                placeholder="Minimum 6 characters",
                help="Choose a strong password"
            )
        
        with col2:
            confirm_password = st.text_input(
                "🔒 Confirm Password *",
                type="password",
                placeholder="Re-enter password"
            )
        
        # Terms and conditions
        agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy *")
        
        submit = st.form_submit_button("📝 Register as User", use_container_width=True)
        
        if submit:
            # Validate inputs
            errors = validate_user_registration(name, phone_number, email, password, confirm_password, agree_terms)
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                register_user(name, phone_number, email, password, address)

def render_authority_registration():
    """Render authority registration form"""
    st.markdown("### 🏛️ Authority Registration")
    st.markdown('<div class="info-box">🏢 Register as a government official or department representative</div>', unsafe_allow_html=True)
    
    with st.form("authority_registration_form"):
        st.markdown("#### Personal Information")

        name = st.text_input(
            "👤 Full Name *",
            placeholder="Enter your full name",
            help="Your official name as per government records"
        )

        position = st.selectbox(
            "💼 Position (routing label) *",
            AUTHORITY_ROUTE_OPTIONS,
            help="Select the citizen routing label that should deliver reports to your team",
        )
        
        st.markdown("#### Contact Information")

        col_contact_1, col_contact_2 = st.columns(2)

        with col_contact_1:
            phone_number = st.text_input(
                "📱 Official Phone Number *",
                placeholder="+1234567890",
                help="Your official contact number"
            )

        with col_contact_2:
            email = st.text_input(
                "📧 Official Email *",
                placeholder="official.email@gov.com",
                help="Your official government email address"
            )

        st.markdown("#### Security")
        
        col1, col2 = st.columns(2)
        
        with col1:
            password = st.text_input(
                "🔒 Password *",
                type="password",
                placeholder="Minimum 6 characters",
                help="Choose a strong password"
            )
        
        with col2:
            confirm_password = st.text_input(
                "🔒 Confirm Password *",
                type="password",
                placeholder="Re-enter password"
            )
        
        # Terms and verification
        agree_terms = st.checkbox("I confirm that I am a government official and agree to the Terms of Service *")
        
        st.info("⚠️ Authority accounts may require admin approval before activation")
        
        submit = st.form_submit_button("📝 Register as Authority", use_container_width=True)
        
        if submit:
            # Validate inputs
            errors = validate_authority_registration(
                name,
                position,
                phone_number,
                email,
                password,
                confirm_password,
                agree_terms,
            )
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                register_authority(name, position, phone_number, email, password)

def validate_user_registration(name, phone, email, password, confirm_password, agree_terms):
    """Validate user registration inputs"""
    errors = []
    
    if not name or len(name.strip()) < 2:
        errors.append("Name must be at least 2 characters long")
    
    if not phone or len(phone.strip()) < 10:
        errors.append("Phone number must be at least 10 digits")
    
    if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        errors.append("Invalid email format")
    
    if not password or len(password) < 6:
        errors.append("Password must be at least 6 characters long")
    
    if password != confirm_password:
        errors.append("Passwords do not match")
    
    if not agree_terms:
        errors.append("You must agree to the Terms of Service")
    
    return errors

def validate_authority_registration(
    name,
    position,
    phone,
    email,
    password,
    confirm_password,
    agree_terms,
):
    """Validate authority registration inputs"""
    errors = []
    
    if not name or len(name.strip()) < 2:
        errors.append("Name must be at least 2 characters long")
    
    if not position or len(position.strip()) < 2:
        errors.append("Position is required")

    if not phone or len(phone.strip()) < 10:
        errors.append("Phone number must be at least 10 digits")
    
    if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        errors.append("Valid email is required for authority registration")
    
    if not password or len(password) < 6:
        errors.append("Password must be at least 6 characters long")
    
    if password != confirm_password:
        errors.append("Passwords do not match")
    
    if not agree_terms:
        errors.append("You must confirm you are a government official and agree to Terms of Service")
    
    return errors

def register_user(name, phone, email, password, address):
    """Register a new user via API"""
    with st.spinner("📝 Creating your account..."):
        try:
            # Prepare registration data
            registration_data = {
                "name": name.strip(),
                "phone_number": phone.strip(),
                "password": password,
                "email": email.strip() if email else None,
                "address": address.strip() if address else None
            }
            
            # Call registration API
            response = requests.post(
                f"http://{settings.api_host}:{settings.api_port}/api/auth/register/user",
                json=registration_data,
                timeout=10
            )
            
            if response.status_code == 200:
                st.success("✅ Registration successful! You can now login.")
                st.balloons()
                
                # Redirect to login after 2 seconds
                import time
                time.sleep(2)
                st.session_state.page = "login"
                st.rerun()
                
            elif response.status_code == 400:
                error_detail = response.json().get("detail", "Registration failed")
                st.error(f"❌ {error_detail}")
            else:
                st.error("❌ Registration failed. Please try again.")
                
        except requests.exceptions.ConnectionError:
            st.error("🔌 Unable to connect to server. Please ensure the backend is running.")
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")

def register_authority(name, position, phone, email, password):
    """Register a new authority via API"""
    with st.spinner("📝 Creating your authority account..."):
        try:
            # Prepare registration data
            registration_data = {
                "name": name.strip(),
                "position": position.strip(),
                "feedback_route": position.strip(),
                "phone_number": phone.strip(),
                "email": email.strip(),
                "password": password
            }
            
            # Call registration API
            response = requests.post(
                f"http://{settings.api_host}:{settings.api_port}/api/auth/register/authority",
                json=registration_data,
                timeout=10
            )
            
            if response.status_code == 200:
                st.success("✅ Authority registration received!")
                st.info(
                    "�️ Your account is pending admin approval. We'll notify you once it's activated."
                )
                st.balloons()
                
                # Redirect to login after 2 seconds
                import time
                time.sleep(2)
                st.session_state.page = "login"
                st.rerun()
                
            elif response.status_code == 400:
                error_detail = response.json().get("detail", "Registration failed")
                st.error(f"❌ {error_detail}")
            else:
                st.error("❌ Registration failed. Please try again.")
                
        except requests.exceptions.ConnectionError:
            st.error("🔌 Unable to connect to server. Please ensure the backend is running.")
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")

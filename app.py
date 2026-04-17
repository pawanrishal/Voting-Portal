import streamlit as st
import sqlite3
from datetime import datetime
import os

# Set page configuration
st.set_page_config(
    page_title="CR Voting Portal",
    page_icon="🗳️",
    layout="centered"
)

# Admin password (change this to your desired password)
ADMIN_PASSWORD = "admin123"

# Database setup
DB_FILE = "votes.db"

def init_database():
    """Initialize the database with votes and candidates tables"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id)
        )
    ''')
    conn.commit()
    conn.close()

def ensure_two_candidates():
    """Ensure exactly 2 candidate slots exist"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM candidates')
    count = c.fetchone()[0]
    
    if count == 0:
        c.execute('INSERT INTO candidates (name) VALUES (?)', ("Rajat Upadhaya",))
        c.execute('INSERT INTO candidates (name) VALUES (?)', ("Bidan Dev",))
        conn.commit()
    conn.close()

def update_candidate(candidate_id, name):
    """Update candidate name"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE candidates SET name = ? WHERE id = ?', (name, candidate_id))
    conn.commit()
    conn.close()

def get_candidates():
    """Get all candidates from the database"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, name FROM candidates ORDER BY id')
    results = c.fetchall()
    conn.close()
    return results

def add_vote(candidate_id):
    """Add a vote to the database"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO votes (candidate_id) VALUES (?)', (candidate_id,))
    conn.commit()
    conn.close()

def get_vote_counts():
    """Get vote counts for all candidates"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        SELECT c.name, COUNT(v.id) as count 
        FROM candidates c 
        LEFT JOIN votes v ON c.id = v.candidate_id 
        GROUP BY c.id, c.name 
        ORDER BY c.id
    ''')
    results = c.fetchall()
    conn.close()
    return results

def reset_votes():
    """Clear all votes from the database"""
    if os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('DELETE FROM votes')
        conn.commit()
        conn.close()

def reset_all():
    """Clear all votes and candidates, then reset to 2 default candidates"""
    if os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('DELETE FROM votes')
        c.execute('DELETE FROM candidates')
        c.execute('INSERT INTO candidates (name) VALUES (?)', ("Rajat Upadhaya",))
        c.execute('INSERT INTO candidates (name) VALUES (?)', ("Bidan Dev",))
        conn.commit()
        conn.close()

# Initialize database
init_database()
ensure_two_candidates()

# Initialize session state variables
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

if "voted" not in st.session_state:
    st.session_state.voted = False

if "confirmation_message" not in st.session_state:
    st.session_state.confirmation_message = ""

# Sidebar - Election Panel
st.sidebar.title("🗳️ Election Panel")

# Admin Login Section
if not st.session_state.is_admin:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔐 Admin Login")
    admin_password = st.sidebar.text_input("Enter Admin Password:", type="password", key="admin_pwd")
    
    if st.sidebar.button("Login as Admin", key="admin_login"):
        if admin_password == ADMIN_PASSWORD:
            st.session_state.is_admin = True
            st.sidebar.success("✅ Admin logged in!")
            st.rerun()
        else:
            st.sidebar.error("❌ Incorrect password!")
else:
    st.sidebar.markdown("---")
    st.sidebar.success("✅ Admin Mode Active")
    
    # Candidate Management
    st.sidebar.subheader("👥 Set Candidate Names")
    
    candidates_list = get_candidates()
    
    for cand_id, cand_name in candidates_list:
        edited_name = st.sidebar.text_input(
            f"Candidate {cand_id}:",
            value=cand_name,
            key=f"candidate_{cand_id}"
        )
        
        if edited_name != cand_name:
            if st.sidebar.button(f"✅ Update Candidate {cand_id}", key=f"update_{cand_id}"):
                if edited_name.strip():
                    update_candidate(cand_id, edited_name.strip())
                    st.sidebar.success("✅ Updated!")
                    st.rerun()
                else:
                    st.sidebar.error("❌ Name cannot be empty!")
    
    st.sidebar.markdown("---")
    
    # Reset votes button - only visible to admin
    if st.sidebar.button("🔄 Reset Votes Only", key="reset_votes"):
        reset_votes()
        st.session_state.confirmation_message = ""
        st.sidebar.success("All votes have been reset!")
        st.rerun()
    
    # Reset all button
    if st.sidebar.button("🗑️ Reset All (Votes & Candidates)", key="reset_all"):
        reset_all()
        st.session_state.confirmation_message = ""
        st.sidebar.success("All votes and candidates have been reset!")
        st.rerun()
    
    # Logout button
    if st.sidebar.button("🚪 Logout", key="admin_logout"):
        st.session_state.is_admin = False
        st.rerun()

# Main content
st.title("Class Representative Voting Portal")
st.subheader("Vote for your preferred candidate.")
st.divider()

# Show voting interface only for non-admin users
if not st.session_state.is_admin:
    # Voting Section
    st.markdown("### 🗳️ Cast Your Vote")
    
    candidates_list = get_candidates()
    
    # Create a mapping of candidate names to IDs
    candidate_dict = {name: cand_id for cand_id, name in candidates_list}
    candidate_names = [name for _, name in candidates_list]
    
    # Radio button for candidate selection
    selected_candidate = st.radio(
        "Select a candidate:",
        candidate_names,
        key="candidate_selection"
    )

    # Submit vote button
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Submit Vote", key="submit_vote", use_container_width=True):
            if selected_candidate:
                candidate_id = candidate_dict[selected_candidate]
                add_vote(candidate_id)
                st.session_state.voted = True
                st.session_state.confirmation_message = f"Your vote for {selected_candidate} has been recorded."
                st.rerun()

    # Display confirmation message
    if st.session_state.voted and st.session_state.confirmation_message:
        st.success(st.session_state.confirmation_message)

    st.divider()
    st.info("💡 To view election results, please contact the admin.", icon="ℹ️")

else:
    # Admin Results Section - Only visible to admin
    st.markdown("### 📊 Election Results (Admin View)")
    st.info("ℹ️ You are viewing as an admin. Voting interface is hidden in admin mode.", icon="ℹ️")
    st.divider()

    vote_results = get_vote_counts()
    total_votes = sum(count for _, count in vote_results)

    # Display vote counts using metrics in columns
    col1, col2 = st.columns(2)
    with col1:
        st.metric(vote_results[0][0], vote_results[0][1], delta=None)
    with col2:
        st.metric(vote_results[1][0], vote_results[1][1], delta=None)

    st.markdown(f"**Total Votes Recorded:** {total_votes}")

    # Determine winner and display announcement
    st.divider()
    if total_votes == 0:
        st.warning("⏳ No votes recorded yet.", icon="⏱️")
    else:
        vote_dict = {name: count for name, count in vote_results}
        max_votes = max(vote_dict.values())
        winners = [name for name, count in vote_dict.items() if count == max_votes]
        
        if len(winners) == 1:
            st.success(
                f"🎉 Congratulations {winners[0]}! You have won the CR Election!",
                icon="✅"
            )
        else:
            st.info(f"🤝 The election resulted in a tie!", icon="ℹ️")

st.divider()

# Footer
st.markdown(
    """
    <div style='text-align: center; margin-top: 2rem; color: #888;'>
        <small>Class Representative Election Portal | Built with Streamlit</small>
    </div>
    """,
    unsafe_allow_html=True
)

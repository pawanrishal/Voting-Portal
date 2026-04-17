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
    """Initialize the database with votes, candidates and voters tables"""
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
            voter_code TEXT UNIQUE NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS voters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT,
            has_voted INTEGER NOT NULL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()


def ensure_votes_schema():
    """Enable voter_code uniqueness for existing votes table"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('PRAGMA table_info(votes)')
    columns = [row[1] for row in c.fetchall()]
    if 'voter_code' not in columns:
        c.execute('ALTER TABLE votes ADD COLUMN voter_code TEXT')
    c.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_votes_voter_code ON votes(voter_code)')
    conn.commit()
    conn.close()

def ensure_two_candidates():
    """Ensure there are at least 2 candidate slots available"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT name FROM candidates')
    existing = [row[0] for row in c.fetchall()]

    default_names = ["Candidate 1", "Candidate 2"]
    for name in default_names:
        if len(existing) >= 2:
            break
        if name not in existing:
            c.execute('INSERT INTO candidates (name) VALUES (?)', (name,))
            existing.append(name)

    if len(existing) < 2 and not existing:
        c.execute('INSERT INTO candidates (name) VALUES (?)', ("Candidate 1",))
        c.execute('INSERT INTO candidates (name) VALUES (?)', ("Candidate 2",))

    conn.commit()
    conn.close()

def add_candidate(name):
    """Add a candidate to the database"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO candidates (name) VALUES (?)', (name,))
    conn.commit()
    conn.close()


def delete_candidate(candidate_id):
    """Delete a candidate and its votes from the database"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM votes WHERE candidate_id = ?', (candidate_id,))
    c.execute('DELETE FROM candidates WHERE id = ?', (candidate_id,))
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

def add_vote(candidate_id, voter_code):
    """Add a vote to the database"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO votes (candidate_id, voter_code) VALUES (?, ?)', (candidate_id, voter_code))
    c.execute('UPDATE voters SET has_voted = 1 WHERE code = ?', (voter_code,))
    conn.commit()
    conn.close()


def add_voter(code, name=None):
    """Add an allowed voter code"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO voters (code, name) VALUES (?, ?)', (code, name))
    conn.commit()
    conn.close()


def get_voter(code):
    """Fetch a registered voter by code"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, code, name, has_voted FROM voters WHERE code = ?', (code,))
    voter = c.fetchone()
    conn.close()
    return voter


def delete_voter(code):
    """Delete a registered voter code and any related vote"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM votes WHERE voter_code = ?', (code,))
    c.execute('DELETE FROM voters WHERE code = ?', (code,))
    conn.commit()
    conn.close()


def get_voters():
    """Get all registered voter codes"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT code, name, has_voted FROM voters ORDER BY id')
    results = c.fetchall()
    conn.close()
    return results

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
        c.execute('UPDATE voters SET has_voted = 0')
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
ensure_votes_schema()
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
    st.sidebar.info("Enter the candidate names for this election. Save to apply changes.")
    
    candidates_list = get_candidates()
    new_names = []
    candidate_ids = []

    for position, (cand_id, cand_name) in enumerate(candidates_list, start=1):
        group = st.sidebar.container()
        edited_name = group.text_input(
            f"Candidate {position}:",
            value=cand_name,
            key=f"candidate_{position}"
        )

        if group.button("Delete", key=f"delete_{position}"):
            if len(candidates_list) <= 1:
                st.sidebar.error("❌ At least one candidate must remain.")
            else:
                delete_candidate(cand_id)
                st.sidebar.success(f"✅ Candidate {position} deleted.")
                st.rerun()

        group.markdown("---")
        new_names.append(edited_name)
        candidate_ids.append(cand_id)

    if st.sidebar.button("💾 Save Candidate Names", key="save_candidate_names"):
        if all(name.strip() for name in new_names):
            for cand_id, name in zip(candidate_ids, new_names):
                update_candidate(cand_id, name.strip())
            st.sidebar.success("✅ Candidate names saved!")
            st.rerun()
        else:
            st.sidebar.error("❌ Candidate names cannot be empty!")

    st.sidebar.markdown("---")
    st.sidebar.subheader("➕ Add New Candidate")
    new_candidate_name = st.sidebar.text_input(
        "New candidate name:",
        value="",
        key="new_candidate_name"
    )

    if st.sidebar.button("Add Candidate", key="add_candidate"):
        if new_candidate_name.strip():
            try:
                add_candidate(new_candidate_name.strip())
                st.sidebar.success("✅ Candidate added successfully!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.sidebar.error("❌ Candidate name must be unique.")
        else:
            st.sidebar.error("❌ Please enter a candidate name.")

    st.sidebar.markdown("---")
    st.sidebar.subheader("🧾 Manage Voter Codes")
    new_voter_code = st.sidebar.text_input(
        "New voter code:",
        value="",
        key="new_voter_code"
    )
    new_voter_name = st.sidebar.text_input(
        "Voter name (optional):",
        value="",
        key="new_voter_name"
    )

    if st.sidebar.button("Add Voter Code", key="add_voter_code"):
        if new_voter_code.strip():
            add_voter(new_voter_code.strip(), new_voter_name.strip() or None)
            st.sidebar.success("✅ Voter code added successfully!")
            st.rerun()
        else:
            st.sidebar.error("❌ Please enter a voter code.")

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Registered voter codes:**")
    voters_list = get_voters()
    if voters_list:
        for position, (code, name, has_voted) in enumerate(voters_list, start=1):
            group = st.sidebar.container()
            badge = "✅ Voted" if has_voted else "⏳ Not voted"
            display_name = f" — {name}" if name else ""
            group.write(f"**{position}.** `{code}`{display_name} {badge}")
            if group.button("Delete", key=f"delete_voter_{position}"):
                delete_voter(code)
                st.sidebar.success(f"✅ Voter code `{code}` deleted.")
                st.rerun()
            group.markdown("---")
    else:
        st.sidebar.info("No voter codes registered yet. Add codes before voting.")

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

    voters_list = get_voters()
    voter_code = st.text_input("Enter your voter code:", key="voter_code")
    
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
            if not voter_code.strip():
                st.error("❌ Please enter your voter code before voting.")
            elif not voters_list:
                st.error("❌ Voting is not available because no voter codes are registered yet.")
            elif selected_candidate:
                code = voter_code.strip()
                voter = get_voter(code)
                if not voter:
                    st.error("❌ Invalid voter code. Please enter a valid registered code.")
                elif voter[3] == 1:
                    st.error("❌ This voter code has already been used.")
                else:
                    candidate_id = candidate_dict[selected_candidate]
                    try:
                        add_vote(candidate_id, code)
                        st.session_state.voted = True
                        st.session_state.confirmation_message = f"Your vote for {selected_candidate} has been recorded."
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("❌ This voter code has already been used.")

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

    # Display vote counts for all candidates
    if vote_results:
        for name, count in vote_results:
            st.metric(name, count, delta=None)
    else:
        st.write("No candidates available.")

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

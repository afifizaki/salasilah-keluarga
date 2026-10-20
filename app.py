import streamlit as st
import pandas as pd
import sqlite3

# ---------------------------------------------------------
# CONFIGURE STREAMLIT PAGE
# ---------------------------------------------------------
st.set_page_config(
    page_title="Salasilah Keluarga",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide"
)

# Connect to SQLite Database
conn = sqlite3.connect('salasilah_keluarga.db', check_same_thread=False)
cursor = conn.cursor()

# Make sure table exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS ahli_keluarga (
        id TEXT PRIMARY KEY,
        branch_no INTEGER,
        full_name TEXT,
        parent_spouse_id TEXT,
        relationship TEXT,
        gender TEXT
    )
''')
conn.commit()

# ---------------------------------------------------------
# SIDEBAR: ADMIN LOGIN SYSTEM (READ-ONLY DEFAULT)
# ---------------------------------------------------------
st.sidebar.title("🔒 Mod Capaian")

# Tentukan kata laluan Admin anda di sini (Boleh ditukar mengikut cita rasa)
ADMIN_PASSWORD = "keluarga123"

is_admin = False
mode = st.sidebar.radio("Pilih Mod:", ["👁️ Paparan Awam (Read-Only)", "✏️ Mod Pentadbir (Admin)"])

if mode == "✏️ Mod Pentadbir (Admin)":
    password_input = st.sidebar.text_input("Masukkan Kata Laluan Admin:", type="password")
    if password_input == ADMIN_PASSWORD:
        is_admin = True
        st.sidebar.success("✅ Log masuk Pentadbir berjaya!")
    elif password_input != "":
        st.sidebar.error("❌ Kata laluan salah!")

st.sidebar.divider()
st.sidebar.info("💡 **Nota:** Ahli keluarga awam tidak boleh mengedit atau memadam sebarang data pangkalan data.")

st.title("👨‍👩‍👧‍👦 Sistem Salasilah Keluarga")

# ---------------------------------------------------------
# TABS SELECTION BASED ON ROLE
# ---------------------------------------------------------
if is_admin:
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Senarai Ahli", 
        "🗺️ Carta Pokok Salasilah", 
        "➕ Tambah / Kemaskini Ahli", 
        "🗑️ Padam Rekod"
    ])
else:
    tab1, tab2 = st.tabs([
        "📋 Senarai Ahli", 
        "🗺️ Carta Pokok Salasilah"
    ])

# ---------------------------------------------------------
# TAB 1: SENARAI AHLI (READ-ONLY FOR ALL)
# ---------------------------------------------------------
with tab1:
    st.subheader("📋 Senarai Ahli Keluarga")
    
    df_display = pd.read_sql_query(
        "SELECT id AS 'Kod ID', branch_no AS 'Cawangan', full_name AS 'Nama Penuh', relationship AS 'Hubungan', gender AS 'Jantina', parent_spouse_id AS 'ID Ibu Bapa / Pasangan' FROM ahli_keluarga ORDER BY branch_no ASC, id ASC", 
        conn
    )
    
    col_search, col_branch = st.columns(2)
    with col_search:
        search_query = st.text_input("🔍 Cari Nama Ahli Keluarga:")
    with col_branch:
        filter_branch = st.selectbox("🎯 Penapis Cawangan:", ["Semua"] + [f"Cawangan {i:02d}" for i in range(1, 13)] + ["Generasi Atas (Moyang/Datuk/Nenek)"])

    filtered_df = df_display.copy()
    
    if search_query:
        filtered_df = filtered_df[filtered_df['Nama Penuh'].str.contains(search_query, case=False, na=False)]
        
    if filter_branch != "Semua":
        if filter_branch == "Generasi Atas (Moyang/Datuk/Nenek)":
            filtered_df = filtered_df[filtered_df['Cawangan'] == 0]
        else:
            b_num = int(filter_branch.split()[1])
            filtered_df = filtered_df[filtered_df['Cawangan'] == b_num]

    st.dataframe(filtered_df, use_container_width=True)

# ---------------------------------------------------------
# TAB 2: CARTA POKOK SALASILAH (READ-ONLY FOR ALL)
# ---------------------------------------------------------
with tab2:
    st.subheader("🗺️ Carta Pokok Salasilah Keluarga")
    
    try:
        import graphviz
        df_tree = pd.read_sql_query(
            "SELECT id, branch_no, full_name, parent_spouse_id, relationship, gender FROM ahli_keluarga ORDER BY branch_no ASC, id ASC", 
            conn
        )
        
        if not df_tree.empty:
            col_f1, _ = st.columns(2)
            with col_f1:
                branches = ["Semua Cawangan (01-12)"] + [f"Cawangan {i:02d}" for i in range(1, 13)]
                selected_branch = st.selectbox("🎯 Pilih Paparan Cawangan:", branches)

            if selected_branch != "Semua Cawangan (01-12)":
                branch_num = int(selected_branch.split()[1])
                df_filtered = df_tree[(df_tree['branch_no'] == branch_num) | (df_tree['branch_no'] == 0)].copy()
            else:
                df_filtered = df_tree.copy()

            dot = graphviz.Digraph(
                comment='Salasilah Keluarga',
                graph_attr={
                    'rankdir': 'LR',
                    'nodesep': '0.2',
                    'ranksep': '0.8',
                    'splines': 'ortho',
                    'ordering': 'out'
                },
                node_attr={
                    'fontsize': '10',
                    'height': '0.3',
                    'margin': '0.08,0.05'
                }
            )

            ggp_nodes, gp_nodes, gen1_nodes, gen2_nodes, gen3_nodes = [], [], [], [], []

            # 1. BINA NOD UNTUK SETIAP AHLI
            for _, row in df_filtered.iterrows():
                node_id = str(row['id'])
                name = str(row['full_name'])
                gender = str(row['gender'])
                
                shape = "box" if gender == "Lelaki" else "ellipse"
                
                if node_id.startswith('GG'):
                    fillcolor = "#FCF3CF"
                    ggp_nodes.append(node_id)
                elif node_id in ['GF', 'GM']:
                    fillcolor = "#F9E79F"
                    gp_nodes.append(node_id)
                else:
                    clean_id = node_id.rstrip('S')
                    level = len(clean_id) // 2
                    if level == 1:
                        fillcolor = "#D4E6F1" if gender == "Lelaki" else "#FADBD8"
                        gen1_nodes.append(node_id)
                    elif level == 2:
                        fillcolor = "#E8F8F5" if gender == "Lelaki" else "#FEF9E7"
                        gen2_nodes.append(node_id)
                    elif level == 3:
                        fillcolor = "#E8DAEF" if gender == "Lelaki" else "#FDEBD0"
                        gen3_nodes.append(node_id)

                label = f"{name}\n({node_id})" if not node_id.startswith('G') else f"{name}"
                dot.node(node_id, label=label, shape=shape, style="filled", fillcolor=fillcolor, fontname="Arial")

            # 2. SEJAJARKAN KOLUM GENERASI (RANK=SAME)
            for group in [ggp_nodes, gp_nodes, gen1_nodes, gen2_nodes, gen3_nodes]:
                if group:
                    with dot.subgraph() as s:
                        s.attr(rank='same')
                        for n in group:
                            s.node(n)

            existing_ids = set(df_filtered['id'].astype(str).tolist())

            # 3. SAMBUNGAN PASANGAN MOYANG & DATUK/NENEK
            if 'GGF_GF' in existing_ids and 'GGM_GF' in existing_ids:
                dot.edge("GGF_GF", "GGM_GF", style="dashed", color="#7F8C8D", label="pasangan")
            if 'GGF_GM' in existing_ids and 'GGM_GM' in existing_ids:
                dot.edge("GGF_GM", "GGM_GM", style="dashed", color="#7F8C8D", label="pasangan")
            if 'GF' in existing_ids and 'GM' in existing_ids:
                dot.edge("GF", "GM", style="dashed", color="#7F8C8D", label="pasangan")

            # 4. SAMBUNGAN KETURUNAN MOYANG -> DATUK & NENEK
            if 'GGF_GF' in existing_ids and 'GF' in existing_ids:
                dot.edge("GGF_GF", "GF", color="#B7950B", weight="2")
            if 'GGF_GM' in existing_ids and 'GM' in existing_ids:
                dot.edge("GGF_GM", "GM", color="#B7950B", weight="2")

            # 5. GARISAN PASANGAN GEN 1-3
            spouse_rows = df_filtered[
                (df_filtered['relationship'] == 'Spouse') & 
                (~df_filtered['id'].astype(str).str.startswith('G'))
            ]
            for _, sp in spouse_rows.iterrows():
                sp_id = str(sp['id'])
                main_id = str(sp['parent_spouse_id'])
                if main_id in existing_ids:
                    dot.edge(main_id, sp_id, style="dashed", constraint="true", color="#7F8C8D", label="pasangan")

            # 6. PAKSA SUSUNAN GEN 1 DARI ATAS KE BAWAH
            gen1_unique_ids = sorted(list(set(gen1_nodes)))
            for i in range(len(gen1_unique_ids) - 1):
                curr_node = gen1_unique_ids[i]
                next_node = gen1_unique_ids[i+1]
                if curr_node.rstrip('S') != next_node.rstrip('S'):
                    dot.edge(curr_node, next_node, style="invis", constraint="true")

            # 7. GARISAN KETURUNAN IBU BAPA -> ANAK (GEN 1, 2, 3)
            for _, row in df_filtered.iterrows():
                node_id = str(row['id'])
                parent_id = str(row['parent_spouse_id']) if row['parent_spouse_id'] else None
                rel = str(row['relationship'])
                
                if parent_id and parent_id in existing_ids and not node_id.startswith('G'):
                    if rel != 'Spouse' and not node_id.endswith('S'):
                        dot.edge(parent_id, node_id, color="#2C3E50")
                        
            st.graphviz_chart(dot, use_container_width=True)

    except Exception as e:
        st.warning(f"Sila pastikan perisian 'graphviz' terpasang dengan betul. Ralat: {e}")

# ---------------------------------------------------------
# TABS 3 & 4: BORANG PENGURUSAN (KHAS UNTUK ADMIN SAHAJA)
# ---------------------------------------------------------
if is_admin:
    with tab3:
        st.subheader("➕ Tambah atau Kemaskini Ahli Keluarga")
        
        with st.form("form_add_edit"):
            col_id, col_branch = st.columns(2)
            with col_id:
                new_id = st.text_input("Kod ID (Contoh: 01, 01S, 0101, GF):")
            with col_branch:
                new_branch = st.number_input("Nombor Cawangan (0 = Generasi Atas, 1-12 = Cawangan):", min_value=0, max_value=12, value=1)

            new_name = st.text_input("Nama Penuh Ahli Keluarga:")
            
            col_rel, col_gender = st.columns(2)
            with col_rel:
                new_rel = st.selectbox("Hubungan / Peranan:", ["Head", "Spouse", "Child"])
            with col_gender:
                new_gender = st.selectbox("Jantina:", ["Lelaki", "Perempuan"])
                
            new_parent_id = st.text_input("ID Ibu Bapa / Pasangan (Parent/Spouse ID):")
            
            submit_btn = st.form_submit_button("💾 Simpan / Kemaskini Rekod")
            
            if submit_btn:
                if new_id and new_name:
                    cursor.execute('''
                        INSERT OR REPLACE INTO ahli_keluarga (id, branch_no, full_name, parent_spouse_id, relationship, gender)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (new_id.strip(), new_branch, new_name.strip(), new_parent_id.strip() if new_parent_id else None, new_rel, new_gender))
                    conn.commit()
                    st.success(f"✅ Rekod untuk '{new_name}' ({new_id}) berjaya disimpan!")
                    st.rerun()
                else:
                    st.error("❌ Sila pastikan Kod ID dan Nama Penuh diisi.")

    with tab4:
        st.subheader("🗑️ Padam Rekod Ahli Keluarga")
        
        df_delete = pd.read_sql_query("SELECT id, full_name FROM ahli_keluarga ORDER BY id ASC", conn)
        member_list = [f"{row['id']} - {row['full_name']}" for _, row in df_delete.iterrows()]
        
        selected_to_delete = st.selectbox("Sila Pilih Ahli Yang Ingin Dipadam:", ["-- Pilih Ahli --"] + member_list)
        
        if selected_to_delete != "-- Pilih Ahli --":
            target_id = selected_to_delete.split(" - ")[0]
            if st.button(f"🔥 Confirm Padam Rekod ({target_id})"):
                cursor.execute("DELETE FROM ahli_keluarga WHERE id = ?", (target_id,))
                conn.commit()
                st.success(f"🗑️ Rekod ID {target_id} telah berjaya dipadam!")
                st.rerun()

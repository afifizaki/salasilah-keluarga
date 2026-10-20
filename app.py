import streamlit as st
import sqlite3
import pandas as pd
import datetime
import json

# 1. Sambungan Pangkalan Data SQLite
conn = sqlite3.connect('salasilah_keluarga.db', check_same_thread=False)
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS ahli_keluarga (
        id TEXT PRIMARY KEY,
        branch_no INTEGER,
        relationship TEXT,
        parent_spouse_id TEXT,
        child_order INTEGER,
        full_name TEXT,
        gender TEXT,
        dob TEXT,
        deceased TEXT
    )
''')
conn.commit()

st.title("🌳 Sistem Salasilah Keluarga Hj Makhtar & Hjh Halimah")

tab1, tab2, tab3, tab4 = st.tabs([
    "➕ Tambah Ahli Baru", 
    "✏️ Edit / Padam Rekod", 
    "📁 Muat Naik JSON (Import)", 
    "🗺️ Carta Salasilah"
])

# ---------------------------------------------------------
# TAB 1: TAMBAH AHLI BARU
# ---------------------------------------------------------
with tab1:
    st.subheader("Borang Pendaftaran Ahli Baru")
    branch = st.number_input("Nombor Cawangan (1-12)", min_value=1, max_value=12, value=1, key="add_branch")
    rel = st.selectbox("Hubungan", ["Sibling (Branch Head)", "Spouse", "Child", "Grandchild", "Great-Grandchild"], key="add_rel")
    parent_id = st.text_input("ID IbuBapa / Pasangan (Contoh: 01 atau 0101)", value="", key="add_parent_id")
    child_order = st.number_input("Urutan Anak (Jika Anak/Cucu)", min_value=0, max_value=20, value=0, key="add_order")
    
    # Kiraan ID Automatik
    auto_id = ""
    if rel == "Sibling (Branch Head)":
        auto_id = f"{branch:02d}"
    elif rel == "Spouse" and parent_id:
        auto_id = f"{parent_id}S"
    elif child_order > 0 and parent_id:
        auto_id = f"{parent_id}{child_order:02d}"

    st.info(f"ID Automatik Dijana: **{auto_id}**")

    name = st.text_input("Nama Penuh", key="add_name")
    gender = st.selectbox("Jantina", ["Lelaki", "Perempuan"], key="add_gender")
    
    today = datetime.date.today()
    min_date = datetime.date(1900, 1, 1)
    
    dob = st.date_input(
        "Tarikh Lahir",
        value=datetime.date(1980, 1, 1),
        min_value=min_date,
        max_value=today,
        key="add_dob"
    )
    
    deceased = st.selectbox("Meninggal Dunia?", ["No", "Yes"], key="add_deceased")

    if st.button("Simpan Ahli Baru"):
        if auto_id and name:
            c.execute('''
                INSERT OR REPLACE INTO ahli_keluarga VALUES (?,?,?,?,?,?,?,?,?)
            ''', (auto_id, branch, rel, parent_id, child_order, name, gender, str(dob), deceased))
            conn.commit()
            st.success(f"Berjaya menyimpan maklumat {name} (ID: {auto_id})!")
            st.rerun()
        else:
            st.error("Sila pastikan ID dan Nama Penuh diisi.")

# ---------------------------------------------------------
# TAB 2: EDIT & PADAM REKOD
# ---------------------------------------------------------
with tab2:
    st.subheader("📋 Jadual & Pengurusan Rekod")
    df = pd.read_sql_query("SELECT * FROM ahli_keluarga ORDER BY id", conn)
    st.dataframe(df, use_container_width=True)

    if not df.empty:
        st.divider()
        st.subheader("⚙️ Kemaskini / Padam Ahli")
        
        all_ids = df['id'].tolist()
        selected_id = st.selectbox("Pilih ID Ahli Untuk Diubah/Dipadam:", all_ids)
        
        record = df[df['id'] == selected_id].iloc[0]
        col_edit, col_del = st.columns(2)
        
        with col_edit:
            st.write(f"**Mengemaskini Rekod: {record['full_name']} ({record['id']})**")
            edit_name = st.text_input("Nama Penuh", value=record['full_name'], key="edit_name")
            edit_gender = st.selectbox("Jantina", ["Lelaki", "Perempuan"], index=0 if record['gender'] == "Lelaki" else 1, key="edit_gender")
            
            try:
                curr_dob = datetime.datetime.strptime(record['dob'], "%Y-%m-%d").date()
            except:
                curr_dob = datetime.date(1980, 1, 1)
                
            edit_dob = st.date_input("Tarikh Lahir", value=curr_dob, min_value=min_date, max_value=today, key="edit_dob")
            edit_deceased = st.selectbox("Meninggal Dunia?", ["No", "Yes"], index=0 if record['deceased'] == "No" else 1, key="edit_deceased")
            
            if st.button("Simpan Perubahan"):
                c.execute('''
                    UPDATE ahli_keluarga 
                    SET full_name = ?, gender = ?, dob = ?, deceased = ?
                    WHERE id = ?
                ''', (edit_name, edit_gender, str(edit_dob), edit_deceased, selected_id))
                conn.commit()
                st.success(f"Rekod {selected_id} telah berjaya dikemaskini!")
                st.rerun()
                
        with col_del:
            st.write("**Padam Rekod**")
            st.warning(f"Adakah anda pasti ingin memadam **{record['full_name']}** (ID: {selected_id})?")
            if st.button("🗑️ Padam Rekod Ini", type="primary"):
                c.execute("DELETE FROM ahli_keluarga WHERE id = ?", (selected_id,))
                conn.commit()
                st.success(f"Rekod {selected_id} telah dipadam.")
                st.rerun()

# ---------------------------------------------------------
# TAB 3: MUAT NAIK FAIL JSON (IMPORT DATA)
# ---------------------------------------------------------
with tab3:
    st.subheader("📥 Import Data Dari Fail JSON")
    st.write("Muat naik fail `.json` anda di sini untuk melengkapkan atau menggabungkan pangkalan data salasilah.")

    uploaded_file = st.file_uploader("Pilih fail JSON dari komputer / MacBook anda", type=["json"])

    if uploaded_file is not None:
        try:
            # Membaca kandungan fail dan membersihkan ruang tersembunyi (\xa0)
            raw_content = uploaded_file.read().decode("utf-8").replace('\xa0', ' ')
            json_data = json.loads(raw_content)
            
            st.success(f"Fail **{uploaded_file.name}** berjaya dibaca! Ditemui {len(json_data)} rekod.")
            
            # Tunjukkan pratonton data
            df_upload = pd.DataFrame(json_data)
            st.dataframe(df_upload.head(10), use_container_width=True)

            if st.button("🚀 Import Rekod Ke Pangkalan Data"):
                count = 0
                for item in json_data:
                    # Penyesuaian nama kunci JSON
                    item_id = item.get("ID") or item.get("id")
                    item_branch = int(item.get("Branch") or item.get("branch_no") or (item_id[:2] if item_id else 1))
                    item_rel = item.get("Relationship") or item.get("relationship") or "Member"
                    item_name = item.get("FullName") or item.get("full_name") or ""
                    item_gender = item.get("Gender") or item.get("gender") or "Lelaki"
                    item_dob = item.get("DOB") or item.get("dob") or "1980-01-01"
                    item_deceased = item.get("Deceased") or item.get("deceased") or "No"
                    
                    # Hubungan Parent/Spouse
                    item_parent = ""
                    if item_rel == "Spouse" and item_id.endswith("S"):
                        item_parent = item_id[:-1]
                    elif len(item_id) > 2 and not item_id.endswith("S"):
                        item_parent = item_id[:-2]

                    if item_id and item_name:
                        c.execute('''
                            INSERT OR REPLACE INTO ahli_keluarga 
                            VALUES (?,?,?,?,?,?,?,?,?)
                        ''', (item_id, item_branch, item_rel, item_parent, 0, item_name, item_gender, item_dob, item_deceased))
                        count += 1

                conn.commit()
                st.balloons()
                st.success(f"Berjaya mengimport {count} rekod ke dalam pangkalan data salasilah!")
                st.rerun()

        except Exception as e:
            st.error(f"Gagal membaca fail JSON: {e}")

# ---------------------------------------------------------
# TAB CARTA SALASILAH (SEMUA DATA DARI PANGKALAN DATA SQLITE)
# ---------------------------------------------------------
with tab4:
    st.subheader("🗺️ Carta Pokok Salasilah Keluarga (Lengkap Dari Pangkalan Data)")
    
    try:
        import graphviz
        # Ambil semua ahli keluarga termasuk Generasi Atas (branch_no = 0)
        df_tree = pd.read_sql_query(
            "SELECT id, branch_no, full_name, parent_spouse_id, relationship, gender FROM ahli_keluarga ORDER BY branch_no ASC, id ASC", 
            conn
        )
        
        if not df_tree.empty:
            col_filter1, _ = st.columns(2)
            with col_filter1:
                branches = ["Semua Cawangan (01-12)"] + [f"Cawangan {i:02d}" for i in range(1, 13)]
                selected_branch = st.selectbox("🎯 Pilih Paparan Cawangan:", branches)

            if selected_branch != "Semua Cawangan (01-12)":
                branch_num = int(selected_branch.split()[1])
                # Sertakan juga Datuk/Nenek/Moyang apabila cawangan individu dipilih
                df_filtered = df_tree[(df_tree['branch_no'] == branch_num) | (df_tree['branch_no'] == 0)].copy()
            else:
                df_filtered = df_tree.copy()

            dot = graphviz.Digraph(
                comment='Salasilah Keluarga',
                graph_attr={
                    'rankdir': 'LR',     # Alur Kiri ke Kanan
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

            # Kumpulan Generasi
            ggp_nodes, gp_nodes, gen1_nodes, gen2_nodes, gen3_nodes = [], [], [], [], []

            # 1. BINA NOD AHLI
            for _, row in df_filtered.iterrows():
                node_id = row['id']
                name = row['full_name']
                gender = row['gender']
                rel = row['relationship']
                
                shape = "box" if gender == "Lelaki" else "ellipse"
                
                # Pengelompokan mengikut Kod ID
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

            # 3. GARISAN PASANGAN MENEGAK
            spouse_rows = df_filtered[df_filtered['relationship'] == 'Spouse']
            for _, sp in spouse_rows.iterrows():
                sp_id = sp['id']
                main_id = sp['parent_spouse_id']
                if main_id in df_filtered['id'].values:
                    dot.edge(main_id, sp_id, style="dashed", constraint="true", color="#7F8C8D", label="pasangan")

            # 4. PAKSA SUSUNAN GEN 1 DARI ATAS KE BAWAH (01 ATAS, 01S BAWAH, 02...)
            gen1_unique_ids = sorted(list(set(gen1_nodes)))
            for i in range(len(gen1_unique_ids) - 1):
                curr_node = gen1_unique_ids[i]
                next_node = gen1_unique_ids[i+1]
                if curr_node.rstrip('S') != next_node.rstrip('S'):
                    dot.edge(curr_node, next_node, style="invis", constraint="true")

            # 5. GARISAN KETURUNAN IBU BAPA -> ANAK
            for _, row in df_filtered.iterrows():
                node_id = row['id']
                parent_id = row['parent_spouse_id']
                rel = row['relationship']
                
                if parent_id and parent_id in df_filtered['id'].values:
                    if rel != 'Spouse' and not node_id.endswith('S'):
                        dot.edge(parent_id, node_id, color="#2C3E50")
                        
            st.graphviz_chart(dot, use_container_width=True)

    except Exception as e:
        st.warning(f"Sila pastikan perisian 'graphviz' terpasang dengan betul. Ralat: {e}")
import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- POŁĄCZENIE Z BAZĄ ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("Błąd konfiguracji kluczy Supabase. Sprawdź sekcję 'Secrets'.")
    st.stop()

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="System Magazynowy", layout="wide")

# --- PASEK BOCZNY (SIDEBAR) ---
with st.sidebar:
    st.title("⚙️ Panel Sterowania")
    st.write("System Zarządzania Zasobami")
    st.divider()
    if st.button("Odśwież dane"):
        st.rerun()
    st.info("Status: Połączono z bazą")

# --- POBIERANIE DANYCH ---
# Pobieramy dane raz, aby zasilić wszystkie zakładki
res_k = supabase.table("kategorie").select("*").order("id").execute()
kategorie = res_k.data

res_p = supabase.table("produkty").select("*, kategorie(nazwa)").order("id").execute()
produkty = res_p.data

# --- GŁÓWNA TREŚĆ ---
st.title("📦 Magazyn i Analityka")

tab1, tab2, tab3 = st.tabs(["📂 Kategorie", "🍎 Produkty", "📊 Analityka"])

# --- TAB 1: KATEGORIE ---
with tab1:
    st.header("Zarządzanie Kategoriami")
    with st.expander("➕ Dodaj nową kategorię"):
        with st.form("form_kat", clear_on_submit=True):
            nazwa_kat = st.text_input("Nazwa kategorii")
            opis_kat = st.text_area("Opis")
            if st.form_submit_button("Zapisz kategorię"):
                if nazwa_kat:
                    supabase.table("kategorie").insert({"nazwa": nazwa_kat, "opis": opis_kat}).execute()
                    st.success(f"Dodano kategorię: {nazwa_kat}")
                    st.rerun()

    if kategorie:
        for k in kategorie:
            c1, c2 = st.columns([5, 1])
            c1.write(f"ID: `{k['id']}` | **{k['nazwa']}**")
            if c2.button("Usuń", key=f"del_kat_{k['id']}"):
                try:
                    supabase.table("kategorie").delete().eq("id", k['id']).execute()
                    st.rerun()
                except:
                    st.error("Nie można usunąć kategorii, która zawiera produkty!")
    else:
        st.info("Brak kategorii w bazie.")

# --- TAB 2: PRODUKTY ---
with tab2:
    st.header("Zarządzanie Produktami")
    with st.expander("➕ Dodaj nowy produkt"):
        if not kategorie:
            st.warning("Najpierw zdefiniuj kategorie w pierwszej zakładce.")
        else:
            with st.form("form_prod", clear_on_submit=True):
                n_p = st.text_input("Nazwa produktu")
                l_p = st.number_input("Liczba sztuk", min_value=0, step=1)
                c_p = st.number_input("Cena jednostkowa (zł)", min_value=0.0, format="%.2f")
                
                kat_map = {k['nazwa']: k['id'] for k in kategorie}
                wybrana_k = st.selectbox("Przypisz do kategorii", options=list(kat_map.keys()))
                
                if st.form_submit_button("Dodaj do magazynu"):
                    if n_p:
                        supabase.table("produkty").insert({
                            "nazwa": n_p,
                            "liczba": int(l_p),
                            "cena": float(c_p),
                            "kategoria_id": int(kat_map[wybrana_k])
                        }).execute()
                        st.success(f"Dodano produkt: {n_p}")
                        st.rerun()

    if produkty:
        for p in produkty:
            col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
            col1.write(f"ID: `{p['id']}`")
            col2.write(f"**{p['nazwa']}**")
            
            kat_obj = p.get('kategorie')
            nazwa_k = kat_obj.get('nazwa', '-') if isinstance(kat_obj, dict) else "-"
            
            col3.write(f"📁 {nazwa_k} | {p['liczba']} szt. | {p['cena']} zł")
            if col4.button("🗑️", key=f"del_p_{p['id']}"):
                supabase.table("produkty").delete().eq("id", p['id']).execute()
                st.rerun()
    else:
        st.info("Magazyn jest pusty.")

# --- TAB 3: ANALITYKA ---
with tab3:
    st.header("📊 Podsumowanie Statystyczne")
    
    if produkty:
        df = pd.DataFrame(produkty)
        
        # Obliczenia metryk
        total_qty = df['liczba'].sum()
        total_val = (df['liczba'] * df['cena']).sum()
        prod_count = len(df)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Rodzajów asortymentu", prod_count)
        m2.metric("Łączna liczba sztuk", f"{total_qty} szt.")
        m3.metric("Całkowita wartość", f"{total_val:,.2f} zł")

import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# --- POŁĄCZENIE Z BAZĄ ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("Błąd konfiguracji kluczy Supabase. Sprawdź sekcję 'Secrets'.")
    st.stop()

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="System Magazynowy Pro", layout="wide")

# --- PASEK BOCZNY (SIDEBAR) ---
with st.sidebar:
    st.title("⚙️ Panel Zarządzania")
    st.write("Wersja Systemu: 2.0")
    st.divider()
    if st.button("🔄 Odśwież dane"):
        st.rerun()
    st.info("Baza danych: Połączono")

# --- POBIERANIE DANYCH ---
res_k = supabase.table("kategorie").select("*").order("id").execute()
kategorie = res_k.data

res_p = supabase.table("produkty").select("*, kategorie(nazwa)").order("id").execute()
produkty = res_p.data

# --- GŁÓWNA TREŚĆ ---
st.title("📦 Magazyn i Zaawansowana Analityka")

tab1, tab2, tab3 = st.tabs(["📂 Kategorie", "🍎 Produkty", "📊 Raporty i Wykresy"])

# --- TAB 1: KATEGORIE ---
with tab1:
    st.header("Zarządzanie Kategoriami")
    with st.expander("➕ Dodaj nową kategorię"):
        with st.form("form_kat", clear_on_submit=True):
            nazwa_kat = st.text_input("Nazwa kategorii")
            opis_kat = st.text_area("Opis")
            if st.form_submit_button("Zapisz"):
                if nazwa_kat:
                    supabase.table("kategorie").insert({"nazwa": nazwa_kat, "opis": opis_kat}).execute()
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
                    st.error("Błąd: Kategoria zawiera produkty!")
    else:
        st.info("Brak kategorii.")

# --- TAB 2: PRODUKTY ---
with tab2:
    st.header("Zarządzanie Produktami")
    with st.expander("➕ Dodaj nowy produkt"):
        if not kategorie:
            st.warning("Najpierw dodaj kategorię!")
        else:
            with st.form("form_prod", clear_on_submit=True):
                n_p = st.text_input("Nazwa produktu")
                l_p = st.number_input("Liczba sztuk", min_value=0)
                c_p = st.number_input("Cena (zł)", min_value=0.0)
                
                kat_map = {k['nazwa']: k['id'] for k in kategorie}
                wybrana_k = st.selectbox("Kategoria", options=list(kat_map.keys()))
                
                if st.form_submit_button("Dodaj produkt"):
                    if n_p:
                        supabase.table("produkty").insert({
                            "nazwa": n_p, "liczba": int(l_p), "cena": float(c_p), "kategoria_id": int(kat_map[wybrana_k])
                        }).execute()
                        st.rerun()

    if produkty:
        for p in produkty:
            col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
            col1.write(f"ID: `{p['id']}`")
            col2.write(f"**{p['nazwa']}**")
            n_k = p.get('kategorie', {}).get('nazwa', '-') if p.get('kategorie') else "-"
            col3.write(f"📁 {n_k} | {p['liczba']} szt. | {p['cena']} zł")
            if col4.button("🗑️", key=f"del_p_{p['id']}"):
                supabase.table("produkty").delete().eq("id", p['id']).execute()
                st.rerun()

# --- TAB 3: ANALITYKA (WYKRESY KOLOWE I KOLUMNOWE) ---
with tab3:
    st.header("📊 Wizualizacja Danych")
    
    if produkty:
        df = pd.DataFrame(produkty)
        df['kat_nazwa'] = df['kategorie'].apply(lambda x: x['nazwa'] if isinstance(x, dict) else 'Brak')
        df['wartosc_calkowita'] = df['liczba'] * df['cena']
        
        # --- METRYKI ---
        m1, m2, m3 = st.columns(3)
        m1.metric("Wartość Magazynu", f"{df['wartosc_calkowita'].sum():,.2f} zł")
        m2.metric("Suma wszystkich sztuk", f"{df['liczba'].sum()} szt.")
        m3.metric("Liczba pozycji", len(df))
        
        st.divider()

        # --- RZĄD 1: WYKRESY KOŁOWE ---
        col_pie1, col_pie2 = st.columns(2)
        
        with col_pie1:
            st.subheader("Udział ilościowy kategorii")
            fig_pie_qty = px.pie(df, values='liczba', names='kat_nazwa', hole=0.4,
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie_qty, use_container_width=True)
            
        with col_pie2:
            st.subheader("Udział wartościowy kategorii")
            fig_pie_val = px.pie(df, values='wartosc_calkowita', names='kat_nazwa',
                                 color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig_pie_val, use_container_width=True)

        st.divider()

        # --- RZĄD 2: WYKRESY KOLUMNOWE ---
        col_bar1, col_bar2 = st.columns(2)
        
        with col_bar1:
            st.subheader("TOP 10 Produktów (Ilość)")
            top_qty = df.nlargest(10, 'liczba')
            fig_bar_qty = px.bar(top_qty, x='nazwa', y='liczba', color='kat_nazwa',
                                 labels={'liczba': 'Sztuk', 'nazwa': 'Produkt'})
            st.plotly_chart(fig_bar_qty, use_container_width=True)
            
        with col_bar2:
            st.subheader("Wartość produktów wg kategorii")
            # Grupowanie dla czystego wykresu kolumnowego
            cat_val = df.groupby('kat_nazwa')['wartosc_calkowita'].sum().reset_index()
            fig_bar_val = px.bar(cat_val, x='kat_nazwa', y='wartosc_calkowita',
                                 color='kat_nazwa', labels={'wartosc_calkowita': 'Wartość (zł)', 'kat_nazwa': 'Kategoria'})
            st.plotly_chart(fig_bar_val, use_container_width=True)

    else:
        st.info("Brak danych do analizy.")

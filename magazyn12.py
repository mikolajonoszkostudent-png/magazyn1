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
st.set_page_config(page_title="Magazyn & Analityka", layout="wide")

# --- PASEK BOCZNY (SIDEBAR) ---
with st.sidebar:
    st.title("🕹️ Automaty do gier")
    st.image("https://img.freepik.com/free-vector/retro-arcade-machine_23-2147500516.jpg", caption="System v1.5")
    st.divider()
    st.info("Zalogowano jako Administrator")

# --- POBIERANIE DANYCH DO ANALIZY ---
# Pobieramy dane raz na początku, aby użyć ich w zakładkach
res_k = supabase.table("kategorie").select("*").order("id").execute()
kategorie = res_k.data

res_p = supabase.table("produkty").select("*, kategorie(nazwa)").order("id").execute()
produkty = res_p.data

# --- GŁÓWNA TREŚĆ ---
st.title("📦 System Zarządzania i Analityki")

tab1, tab2, tab3 = st.tabs(["📂 Kategorie", "🍎 Produkty", "📊 Analityka Magazynowa"])

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
                supabase.table("kategorie").delete().eq("id", k['id']).execute()
                st.rerun()

# --- TAB 2: PRODUKTY ---
with tab2:
    st.header("Zarządzanie Produktami")
    with st.expander("➕ Dodaj nowy produkt"):
        if not kategorie:
            st.warning("Dodaj najpierw kategorię!")
        else:
            with st.form("form_prod", clear_on_submit=True):
                n_p = st.text_input("Nazwa produktu")
                l_p = st.number_input("Ilość", min_value=0)
                c_p = st.number_input("Cena (zł)", min_value=0.0)
                kat_map = {k['nazwa']: k['id'] for k in kategorie}
                wybrana_k = st.selectbox("Kategoria", options=list(kat_map.keys()))
                if st.form_submit_button("Dodaj"):
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

# --- TAB 3: ANALITYKA ---
with tab3:
    st.header("📊 Raport Magazynowy")
    
    if produkty:
        # Konwersja do Pandas DataFrame dla łatwiejszych obliczeń
        df = pd.DataFrame(produkty)
        
        # Obliczenia
        total_items = df['liczba'].sum()
        total_value = (df['liczba'] * df['cena']).sum()
        avg_price = df['cena'].mean()
        count_products = len(df)

        # Wyświetlanie metryk w rzędzie
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Liczba produktów", count_products)
        m2.metric("Suma sztuk", f"{total_items} szt.")
        m3.metric("Wartość magazynu", f"{total_value:,.2f} zł")
        m4.metric("Średnia cena", f"{avg_price:,.2f} zł")

        st.divider()

        # Wykresy
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("Ilość produktów w kategoriach")
            # Przygotowanie danych do wykresu
            df['kat_nazwa'] = df['kategorie'].apply(lambda x: x['nazwa'] if isinstance(x, dict) else 'Brak')
            chart_data = df.groupby('kat_nazwa')['liczba'].sum()
            st.bar_chart(chart_data)

        with c2:
            st.subheader("Wartość finansowa kategorii")
            df['wartosc'] = df['liczba'] * df['cena']
            val_data = df.groupby('kat_nazwa')['wartosc'].sum()
            st.area_chart(val_data)
            
        st.subheader("Podsumowanie tabelaryczne")
        st.dataframe(df[['nazwa', 'liczba', 'cena', 'kat_nazwa']], use_container_width=True)
        
    else:
        st.info("Brak danych do wyświetlenia analityki. Dodaj produkty do bazy.")

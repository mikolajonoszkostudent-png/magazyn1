import streamlit as st
from supabase import create_client, Client

# Konfiguracja połączenia (w Streamlit Cloud dodaj to do 'Secrets')
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(URL, KEY)

st.title("📦 System Zarządzania Magazynem")

# --- ZAKŁADKI ---
tab1, tab2 = st.tabs(["Kategorie", "Produkty"])

# --- TAB 1: KATEGORIE ---
with tab1:
    st.header("Zarządzaj Kategoriami")
    
    # Dodawanie
    with st.expander("Dodaj nową kategorię"):
        nazwa_kat = st.text_input("Nazwa kategorii")
        opis_kat = st.text_area("Opis")
        if st.button("Zapisz kategorię"):
            data = {"nazwa": nazwa_kat, "opis": opis_kat}
            supabase.table("kategorie").insert(data).execute()
            st.success("Dodano kategorię!")
            st.rerun()

    # Wyświetlanie i Usuwanie
    kat_response = supabase.table("kategorie").select("*").execute()
    kategorie = kat_response.data
    
    if kategorie:
        for k in kategorie:
            cols = st.columns([3, 1])
            cols[0].write(f"**{k['nazwa']}** (ID: {k['id']})")
            if cols[1].button("Usuń", key=f"del_kat_{k['id']}"):
                supabase.table("kategorie").delete().eq("id", k['id']).execute()
                st.rerun()
    else:
        st.info("Brak kategorii w bazie.")

# --- TAB 2: PRODUKTY ---
with tab2:
    st.header("Zarządzaj Produktami")

    # Dodawanie
    with st.expander("Dodaj nowy produkt"):
        if not kategorie:
            st.warning("Najpierw dodaj kategorię!")
        else:
            nazwa_prod = st.text_input("Nazwa produktu")
            liczba = st.number_input("Liczba (szt)", min_value=0, step=1)
            cena = st.number_input("Cena", min_value=0.0, format="%.2f")
            
            # Wybór kategorii z listy
            kat_options = {k['nazwa']: k['id'] for k in kategorie}
            wybrana_kat = st.selectbox("Wybierz kategorię", options=list(kat_options.keys()))
            
            if st.button("Zapisz produkt"):
                prod_data = {
                    "nazwa": nazwa_prod,
                    "liczba": liczba,
                    "cena": cena,
                    "kategoria_id": kat_options[wybrana_kat]
                }
                supabase.table("produkty").insert(prod_data).execute()
                st.success("Dodano produkt!")
                st.rerun()

    # Wyświetlanie i Usuwanie
    prod_response = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
    produkty = prod_response.data

    if produkty:
        for p in produkty:
            cols = st.columns([2, 1, 1, 1])
            cols[0].write(f"**{p['nazwa']}**")
            cols[1].write(f"{p['cena']} PLN")
            cols[2].write(f"Kat: {p['kategorie']['nazwa']}")
            if cols[3].button("Usuń", key=f"del_prod_{p['id']}"):
                supabase.table("produkty").delete().eq("id", p['id']).execute()
                st.rerun()
    else:
        st.info("Brak produktów w bazie.")

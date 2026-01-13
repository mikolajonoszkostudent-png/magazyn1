import streamlit as st
from supabase import create_client, Client

# --- KONFIGURACJA POŁĄCZENIA ---
# Upewnij się, że w Streamlit Cloud w sekcji Secrets dodałeś:
# SUPABASE_URL = "twoj_url"
# SUPABASE_KEY = "twoj_klucz"

try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("Błąd konfiguracji kluczy Supabase. Sprawdź 'Secrets' w Streamlit Cloud.")
    st.stop()

st.set_page_config(page_title="Magazyn v2", layout="centered")
st.title("📦 Zarządzanie Produktami i Kategoriami")

# --- ZAKŁADKI ---
tab1, tab2 = st.tabs(["📂 Kategorie", "🍎 Produkty"])

# --- TAB 1: KATEGORIE ---
with tab1:
    st.header("Lista Kategorii")
    
    # Formularz dodawania
    with st.expander("➕ Dodaj nową kategorię"):
        with st.form("form_kat"):
            nazwa_kat = st.text_input("Nazwa kategorii")
            opis_kat = st.text_area("Opis (opcjonalnie)")
            submit_kat = st.form_submit_button("Zapisz kategorię")
            
            if submit_kat and nazwa_kat:
                res_kat = supabase.table("kategorie").insert({"nazwa": nazwa_kat, "opis": opis_kat}).execute()
                st.success(f"Dodano kategorię: {nazwa_kat}")
                st.rerun()

    # Wyświetlanie kategorii
    response_k = supabase.table("kategorie").select("*").execute()
    kategorie = response_k.data
    
    if kategorie:
        for k in kategorie:
            col1, col2 = st.columns([4, 1])
            col1.write(f"**{k['nazwa']}** (ID: {k['id']})")
            if col2.button("Usuń", key=f"del_kat_{k['id']}"):
                try:
                    supabase.table("kategorie").delete().eq("id", k['id']).execute()
                    st.rerun()
                except:
                    st.error("Nie można usunąć kategorii, która ma przypisane produkty!")
    else:
        st.info("Baza kategorii jest pusta.")

# --- TAB 2: PRODUKTY ---
with tab2:
    st.header("Lista Produktów")

    # Formularz dodawania
    with st.expander("➕ Dodaj nowy produkt"):
        if not kategorie:
            st.warning("Najpierw musisz dodać co najmniej jedną kategorię.")
        else:
            with st.form("form_prod"):
                nazwa_p = st.text_input("Nazwa produktu")
                liczba_p = st.number_input("Ilość (liczba)", min_value=0, step=1)
                cena_p = st.number_input("Cena (numeryczny)", min_value=0.0, format="%.2f")
                
                options = {k['nazwa']: k['id'] for k in kategorie}
                wybrana_kat_nazwa = st.selectbox("Kategoria", options=list(options.keys()))
                
                submit_p = st.form_submit_button("Dodaj produkt")
                
                if submit_p and nazwa_p:
                    nowy_produkt = {
                        "nazwa": nazwa_p,
                        "liczba": liczba_p,
                        "cena": cena_p,
                        "kategoria_id": options[wybrana_kat_nazwa]
                    }
                    supabase.table("produkty").insert(nowy_produkt).execute()
                    st.success(f"Dodano produkt: {nazwa_p}")
                    st.rerun()

    # Wyświetlanie produktów z JOIN (Poprawiona linia 79 i okolice)
    try:
        # Pobieramy produkty i nazwę z powiązanej tabeli kategorie
        res_p = supabase.table("produkty").select("id, nazwa, liczba, cena, kategorie(nazwa)").execute()
        produkty = res_p.data

        if produkty:
            for p in produkty:
                c1, c2, c3, c4 = st.columns([2, 1, 2, 1])
                c1.write(f"**{p['nazwa']}**")
                c2.write(f"{p['cena']} zł")
                
                # Bezpieczne wyciąganie nazwy kategorii
                kat_data = p.get('kategorie')
                nazwa_kategorii = kat_data.get('nazwa', 'Brak') if isinstance(kat_data, dict) else "Brak"
                
                c3.write(f"📁 {nazwa_kategorii}")
                
                if c4.button("Usuń", key=f"del_p_{p['id']}"):
                    supabase.table("produkty").delete().eq("id", p['id']).execute()
                    st.rerun()
        else:
            st.info("Brak produktów w magazynie.")
    except Exception as e:
        st.error(f"Wystąpił błąd podczas pobierania danych: {e}")

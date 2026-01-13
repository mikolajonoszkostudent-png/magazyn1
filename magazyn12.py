import streamlit as st
from supabase import create_client, Client

# --- KONFIGURACJA POŁĄCZENIA ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("Błąd połączenia z Supabase. Sprawdź 'Secrets' w panelu Streamlit.")
    st.stop()

st.set_page_config(page_title="Zarządzanie Magazynem", layout="wide")
st.title("📦 System Zarządzania Magazynem")

# --- ZAKŁADKI ---
tab1, tab2 = st.tabs(["📂 Kategorie", "🍎 Produkty"])

# --- TAB 1: KATEGORIE ---
with tab1:
    st.header("Kategorie")
    
    with st.expander("➕ Dodaj nową kategorię"):
        with st.form("form_kat", clear_on_submit=True):
            nazwa_kat = st.text_input("Nazwa kategorii")
            opis_kat = st.text_area("Opis")
            submit_kat = st.form_submit_button("Zapisz do bazy")
            
            if submit_kat:
                if nazwa_kat:
                    # POPRAWIONA LINIA: Jawne przekazanie słownika i obsługa odpowiedzi
                    try:
                        data_to_insert = {"nazwa": str(nazwa_kat), "opis": str(opis_kat)}
                        supabase.table("kategorie").insert(data_to_insert).execute()
                        st.success(f"Dodano kategorię: {nazwa_kat}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Błąd zapisu: {e}")
                else:
                    st.warning("Nazwa kategorii jest wymagana!")

    # Wyświetlanie
    res_k = supabase.table("kategorie").select("*").execute()
    kategorie = res_k.data
    
    if kategorie:
        for k in kategorie:
            c1, c2 = st.columns([5, 1])
            c1.write(f"**{k['nazwa']}** (ID: {k['id']})")
            if c2.button("Usuń", key=f"del_kat_{k['id']}"):
                try:
                    supabase.table("kategorie").delete().eq("id", k['id']).execute()
                    st.rerun()
                except:
                    st.error("Błąd: Nie usuwaj kategorii, która ma produkty!")
    else:
        st.info("Brak kategorii.")

# --- TAB 2: PRODUKTY ---
with tab2:
    st.header("Produkty")

    with st.expander("➕ Dodaj nowy produkt"):
        if not kategorie:
            st.warning("Brak kategorii! Dodaj je w pierwszej zakładce.")
        else:
            with st.form("form_prod", clear_on_submit=True):
                n_p = st.text_input("Nazwa produktu")
                l_p = st.number_input("Ilość", min_value=0, step=1)
                c_p = st.number_input("Cena", min_value=0.0, format="%.2f")
                
                kat_map = {k['nazwa']: k['id'] for k in kategorie}
                wybrana_k = st.selectbox("Wybierz kategorię", options=list(kat_map.keys()))
                
                submit_p = st.form_submit_button("Dodaj produkt")
                
                if submit_p and n_p:
                    try:
                        # POPRAWIONA LINIA: Rzutowanie na typy zgodne ze schematem bazy
                        prod_data = {
                            "nazwa": str(n_p),
                            "liczba": int(l_p),
                            "cena": float(c_p),
                            "kategoria_id": int(kat_map[wybrana_k])
                        }
                        supabase.table("produkty").insert(prod_data).execute()
                        st.success(f"Dodano: {n_p}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Błąd zapisu produktu: {e}")

    # Lista produktów z relacją
    try:
        res_p = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
        produkty = res_p.data

        if produkty:
            for p in produkty:
                col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
                col1.write(f"**{p['nazwa']}**")
                col2.write(f"{p['cena']} zł")
                
                # Bezpieczne pobieranie nazwy kategorii
                kat_info = p.get('kategorie')
                n_kat = kat_info.get('nazwa', '?') if isinstance(kat_info, dict) else "?"
                col3.write(f"📁 {n_kat}")
                
                if col4.button("🗑️", key=f"del_p_{p['id']}"):
                    supabase.table("produkty").delete().eq("id", p['id']).execute()
                    st.rerun()
    except Exception as e:
        st.error(f"Błąd wyświetlania: {e}")

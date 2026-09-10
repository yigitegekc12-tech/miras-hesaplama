import streamlit as st
import pandas as pd

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(
    page_title="TMK Miras ve Mal Rejimi Hesaplama Aracı",
    page_icon="⚖️",
    layout="wide"
)

# --- BASİT OTURUM / ŞİFRE KONTROLÜ ---
def check_password():
    def password_entered():
        if st.session_state["password"] == "ege12345":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("### 🔒 Güvenli Giriş")
        st.text_input("Lütfen Erişim Şifresini Girin:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.markdown("### 🔒 Güvenli Giriş")
        st.text_input("Lütfen Erişim Şifresini Girin:", type="password", on_change=password_entered, key="password")
        st.error("😕 Hatalı şifre. Lütfen tekrar deneyin.")
        return False
    else:
        return True

if not check_password():
    st.stop()

# --- ANA UYGULAMA ---
st.title("⚖️ Türk Medeni Kanunu (TMK) Miras & Mal Rejimi Hesaplama")
st.markdown("Bu araç; yasal miras payları, saklı paylar, mal rejimi tasfiyesi, tapu harçları ve **torunlar/altsoy temsil ilkelerini** kararlı bir arayüzle hesaplar.")

st.sidebar.header("🗂️ İşlem Seçimi")
islem_turu = st.sidebar.selectbox(
    "Hesaplama Modülü Seçin:",
    ["Zümre Bazlı Yasal Miras ve Saklı Paylar", "Edinilmiş Mallara Katılma Rejimi Tasfiyesi", "Tapu Harçları ve Devir Masrafları Hesaplama"]
)

if islem_turu == "Zümre Bazlı Yasal Miras ve Saklı Paylar":
    st.header("👥 Kapsamlı Zümre, Altsoy ve Torun Temsil Hesaplayıcı")
    
    with st.form("miras_formu"):
        tereke_degeri = st.number_input("Toplam Tereke Aktifi (TL):", min_value=0.0, value=1000000.0, step=50000.0)
        zumre_secimi = st.selectbox(
            "Mirasçının Bulunduğu Zümre / Durum:",
            [
                "1. Zümre: Çocuklar, Torunlar (Altsoy) ve Sağ Eş",
                "2. Zümre: Anne, Baba, Kardeşler ve Sağ Eş",
                "3. Zümre: Büyük anne, Büyük baba ve Çocukları / Sağ Eş",
                "Yalnızca Sağ Eş (Hiçbir zümre akrabası yok)"
            ]
        )
        sag_es = st.checkbox("Sağ Eş Hayatta mı?", value=True)

        cocuk_sayisi = 1
        if "1. Zümre" in zumre_secimi:
            cocuk_sayisi = st.number_input("Toplam Çocuk (Kök) Sayısı:", min_value=1, max_value=10, value=2, step=1)
            
            st.markdown("---")
            st.markdown("### 👶 Çocukların Durumu (Vefat Edenler İçin Torun Temsili)")
            cocuk_durumlari = []
            for i in range(1, int(cocuk_sayisi) + 1):
                c_durum = st.selectbox(f"{i}. Çocuğun Durumu:", ["Hayatta", "Vefat Etmiş (Torunlar Temsil Edecek)"], key=f"c_durum_{i}")
                t_sayisi = 1
                if c_durum == "Vefat Etmiş (Torunlar Temsil Edecek)":
                    t_sayisi = st.number_input(f"→ {i}. Çocuğun Kaç Çocuğu (Torun) Var?", min_value=1, max_value=10, value=2, step=1, key=f"t_sayisi_{i}")
                cocuk_durumlari.انياap({"durum": c_durum, "torun_sayisi": t_sayisi})

        submit_btn = st.form_submit_button("Zümre ve Temsil Paylaşımını Hesapla")

    if submit_btn:
        sonuclar = []
        if "1. Zümre" in zumre_secimi:
            es_payi_orani = 0.25 if sag_es else 0.0
            altsoy_toplam_oran = 0.75 if sag_es else 1.0
            
            if sag_es:
                sonuclar.append({
                    "Mirasçı": "Sağ Eş", 
                    "Yasal Pay Oranı": "%25.00 (1/4)", 
                    "Tutar (TL)": tereke_degeri * 0.25, 
                    "Saklı Pay Oranı": "%12.50 (Yasal payın yarısı)"
                })

            her_bir_kok_orani = altsoy_toplam_oran / cocuk_sayisi
            
            for i, c_data in enumerate(cocuk_durumlari, 1):
                if c_data["durum"] == "Hayatta":
                    sonuclar.append({
                        "Mirasçı": f"{i}. Çocuk (Hayatta)", 
                        "Yasal Pay Oranı": f"%{her_bir_kok_orani * 100:.2f}", 
                        "Tutar (TL)": tereke_degeri * her_bir_kok_orani, 
                        "Saklı Pay Oranı": f"%{her_bir_kok_orani * 50:.2f}"
                    })
                else:
                    t_sayisi = c_data["torun_sayisi"]
                    torun_basina_oran = her_bir_kok_orani / t_sayisi
                    for t in range(1, t_sayisi + 1):
                        sonuclar.append({
                            "Mirasçı": f"→ {i}. Çocuğun {t}. Çocuğu (Torun / Temsilen)", 
                            "Yasal Pay Oranı": f"%{torun_basina_oran * 100:.2f}", 
                            "Tutar (TL)": tereke_degeri * torun_basina_oran, 
                            "Saklı Pay Oranı": f"%{torun_basina_oran * 50:.2f}"
                        })

        elif "2. Zümre" in zumre_secimi:
            if sag_es:
                sonuclar.append({"Mirasçı": "Sağ Eş", "Yasal Pay Oranı": "%50.00 (1/2)", "Tutar (TL)": tereke_degeri * 0.50, "Saklı Pay Oranı": "%25.00"})
                sonuclar.append({"Mirasçı": "Anne / Baba / Kardeşler Kolu", "Yasal Pay Oranı": "%50.00", "Tutar (TL)": tereke_degeri * 0.50, "Saklı Pay Oranı": "Yok"})
            else:
                sonuclar.append({"Mirasçı": "2. Zümre Akrabaları", "Yasal Pay Oranı": "%100.00", "Tutar (TL)": tereke_degeri, "Saklı Pay Oranı": "Yok"})

        elif "Yalnızca Sağ Eş" in zumre_secimi:
            sonuclar.append({"Mirasçı": "Sağ Eş (Zümre Akrabası Yok)", "Yasal Pay Oranı": "%100.00", "Tutar (TL)": tereke_degeri, "Saklı Pay Oranı": "%50.00"})

        if sonuclar:
            st.subheader("📊 Kesin Miras Dağılım Tablosu")
            df_sonuc = pd.DataFrame(sonuclar)
            st.dataframe(df_sonuc, use_container_width=True)

elif islem_turu == "Edinilmiş Mallara Katılma Rejimi Tasfiyesi":
    st.header("💍 Mal Rejimi Tasfiyesi (Artık Değer Hesabı)")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        aktif_1 = st.number_input("Eş 1 Aktif", min_value=0.0, value=2000000.0, key="a1")
        borc_1 = st.number_input("Eş 1 Borç", min_value=0.0, value=500000.0, key="b1")
        kisisel_1 = st.number_input("Eş 1 Kişisel", min_value=0.0, value=300000.0, key="k1")
    with col_e2:
        aktif_2 = st.number_input("Eş 2 Aktif", min_value=0.0, value=1000000.0, key="a2")
        borc_2 = st.number_input("Eş 2 Borç", min_value=0.0, value=100000.0, key="b2")
        kisisel_2 = st.number_input("Eş 2 Kişisel", min_value=0.0, value=200000.0, key="k2")

    if st.button("Tasfiye Hesapla"):
        ad1 = max(0.0, aktif_1 - borc_1 - kisisel_1)
        ad2 = max(0.0, aktif_2 - borc_2 - kisisel_2)
        toplam_artik = ad1 + ad2
        katilma = toplam_artik / 2
        st.success(f"💰 Toplam Artık Değer: {toplam_artik:,.2f} TL | Eşlerin Katılma Alacağı: {katilma:,.2f} TL")

elif islem_turu == "Tapu Harçları ve Devir Masrafları Hesaplama":
    st.header("🏛️ Tapu Harçları ve Devir Masrafları")
    gayrimenkul_degeri = st.number_input("Gayrimenkul Değeri (TL):", min_value=0.0, value=2500000.0)
    islem_tipi = st.selectbox("İşlem Türü:", ["Miras İntikal İşlemi", "Mal Rejimi Tasfiyesi Eş Devri", "Normal Satış"])
    
    if st.button("Masraf Hesapla"):
        harc = gayrimenkul_degeri * (0.00227 if "İntikal" in islem_tipi or "Tasfiye" in islem_tipi else 0.04)
        toplam = harc + 1350.0
        st.success(f"Devlete Ödenecek Toplam Masraf: {toplam:,.2f} TL (Harç: {harc:,.2f} TL + Döner Sermaye: 1,350 TL)")

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
st.markdown("Bu araç; yasal miras payları, saklı paylar, torun temsil ilkeleri ve **masrafların mirasçı paylarından otomatik düşüldüğü** net intikal hesaplamalarını yapar.")

st.sidebar.header("🗂️ İşlem Seçimi")
islem_turu = st.sidebar.selectbox(
    "Hesaplama Modülü Seçin:",
    [
        "Zümre Bazlı Yasal Miras ve Saklı Paylar", 
        "Edinilmiş Mallara Katılma Rejimi Tasfiyesi", 
        "Tapu İntikal ve Masraf Düşüm Hesabı"
    ]
)

if islem_turu == "Zümre Bazlı Yasal Miras ve Saklı Paylar":
    st.header("👥 Kapsamlı Zümre, Altsoy ve Torun Temsil Hesaplayıcı")
    
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

    cocuk_durumlari = []
    cocuk_sayisi = 1
    
    if "1. Zümre" in zumre_secimi:
        cocuk_sayisi = st.number_input("Toplam Çocuk (Kök) Sayısı:", min_value=1, max_value=10, value=2, step=1)
        
        st.markdown("---")
        st.markdown("### 👶 Çocukların Durumu (Vefat Edenler İçin Torun Temsili)")
        for i in range(1, int(cocuk_sayisi) + 1):
            c_durum = st.selectbox(f"{i}. Çocuğun Durumu:", ["Hayatta", "Vefat Etmiş (Torunlar Temsil Edecek)"], key=f"c_durum_{i}")
            t_sayisi = 1
            if c_durum == "Vefat Etmiş (Torunlar Temsil Edecek)":
                t_sayisi = st.number_input(f"→ {i}. Çocuğun Kaç Çocuğu (Torun) Var?", min_value=1, max_value=10, value=2, step=1, key=f"t_sayisi_{i}")
            cocuk_durumlari.append({"durum": c_durum, "torun_sayisi": t_sayisi})

    if st.button("Zümre ve Temsil Paylaşımını Hesapla"):
        sonuclar = []
        if "1. Zümre" in zumre_secimi:
            altsoy_toplam_oran = 0.75 if sag_es else 1.0
            
            if sag_es:
                sonuclar.append({
                    "Mirasçı": "Sağ Eş", 
                    "Yasal Pay Oranı": "%25.00 (1/4)", 
                    "Tutar (TL)": tereke_degeri * 0.25, 
                    "Saklı Pay Oranı": "%12.50"
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

elif islem_turu == "Tapu İntikal ve Masraf Düşüm Hesabı":
    st.header("🏛️ Tapu İntikal Harçları ve Masrafların Paylardan Düşülmesi")
    st.markdown("Bu modül; intikal harcı, döner sermaye ve diğer resmi masrafları toplam tereke üzerinden hesaplayıp **tüm mirasçıların payından oranları doğrultusunda otomatik olarak düşer**.")

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        gayrimenkul_degeri = st.number_input("Tapu / Gayrimenkul Toplam Değeri (TL):", min_value=0.0, value=3000000.0, step=100000.0)
        intikal_orani = st.number_input("Tapu İntikal Harcı Oranı (%):", min_value=0.0, value=0.227, step=0.01, help="Miras intikallerinde binde 2.27 (%0.227) uygulanır.")
        doner_serg = st.number_input("Tapu Döner Sermaye / Ek Masraflar (TL):", min_value=0.0, value=1350.0, step=100.0)
    
    with col_m2:
        st.markdown("### 📋 Mirasçı Dağılım Parametreleri")
        mirasci_tipi = st.selectbox("Miras Grubu:", ["1. Zümre (Eş + Çocuklar/Torunlar)", "Yalnızca Çocuklar (Eş Yok)"])
        toplam_cocuk = st.number_input("Çocuk / Kök Sayısı:", min_value=1, value=2, step=1)
        var_es = True if "Eş +" in mirasci_tipi else False

    if st.button("Masrafları Düşerek Net Payları Hesapla"):
        # Toplam Resmi Masraf Tutarı
        toplam_tapu_harci = gayrimenkul_degeri * (intikal_orani / 100.0)
        toplam_resmi_masraf = toplam_tapu_harci + doner_serg
        
        # Miras pay oranlarının tespiti
        detaylar = []
        if var_es:
            es_pay_orani = 0.25
            cocuklar_toplam_oran = 0.75
            
            # Sağ eş hak edişleri
            brut_es = gayrimenkul_degeri * es_pay_orani
            masraf_es = toplam_resmi_masraf * es_pay_orani
            net_es = brut_es - masraf_es
            
            detaylar.append({
                "Mirasçı": "Sağ Eş",
                "Yasal Payı (%)": "%25.00",
                "Brüt Pay (TL)": brut_es,
                "Payına Düşen Masraf (TL)": masraf_es,
                "Net Alacağı (TL)": net_es
            })
            
            her_cocuk_orani = cocuklar_toplam_oran / toplam_cocuk
            for c in range(1, int(toplam_cocuk) + 1):
                brut_c = gayrimenkul_degeri * her_cocuk_orani
                masraf_c = toplam_resmi_masraf * her_cocuk_orani
                net_c = brut_c - masraf_c
                detaylar.append({
                    "Mirasçı": f"{c}. Çocuk",
                    "Yasal Payı (%)": f"%{her_cocuk_orani * 100:.2f}",
                    "Brüt Pay (TL)": brut_c,
                    "Payına Düşen Masraf (TL)": masraf_c,
                    "Net Alacağı (TL)": net_c
                })
        else:
            her_cocuk_orani = 1.0 / toplam_cocuk
            for c in range(1, int(toplam_cocuk) + 1):
                brut_c = gayrimenkul_degeri * her_cocuk_orani
                masraf_c = toplam_resmi_masraf * her_cocuk_orani
                net_c = brut_c - masraf_c
                detaylar.append({
                    "Mirasçı": f"{c}. Çocuk",
                    "Yasal Payı (%)": f"%{her_cocuk_orani * 100:.2f}",
                    "Brüt Pay (TL)": brut_c,
                    "Payına Düşen Masraf (TL)": masraf_c,
                    "Net Alacağı (TL)": net_c
                })

        st.info(f"💡 **Toplam Tahsil Edilecek Devlet Masrafı:** {toplam_resmi_masraf:,.2f} TL (İntikal Harcı: {toplam_tapu_harci:,.2f} TL + Döner Sermaye: {doner_serg:,.2f} TL)")
        
        st.subheader("📉 Masrafların Otomatik Düşüldüğü Net Mirasçı Dağılım Tablosu")
        df_net = pd.DataFrame(detaylar)
        st.dataframe(df_net, use_container_width=True)

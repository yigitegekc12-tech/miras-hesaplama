import streamlit as st
import pandas as pd

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(
    page_title="TMK Profesyonel Miras ve Mal Rejimi Sistemi",
    page_icon="⚖️",
    layout="wide"
)

# --- BASİT OTURUM / ŞİFRE KONTROLÜ ---
def check_password():
    def password_entered():
        if st.session_state["password"] == "tmk2026":
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

# --- ANA BAŞLIK ---
st.title("⚖️ Türk Medeni Kanunu Profesyonel Miras & Mali Tasfiye Sistemi")
st.markdown("Bu araç; varlık-borç analizinden zümre paylaşımlarına, mal rejimi tasfiyesinden tapu masraflarına kadar süreci **adım adım ve kolayca** yönetmenizi sağlar.")

# --- MODERN SEKME (TAB) YAPISI İLE KOLAY ARAYÜZ ---
tab1, tab2, tab3, tab4 = st.tabs([
    "1️⃣ Aktif & Borç Analizi", 
    "2️⃣ Zümre & Miras Paylaşımı", 
    "3️⃣ Mal Rejimi Tasfiyesi", 
    "4️⃣ Tapu ve Masraf Düşümleri"
])

# --- TAB 1: AKTİF / PASİF (NET TEREKE) ANALİZİ ---
with tab1:
    st.header("💼 Adım 1: Tereke Varlıkları ve Borçlarının Tespiti")
    st.markdown("Mirasbırakanın tüm varlıklarını ve borçlarını girerek paylaşılacak **Net Tereke** tutarını belirleyin.")

    col_ap1, col_ap2 = st.columns(2)
    
    with col_ap1:
        st.subheader("📈 Tereke Aktifleri (Mal Varlıkları)")
        gayrimenkul_aktif = st.number_input("Gayrimenkuller Toplam Değeri (TL):", min_value=0.0, value=3000000.0, step=50000.0, key="g_aktif")
        nakit_aktif = st.number_input("Banka Mevduatı / Nakit Değeri (TL):", min_value=0.0, value=500000.0, step=10000.0, key="n_aktif")
        arac_aktif = st.number_input("Menkul / Araç Toplam Değeri (TL):", min_value=0.0, value=750000.0, step=25000.0, key="a_aktif")
        diger_aktif = st.number_input("Diğer Haklar ve Alacaklar (TL):", min_value=0.0, value=0.0, step=10000.0, key="d_aktif")

    with col_ap2:
        st.subheader("📉 Tereke Pasifleri (Borçlar ve Giderler)")
        banka_kredi_borcu = st.number_input("Banka Kredileri ve Kredi Kartı Borçları (TL):", min_value=0.0, value=200000.0, step=10000.0, key="b_borc")
        piyasa_borcu = st.number_input("Şahıs / Ticari Piyasa Borçları (TL):", min_value=0.0, value=50000.0, step=10000.0, key="p_borc")
        cenaze_masrafi = st.number_input("Cenaze ve Defin Masrafları (TMK m.507) (TL):", min_value=0.0, value=75000.0, step=5000.0, key="c_masraf")
        tereke_yonetim_gideri = st.number_input("Terekenin Mühürlenmesi ve Yönetim Giderleri (TL):", min_value=0.0, value=25000.0, step=5000.0, key="t_gider")

    if st.button("Net Terekeyi Hesapla ve Hafızaya Al", type="primary"):
        toplam_aktif = gayrimenkul_aktif + nakit_aktif + arac_aktif + diger_aktif
        toplam_pasif = banka_kredi_borcu + piyasa_borcu + cenaze_masrafi + tereke_yonetim_gideri
        net_tereke = max(0.0, toplam_aktif - toplam_pasif)

        st.session_state["net_tereke"] = net_tereke
        st.session_state["gayrimenkul_degeri"] = gayrimenkul_aktif # Tapu sekmesi için otomatik aktarım

        st.success("✅ Net Tereke başarıyla hesaplandı! Artık diğer sekmelere geçebilirsiniz.")
        
        st.markdown("---")
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("Toplam Brüt Aktif", f"{toplam_aktif:,.2f} TL")
        col_s2.metric("Toplam Pasif (Borçlar)", f"{toplam_pasif:,.2f} TL")
        col_s3.metric("Net Tereke", f"{net_tereke:,.2f} TL")

# --- TAB 2: ZÜMRE BAZLI YASAL MİRAS VE SAKLI PAYLAR ---
with tab2:
    st.header("👥 Adım 2: Zümre, Altsoy ve Torun Temsil Hesaplayıcı")
    
    varsayilan_tereke = st.session_state.get("net_tereke", 3500000.0)
    tereke_degeri = st.number_input("Paylaştırılacak Net Tereke Aktifi (TL):", min_value=0.0, value=varsayilan_tereke, step=50000.0, help="1. Adımdaki net tereke buraya otomatik gelir, dilerseniz değiştirebilirsiniz.")
    
    zumre_secimi = st.selectbox(
        "Mirasçının Bulunduğu Zümre / Durum:",
        [
            "1. Zümre: Çocuklar, Torunlar (Altsoy) ve Sağ Eş",
            "2. Zümre: Anne, Baba, Kardeşler ve Sağ Eş",
            "3. Zümre: Büyük anne, Büyük baba ve Çocukları / Sağ Eş",
            "Yalnızca Sağ Eş (Hiçbir zümre akrabası yok)"
        ]
    )
    sag_es = st.checkbox("Sağ Eş Hayatta mı?", value=True, key="sag_es_t2")

    cocuk_durumlari = []
    cocuk_sayisi = 1
    
    if "1. Zümre" in zumre_secimi:
        cocuk_sayisi = st.number_input("Toplam Çocuk (Kök) Sayısı:", min_value=1, max_value=10, value=2, step=1, key="c_sayisi_t2")
        
        st.markdown("---")
        st.markdown("### 👶 Çocukların Durumu (Vefat Edenler İçin Torun Temsili)")
        for i in range(1, int(cocuk_sayisi) + 1):
            c_durum = st.selectbox(f"{i}. Çocuğun Durumu:", ["Hayatta", "Vefat Etmiş (Torunlar Temsil Edecek)"], key=f"c_durum_t2_{i}")
            t_sayisi = 1
            if c_durum == "Vefat Etmiş (Torunlar Temsil Edecek)":
                t_sayisi = st.number_input(f"→ {i}. Çocuğun Kaç Çocuğu (Torun) Var?", min_value=1, max_value=10, value=2, step=1, key=f"t_sayisi_t2_{i}")
            cocuk_durumlari.append({"durum": c_durum, "torun_sayisi": t_sayisi})

    if st.button("Miras Paylaşımını Hesapla", type="primary", key="btn_zumre"):
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

# --- TAB 3: EDİNİLMİŞ MALLARA KATILMA REJİMİ TASFİYESİ ---
with tab3:
    st.header("💍 Adım 3: Mal Rejimi Tasfiyesi (Artık Değer Hesabı)")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        aktif_1 = st.number_input("Eş 1 Mal Varlığı Aktifi", min_value=0.0, value=2000000.0, key="a1")
        borc_1 = st.number_input("Eş 1 Borçları", min_value=0.0, value=500000.0, key="b1")
        kisisel_1 = st.number_input("Eş 1 Kişisel Malları", min_value=0.0, value=300000.0, key="k1")
    with col_e2:
        aktif_2 = st.number_input("Eş 2 Mal Varlığı Aktifi", min_value=0.0, value=1000000.0, key="a2")
        borc_2 = st.number_input("Eş 2 Borçları", min_value=0.0, value=100000.0, key="b2")
        kisisel_2 = st.number_input("Eş 2 Kişisel Malları", min_value=0.0, value=200000.0, key="k2")

    if st.button("Tasfiye Hesapla", type="primary", key="btn_tasfiye"):
        ad1 = max(0.0, aktif_1 - borc_1 - kisisel_1)
        ad2 = max(0.0, aktif_2 - borc_2 - kisisel_2)
        toplam_artik = ad1 + ad2
        katilma = toplam_artik / 2
        st.success(f"💰 Toplam Artık Değer: {toplam_artik:,.2f} TL | Eşlerin Katılma Alacağı: {katilma:,.2f} TL")

# --- TAB 4: TAPU İNTİKAL VE MASRAF DÜŞÜM HESABI ---
with tab4:
    st.header("🏛️ Adım 4: Tapu İntikal Harçları ve Masrafların Paylardan Düşülmesi")
    
    varsayilan_gayrimenkul = st.session_state.get("gayrimenkul_degeri", 3000000.0)
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        gayrimenkul_degeri = st.number_input("Tapu / Gayrimenkul Toplam Değeri (TL):", min_value=0.0, value=varsayilan_gayrimenkul, step=100000.0, key="g_deger_t4")
        intikal_orani = st.number_input("Tapu İntikal Harcı Oranı (%):", min_value=0.0, value=0.227, step=0.01, key="int_oran_t4")
        doner_serg = st.number_input("Tapu Döner Sermaye / Ek Masraflar (TL):", min_value=0.0, value=1350.0, step=100.0, key="doner_t4")
    
    with col_m2:
        st.markdown("### 📋 Mirasçı Dağılım Parametreleri")
        mirasci_tipi = st.selectbox("Miras Grubu:", ["1. Zümre (Eş + Çocuklar/Torunlar)", "Yalnızca Çocuklar (Eş Yok)"], key="m_tip_t4")
        toplam_cocuk = st.number_input("Çocuk / Kök Sayısı:", min_value=1, value=2, step=1, key="c_say_t4")
        var_es = True if "Eş +" in mirasci_tipi else False

    if st.button("Masrafları Düşerek Net Payları Hesapla", type="primary", key="btn_tapu"):
        toplam_tapu_harci = gayrimenkul_degeri * (intikal_orani / 100.0)
        toplam_resmi_masraf = toplam_tapu_harci + doner_serg
        
        detaylar = []
        if var_es:
            es_pay_orani = 0.25
            cocuklar_toplam_oran = 0.75
            
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

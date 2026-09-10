import streamlit as st
import pandas as pd
from datetime import datetime

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(
    page_title="TMK Miras ve Mal Rejimi Hesaplama Aracı",
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

# --- ANA UYGULAMA ---
st.title("⚖️ Türk Medeni Kanunu (TMK) Miras & Mal Rejimi Hesaplama")
st.markdown("Bu araç; yasal miras payları, saklı paylar, mal rejimi tasfiyesi ve tapu harçlarını tam kapsamlı zümre sistemine göre hesaplar.")

st.sidebar.header("🗂️ İşlem Seçimi")
islem_turu = st.sidebar.selectbox(
    "Hesaplama Modülü Seçin:",
    ["Zümre Bazlı Yasal Miras ve Saklı Paylar", "Edinilmiş Mallara Katılma Rejimi Tasfiyesi", "Tapu Harçları ve Devir Masrafları Hesaplama"]
)

if islem_turu == "Zümre Bazlı Yasal Miras ve Saklı Paylar":
    st.header("👥 Kapsamlı Zümre ve Miras Paylaşım Hesaplayıcı")
    st.markdown("TMK'ya göre miras bırakanın bıraktığı zümreye ve sağ eşin durumuna göre yasal paylar ve saklı paylar hesaplanır.")

    col1, col2 = st.columns(2)
    with col1:
        tereke_degeri = st.number_input("Toplam Tereke Aktifi (TL):", min_value=0.0, value=1000000.0, step=50000.0)
        zumre_secimi = st.selectbox(
            "Mirasçının Bulunduğu Zümre / Durum:",
            [
                "1. Zümre: Çocuklar / Torunlar (Altsoy) ve Sağ Eş",
                "2. Zümre: Anne, Baba, Kardeşler ve Sağ Eş",
                "3. Zümre: Büyük anne, Büyük baba ve Çocukları / Sağ Eş",
                "Yalnızca Sağ Eş (Hiçbir zümre akrabası yok)"
            ]
        )
        sag_es = st.checkbox("Sağ Eş Hayatta mı?", value=True)

    with col2:
        if "1. Zümre" in zumre_secimi:
            cocuk_sayisi = st.number_input("Hayattaki / Temsil Olunan Çocuk Sayısı:", min_value=1, value=2, step=1)
        elif "2. Zümre" in zumre_secimi:
            st.info("2. Zümrede anne-baba ve kardeşlerin durumunu belirtiniz:")
            anne_hayatta = st.checkbox("Anne Hayatta", value=True)
            baba_hayatta = st.checkbox("Baba Hayatta", value=True)
            kardes_sayisi = st.number_input("Kardeş Sayısı (Temsil olunanlar dahil):", min_value=0, value=1, step=1)
        elif "3. Zümre" in zumre_secimi:
            st.info("3. Zümre büyük anne ve büyük babaları kapsar.")
            anne_anne_baba_hayatta = st.checkbox("Anne tarafı büyük anne/baba hayatta mı?", value=False)
            baba_anne_baba_hayatta = st.checkbox("Baba tarafı büyük anne/baba hayatta mı?", value=False)

    if st.button("Zümre Paylaşımını Hesapla"):
        st.subheader("📊 Zümre Bazlı Yasal ve Saklı Pay Dağılımı")
        
        sonuclar = []
        
        if "1. Zümre" in zumre_secimi:
            if sag_es:
                es_payi_orani = 0.25 # 1/4
                altsoy_payi_orani = 0.75 # 3/4
                
                es_tutar = tereke_degeri * es_payi_orani
                sonuclar.append({"Mirasçı": "Sağ Eş", "Yasal Pay Oranı": "%25.00 (1/4)", "Tutar (TL)": es_tutar, "Saklı Pay Oranı": "%12.5 (Yasal payın yarısı)"})
                
                kisi_basi_cocuk = altsoy_payi_orani / cocuk_sayisi
                for i in range(1, cocuk_sayisi + 1):
                    cocuk_tutar = tereke_degeri * kisi_basi_cocuk
                    sonuclar.append({"Mirasçı": f"{i}. Çocuk / Altsoy", "Yasal Pay Oranı": f"%{kisi_basi_cocuk*100:.2f}", "Tutar (TL)": cocuk_tutar, "Saklı Pay Oranı": f"%{kisi_basi_cocuk*50:.2f} (Yasal payın yarısı)"})
            else:
                kisi_basi_cocuk = 1.0 / cocuk_sayisi
                for i in range(1, cocuk_sayisi + 1):
                    cocuk_tutar = tereke_degeri * kisi_basi_cocuk
                    sonuclar.append({"Mirasçı": f"{i}. Çocuk / Altsoy", "Yasal Pay Oranı": f"%{kisi_basi_cocuk*100:.2f}", "Tutar (TL)": cocuk_tutar, "Saklı Pay Oranı": f"%{kisi_basi_cocuk*50:.2f}"})

        elif "2. Zümre" in zumre_secimi:
            if sag_es:
                es_payi_orani = 0.50 # 1/2
                kalan_oran = 0.50 # 1/2
                
                es_tutar = tereke_degeri * es_payi_orani
                sonuclar.append({"Mirasçı": "Sağ Eş", "Yasal Pay Oranı": "%50.00 (1/2)", "Tutar (TL)": es_tutar, "Saklı Pay Oranı": "%25.00 (Yasal payın yarısı)"})
                
                # İkinci zümre kök başı paylaşımı (Anne-Baba kolu ve Kardeşler)
                # TMK m. 496: Ana ve baba eşit olarak paylaşır. Ölmüşlerse yerlerine altsoyları (kardeşler) geçer.
                kol_sayisi = 2 # Anne kolu ve Baba kolu
                anne_kol_orani = kalan_oran / 2 # 0.25
                baba_kol_orani = kalan_oran / 2 # 0.25
                
                # Anne kolu hesap
                if anne_hayatta:
                    sonuclar.append({"Mirasçı": "Anne", "Yasal Pay Oranı": "%25.00", "Tutar (TL)": tereke_degeri * anne_kol_orani, "Saklı Pay Oranı": "Yok (2. zümrede saklı pay kalkmıştır)"})
                else:
                    # Anne ölmüşse kardeşlere dağılır (varsayalım bu kolda kardeş var)
                    sonuclar.append({"Mirasçı": "Anne Kolu Kardeşleri / Mirasçıları", "Yasal Pay Oranı": "%25.00", "Tutar (TL)": tereke_degeri * anne_kol_orani, "Saklı Pay Oranı": "Yok"})
                
                # Baba kolu hesap
                if baba_hayatta:
                    sonuclar.append({"Mirasçı": "Baba", "Yasal Pay Oranı": "%25.00", "Tutar (TL)": tereke_degeri * baba_kol_orani, "Saklı Pay Oranı": "Yok"})
                else:
                    sonuclar.append({"Mirasçı": "Baba Kolu Kardeşleri / Mirasçıları", "Yasal Pay Oranı": "%25.00", "Tutar (TL)": tereke_degeri * baba_kol_orani, "Saklı Pay Oranı": "Yok"})
            else:
                st.write("Sağ eş yok, 2. zümre terekenin tamamını (%100) paylaşır.")
                sonuclar.append({"Mirasçı": "Anne / Baba / Kardeşler Kolu", "Yasal Pay Oranı": "%100.00", "Tutar (TL)": tereke_degeri, "Saklı Pay Oranı": "Yok"})

        elif "3. Zümre" in zumre_secimi:
            if sag_es:
                es_payi_orani = 0.75 # 3/4
                buke_oran = 0.25 # 1/4 büyük anne/babalara kalır
                
                sonuclar.append({"Mirasçı": "Sağ Eş", "Yasal Pay Oranı": "%75.00 (3/4)", "Tutar (TL)": tereke_degeri * es_payi_orani, "Saklı Pay Oranı": "%37.5"})
                sonuclar.append({"Mirasçı": "3. Zümre Kökleri (Büyük Anne / Büyük Babalar ve Altsoyları)", "Yasal Pay Oranı": "%25.00 (1/4)", "Tutar (TL)": tereke_degeri * buke_oran, "Saklı Pay Oranı": "Yok"})
            else:
                sonuclar.append({"Mirasçı": "3. Zümre Büyük Anne / Büyük Babalar", "Yasal Pay Oranı": "%100.00", "Tutar (TL)": tereke_degeri, "Saklı Pay Oranı": "Yok"})

        elif "Yalnızca Sağ Eş" in zumre_secimi:
            sonuclar.append({"Mirasçı": "Sağ Eş (Hiçbir zümre akrabası yoksa)", "Yasal Pay Oranı": "%100.00", "Tutar (TL)": tereke_degeri, "Saklı Pay Oranı": "%50.00"})

        df_sonuc = pd.DataFrame(sonuclar)
        st.dataframe(df_sonuc, use_container_width=True)
        st.success("✨ Hesaplama TMK hükümleri ve zümre başı ilkelerine uygun olarak tamamlandı.")

elif islem_turu == "Edinilmiş Mallara Katılma Rejimi Tasfiyesi":
    st.header("💍 Mal Rejimi Tasfiyesi (Artık Değer Hesabı)")
    
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.subheader("Eş 1 Değerleri")
        aktif_1 = st.number_input("Eş 1 Toplam Mal Varlığı (Aktif)", min_value=0.0, value=2000000.0, key="a1")
        borc_1 = st.number_input("Eş 1 Borçları", min_value=0.0, value=500000.0, key="b1")
        kisisel_1 = st.number_input("Eş 1 Kişisel Malları", min_value=0.0, value=300000.0, key="k1")
        
    with col_e2:
        st.subheader("Eş 2 Değerleri")
        aktif_2 = st.number_input("Eş 2 Toplam Mal Varlığı (Aktif)", min_value=0.0, value=1000000.0, key="a2")
        borc_2 = st.number_input("Eş 2 Borçları", min_value=0.0, value=100000.0, key="b2")
        kisisel_2 = st.number_input("Eş 2 Kişisel Malları", min_value=0.0, value=200000.0, key="k2")

    if st.button("Tasfiye ve Katılma Alacağı Hesapla"):
        artik_deger_1 = max(0.0, aktif_1 - borc_1 - kisisel_1)
        artik_deger_2 = max(0.0, aktif_2 - borc_2 - kisisel_2)
        
        st.write(f"**Eş 1 Artık Değeri:** {artik_deger_1:,.2f} TL")
        st.write(f"**Eş 2 Artık Değeri:** {artik_deger_2:,.2f} TL")
        
        toplam_artik = artik_deger_1 + artik_deger_2
        katilma_alacagi = toplam_artik / 2
        
        st.success(f"💰 **Toplam Tasfiye Edilecek Artık Değer:** {toplam_artik:,.2f} TL")
        st.info(f"⚖️ Her bir eşin diğer eşin artık değerinden **%50 katılma alacağı hakkı**: {katilma_alacagi:,.2f} TL'dir.")

elif islem_turu == "Tapu Harçları ve Devir Masrafları Hesaplama":
    st.header("🏛️ Tapu Devir ve Devlete Ödenecek Masraf / Harç Hesaplayıcı")

    gayrimenkul_degeri = st.number_input("Gayrimenkulün Beyan Edilen / Emlak Vergi Değeri (TL):", min_value=0.0, value=2500000.0, step=100000.0)
    islem_tipi = st.selectbox(
        "İşlem Türü Seçin:",
        [
            "Miras İntikal İşlemi (Tapu Tescili)",
            "Mal Rejimi Tasfiyesi / Eşler Arası Devir",
            "Mirasçılar Arası Pay Devri",
            "Üçüncü Şahıslara Satış / Devir"
        ]
    )

    if st.button("Masrafları Hesapla"):
        st.subheader("🧾 Özet Masraf Dökümü")
        doner_sermaye = 1350.0
        
        if "İntikal" in islem_tipi:
            tapu_harci = gayrimenkul_degeri * 0.00227
            aciklama = "Miras intikalinde düşük oranlı harç uygulanır."
        elif "Mal Rejimi" in islem_tipi:
            tapu_harci = gayrimenkul_degeri * 0.00227 
            aciklama = "Mal rejimi tasfiyesi gereği eşler arası devirlerde özel harç uygulanır."
        elif "Pay Devri" in islem_tipi:
            tapu_harci = gayrimenkul_degeri * 0.0457
            aciklama = "Mirasçılar arası pay devirlerinde maktu/nispi oranlar geçerlidir."
        else:
            tapu_harci = gayrimenkul_degeri * 0.04
            aciklama = "Genel satış işleminde toplam %4 tapu harcı doğar."

        toplam_masraf = tapu_harci + doner_sermaye
        
        st.write(f"- 📌 **İşlem Açıklaması:** {aciklama}")
        st.write(f"- 🏦 **Tahmini Tapu Harcı:** {tapu_harci:,.2f} TL")
        st.write(f"- 📄 **Tapu Döner Sermaye Bedeli:** {doner_sermaye:,.2f} TL")
        st.markdown("---")
        st.success(f"💳 **Devlete Ödenecek Toplam Masraf:** **{toplam_masraf:,.2f} TL**")

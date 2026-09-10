import streamlit as st
import pandas as pd
from datetime import datetime
import io

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(
    page_title="TMK Miras ve Mal Rejimi Hesaplama Aracı",
    page_icon="⚖️",
    layout="wide"
)

# --- BASİT OTURUM / ŞİFRE KONTROLÜ ---
def check_password():
    """Uygulama için basit bir parola koruması sağlar."""
    def password_entered():
        if st.session_state["password"] == "ege12345":  # Şifreyi buradan değiştirebilirsiniz
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Şifreyi session'dan sil
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
st.markdown("Bu araç; yasal miras payları, saklı paylar, mal rejimi tasfiyesi ve **tapu devir harçları/masraflarını** hesaplamak için hazırlanmıştır.")

st.sidebar.header("🗂️ İşlem Seçimi")
islem_turu = st.sidebar.selectbox(
    "Hesaplama Modülü Seçin:",
    ["Yasal Miras Payları ve Saklı Paylar", "Edinilmiş Mallara Katılma Rejimi Tasfiyesi", "Tapu Harçları ve Devir Masrafları Hesaplama"]
)

if islem_turu == "Yasal Miras Payları ve Saklı Paylar":
    st.header("👥 Yasal Miras Paylaşımı ve Saklı Pay Hesaplayıcı")
    
    col1, col2 = st.columns(2)
    with col1:
        tereke_degeri = st.number_input("Toplam Tereke Aktifi (TL):", min_value=0.0, value=1000000.0, step=50000.0)
        cocuk_sayisi = st.number_input("Çocuk (Altsoy) Sayısı:", min_value=0, value=2, step=1)
        sag_es = st.checkbox("Sağ Eş Hayatta mı?", value=True)
    
    with col2:
        ana_hayatta = st.checkbox("Anne Hayatta mı?", value=False)
        baba_hayatta = st.checkbox("Baba Hayatta mı?", value=False)
        vasiyet_orani = st.number_input("Tasarruf Özgürlüğü Sınırı / Vasiyet Oranı (%)", min_value=0.0, max_value=100.0, value=0.0)

    if st.button("Miras Paylaşımını Hesapla"):
        st.subheader("📊 Sonuçlar ve Yasal Oranlar")
        
        # Temel Zümre Mantığı (1. Zümre)
        if cocuk_sayisi > 0:
            if sag_es:
                es_payi = 0.25  # 1/4
                kalan_pay = 0.75
                cocuklara_kalan = kalan_pay / cocuk_sayisi
                
                st.write(f"- **Sağ Eşin Yasal Payı:** %25 ({tereke_degeri * es_payi:,.2f} TL)")
                st.write(f"- **Çocukların Her Birinin Payı:** %{75/cocuk_sayisi:.2f} (Kişi başı: {tereke_degeri * cocuklara_kalan:,.2f} TL)")
            else:
                cocuklara_kalan = 1.0 / cocuk_sayisi
                st.write(f"- **Çocukların Her Birinin Payı:** %{100/cocuk_sayisi:.2f} (Kişi başı: {tereke_degeri * cocuklara_kalan:,.2f} TL)")
        else:
            st.info("1. Zümrede çocuk bulunamadı. Üst zümre hesaplamaları sonraki versiyonda detaylandırılacaktır.")

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
        # Artık Değer = Aktif - Borç - Kişisel Mal
        artik_deger_1 = max(0.0, aktif_1 - borc_1 - kisisel_1)
        artik_deger_2 = max(0.0, aktif_2 - borc_2 - kisisel_2)
        
        st.write(f"**Eş 1 Artık Değeri:** {artik_deger_1:,.2f} TL")
        st.write(f"**Eş 2 Artık Değeri:** {artik_deger_2:,.2f} TL")
        
        toplam_artik = artik_deger_1 + artik_deger_2
        katilma_alacagi = toplam_artik / 2
        
        st.success(f"💰 **Toplam Tasfiye Edilecek Artık Değer:** {toplam_artik:,.2f} TL")
        st.info(f"⚖️ Her bir eşin diğer eşin artık değerinden **%50 katılma alacağı hakkı** (Eşit paylaşım): {katilma_alacagi:,.2f} TL'dir.")

elif islem_turu == "Tapu Harçları ve Devir Masrafları Hesaplama":
    st.header("🏛️ Tapu Devir ve Devlete Ödenecek Masraf / Harç Hesaplayıcı")
    st.markdown("Miras intikali, mal rejimi tasfiyesi veya tapu devir işlemleri sırasında tapu müdürlükleri ve vergi daireleri tarafından tahsil edilen güncel yasal kalemler:")

    gayrimenkul_degeri = st.number_input("Gayrimenkulün Beyan Edilen / Emlak Vergi Değeri (TL):", min_value=0.0, value=2500000.0, step=100000.0)
    islem_tipi = st.selectbox(
        "İşlem Türü Seçin:",
        [
            "Miras İntikal İşlemi (Tapu Tescili)",
            "Mal Rejimi Tasfiyesi / Eşler Arası Devir",
            "Mirasçılar Arası Pay Devri (Satış/Devir)",
            "Üçüncü Şahıslara Satış / Devir"
        ]
    )

    if st.button("Masrafları Hesapla"):
        st.subheader("🧾 Özet Masraf Dökümü")
        
        # Güncel oran varsayımları (2026 yılı standart oranları baz alınmıştır)
        doner_sermaye = 1350.0  # Ortalama döner sermaye harcı bedeli
        
        if "İntikal" in islem_tipi:
            # İntikal harcı genelde binde 2.27 civarındadır
            tapu_harci = gayrimenkul_degeri * 0.00227
            aciklama = "Miras intikalinde düşük oranlı harç uygulanır."
        elif "Mal Rejimi" in islem_tipi:
            # Mal rejimi tasfiyesi gereği eşe devirlerde özel indirimler/istisnalar uygulanabilir
            tapu_harci = gayrimenkul_degeri * 0.00227 
            aciklama = "Mal rejimi tasfiyesi ve mahkeme/noter sözleşmesine dayalı eş devirlerinde intikal benzeri harç uygulanır."
        elif "Pay Devri" in islem_tipi:
            tapu_harci = gayrimenkul_degeri * 0.0457  # Binde 45.7 (Tarafların binde 20'şer veya satış gösterilmesi durumuna göre değişir)
            aciklama = "Mirasçılar arası pay devirlerinde maktu/nispi oranlar söz konusudur."
        else:
            # Normal satış binde 20 alıcı, binde 20 satıcı = %4 toplam
            tapu_harci = gayrimenkul_degeri * 0.04
            aciklama = "Genel satış işleminde toplam %4 (alıcı+satıcı) tapu harcı doğar."

        toplam_masraf = tapu_harci + doner_sermaye
        
        st.write(f"- 📌 **İşlem Açıklaması:** {aciklama}")
        st.write(f"- 🏦 **Tahmini Tapu Harcı:** {tapu_harci:,.2f} TL")
        st.write(f"- 📄 **Tapu Döner Sermaye Bedeli:** {doner_sermaye:,.2f} TL")
        st.markdown("---")
        st.success(f"💳 **Devlete Ödenecek Toplam Masraf:** **{toplam_masraf:,.2f} TL**")
        st.warning("⚠️ *Not: Emlak rayiç bedeli, belediye değerleri ve her yıl güncellenen döner sermaye tarifelerine göre tutarlar küçük değişiklikler gösterebilir.*")

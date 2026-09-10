from fractions import Fraction
import streamlit as st
import pandas as pd
import plotly.express as px
from docx import Document
from io import BytesIO

st.set_page_config(page_title="Gelişmiş Bilirkişi Miras ve Mal Rejimi Sistemi", layout="wide")

# --- ŞİFRE KORUMA MEKANİZMASI ---
def check_password():
    def password_entered():
        if st.session_state["password"] == "ege12345":  # Buradaki şifreyi dilediğiniz gibi değiştirebilirsiniz
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Şifreyi hafızadan temizle
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Lütfen Erişim Şifresini Girin:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Lütfen Erişim Şifresini Girin:", type="password", on_change=password_entered, key="password")
        st.error("😕 Şifre hatalı, lütfen tekrar deneyin.")
        return False
    else:
        return True

if not check_password():
    st.stop()  # Şifre doğru girilene kadar uygulamanın geri kalanını durdur
# ---------------------------------

st.title("⚖️ TMK Mal Rejimi Tasfiyesi, Zümre Paylaşımı ve Kurumsal Raporlama")
st.markdown("---")

# Sekme Mimarisi
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📁 1. Varlık, Borç ve Mal Rejimi", 
    "👥 2. Gelişmiş Zümre Paylaşımı", 
    "🛡️ 3. Tenkis (Saklı Pay) Analizi", 
    "🏠 4. Tapu ve Aynen Taksim",
    "📄 5. Görselleştirme ve Word Raporu"
])

# Session State Tanımları
if "df_aktif" not in st.session_state:
    st.session_state.df_aktif = pd.DataFrame([
        {"Varlık Adı": "Merkez Konut", "Niteliği": "Mesken", "Yüzölçümü (m2)": 120, "Değer (TL)": 3000000.0},
        {"Varlık Adı": "Tarla (Tarım Arazisi)", "Niteliği": "Tarla", "Yüzölçümü (m2)": 15000, "Değer (TL)": 800000.0}
    ])

if "df_pasif" not in st.session_state:
    st.session_state.df_pasif = pd.DataFrame([
        {"Borç Açıklaması": "Konut Kredisi", "Tutar (TL)": 200000.0}
    ])

# TAB 1: VARLIK, BORÇ VE MAL REJİMİ TASFİYESİ
with tab1:
    st.header("Aktif Varlıklar, Pasif Borçlar ve Mal Rejimi Tasfiyesi")
    st.write("Ölümle sona eren evliliklerde miras paylaşımı öncesi yasal mal rejimi tasfiyesi (edinilmiş mallar / katılma alacağı) hesaplanır.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏠 Aktif Mülkler ve Varlıklar")
        st.session_state.df_aktif = st.data_editor(
            st.session_state.df_aktif, num_rows="dynamic", key="edit_aktif", use_container_width=True
        )
    with col2:
        st.subheader("💳 Pasif Borçlar ve Masraflar")
        st.session_state.df_pasif = st.data_editor(
            st.session_state.df_pasif, num_rows="dynamic", key="edit_pasif", use_container_width=True
        )

    toplam_aktif = st.session_state.df_aktif["Değer (TL)"].sum()
    toplam_pasif = st.session_state.df_pasif["Tutar (TL)"].sum()
    
    st.markdown("---")
    st.subheader("💍 Mal Rejimi Tasfiyesi (Eşlerin Katılma Alacağı)")
    col_mr1, col_mr2 = st.columns(2)
    with col_mr1:
        edinilmis_aktif = st.number_input("Evlilik İçinde Edinilen Toplam Aktif Değer (TL)", min_value=0.0, value=3000000.0)
        edinilmis_borc = st.number_input("Edinilen Mallara İlişkin Borçlar (TL)", min_value=0.0, value=200000.0)
    with col_mr2:
        kisisel_mallar_toplami = st.number_input("Miras Bırakanın Kişisel Malları Toplamı (TL)", min_value=0.0, value=800000.0)

    artik_deger = max(0.0, edinilmis_aktif - edinilmis_borc)
    es_katilma_alacagi = artik_deger * 0.5 
    
    net_tereke = max(0.0, (toplam_aktif - toplam_pasif) - es_katilma_alacagi)

    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Toplam Aktif", f"{toplam_aktif:,.2f} TL")
    m2.metric("Toplam Borç", f"{toplam_pasif:,.2f} TL")
    m3.metric("Eş Katılma Alacağı", f"{es_katilma_alacagi:,.2f} TL")
    m4.metric("Net Dağıtılabilir Tereke", f"{net_tereke:,.2f} TL", delta="Mal Rejimi Düşülmüş")

# TAB 2: GELİŞMİŞ ZÜMRE PAYLAŞIMI
with tab2:
    st.header("Türk Medeni Kanunu (TMK) Zümre ve Halefiyet Paylaşım Motoru")
    
    col_k1, col_k2 = st.columns(2)
    with col_k1:
        dosya_no = st.text_input("Mahkeme / Esas No", "2026/450 Esas")
        miras_birakan = st.text_input("Miras Bırakanın Adı Soyadı", "Mehmet Demir")
    with col_k2:
        es_var_mi = st.checkbox("Sağ Kalan Eş Var mı?", value=True)
        es_adi = st.text_input("Sağ Kalan Eşin Adı Soyadı", "Ayşe Demir" if es_var_mi else "")

    zumre_secimi = st.selectbox(
        "Uygulanacak Zümre Sistemi",
        [
            "1. Zümre (Alt Soy: Çocuklar ve Torunlar)",
            "2. Zümre (Ana, Baba, Kardeşler ve Yeğenler)",
            "3. Zümre (Büyük Anne, Büyük Baba, Amca, Hala, Dayı, Teyze)"
        ]
    )

    hisseler = {}
    kalan_pay = Fraction(1, 1)

    if es_var_mi:
        if "1. Zümre" in zumre_secimi:
            es_orani = Fraction(1, 4)
        elif "2. Zümre" in zumre_secimi:
            es_orani = Fraction(1, 2)
        else:
            es_orani = Fraction(3, 4)
        
        hisseler[f"Eş: {es_adi} (Yasal Miras Payı)"] = es_orani
        kalan_pay = Fraction(1, 1) - es_orani

    if "1. Zümre" in zumre_secimi:
        st.subheader("1. Zümre Detayları (Çocuklar ve Halefiyet)")
        cocuk_sayisi = st.number_input("Kök Çocuk Sayısı", min_value=1, max_value=10, value=2)
        
        cocuk_listesi = []
        for i in range(int(cocuk_sayisi)):
            c_adi = st.text_input(f"{i+1}. Çocuğun Adı", f"Çocuk {i+1}", key=f"z1_c_{i}")
            c_durum = st.selectbox(f"{c_adi} Durumu", ["Hayatta", "Vefat Etmiş (Torunlar Var)"], key=f"z1_d_{i}")
            
            torunlar = []
            if "Vefat" in c_durum:
                t_sayisi = st.number_input(f"'{c_adi}' Çocuk (Torun) Sayısı", min_value=1, max_value=5, key=f"z1_t_{i}")
                for t in range(int(t_sayisi)):
                    t_ad = st.text_input(f"  -> {t+1}. Torun Adı", f"Torun {i+1}-{t+1}", key=f"z1_tad_{i}_{t}")
                    torunlar.append(t_ad)
            
            cocuk_listesi.append({"ad": c_adi, "durum": c_durum, "torunlar": torunlar})

        if st.button("1. Zümre Paylaşımını Hesapla", type="primary"):
            cocuk_basina = kalan_pay / cocuk_sayisi
            for c in cocuk_listesi:
                if c["durum"] == "Hayatta":
                    unvan = f"Çocuk: {c['ad']} (Hayatta)"
                    hisseler[unvan] = hisseler.get(unvan, Fraction(0)) + cocuk_basina
                else:
                    if len(c["torunlar"]) > 0:
                        torun_payi = cocuk_basina / len(c["torunlar"])
                        for tad in c["torunlar"]:
                            tunvan = f"Torun: {tad} ({c['ad']} Hısımlığı)"
                            hisseler[tunvan] = hisseler.get(tunvan, Fraction(0)) + torun_payi

    elif "2. Zümre" in zumre_secimi:
        st.subheader("2. Zümre Detayları (Ana, Baba ve Kardeşler)")
        anne_hayatta = st.checkbox("Anne Hayatta mı?")
        baba_hayatta = st.checkbox("Baba Hayatta mı?")
        kardes_sayisi = st.number_input("Kardeş Sayısı", min_value=0, max_value=10, value=1)
        
        kardesler = [st.text_input(f"{k+1}. Kardeşin Adı", f"Kardeş {k+1}", key=f"z2_k_{k}") for k in range(int(kardes_sayisi))]

        if st.button("2. Zümre Paylaşımını Hesapla", type="primary"):
            anababa_sayisi = (1 if anne_hayatta else 0) + (1 if baba_hayatta else 0)
            if anababa_sayisi == 2:
                hisseler["Anne"] = kalan_pay * Fraction(1, 4)
                hisseler["Baba"] = kalan_pay * Fraction(1, 4)
                kp = (kalan_pay * Fraction(1, 2)) / (kardes_sayisi or 1)
                for kad in kardesler: hisseler[f"Kardeş: {kad}"] = kp
            elif anababa_sayisi == 1:
                if anne_hayatta: hisseler["Anne"] = kalan_pay * Fraction(1, 2)
                if baba_hayatta: hisseler["Baba"] = kalan_pay * Fraction(1, 2)
                kp = (kalan_pay * Fraction(1, 2)) / (kardes_sayisi or 1)
                for kad in kardesler: hisseler[f"Kardeş: {kad}"] = kp
            else:
                kp = kalan_pay / (kardes_sayisi or 1)
                for kad in kardesler: hisseler[f"Kardeş: {kad}"] = kp

    elif "3. Zümre" in zumre_secimi:
        st.subheader("3. Zümre Detayları (Büyük Anne, Büyük Baba, Amca vb.)")
        akraba_sayisi = st.number_input("3. Zümre Yakın Sayısı", min_value=1, max_value=10, value=2)
        akraba_adlari = [st.text_input(f"{a+1}. Yakın Adı", f"Akraba {a+1}", key=f"z3_{a}") for a in range(int(akraba_sayisi))]
        if st.button("3. Zümre Paylaşımını Hesapla", type="primary"):
            ap = kalan_pay / akraba_sayisi
            for aad in akraba_adlari: hisseler[f"3. Zümre Yakını: {aad}"] = ap

    if hisseler:
        st.markdown("---")
        st.subheader("🏆 Kesinleşmiş Mirasçı Payları Matrisi")
        mirasci_liste = [
            {"Sıra": idx, "Hak Sahibi": hs, "Kesirli Hisse": str(oran), "Yüzde (%)": round(float(oran)*100, 4), "Net Tutar (TL)": round(net_tereke * float(oran), 2)}
            for idx, (hs, oran) in enumerate(hisseler.items(), 1)
        ]
        st.session_state.df_paylar = pd.DataFrame(mirasci_liste)
        st.dataframe(st.session_state.df_paylar, use_container_width=True)

# TAB 3: TENKİS (SAKLI PAY) ANALİZİ
with tab3:
    st.header("Tenkis (Saklı Pay İhlali) Hesaplama Modülü")
    bagis_tutari = st.number_input("Sağlığında Yapılan Karşılıksız Kazandırma / Bağış Tutarı (TL)", min_value=0.0, value=500000.0)
    hesap_terekesi = net_tereke + bagis_tutari
    st.metric("Hesaplama Terekesi", f"{hesap_terekesi:,.2f} TL")

    if st.button("Tenkis Testini Çalıştır"):
        tasarruf_kismi = hesap_terekesi * 0.5
        if bagis_tutari > tasarruf_kismi:
            st.error(f"⚠️ SAKLI PAY İHLALİ TESPİT EDİLDİ! Bağış tasarruf edilebilir kısmı {bagis_tutari - tasarruf_kismi:,.2f} TL aşmaktadır.")
        else:
            st.success("✔ Saklı pay ihlali bulunmuyor.")

# TAB 4: TAPU VE AYNEN TAKSİM
with tab4:
    st.header("Tapu Taşınmazları ve Aynen Taksim Uygunluk Analizi")
    for idx, row in st.session_state.df_aktif.iterrows():
        st.markdown(f"**Mülk:** {row['Varlık Adı']} | **Niteliği:** {row['Niteliği']} | **Alan:** {row['Yüzölçümü (m2)']} m2")
        if row['Niteliği'].lower() in ['tarla', 'tarım arazisi', 'bağ', 'bahçe']:
            if row['Yüzölçümü (m2)'] < 20000:
                st.warning("⚠️ 20.000 m² altında olduğu için **Aynen Taksim (ifraz) yapılamaz!** İştirak halinde ortak mülkiyet gerekir.")
            else:
                st.success("✔ Aynen taksim (ifraz) mümkündür.")
        st.markdown("---")

# TAB 5: GÖRSELLEŞTİRME VE WORD RAPORU
with tab5:
    st.header("📊 Grafiksel Dağılım ve Kurumsal Word Raporu Üretimi")
    
    if "df_paylar" in st.session_state and not st.session_state.df_paylar.empty:
        st.subheader("Mirasçı Payları Pasta Grafiği")
        fig = px.pie(st.session_state.df_paylar, names="Hak Sahibi", values="Net Tutar (TL)", title="Tereke Dağılım Grafiği")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("Kurumsal Bilirkişi Raporunu İndir (.docx)")
        
        if st.button("📥 Resmî Word Bilirkişi Raporunu Oluştur"):
            doc = Document()
            doc.add_heading(f"BİLİRKİŞİ RAPORU", level=1)
            doc.add_paragraph(f"Dosya Esas No: {dosya_no}")
            doc.add_paragraph(f"Miras Bırakan: {miras_birakan}")
            doc.add_paragraph(f"Net Dağıtılabilir Tereke Tutarı: {net_tereke:,.2f} TL")
            
            doc.add_heading("Hakkında Karar Verilen Mirasçı Payları:", level=2)
            for index, row in st.session_state.df_paylar.iterrows():
                doc.add_paragraph(f"- {row['Hak Sahibi']}: {row['Kesirli Hisse']} oran, %{row['Yüzde (%)']} pay, {row['Net Tutar (TL)']:,.2f} TL")
            
            doc_buffer = BytesIO()
            doc.save(doc_buffer)
            doc_buffer.seek(0)

            st.download_button(
                label="📥 Bilirkişi Raporu Word Belgesini İndir",
                data=doc_buffer,
                file_name=f"Bilirkisi_Raporu_{miras_birakan.replace(' ', '_')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
    else:
        st.info("ℹ️ Lütfen önce '2. Gelişmiş Zümre Paylaşımı' sekmesinden hesaplama işlemini gerçekleştirin.")
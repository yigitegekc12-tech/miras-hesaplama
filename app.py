import streamlit as st
import pandas as pd
import io
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl import load_workbook

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(
    page_title="TMK Profesyonel Miras ve Mal Rejimi Sistemi",
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

# --- ANA BAŞLIK ---
st.title("⚖️ Türk Medeni Kanunu Profesyonel Miras & Mali Tasfiye Sistemi")
st.markdown("Bu araç; varlık-borç analizinden zümre paylaşımlarına, **tenkis hesaplamalarından** tapu masraflarına ve büyük puntolu profesyonel Excel raporlarına kadar kurumsal çözümler sunar.")

# --- MODERN SEKME (TAB) YAPISI ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "1️⃣ Aktif & Borç Analizi", 
    "2️⃣ Zümre & Miras Paylaşımı", 
    "3️⃣ Mal Rejimi Tasfiyesi", 
    "4️⃣ Tenkis (Saklı Pay İhlali) Hesabı",
    "5️⃣ Tapu ve Masraf Düşümleri",
    "6️⃣ 📊 Kapsamlı Rapor ve Dışa Aktarım"
])

# --- TAB 1: AKTİF / PASİF (NET TEREKE) ANALİZİ ---
with tab1:
    st.header("💼 Adım 1: Tereke Varlıkları ve Borçlarının Tespiti")
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
        st.session_state["toplam_aktif"] = toplam_aktif
        st.session_state["toplam_pasif"] = toplam_pasif
        st.session_state["gayrimenkul_degeri"] = gayrimenkul_aktif

        st.success("✅ Net Tereke başarıyla hesaplandı ve rapor motoruna kaydedildi!")
        
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("Toplam Brüt Aktif", f"{toplam_aktif:,.2f} TL")
        col_s2.metric("Toplam Pasif (Borçlar)", f"{toplam_pasif:,.2f} TL")
        col_s3.metric("Net Tereke", f"{net_tereke:,.2f} TL")

# --- TAB 2: ZÜMRE BAZLI YASAL MİRAS VE SAKLI PAYLAR ---
with tab2:
    st.header("👥 Adım 2: Zümre, Altsoy ve Torun Temsil Hesaplayıcı")
    varsayilan_tereke = st.session_state.get("net_tereke", 3500000.0)
    tereke_degeri = st.number_input("Paylaştırılacak Net Tereke Aktifi (TL):", min_value=0.0, value=varsayilan_tereke, step=50000.0, key="t_deger_t2")
    
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
                sonuclar.append({"Mirasçı": "Sağ Eş", "Yasal Pay Oranı": "%25.00 (1/4)", "Tutar (TL)": tereke_degeri * 0.25, "Saklı Pay Oranı": "%12.50"})

            her_bir_kok_orani = altsoy_toplam_oran / cocuk_sayisi
            for i, c_data in enumerate(cocuk_durumlari, 1):
                if c_data["durum"] == "Hayatta":
                    sonuclar.append({"Mirasçı": f"{i}. Çocuk (Hayatta)", "Yasal Pay Oranı": f"%{her_bir_kok_orani * 100:.2f}", "Tutar (TL)": tereke_degeri * her_bir_kok_orani, "Saklı Pay Oranı": f"%{her_bir_kok_orani * 50:.2f}"})
                else:
                    t_sayisi = c_data["torun_sayisi"]
                    torun_basina_oran = her_bir_kok_orani / t_sayisi
                    for t in range(1, t_sayisi + 1):
                        sonuclar.append({"Mirasçı": f"→ {i}. Çocuğun {t}. Çocuğu (Torun / Temsilen)", "Yasal Pay Oranı": f"%{torun_basina_oran * 100:.2f}", "Tutar (TL)": tereke_degeri * torun_basina_oran, "Saklı Pay Oranı": f"%{torun_basina_oran * 50:.2f}"})

        elif "2. Zümre" in zumre_secimi:
            if sag_es:
                sonuclar.append({"Mirasçı": "Sağ Eş", "Yasal Pay Oranı": "%50.00 (1/2)", "Tutar (TL)": tereke_degeri * 0.50, "Saklı Pay Oranı": "%25.00"})
                sonuclar.append({"Mirasçı": "Anne / Baba / Kardeşler Kolu", "Yasal Pay Oranı": "%50.00", "Tutar (TL)": tereke_degeri * 0.50, "Saklı Pay Oranı": "Yok"})
            else:
                sonuclar.append({"Mirasçı": "2. Zümre Akrabaları", "Yasal Pay Oranı": "%100.00", "Tutar (TL)": tereke_degeri, "Saklı Pay Oranı": "Yok"})

        elif "Yalnızca Sağ Eş" in zumre_secimi:
            sonuclar.append({"Mirasçı": "Sağ Eş (Zümre Akrabası Yok)", "Yasal Pay Oranı": "%100.00", "Tutar (TL)": tereke_degeri, "Saklı Pay Oranı": "%50.00"})

        if sonuclar:
            df_sonuc = pd.DataFrame(sonuclar)
            st.session_state["df_miras_pay"] = df_sonuc
            st.subheader("📊 Kesin Miras Dağılım Tablosu")
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
        st.session_state["mal_rejimi_sonuc"] = f"Toplam Artık Değer: {toplam_artik:,.2f} TL | Eşlerin Katılma Alacağı: {katilma:,.2f} TL"
        st.success(st.session_state["mal_rejimi_sonuc"])

# --- TAB 4: TENKİS (SAKLI PAY İHLALİ) HESABI ---
with tab4:
    st.header("📜 Adım 4: Vasiyetname ve Saklı Pay İhlali (Tenkis) Analizi")
    st.markdown("Mirasbırakanın yasal saklı payları aşarak yaptığı kazandırmaların (vasiyetname / bağışlar) tenkise (indirime) tabi olup olmadığını hesaplayın.")
    
    base_tereke = st.session_state.get("net_tereke", 3500000.0)
    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        net_tereke_t4 = st.number_input("Net Tereke Değeri (TL):", min_value=0.0, value=base_tereke, step=50000.0, key="net_t_t4")
        tenkise_tabi_kazandirma = st.number_input("Üçüncü Kişilere Yapılan Vasiyet / Karşılıksız Kazandırma Tutarı (TL):", min_value=0.0, value=1000000.0, step=50000.0, key="kazandirma_t4")
    
    with col_t2:
        mirasci_durumu_t4 = st.selectbox(
            "Saklı Pay Sahibi Miras Grubu:",
            [
                "Altsoy (Çocuklar) ve Sağ Eş Var",
                "Yalnızca Altsoy (Çocuklar) Var (Eş Yok)",
                "Anne ve Baba Var (Altsoy ve Eş Yok)"
            ],
            key="m_durum_t4"
        )
        toplam_cocuk_t4 = st.number_input("Çocuk / Kök Sayısı:", min_value=1, value=2, step=1, key="c_say_t4")

    if st.button("Tenkis (Saklı Pay İhlali) Hesabını Çalıştır", type="primary", key="btn_tenkis_calistir"):
        # Hesaplama Terekkesi = Net Tereke + Tenkise Tabi Kazandırmalar (TMK m.506)
        hesaplama_terekkesi = net_tereke_t4 + tenkise_tabi_kazandirma
        
        # Tasarruf Edilebilir Kısım ve Saklı Pay Oranları Tespiti
        if "Altsoy (Çocuklar) ve Sağ Eş Var" in mirasci_durumu_t4:
            # Altsoy ve eş varsa tasarruf edilebilir kısım 1/4'tür (Kalan 3/4 saklı paylar toplamıdır: Eş 1/4, Altsoy 1/2)
            tasarruf_orani = 0.25
            sakli_paylar_toplam_orani = 0.75
        elif "Yalnızca Altsoy (Çocuklar) Var" in mirasci_durumu_t4:
            # Sadece altsoy varsa tasarruf edilebilir kısım 1/2'dir
            tasarruf_orani = 0.50
            sakli_paylar_toplam_orani = 0.50
        else:
            # Anne baba varsa tasarruf edilebilir kısım 1/2'dir
            tasarruf_orani = 0.50
            sakli_paylar_toplam_orani = 0.50

        tasarruf_edilebilir_kisim = hesaplama_terekkesi * tasarruf_orani
        toplam_sakli_pay = hesaplama_terekkesi * sakli_paylar_toplam_orani
        
        # Aşım / İhlal Tutarı (Tenkise Tabi Tutar)
        # Eğer yapılan kazandırma tasarruf edilebilir kısmı aşıyorsa, aşan miktar tenkise tabidir.
        asir_kazandirma = max(0.0, tenkise_tabi_kazandirma - tasarruf_edilebilir_kisim)
        ihlal_var_mi = asir_kazandirma > 0

        tenkis_sonuclar = [
            {"Tenkis / Analiz Kalemi": "Hesaplama Terekkesi (Net Tereke + Kazandırmalar)", "Tutar (TL)": hesaplama_terekkesi},
            {"Tenkis / Analiz Kalemi": "Tasarruf Edilebilir Kısım Sınırı", "Tutar (TL)": tasarruf_edilebilir_kisim},
            {"Tenkis / Analiz Kalemi": "Yasal Mirasçıların Toplam Saklı Payı", "Tutar (TL)": toplam_sakli_pay},
            {"Tenkis / Analiz Kalemi": "Yapılan Vasiyet / Bağış Toplamı", "Tutar (TL)": tenkise_tabi_kazandirma},
            {"Tenkis / Analiz Kalemi": "Saklı Payları İhlal Eden Aşan Tutar (Tenkise Tabi Tutar)", "Tutar (TL)": asir_kazandirma}
        ]
        
        df_tenkis = pd.DataFrame(tenkis_sonuclar)
        st.session_state["df_tenkis_sonuc"] = df_tenkis
        
        st.markdown("---")
        if ihlal_var_mi:
            st.error(f"⚠️ **DİKKAT: Saklı Pay İhlali (Tenkis Sebebi) Var!** Yapılan kazandırmalar tasarruf edilebilir kısmı **{asir_kazandirma:,.2f} TL** aşmaktadır. Saklı pay sahipleri bu miktar için Tenkis Davası açabilir.")
        else:
            st.success("✅ **Saklı Pay İhlali Bulunmuyor.** Yapılan kazandırma tasarruf edilebilir kısım sınırları içindedir.")
            
        st.subheader("📊 Ayrıntılı Tenkis ve Tasarruf Sınırı Tablosu")
        st.dataframe(df_tenkis, use_container_width=True)

# --- TAB 5: TAPU İNTİKAL VE MASRAF DÜŞÜM HESABI ---
with tab5:
    st.header("🏛️ Adım 5: Tapu İntikal Harçları ve Masrafların Paylardan Düşülmesi")
    varsayilan_gayrimenkul = st.session_state.get("gayrimenkul_degeri", 3000000.0)
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        gayrimenkul_degeri = st.number_input("Tapu / Gayrimenkul Toplam Değeri (TL):", min_value=0.0, value=varsayilan_gayrimenkul, step=100000.0, key="g_deger_t5")
        intikal_orani = st.number_input("Tapu İntikal Harcı Oranı (%):", min_value=0.0, value=0.227, step=0.01, key="int_oran_t5")
        doner_serg = st.number_input("Tapu Döner Sermaye / Ek Masraflar (TL):", min_value=0.0, value=1350.0, step=100.0, key="doner_t5")
    
    with col_m2:
        mirasci_tipi = st.selectbox("Miras Grubu:", ["1. Zümre (Eş + Çocuklar/Torunlar)", "Yalnızca Çocuklar (Eş Yok)"], key="m_tip_t5")
        toplam_cocuk = st.number_input("Çocuk / Kök Sayısı:", min_value=1, value=2, step=1, key="c_say_t5")
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
            detaylar.append({"Mirasçı": "Sağ Eş", "Yasal Payı (%)": "%25.00", "Brüt Pay (TL)": brut_es, "Payına Düşen Masraf (TL)": masraf_es, "Net Alacağı (TL)": net_es})
            
            her_cocuk_orani = cocuklar_toplam_oran / toplam_cocuk
            for c in range(1, int(toplam_cocuk) + 1):
                brut_c = gayrimenkul_degeri * her_cocuk_orani
                masraf_c = toplam_resmi_masraf * her_cocuk_orani
                net_c = brut_c - masraf_c
                detaylar.append({"Mirasçı": f"{c}. Çocuk", "Yasal Payı (%)": f"%{her_cocuk_orani * 100:.2f}", "Brüt Pay (TL)": brut_c, "Payına Düşen Masraf (TL)": masraf_c, "Net Alacağı (TL)": net_c})
        else:
            her_cocuk_orani = 1.0 / toplam_cocuk
            for c in range(1, int(toplam_cocuk) + 1):
                brut_c = gayrimenkul_degeri * her_cocuk_orani
                masraf_c = toplam_resmi_masraf * her_cocuk_orani
                net_c = brut_c - masraf_c
                detaylar.append({"Mirasçı": f"{c}. Çocuk", "Yasal Payı (%)": f"%{her_cocuk_orani * 100:.2f}", "Brüt Pay (TL)": brut_c, "Payına Düşen Masraf (TL)": masraf_c, "Net Alacağı (TL)": net_c})

        df_net = pd.DataFrame(detaylar)
        st.session_state["df_tapu_masraf"] = df_net
        st.info(f"💡 **Toplam Tahsil Edilecek Devlet Masrafı:** {toplam_resmi_masraf:,.2f} TL (İntikal Harcı: {toplam_tapu_harci:,.2f} TL + Döner Sermaye: {doner_serg:,.2f} TL)")
        st.subheader("📉 Masrafların Otomatik Düşüldüğü Net Mirasçı Dağılım Tablosu")
        st.dataframe(df_net, use_container_width=True)

# --- TAB 6: 📊 KAPSAMLI RAPOR VE DIŞA AKTARIM (EXCEL / PDF) ---
with tab6:
    st.header("📊 Adım 6: Profesyonel Büyük Puntolu Çok Sayfalı Excel ve PDF Raporu")
    st.markdown("Sistem üzerindeki tüm verileri **büyük ve okunaklı yazı tipleri, kurumsal renkler ve otomatik genişletilmiş sütunlarla** biçimlendirilmiş olarak indirebilirsiniz.")

    col_dl1, col_dl2 = st.columns(2)

    with col_dl1:
        st.subheader("🟢 Büyük Yazı Tipli Kapsamlı Excel Raporu")
        st.markdown("Başlıklar **14 punto bold**, veri hücreleri **12 punto** olarak biçimlendirilmiş, kenarlıklı profesyonel Excel kitabı.")

        if st.button("📥 Büyük Puntolu Profesyonel Excel Dosyasını İndir", type="primary"):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # 1. Sekme: Tereke Özet Bilgileri
                ozet_data = {
                    "Rapor Kalemleri": ["Toplam Brüt Aktif", "Toplam Pasif (Borçlar & Masraflar)", "Net Tereke Değeri"],
                    "Tutar (TL)": [
                        st.session_state.get("toplam_aktif", 4250000.0),
                        st.session_state.get("toplam_pasif", 350000.0),
                        st.session_state.get("net_tereke", 3900000.0)
                    ]
                }
                pd.DataFrame(ozet_data).to_excel(writer, sheet_name='01_Tereke_Ozet', index=False)

                # 2. Sekme: Miras Paylaşım Tablosu
                if "df_miras_pay" in st.session_state:
                    st.session_state["df_miras_pay"].to_excel(writer, sheet_name='02_Miras_Paylari', index=False)
                else:
                    pd.DataFrame({"Bilgi": ["Lütfen önce 2. Adımdan miras paylaşımını hesaplayın."]}).to_excel(writer, sheet_name='02_Miras_Paylari', index=False)

                # 3. Sekme: Tenkis Hesaplamaları
                if "df_tenkis_sonuc" in st.session_state:
                    st.session_state["df_tenkis_sonuc"].to_excel(writer, sheet_name='03_Tenkis_Analizi', index=False)
                else:
                    pd.DataFrame({"Bilgi": ["Lütfen önce 4. Adımdan tenkis analizini çalıştırın."]}).to_excel(writer, sheet_name='03_Tenkis_Analizi', index=False)

                # 4. Sekme: Tapu Harçları ve Masraf Düşümleri
                if "df_tapu_masraf" in st.session_state:
                    st.session_state["df_tapu_masraf"].to_excel(writer, sheet_name='04_Tapu_Ve_Masraflar', index=False)
                else:
                    pd.DataFrame({"Bilgi": ["Lütfen önce 5. Adımdan tapu masraflarını hesaplayın."]}).to_excel(writer, sheet_name='04_Tapu_Ve_Masraflar', index=False)

            # --- OPENPYXL İLE BÜYÜK FONT VE STİL UYGULAMA ---
            output.seek(0)
            wb = load_workbook(output)
            
            # Tasarım Stilleri
            header_font = Font(name='Calibri', size=14, bold=True, color='FFFFFF')
            header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid') # Şık Koyu Mavi
            cell_font = Font(name='Calibri', size=12, bold=False)
            thin_border = Border(
                left=Side(style='thin', color='D9D9D9'),
                right=Side(style='thin', color='D9D9D9'),
                top=Side(style='thin', color='D9D9D9'),
                bottom=Side(style='thin', color='D9D9D9')
            )

            for sheetname in wb.sheetnames:
                ws = wb[sheetname]
                
                # Sütun Genişliği Ayarı ve Büyük Font Entegrasyonu
                for col in ws.columns:
                    max_len = 0
                    col_letter = get_column_letter(col[0].column)
                    for cell in col:
                        if cell.value is not None:
                            max_len = max(max_len, len(str(cell.value)))
                        
                        if cell.row == 1:
                            cell.font = header_font
                            cell.fill = header_fill
                            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                        else:
                            cell.font = cell_font
                            cell.border = thin_border
                            cell.alignment = Alignment(horizontal='left', vertical='center')
                    
                    ws.column_dimensions[col_letter].width = max(max_len + 5, 22)
                
                ws.row_dimensions[1].height = 30
                for r in range(2, ws.max_row + 1):
                    ws.row_dimensions[r].height = 24

            final_output = io.BytesIO()
            wb.save(final_output)
            final_output.seek(0)

            st.download_button(
                label="📁 Büyük Yazı Tipli Excel Dosyasını (.xlsx) İndir",
                data=final_output,
                file_name="TMK_Kapsamli_Buyuk_Font_Miras_Raporu.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    with col_dl2:
        st.subheader("🔴 Antetli PDF Rapor Özeti")
        st.markdown("Yazdırılabilir, resmi kurumlara sunulabilecek formatta özet metin ve döküm çıktısı.")
        
        if st.button("📄 PDF Bilgi Paketini Hazırla"):
            pdf_metni = f"""
            TÜRK MEDENİ KANUNU RESMİ MİRAS VE TASFİYE RAPORU
            --------------------------------------------------
            Rapor Tarihi: 2026
            Toplam Brüt Aktif: {st.session_state.get('toplam_aktif', 4250000.0):,.2f} TL
            Toplam Borçlar / Pasif: {st.session_state.get('toplam_pasif', 350000.0):,.2f} TL
            NET TEREKE: {st.session_state.get('net_tereke', 3900000.0):,.2f} TL
            
            Bu belge TMK hükümleri doğrultusunda sistem tarafından otomatik üretilmiştir.
            """
            st.text_area("Üretilen Resmi Özet Metin:", pdf_metni, height=180)
            st.success("✅ Rapor başarıyla derlendi!")

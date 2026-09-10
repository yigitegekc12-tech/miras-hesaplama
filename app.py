import streamlit as st
import pandas as pd
import numpy as np
import io
import os
import json
import hashlib
import logging
from datetime import datetime
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl import load_workbook

# --- 1. KURUMSAL LOGLAMA VE GÜVENLİK YAPILANDIRMASI ---
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "enterprise_audit.log"),
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] (UserSession: %(session_id)s) - %(message)s'
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

# --- 2. SAYFA YAPILANDIRMASI VE GELİŞMİŞ KURUMSAL CSS ---
st.set_page_config(
    page_title="TMK Kurumsal Enterprise Miras ve Mal Rejimi Tasfiye Sistemi",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Gelişmiş Kurumsal Tema, Kartlar ve Tipografi CSS Entegrasyonu
st.markdown("""
    <style>
        /* Genel Arka Plan ve Font */
        .main { background-color: #f4f7f6; font-family: 'Inter', sans-serif; }
        
        /* Özel Kurumsal Kart Tasarımları */
        .enterprise-card {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0, 0, 0, 0.1);
            border-left: 5px solid #1F4E78;
            margin-bottom: 20px;
        }
        
        .metric-container {
            background: linear-gradient(135deg, #1F4E78 0%, #2c6cb0 100%);
            color: white;
            padding: 18px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        /* Buton Stilleri */
        .stButton>button { 
            width: 100%; 
            border-radius: 6px; 
            font-weight: 600; 
            background-color: #1F4E78; 
            color: white;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #163857;
            border-color: #163857;
        }
        
        /* Başlık Düzenlemeleri */
        h1, h2, h3 { color: #1F4E78; font-weight: 700; }
        
        /* Sekme Güzelleştirmeleri */
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] {
            border-radius: 4px 4px 0px 0px;
            padding: 10px 16px;
            font-weight: 600;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. DİNAMİK ŞİFRE YÖNETİMLİ GÜVENLİK VE RBAC ---
def enterprise_security_gateway():
    """Oturum durumunda dinamik şifre değiştirmeye olanak tanıyan kurumsal kimlik doğrulama katmanı."""
    if "audit_trail" not in st.session_state:
        st.session_state["audit_trail"] = []
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = hashlib.sha256(str(datetime.now()).encode()).hexdigest()[:12]

    # Şifrelerin oturum hafızasında tutulması (İlk açılışta varsayılanlar)
    if "users_db" not in st.session_state:
        st.session_state["users_db"] = {
            "admin": {"pass": "ege12345", "role": "Kıdemli Ortak / Admin", "dept": "Hukuk Departmanı"},
            "avukat": {"pass": "ege12345", "role": "Avukat / Uzman Bilirkişi", "dept": "Dava ve Tasfiye"},
            "noter": {"pass": "ege12345", "role": "Noter / Denetmen", "dept": "İntikal İşlemleri"}
        }

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.sidebar.markdown("### 🔐 Kurumsal Güvenli Giriş")
        st.sidebar.markdown(f"**Oturum ID:** `{st.session_state['session_id']}`")
        
        users_db = st.session_state["users_db"]
        username = st.sidebar.selectbox("Kullanıcı Profili:", list(users_db.keys()), key="login_user")
        password = st.sidebar.text_input("Kurumsal Şifre:", type="password", key="login_pass")
        
        if st.sidebar.button("Sisteme Güvenli Giriş Yap", type="primary"):
            if password == users_db[username]["pass"]:
                st.session_state["authenticated"] = True
                st.session_state["current_user"] = username
                st.session_state["user_role"] = users_db[username]["role"]
                st.session_state["user_dept"] = users_db[username]["dept"]
                
                log_msg = f"Kullanıcı girişi başarılı: {username} ({users_db[username]['role']})"
                st.session_state["audit_trail"].append({"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "log": log_msg})
                logging.info(log_msg, extra={'session_id': st.session_state['session_id']})
                st.rerun()
            else:
                st.sidebar.error("❌ Yetkisiz erişim denemesi! Hatalı şifre.")
                logging.warning(f"Hatalı şifre denemesi: {username}", extra={'session_id': st.session_state['session_id']})
        return False
    else:
        st.sidebar.markdown("### 👤 Aktif Oturum Bilgileri")
        st.sidebar.info(f"**Kullanıcı:** {st.session_state['current_user']}\n\n**Rol:** {st.session_state['user_role']}\n\n**Birim:** {st.session_state['user_dept']}")
        
        # --- ŞİFRE DEĞİŞTİRME PANELİ ---
        with st.sidebar.expander("🔑 Şifremi Değiştir"):
            eski_sifre = st.text_input("Mevcut Şifre:", type="password", key="pwd_old")
            yeni_sifre = st.text_input("Yeni Şifre:", type="password", key="pwd_new")
            yeni_sifre_tekrar = st.text_input("Yeni Şifre (Tekrar):", type="password", key="pwd_new_repeat")
            
            if st.button("Şifreyi Güncelle", key="btn_update_pwd"):
                curr_usr = st.session_state["current_user"]
                if eski_sifre == st.session_state["users_db"][curr_usr]["pass"]:
                    if yeni_sifre and yeni_sifre == yeni_sifre_tekrar:
                        st.session_state["users_db"][curr_usr]["pass"] = yeni_sifre
                        st.sidebar.success("✅ Şifreniz başarıyla değiştirildi!")
                        logging.info(f"Kullanıcı şifresini güncelledi: {curr_usr}", extra={'session_id': st.session_state['session_id']})
                    else:
                        st.sidebar.error("⚠️ Yeni şifreler eşleşmiyor veya boş bırakılamaz.")
                else:
                    st.sidebar.error("❌ Mevcut şifrenizi hatalı girdiniz.")

        if st.sidebar.button("Oturumu Kapat (Logout)"):
            log_msg = f"Oturum kapatıldı: {st.session_state['current_user']}"
            logging.info(log_msg, extra={'session_id': st.session_state['session_id']})
            for key in list(st.session_state.keys()):
                if key not in ["users_db"]: 
                    del st.session_state[key]
            st.rerun()
        return True

if not enterprise_security_gateway():
    st.stop()

# --- 4. SİSTEM BAŞLIĞI VE EXECUTIVE HEADER ---
st.title("⚖️ TMK Kurumsal Enterprise Miras, Mal Rejimi ve Tasfiye Bilirkişilik Sistemi")
st.markdown("""
<div class="enterprise-card">
    <b>Yasal Çerçeve & Kapsam:</b> Türk Medeni Kanunu'nun (TMK) miras hukuku (m. 495 vd.) ve mal rejimi hükümleri (m. 214 vd.) çerçevesinde; 
    aktif-pasif terekelerin tespiti, zümre/kök/temsil oranları, borçların orantısal tenkisi, edinilmiş mallara katılma tasfiyesi, 
    saklı pay ihlalleri (tenkis) ve tapu intikal harç hesaplamalarını kurumsal denetim standartlarında gerçekleştirir.
</div>
""", unsafe_allow_html=True)

# --- 5. SEKMELER (TABS) YAPILANDIRMASI ---
tabs = st.tabs([
    "1️⃣ Aktif & Pasif (Net Tereke)", 
    "2️⃣ Zümre & Miras Paylaşımı", 
    "3️⃣ Borçlar & Net Alacaklar", 
    "4️⃣ Mal Rejimi Tasfiyesi", 
    "5️⃣ Tenkis (Saklı Pay İhlali)",
    "6️⃣ Tapu & Harç Düşümleri",
    "7️⃣ 📊 Çok Sayfalı Kurumsal Rapor",
    "8️⃣ 📋 Denetim İzi (Audit Trail)"
])

# ==========================================
# TAB 1: AKTİF & PASİF (NET TEREKE) ANALİZİ
# ==========================================
with tabs[0]:
    st.markdown("### 💼 Modül 1: Kapsamlı Tereke Aktif ve Pasif Envanter Yönetimi")
    st.write("Mirasbırakanın vefat anındaki tüm mal varlığı değerleri ile borç ve cenaze giderlerinin TMK m. 507 uyarınca tespiti.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📈 Tereke Aktif Kalemleri (Rayiç Değer)")
        g_aktif = st.number_input("Gayrimenkuller Toplam Rayiç Değeri (TL):", min_value=0.0, value=7500000.0, step=100000.0, format="%.2f", key="t1_g_aktif")
        n_aktif = st.number_input("Banka Mevduatı, Döviz ve Kıymetli Madenler (TL):", min_value=0.0, value=1250000.0, step=50000.0, format="%.2f", key="t1_n_aktif")
        a_aktif = st.number_input("Araç ve Motorlu Taşıtlar (TL):", min_value=0.0, value=1500000.0, step=25000.0, format="%.2f", key="t1_a_aktif")
        s_aktif = st.number_input("Şirket Hisseleri, Ticari İşletme Değerleri (TL):", min_value=0.0, value=2000000.0, step=50000.0, format="%.2f", key="t1_s_aktif")
        d_aktif = st.number_input("Alacaklar, Senetler ve Diğer Menkul Kıymetler (TL):", min_value=0.0, value=250000.0, step=10000.0, format="%.2f", key="t1_d_aktif")

    with col2:
        st.markdown("#### 📉 Tereke Pasif Kalemleri (Borçlar ve Masraflar)")
        b_kredi = st.number_input("Banka Kredileri, Kredi Kartı ve Finansal Borçlar (TL):", min_value=0.0, value=600000.0, step=20000.0, format="%.2f", key="t1_b_kredi")
        p_borc = st.number_input("Piyasa / Senetli Ticari Borçlar (TL):", min_value=0.0, value=300000.0, step=10000.0, format="%.2f", key="t1_p_borc")
        v_borc = st.number_input("Vergi Daireleri ve SGK Borçları (TL):", min_value=0.0, value=150000.0, step=5000.0, format="%.2f", key="t1_v_borc")
        c_masraf = st.number_input("Cenaze ve Defin Masrafları (TMK m. 507) (TL):", min_value=0.0, value=120000.0, step=5000.0, format="%.2f", key="t1_c_masraf")
        t_gider = st.number_input("Terekenin Mühürlenmesi, Korunması ve Yönetim Giderleri (TL):", min_value=0.0, value=80000.0, step=5000.0, format="%.2f", key="t1_t_gider")

    if st.button("Net Tereke Değerini Hesapla ve Kaydet", type="primary", key="btn_t1_calc"):
        toplam_aktif = g_aktif + n_aktif + a_aktif + s_aktif + d_aktif
        toplam_pasif = b_kredi + p_borc + v_borc + c_masraf + t_gider
        net_tereke = max(0.0, toplam_aktif - toplam_pasif)

        st.session_state["toplam_aktif"] = toplam_aktif
        st.session_state["toplam_pasif"] = toplam_pasif
        st.session_state["net_tereke"] = net_tereke
        st.session_state["gayrimenkul_degeri"] = g_aktif

        log_txt = f"Net tereke hesaplandı -> Brüt Aktif: {toplam_aktif:,.2f} TL, Toplam Pasif: {toplam_pasif:,.2f} TL, Net Tereke: {net_tereke:,.2f} TL"
        st.session_state["audit_trail"].append({"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "log": log_txt})
        logging.info(log_txt, extra={'session_id': st.session_state['session_id']})

        st.success("✅ Net Tereke başarıyla hesaplandı ve oturum hafızasına kaydedildi.")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Toplam Brüt Varlıklar", f"{toplam_aktif:,.2f} TL")
        c2.metric("Toplam Pasifler ve Borçlar", f"{toplam_pasif:,.2f} TL")
        c3.metric("Net Tereke (Aktif - Pasif)", f"{net_tereke:,.2f} TL")

# ==========================================
# TAB 2: ZÜMRE & MİRAS PAYLAŞIMI
# ==========================================
with tabs[1]:
    st.markdown("### 👥 Modül 2: Gelişmiş Zümre, Kök ve Temsil Sistemi (TMK m. 495-501)")
    st.write("Yasal mirasçıların zümre sistemine göre pay oranlarının tespiti ve sağ eşin zümrelere göre entegre katılım payı hesaplaması.")

    default_tereke_t2 = st.session_state.get("net_tereke", 10250000.0)
    tereke_t2 = st.number_input("Paylaşıma Esas Net Tereke Değeri (TL):", min_value=0.0, value=default_tereke_t2, step=50000.0, format="%.2f", key="t2_tereke")

    zumre_tipi = st.selectbox(
        "Mirasbırakanın Geride Kalan Mirasçı Grubu (Zümre Yapısı):",
        [
            "1. Zümre: Altsoy (Çocuklar, Torunlar) ve Sağ Eş",
            "2. Zümre: Anne, Baba, Kardeşler, Yeğenler ve Sağ Eş",
            "3. Zümre: Büyük Anne, Büyük Baba ve Kollar / Sağ Eş",
            "Yalnızca Sağ Eş (Zümre Akrabası Bulunmamaktadır)"
        ],
        key="t2_zumre_tipi"
    )
    
    sag_es_var = st.checkbox("Sağ Eş Hayatta mı?", value=True, key="t2_sag_es")

    cocuk_listesi = []
    cocuk_sayisi = 1
    if "1. Zümre" in zumre_tipi:
        cocuk_sayisi = st.number_input("Toplam Çocuk (Kök) Sayısı:", min_value=1, max_value=20, value=2, step=1, key="t2_cocuk_sayisi")
        for i in range(1, int(cocuk_sayisi) + 1):
            c_durum = st.selectbox(f"{i}. Çocuğun Durumu:", ["Hayatta", "Vefat Etmiş (Torunlar Temsil Edecek)"], key=f"t2_c_durum_{i}")
            t_sayisi = 1
            if c_durum == "Vefat Etmiş (Torunlar Temsil Edecek)":
                t_sayisi = st.number_input(f"→ {i}. Çocuğun Altsoy / Torun Sayısı:", min_value=1, max_value=10, value=2, step=1, key=f"t2_t_sayisi_{i}")
            cocuk_listesi.append({"durum": c_durum, "torun_sayisi": t_sayisi})

    if st.button("Kurumsal Zümre Paylaşım Tablosunu Oluştur", type="primary", key="btn_t2_calc"):
        try:
            paylasma_sonuclari = []
            if "1. Zümre" in zumre_tipi:
                altsoy_pay_orani = 0.75 if sag_es_var else 1.0
                if sag_es_var:
                    paylasma_sonuclari.append({
                        "Mirasçı Sıfatı": "Sağ Eş",
                        "Yasal Pay Oranı (Kesir)": "%25.00 (1/4)",
                        "Hisse Oranı (Ondalık)": 0.25,
                        "Net Tutar (TL)": tereke_t2 * 0.25,
                        "Saklı Pay Oranı": "%12.50 (Yasal Payın Yarısı)"
                    })

                birer_kok = altsoy_pay_orani / cocuk_sayisi
                for idx, cdata in enumerate(cocuk_listesi, 1):
                    if cdata["durum"] == "Hayatta":
                        paylasma_sonuclari.append({
                            "Mirasçı Sıfatı": f"{idx}. Çocuk (Hayatta)",
                            "Yasal Pay Oranı (Kesir)": f"%{birer_kok * 100:.2f}",
                            "Hisse Oranı (Ondalık)": birer_kok,
                            "Net Tutar (TL)": tereke_t2 * birer_kok,
                            "Saklı Pay Oranı": f"%{birer_kok * 50:.2f}"
                        })
                    else:
                        t_adet = cdata["torun_sayisi"]
                        t_oran = birer_kok / t_adet
                        for t_idx in range(1, t_adet + 1):
                            paylasma_sonuclari.append({
                                "Mirasçı Sıfatı": f"→ {idx}. Çocuğun {t_idx}. Altsoyu (Torun / Temsilen)",
                                "Yasal Pay Oranı (Kesir)": f"%{t_oran * 100:.2f}",
                                "Hisse Oranı (Ondalık)": t_oran,
                                "Net Tutar (TL)": tereke_t2 * t_oran,
                                "Saklı Pay Oranı": f"%{t_oran * 50:.2f}"
                            })

            elif "2. Zümre" in zumre_tipi:
                if sag_es_var:
                    paylasma_sonuclari.append({"Mirasçı Sıfatı": "Sağ Eş", "Yasal Pay Oranı (Kesir)": "%50.00 (1/2)", "Hisse Oranı (Ondalık)": 0.50, "Net Tutar (TL)": tereke_t2 * 0.50, "Saklı Pay Oranı": "%25.00"})
                    paylasma_sonuclari.append({"Mirasçı Sıfatı": "2. Zümre (Anne, Baba ve Kolları)", "Yasal Pay Oranı (Kesir)": "%50.00 (1/2)", "Hisse Oranı (Ondalık)": 0.50, "Net Tutar (TL)": tereke_t2 * 0.50, "Saklı Pay Oranı": "Yok"})
                else:
                    paylasma_sonuclari.append({"Mirasçı Sıfatı": "2. Zümre Akrabaları (Tamamı)", "Yasal Pay Oranı (Kesir)": "%100.00", "Hisse Oranı (Ondalık)": 1.0, "Net Tutar (TL)": tereke_t2, "Saklı Pay Oranı": "Yok"})

            elif "Yalnızca Sağ Eş" in zumre_tipi:
                paylasma_sonuclari.append({"Mirasçı Sıfatı": "Sağ Eş (Zümre Bulunmadığından Tamamı)", "Yasal Pay Oranı (Kesir)": "%100.00", "Hisse Oranı (Ondalık)": 1.0, "Net Tutar (TL)": tereke_t2, "Saklı Pay Oranı": "%50.00"})

            df_t2 = pd.DataFrame(paylasma_sonuclari)
            st.session_state["df_miras_pay"] = df_t2
            
            log_t2 = f"Zümre paylaşımı hesaplandı. Grup: {zumre_tipi}, Toplam Tutar: {tereke_t2:,.2f} TL"
            st.session_state["audit_trail"].append({"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "log": log_t2})
            logging.info(log_t2, extra={'session_id': st.session_state['session_id']})

            st.success("✅ Zümre ve yasal miras payları başarıyla hesaplandı.")
            st.dataframe(df_t2, use_container_width=True)
        except Exception as e:
            st.error(f"⚠️ Hesaplama hatası: {str(e)}")

# ==========================================
# TAB 3: BORÇLAR & NET ALACAKLAR
# ==========================================
with tabs[2]:
    st.markdown("### 📋 Modül 3: Brüt Aktiften Borçların Orantısal Tenkisi ve Net Alacak Tablosu")
    st.write("Mirasçılara düşen yasal paylar oranında tereke pasiflerinin (borçlar, masraflar) düşülmesi ve net tasfiye alacaklarının tespiti.")

    brut_aktif_t3 = st.number_input("Toplam Brüt Varlık Değeri (TL):", min_value=0.0, value=st.session_state.get("toplam_aktif", 12300000.0), step=50000.0, format="%.2f", key="t3_brut")
    toplam_pasif_t3 = st.number_input("Toplam Tereke Borçları ve Pasifleri (TL):", min_value=0.0, value=st.session_state.get("toplam_pasif", 2050000.0), step=20000.0, format="%.2f", key="t3_pasif")

    if st.button("Borçlar Düşülmüş Net Mirasçı Alacaklarını Hesapla", type="primary", key="btn_t3_calc"):
        if "df_miras_pay" not in st.session_state:
            st.warning("⚠️ Lütfen önce **2. Adımdan (Zümre & Miras Paylaşımı)** pay tablosunu oluşturun.")
        else:
            try:
                df_orin = st.session_state["df_miras_pay"].copy()
                net_list = []
                toplam_pay_tutar = df_orin["Net Tutar (TL)"].sum()

                for _, row in df_orin.iterrows():
                    m_ad = row["Mirasçı Sıfatı"]
                    b_pay = row["Net Tutar (TL)"]
                    pay_oran = b_pay / toplam_pay_tutar if toplam_pay_tutar > 0 else 0
                    dusen_borc = toplam_pasif_t3 * pay_oran
                    net_alinacak = max(0.0, b_pay - dusen_borc)

                    net_list.append({
                        "Mirasçı Sıfatı": m_ad,
                        "Brüt Miras Payı (TL)": b_pay,
                        "Payına Düşen Borç (TL)": dusen_borc,
                        "Eline Geçecek Net Alacak (TL)": net_alinacak
                    })

                df_t3 = pd.DataFrame(net_list)
                st.session_state["df_net_miras_borclu"] = df_t3
                
                log_t3 = f"Net borç düşüm tablosu oluşturuldu. Pasif toplamı: {toplam_pasif_t3:,.2f} TL"
                st.session_state["audit_trail"].append({"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "log": log_t3})
                logging.info(log_t3, extra={'session_id': st.session_state['session_id']})

                st.success("✅ Borçlar miras paylarına yansıtıldı ve net alacaklar belirlendi.")
                st.dataframe(df_t3, use_container_width=True)
            except Exception as e:
                st.error(f"⚠️ Hesaplama hatası: {str(e)}")

# ==========================================
# TAB 4: MAL REJİMİ TASFİYESİ
# ==========================================
with tabs[3]:
    st.markdown("### 💍 Modül 4: Edinilmiş Mallara Katılma Rejimi Tasfiyesi ve Artık Değer Hesabı (TMK m. 218 vd.)")
    st.write("Eşlerin mal rejiminin sona ermesi anındaki malvarlıklarının tasfiyesi, kişisel mallar indirimi, artık değer ve katılma alacağı hesabı.")

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.markdown("#### Eş 1 Mali Verileri")
        aktif_1 = st.number_input("Eş 1 Mal Varlığı Aktifi (TL)", min_value=0.0, value=6000000.0, step=100000.0, format="%.2f", key="t4_a1")
        borc_1 = st.number_input("Eş 1 Borçları (TL)", min_value=0.0, value=1000000.0, step=20000.0, format="%.2f", key="t4_b1")
        kisisel_1 = st.number_input("Eş 1 Kişisel Malları (TMK m. 220) (TL)", min_value=0.0, value=1500000.0, step=50000.0, format="%.2f", key="t4_k1")

    with col_e2:
        st.markdown("#### Eş 2 Mali Verileri")
        aktif_2 = st.number_input("Eş 2 Mal Varlığı Aktifi (TL)", min_value=0.0, value=4000000.0, step=100000.0, format="%.2f", key="t4_a2")
        borc_2 = st.number_input("Eş 2 Borçları (TL)", min_value=0.0, value=500000.0, step=20000.0, format="%.2f", key="t4_b2")
        kisisel_2 = st.number_input("Eş 2 Kişisel Malları (TMK m. 220) (TL)", min_value=0.0, value=1000000.0, step=50000.0, format="%.2f", key="t4_k2")

    if st.button("Kurumsal Mal Rejimi Tasfiyesini Hesapla", type="primary", key="btn_t4_calc"):
        try:
            artik_deger_1 = max(0.0, aktif_1 - borc_1 - kisisel_1)
            artik_deger_2 = max(0.0, aktif_2 - borc_2 - kisisel_2)
            toplam_artik = artik_deger_1 + artik_deger_2
            katilma_alacagi = toplam_artik / 2.0

            tasfiye_data = [
                {"Kalem Açıklaması": "Eş 1 Toplam Aktif", "Tutar (TL)": aktif_1},
                {"Kalem Açıklaması": "Eş 1 Borçlar", "Tutar (TL)": borc_1},
                {"Kalem Açıklaması": "Eş 1 Kişisel Mallar", "Tutar (TL)": kisisel_1},
                {"Kalem Açıklaması": "Eş 1 Artık Değer (Edinilmiş Mal Neti)", "Tutar (TL)": artik_deger_1},
                {"Kalem Açıklaması": "---", "Tutar (TL)": 0.0},
                {"Kalem Açıklaması": "Eş 2 Toplam Aktif", "Tutar (TL)": aktif_2},
                {"Kalem Açıklaması": "Eş 2 Borçlar", "Tutar (TL)": borc_2},
                {"Kalem Açıklaması": "Eş 2 Kişisel Mallar", "Tutar (TL)": kisisel_2},
                {"Kalem Açıklaması": "Eş 2 Artık Değer (Edinilmiş Mal Neti)", "Tutar (TL)": artik_deger_2},
                {"Kalem Açıklaması": "Toplam Artık Değerler Toplamı", "Tutar (TL)": toplam_artik},
                {"Kalem Açıklaması": "Karşılıklı Yarı Oranlı Katılma Alacağı Hakkı", "Tutar (TL)": katilma_alacagi}
            ]

            df_t4 = pd.DataFrame(tasfiye_data)
            st.session_state["df_mal_rejimi"] = df_t4

            log_t4 = f"Mal rejimi tasfiyesi tamamlandı. Eş 1 Artık: {artik_deger_1:,.2f} TL, Eş 2 Artık: {artik_deger_2:,.2f} TL"
            st.session_state["audit_trail"].append({"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "log": log_t4})
            logging.info(log_t4, extra={'session_id': st.session_state['session_id']})

            st.success("✅ Mal rejimi tasfiyesi ve artık değer hesaplaması başarıyla tamamlandı.")
            st.dataframe(df_t4, use_container_width=True)
        except Exception as e:
            st.error(f"⚠️ Hesaplama hatası: {str(e)}")

# ==========================================
# TAB 5: TENKİS (SAKLI PAY İHLALİ)
# ==========================================
with tabs[4]:
    st.markdown("### 📜 Modül 5: Saklı Pay İhlali ve Tenkis Analiz Modülü (TMK m. 560 vd.)")
    st.write("Ölüme bağlı tasarrufların (vasiyetname / ölüme bağlı kazandırmalar) ve denkleştirmeye tabi karşılıksız kazandırmaların saklı payları ihlal edip etmediğinin tespiti.")

    base_t5 = st.session_state.get("net_tereke", 10250000.0)
    col_t5_1, col_t5_2 = st.columns(2)
    with col_t5_1:
        net_tereke_t5 = st.number_input("Net Tereke Değeri (TL):", min_value=0.0, value=base_t5, step=50000.0, format="%.2f", key="t5_net_t")
        kazandirma_t5 = st.number_input("Üçüncü Kişilere Yapılan Tenkise Tabi Kazandırmalar / Bağışlar (TL):", min_value=0.0, value=3000000.0, step=50000.0, format="%.2f", key="t5_kazandirma")
    with col_t5_2:
        mirasci_grup_t5 = st.selectbox(
            "Saklı Pay Sahibi Miras Grubu:",
            [
                "Altsoy (Çocuklar) ve Sağ Eş Birlikte",
                "Yalnızca Altsoy (Çocuklar) Var",
                "Anne ve Baba Var (Altsoy / Eş Yok)"
            ],
            key="t5_grup"
        )

    if st.button("Kurumsal Tenkis Analizini Çalıştır", type="primary", key="btn_t5_calc"):
        try:
            hesap_terekkesi = net_tereke_t5 + kazandirma_t5

            if "Altsoy (Çocuklar) ve Sağ Eş Birlikte" in mirasci_grup_t5:
                tasarruf_orani = 0.25
                sakli_pay_orani = 0.75
            elif "Yalnızca Altsoy (Çocuklar) Var" in mirasci_grup_t5:
                tasarruf_orani = 0.50
                sakli_pay_orani = 0.50
            else:
                tasarruf_orani = 0.50
                sakli_pay_orani = 0.50

            tasarruf_edilebilir_kisim = hesap_terekkesi * tasarruf_orani
            toplam_sakli_pay = hesap_terekkesi * sakli_pay_orani
            asir_tutar = max(0.0, kazandirma_t5 - tasarruf_edilebilir_kisim)
            ihlal_var = asir_tutar > 0

            tenkis_sonuc_listesi = [
                {"Tenkis Analiz Kalemi": "Hesaplama Terekkesi (Net Tereke + Kazandırmalar)", "Tutar (TL)": hesap_terekkesi},
                {"Tenkis Analiz Kalemi": "Yasal Tasarruf Edilebilir Kısım Üst Sınırı", "Tutar (TL)": tasarruf_edilebilir_kisim},
                {"Tenkis Analiz Kalemi": "Yasal Mirasçıların Toplam Saklı Payı", "Tutar (TL)": toplam_sakli_pay},
                {"Tenkis Analiz Kalemi": "Yapılan Toplam Kazandırma / Bağış", "Tutar (TL)": kazandirma_t5},
                {"Tenkis Analiz Kalemi": "Saklı Payları İhlal Eden Aşan Tutar (Tenkise Tabi Aşım)", "Tutar (TL)": asir_tutar}
            ]

            df_t5 = pd.DataFrame(tenkis_sonuc_listesi)
            st.session_state["df_tenkis_sonuc"] = df_t5

            log_t5 = f"Tenkis analizi tamamlandı. İhlal Durumu: {ihlal_var}, Aşım Tutarı: {asir_tutar:,.2f} TL"
            st.session_state["audit_trail"].append({"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "log": log_t5})
            logging.info(log_t5, extra={'session_id': st.session_state['session_id']})

            st.markdown("---")
            if ihlal_var:
                st.error(f"⚠️ **DİKKAT: Saklı Pay İhlali Mevcuttur!** Yapılan karşılıksız kazandırmalar, tasarruf edilebilir kısmı **{asir_tutar:,.2f} TL** oranında aşmaktadır ve bu kısım tenkise tabidir.")
            else:
                st.success("✅ **Saklı Pay İhlali Bulunmamaktadır.** Yapılan kazandırmalar yasal tasarruf edilebilir sınırlar içerisindedir.")

            st.dataframe(df_t5, use_container_width=True)
        except Exception as e:
            st.error(f"⚠️ Hesaplama hatası: {str(e)}")

# ==========================================
# TAB 6: TAPU & HARÇ DÜŞÜMLERİ
# ==========================================
with tabs[5]:
    st.markdown("### 🏛️ Modül 6: Tapu İntikal Harçları ve Döner Sermaye Giderleri")
    st.write("Gayrimenkul intikallerinde Harçlar Kanunu ve Tapu Sicil Müdürlüğü tarifelerine göre ödenecek harç, döner sermaye ve masrafların mirasçı paylarına yansıtılması.")

    base_gayrimenkul_t6 = st.session_state.get("gayrimenkul_degeri", 7500000.0)
    col_t6_1, col_t6_2 = st.columns(2)
    with col_t6_1:
        gayrimenkul_t6 = st.number_input("Tapu / Gayrimenkul Toplam Rayiç Değeri (TL):", min_value=0.0, value=base_gayrimenkul_t6, step=100000.0, format="%.2f", key="t6_g_val")
        harc_orani = st.number_input("Tapu İntikal Harcı Oranı (%):", min_value=0.0, value=0.227, step=0.01, format="%.3f", key="t6_harc")
        doner_sermaye = st.number_input("Döner Sermaye ve Evrak Masrafları (TL):", min_value=0.0, value=2500.0, step=100.0, format="%.2f", key="t6_doner")
    with col_t6_2:
        miras_grup_t6 = st.selectbox("Miras Grubu (Tapu Paylaşım Yapısı):", ["1. Zümre (Sağ Eş + Çocuklar)", "Yalnızca Çocuklar (Eş Yok)"], key="t6_grup")
        toplam_cocuk_t6 = st.number_input("Çocuk / Kök Sayısı:", min_value=1, value=2, step=1, key="t6_cocuk_s")

    if st.button("Masrafları Düşerek Net Tapu Paylarını Hesapla", type="primary", key="btn_t6_calc"):
        try:
            toplam_harc_tutar = gayrimenkul_t6 * (harc_orani / 100.0)
            toplam_resmi_gider = toplam_harc_tutar + doner_sermaye

            tapu_detay = []
            if "Sağ Eş +" in miras_grup_t6:
                es_pay_oran = 0.25
                cocuklar_toplam_oran = 0.75
                
                brut_es = gayrimenkul_t6 * es_pay_oran
                masraf_es = toplam_resmi_gider * es_pay_oran
                net_es = brut_es - masraf_es
                tapu_detay.append({"Mirasçı Sıfatı": "Sağ Eş", "Tapu Payı": "%25.00 (1/4)", "Brüt Pay Değeri (TL)": brut_es, "Payına Düşen Masraf (TL)": masraf_es, "Net Değer (TL)": net_es})

                her_cocuk_oran = cocuklar_toplam_oran / toplam_cocuk_t6
                for c_idx in range(1, int(toplam_cocuk_t6) + 1):
                    brut_c = gayrimenkul_t6 * her_cocuk_oran
                    masraf_c = toplam_resmi_gider * her_cocuk_oran
                    net_c = brut_c - masraf_c
                    tapu_detay.append({"Mirasçı Sıfatı": f"{c_idx}. Çocuk", "Tapu Payı": f"%{her_cocuk_oran * 100:.2f}", "Brüt Pay Değeri (TL)": brut_c, "Payına Düşen Masraf (TL)": masraf_c, "Net Değer (TL)": net_c})
            else:
                her_cocuk_oran = 1.0 / toplam_cocuk_t6
                for c_idx in range(1, int(toplam_cocuk_t6) + 1):
                    brut_c = gayrimenkul_t6 * her_cocuk_oran
                    masraf_c = toplam_resmi_gider * her_cocuk_oran
                    net_c = brut_c - masraf_c
                    tapu_detay.append({"Mirasçı Sıfatı": f"{c_idx}. Çocuk", "Tapu Payı": f"%{her_cocuk_oran * 100:.2f}", "Brüt Pay Değeri (TL)": brut_c, "Payına Düşen Masraf (TL)": masraf_c, "Net Değer (TL)": net_c})

            df_t6 = pd.DataFrame(tapu_detay)
            st.session_state["df_tapu_masraf"] = df_t6

            log_t6 = f"Tapu masraf hesaplaması yapıldı. Toplam masraf: {toplam_resmi_gider:,.2f} TL"
            st.session_state["audit_trail"].append({"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "log": log_t6})
            logging.info(log_t6, extra={'session_id': st.session_state['session_id']})

            st.info(f"💡 **Toplam Tahsil Edilecek Tapu Harcı ve Resmi Gider:** {toplam_resmi_gider:,.2f} TL")
            st.dataframe(df_t6, use_container_width=True)
        except Exception as e:
            st.error(f"⚠️ Hesaplama hatası: {str(e)}")

# ==========================================
# TAB 7: 📊 ÇOK SAYFALI KURUMSAL RAPOR
# ==========================================
with tabs[6]:
    st.markdown("### 📊 Modül 7: Çok Sayfalı Kurumsal Excel & PDF Raporlama Motoru")
    st.write("Tüm modüllerde yapılan hesaplama adımlarını; kurumsal renk paleti (Koyu Lacivert Başlıklar), 14 punto kalın başlık fontları ve 12 punto hücre fontlarıyla profesyonel Excel formatında dışa aktarın.")

    if st.button("📥 Kurumsal Çok Sayfalı Excel Raporunu Üret ve İndir", type="primary", key="btn_excel_export"):
        try:
            output_buffer = io.BytesIO()
            with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
                # 1. Tereke Genel Özet
                ozet_df = pd.DataFrame({
                    "Kurumsal Rapor Kalemi": ["Toplam Brüt Aktif Varlıklar", "Toplam Pasif Borçlar ve Masraflar", "Net Tereke Değeri"],
                    "Tutar (TL)": [
                        st.session_state.get("toplam_aktif", 12300000.0),
                        st.session_state.get("toplam_pasif", 2050000.0),
                        st.session_state.get("net_tereke", 10250000.0)
                    ]
                })
                ozet_df.to_excel(writer, sheet_name='01_Tereke_Genel_Ozet', index=False)

                # 2. Zümre Payları
                if "df_miras_pay" in st.session_state:
                    st.session_state["df_miras_pay"].to_excel(writer, sheet_name='02_Zumre_Miras_Paylari', index=False)
                else:
                    pd.DataFrame({"Bilgi": ["Veri bulunamadı."]}).to_excel(writer, sheet_name='02_Zumre_Miras_Paylari', index=False)

                # 3. Borçlar Düşülmüş Net Miras
                if "df_net_miras_borclu" in st.session_state:
                    st.session_state["df_net_miras_borclu"].to_excel(writer, sheet_name='03_Net_Miras_Ve_Borclar', index=False)
                else:
                    pd.DataFrame({"Bilgi": ["Veri bulunamadı."]}).to_excel(writer, sheet_name='03_Net_Miras_Ve_Borclar', index=False)

                # 4. Mal Rejimi Tasfiyesi
                if "df_mal_rejimi" in st.session_state:
                    st.session_state["df_mal_rejimi"].to_excel(writer, sheet_name='04_Mal_Rejimi_Tasfiyesi', index=False)
                else:
                    pd.DataFrame({"Bilgi": ["Veri bulunamadı."]}).to_excel(writer, sheet_name='04_Mal_Rejimi_Tasfiyesi', index=False)

                # 5. Tenkis Analizi
                if "df_tenkis_sonuc" in st.session_state:
                    st.session_state["df_tenkis_sonuc"].to_excel(writer, sheet_name='05_Tenkis_Analizi', index=False)
                else:
                    pd.DataFrame({"Bilgi": ["Veri bulunamadı."]}).to_excel(writer, sheet_name='05_Tenkis_Analizi', index=False)

                # 6. Tapu Masrafları
                if "df_tapu_masraf" in st.session_state:
                    st.session_state["df_tapu_masraf"].to_excel(writer, sheet_name='06_Tapu_Ve_Masraflar', index=False)
                else:
                    pd.DataFrame({"Bilgi": ["Veri bulunamadı."]}).to_excel(writer, sheet_name='06_Tapu_Ve_Masraflar', index=False)

            # OpenPyxl kurumsal stil entegrasyonu
            output_buffer.seek(0)
            wb = load_workbook(output_buffer)
            
            header_font = Font(name='Calibri', size=14, bold=True, color='FFFFFF')
            header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid') 
            cell_font = Font(name='Calibri', size=12, bold=False)
            thin_border = Border(
                left=Side(style='thin', color='D9D9D9'),
                right=Side(style='thin', color='D9D9D9'),
                top=Side(style='thin', color='D9D9D9'),
                bottom=Side(style='thin', color='D9D9D9')
            )

            for sname in wb.sheetnames:
                ws = wb[sname]
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
                    ws.column_dimensions[col_letter].width = max(max_len + 6, 26)
                ws.row_dimensions[1].height = 32
                for r_idx in range(2, ws.max_row + 1):
                    ws.row_dimensions[r_idx].height = 25

            final_output = io.BytesIO()
            wb.save(final_output)
            final_output.seek(0)

            st.download_button(
                label="📁 Kurumsal Büyük Puntolu Excel Raporunu İndir (.xlsx)",
                data=final_output,
                file_name=f"TMK_Kurumsal_Miras_Tasfiye_Raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.success("✅ Kurumsal çok sayfalı Excel raporu başarıyla derlendi ve indirilmeye hazır hale getirildi.")
        except Exception as e:
            st.error(f"⚠️ Rapor üretme hatası: {str(e)}")

# ==========================================
# TAB 8: 📋 SİSTEM LOGLARI VE DENETİM İZİ
# ==========================================
with tabs[7]:
    st.markdown("### 📋 Modül 8: Şifreli Denetim İzi ve Oturum Güvenlik Logları (Audit Trail)")
    st.write("ISO / KVKK / HMK denetim gereklilikleri uyarınca oturum boyunca gerçekleştirilen tüm veri işleme adımlarının zaman damgalı dökümü.")

    if "audit_trail" in st.session_state and st.session_state["audit_trail"]:
        for item in st.session_state["audit_trail"]:
            st.text(f"[{item['time']}] - {item['log']}")
    else:
        st.info("Henüz sisteme kaydedilmiş denetim izi bulunmuyor.")

    if st.button("Denetim Geçmişini Temizle", key="btn_clear_audit"):
        st.session_state["audit_trail"] = []
        st.success("Denetim geçmişi güvenli bir şekilde sıfırlandı.")
        st.rerun()

# -*- coding: utf-8 -*-
import streamlit as st
import matplotlib.pyplot as plt
from lunar_python import Solar
import math
import datetime # 引入时间处理库，专门解决跨天问题

# --- 网页配置 ---
st.set_page_config(page_title="八字运势分析系统", layout="centered")

# 解决绘图中文乱码
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
#          【顶部广告位】
# ==========================================
st.info("📢 **如需详细测评或打赏，请联系微信：ep7992**")
st.title("🔮 八字流年运势分析系统")
st.markdown("---")

# ==========================================
#          核心逻辑 (逻辑引擎)
# ==========================================
class BaziLogic:
    def __init__(self):
        self.GAN = "甲乙丙丁戊己庚辛壬癸"
        self.ZHI = "子丑寅卯辰巳午未申酉戌亥"
        self.GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', 
                       '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
        self.ZHI_WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', 
                       '巳': '火', '午': '火', '未': '土', '申': '金', '酉': '金', 
                       '戌': '土', '亥': '水'}
        self.SHENG = {'水': '木', '木': '火', '火': '土', '土': '金', '金': '水'}
        self.KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}

    def get_parent_wx(self, me_wx):
        for mother, child in self.SHENG.items():
            if child == me_wx: return mother
        return None

    def get_bazi(self, year, month, day, hour):
        # 【核心修正】：晚子时自动换日
        # 如果 hour >= 23，利用 datetime 自动加一天，hour 变为 0
        if hour >= 23:
            dt = datetime.datetime(year, month, day, 0, 0, 0) + datetime.timedelta(days=1)
            year = dt.year
            month = dt.month
            day = dt.day
            hour = 0
            
        solar = Solar.fromYmdHms(year, month, day, hour, 0, 0)
        bazi = solar.getLunar().getEightChar()
        
        y_g, y_z = bazi.getYearGan(), bazi.getYearZhi()
        m_g, m_z = bazi.getMonthGan(), bazi.getMonthZhi()
        d_g, d_z = bazi.getDayGan(), bazi.getDayZhi()
        t_g, t_z = bazi.getTimeGan(), bazi.getTimeZhi()
        
        return [y_g, y_z, m_g, m_z, d_g, d_z, t_g, t_z]

    def analyze_auto(self, pillars):
        me = pillars[4]
        me_wx = self.GAN_WX[me]
        month_zhi = pillars[3]
        month_wx = self.ZHI_WX[month_zhi]
        parent_wx = self.get_parent_wx(me_wx)
        
        # 强弱打分
        score = 0
        if month_wx == me_wx: score += 50
        elif month_wx == parent_wx: score += 50
        
        for i, char in enumerate(pillars):
            if i == 4: continue
            wx = self.GAN_WX.get(char) or self.ZHI_WX.get(char)
            w = 10
            if i == 3: w = 0
            elif i % 2 == 1: w = 15
            if wx == me_wx: score += w
            elif wx == parent_wx: score += w
            
        is_strong = score >= 50
        
        # 初始喜忌
        if is_strong:
            ke_me = [k for k,v in self.KE.items() if v == me_wx][0] # 官杀
            wo_sheng = self.SHENG[me_wx] # 食伤
            wo_ke = self.KE[me_wx]       # 财
            fav = [ke_me, wo_sheng, wo_ke]
            unfav = [me_wx, parent_wx]
        else:
            fav = [parent_wx, me_wx]
            unfav = [k for k in "金木水火土" if k not in fav]
            
        # 调候 (冬木修正)
        info_msg = ""
        # 甲/乙木 生于 亥/子/丑月
        if me_wx == "木" and month_zhi in ["亥", "子", "丑"]:
            info_msg = "❄️ 调候提示：检测到【冬木】，喜火暖局，忌金生水寒。"
            if "金" in fav: fav.remove("金")
            if "金" not in unfav: unfav.append("金")
            
        return fav, unfav, info_msg, is_strong

    def calc_score(self, year_gan, year_zhi, day_zhi, fav, unfav):
        score = 60
        g_wx = self.GAN_WX[year_gan]
        z_wx = self.ZHI_WX[year_zhi]
        
        if g_wx in fav: score += 15
        elif g_wx in unfav: score -= 10
        if z_wx in fav: score += 25
        elif z_wx in unfav: score -= 20
        # 简单刑冲
        if day_zhi == '午' and year_zhi == '子': score -= 15
        if day_zhi == '巳' and year_zhi == '亥': score -= 10
        
        return max(10, min(100, score))

# ==========================================
#          网页界面 (UI)
# ==========================================

with st.sidebar:
    st.header("1. 输入出生信息")
    st.warning("⚠️ 请务必输入【阳历 (公历)】时间！")
    
    in_year = st.number_input("出生年份", min_value=1900, max_value=2050, value=2000)
    in_month = st.number_input("出生月份", min_value=1, max_value=12, value=1)
    in_day = st.number_input("出生日期", min_value=1, max_value=31, value=1)
    in_hour = st.number_input("出生小时 (0-23)", min_value=0, max_value=23, value=0)
    
    st.header("2. 分析设置")
    max_age = st.slider("分析年限 (岁)", 10, 100, 60)
    
    run_btn = st.button("🚀 开始排盘分析", type="primary")

if run_btn:
    logic = BaziLogic()
    pillars = logic.get_bazi(in_year, in_month, in_day, in_hour)
    
    day_zhi = pillars[5]
    bazi_str = ' '.join([''.join(pillars[i:i+2]) for i in range(0,8,2)])
    
    fav, unfav, msg, is_strong = logic.analyze_auto(pillars)
    
    st.success(f"### 您的八字：{bazi_str}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**格局判定**：{'身强' if is_strong else '身弱'}")
    with col2:
        st.warning(f"**喜用神**：{fav}")
        
    if msg:
        st.error(msg)
        
    st.markdown(f"**忌神**：{unfav}")
    
    ages, scores, labels = [], [], []
    gan_list, zhi_list = [], []
    
    progress_bar = st.progress(0)
    
    for i in range(max_age):
        year = in_year + i
        age = i + 1
        
        temp = Solar.fromYmdHms(year, 6, 1, 12, 0, 0).getLunar()
        ln_gan, ln_zhi = temp.getYearGan(), temp.getYearZhi()
        
        final_score = logic.calc_score(ln_gan, ln_zhi, day_zhi, fav, unfav)
        
        ages.append(age)
        scores.append(final_score)
        labels.append(f"{year}\n{ln_gan}{ln_zhi}")
        gan_list.append(ln_gan)
        zhi_list.append(ln_zhi)
        
        progress_bar.progress((i + 1) / max_age)
        
    progress_bar.empty() 
    
    st.subheader("📈 人生运势起伏图")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(ages, scores, color='#34495e', linewidth=2, marker='o', markersize=4)
    ax.axhline(y=60, color='gray', linestyle='--', alpha=0.5)
    
    fav_str = "".join(fav)
    ax.fill_between(ages, 60, scores, where=[s>=60 for s in scores], facecolor='#e74c3c', alpha=0.4, label=f'喜 ({fav_str})')
    ax.fill_between(ages, 60, scores, where=[s<60 for s in scores], facecolor='#2980b9', alpha=0.4, label='忌')
    
    ax.set_ylabel('运势得分', fontsize=12)
    ax.set_ylim(0, 110)
    ax.set_xticks(ages)
    ax.set_xticklabels(labels, rotation=90, fontsize=8)
    ax.grid(True, linestyle=':', alpha=0.3)
    ax.legend(loc='upper right')
    
    st.pyplot(fig)
    
    with st.expander("查看详细数据表"):
        data = {
            "年龄": ages,
            "年份": [in_year + i for i in range(max_age)],
            "干支": [f"{g}{z}" for g, z in zip(gan_list, zhi_list)],
            "得分": scores,
            "评价": ["大吉 🔥" if s >= 85 else "吉" if s >= 70 else "凶 🌧" if s <= 40 else "平" for s in scores]
        }
        st.dataframe(data)

else:
    st.info("👈 请在左侧侧边栏输入出生时间，然后点击“开始排盘分析”")

import streamlit as st
import pandas as pd
from openai import OpenAI

st.set_page_config(page_title="本科论文写作与文献辅助", page_icon="📚", layout="wide")

st.title("📚 本科论文写作与文献综述平台")
st.caption("可上传知网导出的 xlsx 文件，一键生成高质量文献综述！")

# 读取 API 密钥
try:
    client = OpenAI(
        api_key=st.secrets["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com"
    )
except Exception:
    st.error("❌ 未找到 API Key，请在 Streamlit 后台 Secrets 中配置 DEEPSEEK_API_KEY")

# ---------------- 页面布局 ----------------
left_col, right_col = st.columns([1, 3])

with left_col:
    st.header("📁 1. 上传知网文献")
    uploaded_file = st.file_uploader("导出的知网 xlsx/csv 文件", type=["xlsx", "csv"])
    
    st.header("⚙️ 2. 功能选择")
    doc_type = st.radio("选择生成内容", ["开题报告大纲", "文献综述大纲", "完整论文框架", "根据上传文件写综述"])
    st.markdown("---")
    
    st.write("📏 字数参考")
    word_limit = st.radio("字数参考", ["3000字", "5000字", "10000字"], index=2, horizontal=True)

with right_col:
    st.header("✍️ 论文题目")
    topic = st.text_input("请输入本科毕业论文题目：", placeholder="例如：基于NX MCD与S7-1200的矿泉水瓶自动上盖旋盖装置设计")
    
    if st.button("🚀 一键生成", type="primary", use_container_width=True):
        if not topic:
            st.warning("请先输入论文题目！")
        else:
            # 处理“根据上传文件写综述”的逻辑
            if doc_type == "根据上传文件写综述":
                if uploaded_file is None:
                    st.error("你选择了【根据上传文件写综述】，但还没有上传知网导出的 xlsx/csv 文件！请在左侧上传。")
                else:
                    with st.spinner("📖 正在解析上传的文献并提炼文献综述..."):
                        try:
                            df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('xlsx') else pd.read_csv(uploaded_file)
                            # 找出知网导出文件常见的列名
                            title_col = next((c for c in df.columns if '标题' in c or '题名' in c), None)
                            abstract_col = next((c for c in df.columns if '摘要' in c), None)
                            author_col = next((c for c in df.columns if '作者' in c), None)
                            source_col = next((c for c in df.columns if '来源' in c or '刊名' in c), None)
                            
                            # 提取前 10 条作为样本（避免字数太长消耗过多余额）
                            lit_info = []
                            for i in range(min(10, len(df))):
                                row = df.iloc[i]
                                meta = f"标题: {row[title_col] if title_col else '无'}\n作者: {row[author_col] if author_col else '无'}\n来源: {row[source_col] if source_col else '无'}\n摘要: {row[abstract_col] if abstract_col else '无'}"
                                lit_info.append(meta)
                            
                            file_prompt = f"""
                            用户上传了 {len(df)} 条知网文献（系统提取了前10条示例供你分析）。
                            文献详情如下：
                            {chr(10).join(lit_info)}
                            
                            根据以上文献，结合用户论文题目《{topic}》，撰写一篇高质量的【文献综述】。
                            要求包含：研究背景、国外研究现状、国内研究现状、研究述评（现有研究的不足与未来趋势），并列出参考文献。
                            字数约为{word_limit}。
                            """
                            sys_prompt = "你是资深学术论文导师。"
                            response = client.chat.completions.create(
                                model="deepseek-chat",
                                messages=[
                                    {"role": "system", "content": sys_prompt},
                                    {"role": "user", "content": file_prompt}
                                ],
                            )
                            st.success("✅ 文献综述生成成功！可复制到 Word 中核对。")
                            st.markdown(response.choices[0].message.content)
                        except Exception as e:
                            st.error(f"解析文件或生成时出现错误：{e}")
            else:
                # 传统的生成大纲逻辑（不依赖文件）
                with st.spinner(f"🤖 正在生成 {doc_type}..."):
                    sys_prompt = f"""
                    你是高校本科论文写作导师。请根据用户提供的《{topic}》生成一份 {doc_type}。
                    如果选择【文献综述大纲】，请严格输出：引言、国外研究现状、国内研究现状、研究述评，以及10条知网格式的模拟参考文献。
                    """
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": sys_prompt},
                            {"role": "user", "content": f"我的题目是《{topic}》，请生成 {doc_type}，字数约 {word_limit}。"}
                        ]
                    )
                    st.success("✅ 生成成功！")
                    st.markdown(response.choices[0].message.content)
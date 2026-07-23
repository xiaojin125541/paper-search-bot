import streamlit as st
import pandas as pd
from openai import OpenAI
import markdown

st.set_page_config(page_title="本科毕业论文开题报告生成器", page_icon="📄", layout="wide")
st.title("📄 文山学院本科毕业论文开题报告一键生成器")

# 初始化 AI 客户端（使用免费的国内大模型网关）
try:
    client = OpenAI(
        api_key=st.secrets["SILICONFLOW_API_KEY"],
        base_url="https://api.siliconflow.cn/v1"
    )
    MODEL_NAME = "deepseek-ai/DeepSeek-V3"
except Exception:
    st.error("❌ 未找到 SILICONFLOW_API_KEY，请在 Streamlit 后台 Settings -> Secrets 配置。")

# --- 左侧：基本信息填写区域 ---
with st.sidebar:
    st.header("📝 1. 填写基础与选题信息")
    with st.form("student_info_form"):
        name = st.text_input("姓名", value="孙继恒")
        student_id = st.text_input("学号", value="20220806011046")
        college = st.text_input("学院", value="人工智能学院")
        major = st.text_input("专业", value="电气工程及其自动化")
        grade = st.text_input("年级", value="2022级")
        tutor_name = st.text_input("指导教师", value="李爱玲")
        
        source_options = ["教师科研", "社会实践", "实验教学", "教育教学", "其他"]
        source = st.selectbox("题目来源", source_options, index=0)
        
        category_options = ["应用研究", "理论研究", "艺术设计", "程序软件开发", "其他"]
        category = st.selectbox("题目类别", category_options, index=0)
        
        st.form_submit_button("信息已确认")

    st.markdown("---")
    st.header("📁 2. 上传知网文献（可选）")
    uploaded_file = st.file_uploader("导出的知网 xlsx 或 csv 文件", type=["xlsx", "csv"])

# --- 右侧：核心生成区域 ---
st.subheader("✍️ 输入论文题目，开始生成报告")
topic = st.text_input("请输入本科毕业论文题目：", placeholder="例如：基于PLC设计的直线振荡器激振器振动自动加油控制系统")
word_limit = st.selectbox("预估字数要求（影响生成内容的详细程度）：", ["3000字", "5000字", "10000字"], index=0)

# 定义一个将Markdown转换为Word可读HTML的函数
def generate_word_html(title, name, student_id, college, major, grade, tutor_name, source, category, content_md):
    html_content = markdown.markdown(content_md)
    html_doc = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>开题报告</title>
        <style>
            body {{ font-family: 'SimSun', serif; line-height: 1.6; margin: 2cm; }}
            h1 {{ text-align: center; font-size: 22pt; }}
            h2 {{ font-size: 16pt; margin-top: 20pt; }}
            h3 {{ font-size: 14pt; margin-top: 15pt; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 15pt; margin-top: 15pt; }}
            th, td {{ border: 1px solid black; padding: 8px; text-align: left; }}
            p {{ text-indent: 2em; margin: 5px 0; }}
        </style>
    </head>
    <body>
        <p style="text-align:center; font-size:18pt; font-weight:bold;">文山学院本科生毕业论文（设计）开题报告</p>
        <table>
            <tr><td width="15%">姓名</td><td width="25%">{name}</td><td width="15%">学号</td><td width="45%">{student_id}</td></tr>
            <tr><td>学院</td><td>{college}</td><td>专业</td><td>{major}</td></tr>
            <tr><td>年级</td><td>{grade}</td><td>指导教师</td><td>{tutor_name}</td></tr>
            <tr><td>论文题目</td><td colspan="3">{title}</td></tr>
            <tr><td>题目来源</td><td colspan="3">{source}</td></tr>
            <tr><td>题目类别</td><td colspan="3">{category}</td></tr>
        </table>
        {html_content}
    </body>
    </html>
    """
    return html_doc

if st.button("🚀 一键生成完整开题报告", type="primary", use_container_width=True):
    if not topic:
        st.warning("请先输入论文题目！")
    else:
        with st.spinner(f"🤖 AI 正在根据题目《{topic}》生成开题报告..."):
            
            uploaded_literatures = ""
            if uploaded_file is not None:
                try:
                    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('xlsx') else pd.read_csv(uploaded_file)
                    title_col = next((c for c in df.columns if '标题' in c or '题名' in c), None)
                    abstract_col = next((c for c in df.columns if '摘要' in c), None)
                    author_col = next((c for c in df.columns if '作者' in c), None)
                    
                    lit_info = []
                    for i in range(min(8, len(df))):
                        row = df.iloc[i]
                        meta = f"标题: {row[title_col] if title_col else '无'}\n作者: {row[author_col] if author_col else '无'}\n摘要: {row[abstract_col] if abstract_col else '无'}"
                        lit_info.append(meta)
                    uploaded_literatures = chr(10).join(lit_info)
                except Exception:
                    pass

            system_prompt = f"""
            你是一位经验丰富的大学本科毕业设计指导教师。请根据用户提供的信息，写一份标准规范的《文山学院本科生毕业论文（设计）开题报告》。
            
            学生信息如下：
            姓名：{name}，学号：{student_id}，学院：{college}，专业：{major}，年级：{grade}。
            指导教师：{tutor_name}。
            论文题目：《{topic}》。
            题目来源：{source}，题目类别：{category}。
            字数目标：约 {word_limit}。

            请务必严格且详细包含以下板块（必须包含标题和加粗的小标题）：
            1. 选题的目的、意义（包含理论意义、现实意义）。
            2. 选题的研究现状（国内外相关研究综述）。
            3. 论文主要内容（提纲，至少包含6个章节的一级标题）。
            4. 拟研究的主要问题、重点和难点。
            5. 研究目标。
            6. 研究方法、技术路线、实验方案、可行性分析。
            7. 研究的创新之处（至少3点）。
            8. 进度安排。
            9. 参考文献（如果上传了文档，将上传文档列为参考文献；如果没有，请模拟生成10篇符合学术规范的真实文献）。
            """

            # 【修正点】将容易报错的嵌套 f-string 移到外面来写
            ref_section = ""
            if uploaded_literatures:
                ref_section = f"下面是用户实际找到的参考文献资料，请务必基于此资料写研究现状(文献综述)，并参考作为最终的参考文献：\n{uploaded_literatures}"
            
            user_prompt = f"""
            我的论文题目是《{topic}》，指导老师是{tutor_name}，字数要求约{word_limit}，请帮我写开题报告。
            {ref_section}
            """

            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7
                )
                
                final_answer = response.choices[0].message.content

                st.success("✅ 开题报告生成成功！")
                st.markdown("---")
                st.markdown(final_answer)
                st.markdown("---")
                
                doc_bytes = generate_word_html(topic, name, student_id, college, major, grade, tutor_name, source, category, final_answer)
                st.download_button(
                    label="📥 下载开题报告 (.doc)",
                    data=doc_bytes,
                    file_name=f"{topic}_开题报告.doc",
                    mime="application/msword"
                )
                st.caption("💡 下载后使用 Microsoft Word 打开，表格和正文排版均已自动完成。")
                
            except Exception as e:
                st.error(f"⚠️ 生成失败！请将以下错误截图发给我帮助排查：{e}")
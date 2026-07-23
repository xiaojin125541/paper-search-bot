import streamlit as st
from openai import OpenAI
from duckduckgo_search import DDGS

st.set_page_config(page_title="学术文献搜索助手", layout="centered")
st.title("📚 同学共享学术助手")

# 【安全关键点】：这里的 Key 不写死，而是从隐藏的环境变量里读取
# 这样就算你把代码公开给同学，他们也看不到你的密钥！
client = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"  # 加上这一行，指定去 DeepSeek 服务器
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("请输入你的论文题目或关键词："):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # 模仿截图中的“步骤展开”，显示正在调用 web_search
        with st.status("🔍 正在调用 web_search 工具检索全网资源...", expanded=True) as status:
            search_content = []
            try:
                with DDGS() as ddgs:
                    # 爬取前 5 条公开搜索结果（完全免费无上限）
                    for r in ddgs.text(prompt, max_results=5):
                        search_content.append(f"标题：{r['title']}\n摘要：{r['body']}\n链接：{r['href']}")
                status.update(label="✅ 检索完成，正在结合资料生成回答...", state="complete")
            except Exception:
                search_content = ["搜索服务暂时拥堵，仅根据内部知识回答。"]

        # 组装提示词发给 DeepSeek
        system_prompt = f"你是学术助手。请根据问题以及搜索到的公开资料，给同学提供有参考价值的回答。如果资料不相关，请说明。\n\n【搜索到的资料】\n{chr(10).join(search_content)}"
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        answer = response.choices[0].message.content
        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
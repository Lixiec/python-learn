from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

llm = ChatOpenAI(model="gpt-4o-mini")

response = llm.invoke([HumanMessage(content="用一句话介绍一下你自己")])

print(response.content)

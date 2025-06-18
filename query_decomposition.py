from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')


def decompose_prompt(user_prompt: str) -> list:
    """
    Decompose a user prompt into sub-questions or tasks using LangChain and Gemini model.

    Args:
        user_prompt (str): The user's input prompt.

    Returns:
        list: A list of decomposed sub-questions or tasks.
    """
    # Initialize Gemini model (make sure to set your API key in the environment)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=GOOGLE_API_KEY, max_tokens=4096)

    # Define a prompt template for decomposition
    messages = [
        SystemMessage('''Bạn là một trợ lý phân rã câu hỏi thông minh, chuyên phân tích ý định của người dùng trong bối cảnh cuộc trò chuyện.

Nhiệm vụ của bạn là:
1.  Đọc kỹ `Lịch sử trò chuyện` và `Câu nói hiện tại của người dùng`.
2.  Hiểu rõ ý định thực sự của người dùng, làm rõ mọi đại từ hoặc ám chỉ dựa trên ngữ cảnh.
3.  **Tạo ra một hoặc nhiều câu hỏi độc lập, rõ ràng, và tự chứa (self-contained)** mà có thể được sử dụng để tìm kiếm thông tin trong cơ sở dữ liệu.
4.  Nếu `Câu nói hiện tại của người dùng` đã là một câu hỏi rõ ràng và độc lập, hãy trả về chính câu hỏi đó (có thể tinh chỉnh nhẹ để tối ưu tìm kiếm).
5.  Nếu `Câu nói hiện tại của người dùng` không phải là câu hỏi (ví dụ: lời chào, xác nhận, hoặc một phản hồi đơn giản không yêu cầu tìm kiếm), hãy trả về một chuỗi rỗng hoặc thông báo rằng không cần tìm kiếm.

**Định dạng đầu ra:**
Liệt kê mỗi câu hỏi con trên một dòng mới.
                      Input: {user_prompt}'''),
        HumanMessage(user_prompt),
    ]

    # Get the response from Gemini
    response = llm.invoke(messages)
    # Extract the decomposed tasks from the response
    lines = response.content.strip().split('\n')
    # tasks = [line.split('.', 1)[1].strip() for line in lines if '.' in line]

    return lines

print(decompose_prompt("làm sao để gửi hàng và nhận hàng?"))
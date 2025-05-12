# main.py
from mcp.server.fastmcp import FastMCP
import aiohttp
from typing_extensions import TypedDict
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variables
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

class State(TypedDict):
    question:str
    query:str
    result:str
    answer:str
    formatted:str

class QueryOutput(BaseModel):
    """Generated SQL query."""
    query: str = Field(..., description="Syntactically valid SQL query.")

model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=GOOGLE_API_KEY, max_tokens=4096)

mcp = FastMCP("getindustrialzones")
@mcp.tool()
async def get_industrial_parks_info(prompt:str) -> dict:
    """
      Tool để trả lời các câu hỏi về danh sách các khu công nghiệp có sẵn. 
      Câu hỏi có thể yêu cầu một danh sách hoặc thông tin tổng quan về các khu công nghiệp.
      
      Các câu hỏi ví dụ mà tool có thể xử lý:
      - "Bạn có các khu công nghiệp nào?"
      - "Hãy liệt kê các khu công nghiệp có sẵn"
      - "Danh sách các khu công nghiệp"
      - "Các khu công nghiệp ở khu vực XYZ là gì?"
      
      Công cụ này sẽ trả về thông tin về các khu công nghiệp có trong cơ sở dữ liệu, bao gồm các chi tiết như tên, diện tích, giá thuê, và các đặc điểm khác.
      
      Các câu hỏi yêu cầu thông tin chi tiết hơn về từng khu công nghiệp có thể cần sử dụng công cụ khác để cung cấp thông tin cụ thể hơn.
    """
    try:
        response = await execute(prompt)
        return response
    except Exception as e:
        return {"error": str(e)}
    
def write_query(state: State) -> str:

    table = """
    Table: industrial_parks
    Columns:
    - id (int, primary key)
    - name (varchar)
    - address (varchar)
    - area (float8)
    - lease_area_options (float8[])
    - lease_price (float8)
    - occupancy_rate (float8)
    - legal_status (boolean)
    - lease_term (int)
    - description (varchar)
    - advantages (varchar)
    - additional_info (varchar)
    - detail_url (varchar)
    - image (varchar)
    - lat (float8)
    - long (float8)
    """
    systemPrompt = """Bạn là một công cụ tạo truy vấn SQL cho PostgreSQL.
        **Schema**:
        {table_info}

        Nhiệm vụ:
        Tạo câu truy vấn PostgreSQL để trả lời câu hỏi sau:
        {input}

        HƯỚNG DẪN QUAN TRỌNG:
        ❌ Không hỏi lại người dùng dưới bất kỳ hình thức nào.
        ❌ Không ở vai trợ lý hoặc hệ thống.
        Khu công nghiệp lớn nhất / rộng nhất: Dựa vào cột area. Giá trị lớn hơn nghĩa là quy mô lớn hơn.
        Sắp xếp mặc định: Theo area DESC, sau đó id ASC trừ khi có yêu cầu khác.
        Luôn lấy tất cả cột: Sử dụng SELECT * trừ khi được yêu cầu chỉ lấy một số cột cụ thể.
        Giới hạn kết quả: Trả về tất cả kết quả trừ khi có yêu cầu số lượng cụ thể.
        Chỉ lọc theo cấu trúc có sẵn: Chỉ lọc theo area, lease_price, occupancy_rate, lease_term, legal_status, và address. Không lọc theo name, description, hay advantages.
        Không phỏng đoán: Chỉ sử dụng các cột có trong bảng. Không tự tạo thêm cột như "trạng thái hoạt động", "tiện ích", hay "mức độ phát triển".
        Tìm khu công nghiệp gần một vị trí cụ thể: Nếu câu hỏi đề cập đến một địa điểm (ví dụ: "các khu công nghiệp trong bán kính 100km từ Cần Thơ"), hãy tính khoảng cách dựa trên công thức Haversine sau:
        sql
        SELECT * FROM (
          SELECT *, (
            6371 * acos(
              cos(radians([LAT])) *
              cos(radians(lat)) *
              cos(radians("long") - radians([LON])) +
              sin(radians([LAT])) *
              sin(radians(lat))
            )
          ) AS distance_km
          FROM industrial_parks
        ) AS sub
        WHERE distance_km <= [DISTANCE_IN_KM]
        ORDER BY distance_km;

        Trong đó:
        [LAT], [LON] là tọa độ của địa điểm cần so sánh
        [DISTANCE_IN_KM] là bán kính cần lọc (ví dụ: 100)

        👉 Giờ thì khi user hỏi câu như:
        "Tìm các khu công nghiệp trong bán kính 100km từ Bến Lức, Long An",
        bạn chỉ cần:
        Lấy tọa độ của "Bến Lức, Long An" (ví dụ: 10.6168, 106.4984)
        Thay [LAT], [LON], và [DISTANCE_IN_KM] trong truy vấn Haversine
        Ghép truy vấn vào kết quả đầu ra

        Kết quả đầu ra:
        Chỉ trả về câu truy vấn SQL thuần túy. Không bao gồm giải thích, định dạng hoặc chú thích.
    """
    structured_model = model.with_structured_output(QueryOutput)
    prompt_template = ChatPromptTemplate.from_template(systemPrompt)
    chain = prompt_template | structured_model
    query = chain.invoke({"input": state["question"], "table_info": table})
    
    state["query"] = query.query
    return state

async def call_backend(state: State):
    URL = f"http://10.66.68.17:31797/industrial-parks/raw?query={state["query"]}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as response:
                state["result"] = ((await response.json()))
                return state
    except Exception as e:
        return {"error": str(e)}

async def answer(state: State):
    systemPrompt = """
      Bạn là một chuyên gia bất động sản cho công ty bất động sản **Phát Đạt Corporation** tên Terra, chuyên về việc đề xuất các sản phẩm bất động sản phù hợp trong đó có:khu công nghiệp, các dự án nổi bật.
      Kiến thức của bạn chỉ giới hạn trong danh sách được cung cấp trong các thẻ XML 
      <context>  
      {history}  
      </context>
      Hãy dùng 5 documents liên quan nhất trong context để trả lời.
      Đây là một số dữ liệu tăng cường để trả lời: {enhance}

      Quy tắc đề xuất sản phẩm bất động sản
      1. Ghép chính xác và hỏi rõ thêm nếu cần:
      Đề xuất khu công nghiệp hoàn toàn phù hợp với tất cả tiêu chí mà người dùng đưa ra (ví dụ: diện tích, giá thuê, tình trạng pháp lý, lợi thế, tỉ lệ lấp đầy, v.v.) hoặc 1 phần, ưu tiên những nơi gần nhất rồi đến giá cả. Nếu nêu thông tin của các đối tượng chỉ nêu những thông tin quan trọng như tên và thông tin liên quan đến câu hỏi, tránh liệt kê quá nhiều thông tin trong phần text.
      Nếu yêu cầu của người dùng mơ hồ hoặc chưa đầy đủ, hãy đặt các câu hỏi làm rõ để thu hẹp nhu cầu của họ. Ví dụ:
      "Bạn đang tìm khu công nghiệp với diện tích khoảng bao nhiêu ha?"
      "Ngân sách của bạn cho mỗi ha là bao nhiêu?"
      "Bạn có ưu tiên khu công nghiệp đầy đủ tình trạng pháp lý không"

      2. Khi trả lời, hãy trả về theo định dạng JSON chỉ gồm 2 property:
      text: Chứa nội dung câu trả lời chính của bạn.
      objects: Nếu có, trả về các đối tượng liên quan (ví dụ: dự án nổi bật, khu công nghiệp, thông tin chi tiết khác), nếu không có thông tin, trả về một mảng trống.
      Đối với khu công nghiệp format json là : {{
            "name": "Chuỗi - Tên khu công nghiệp",
            "price_per_m2": "Chuỗi - ví dụ: '100 USD'",
            "area": '100 ha',
        "description": "mô tả",
            "address": "Chuỗi - ví dụ: 'Bà Rịa Vũng Tàu'",
            "occupancy_rate": "Chuỗi - tỉ lệ lấp đầy",
            "lease_area_options": "Chuỗi - các lựa chọn diện tích thuê",
            "legal_status": "Chuỗi - tình trạng pháp lý'",
            "lease_term": "Chuỗi - Thời hạn thuê",
      "advantages": "lợi thế",
      "additional_info": "thông tin thêm",
            "detail_url": "Chuỗi - URL tới bài viết chi tiết (bắt buộc)",
            "image": "Chuỗi - URL ảnh đại diện (bắt buộc)",
            "reason": "Chuỗi - Giải thích vì sao đề xuất khu công nghiệp này"
          }}, đối với dự án nổi bật format json là 
      {{
          "id": 1,
          "name": "Khu công nghiệp ABC",
          "location": "Long An",
      "description": "some description",
          "area": "100 ha",
          "image": "https://www.phatdat.com.vn/wp-content/uploads/2019/07/QN-ICONIC.png",
      "detail_url": "https://www.phatdat.com.vn/project/khu-do-thi-bac-ha-thanh/"
        }}
      Ví dụ:
      json
      {{
        "text": "Cảm ơn bạn đã hỏi! Tôi không có đủ thông tin từ ngữ cảnh để trả lời đầy đủ, nhưng dưới đây là những gì tôi có thể gợi ý: Hãy thử cung cấp thêm thông tin về yêu cầu của bạn, như diện tích hoặc vị trí để tôi có thể giúp bạn tìm kiếm thông tin chính xác hơn.",
        "objects": []
      }}
      3. Tùy biến ngôn ngữ:
      Phát hiện ngôn ngữ từ câu hỏi của người dùng.
      Giữ nguyên các trường trong JSON như "name", "price_per_m2", v.v. (thường là tiếng Việt hoặc tiếng Anh từ <context>).
      Nếu không thể phát hiện được ngôn ngữ, mặc định sử dụng tiếng Việt và ghi chú:
      "Tôi không thể xác định được ngôn ngữ của bạn nên tôi sẽ sử dụng tiếng Việt."
    """
    prompt_template = ChatPromptTemplate.from_template(systemPrompt)
    chain = prompt_template | model
    final = chain.invoke({"enhance": state["result"], "history": ""})
     
    state["formatted"] = final
    return state

async def execute(prompt: str):
    workflow = StateGraph(State)
    workflow.add_node("write_query", write_query)
    workflow.add_node("execute_query", call_backend)
    workflow.add_edge("write_query", "execute_query")
    workflow.add_edge("execute_query", END)
    workflow.set_entry_point("write_query")
    graph = workflow.compile()

    result = await graph.ainvoke({"question": prompt})
    
    return result
if __name__ == "__main__":
    mcp.run()

# Tổng quan dự án: Learning Journey Tracker

## 1. Mục tiêu dự án

Đây là một ứng dụng web full-stack được thiết kế để theo dõi tiến độ học tập của một nhóm người dùng (học viên). Ứng dụng cho phép người dùng đăng nhập, xem tiến độ của tất cả mọi người, cập nhật tiến độ của bản thân và tạo các ghi chú liên quan đến các học phần.

## 2. Cấu trúc thư mục

Dự án được cấu trúc theo dạng monorepo với hai phần chính:

-   `/backend`: Chứa mã nguồn cho API server.
-   `/frontend`: Chứa mã nguồn cho ứng dụng giao diện người dùng (SPA - Single Page Application).
-   `/backend_test.py`: Một script để kiểm thử tích hợp (integration test) cho API backend.
-   `README.md`: **Lưu ý: File này đã lỗi thời** và không phản ánh đúng công nghệ của dự án hiện tại.

---

## 3. Backend

-   **Ngôn ngữ**: Python
-   **Framework**: **FastAPI** được sử dụng để xây dựng API, với `uvicorn` làm máy chủ ASGI.
-   **Cơ sở dữ liệu**:
    -   **MongoDB**: Sử dụng cho các dữ liệu động như tiến độ (`progress`) và ghi chú (`notes`) thông qua thư viện `motor` (bất đồng bộ).
    -   **File-based**: Sử dụng các tệp `.txt` (`users.txt`, `levels.txt`) để lưu trữ danh sách người dùng, mật khẩu và các cấp độ học tập. Đây là một cơ chế đơn giản thay cho bảng dữ liệu tĩnh.
-   **Xác thực (Authentication)**: Sử dụng JWT (JSON Web Tokens). Người dùng đăng nhập để nhận token và sử dụng token đó cho các yêu cầu tiếp theo.
-   **API**: Tất cả các endpoint đều có tiền tố là `/api`.
-   **Phụ thuộc chính (`requirements.txt`)**:
    -   `fastapi`, `uvicorn`: Nền tảng web.
    -   `pymongo`, `motor`: Tương tác với MongoDB.
    -   `python-jose`, `pyjwt`, `passlib`: Xử lý JWT và mật khẩu.
    -   `python-dotenv`: Quản lý biến môi trường.
-   **Để chạy backend**:
    1.  Cài đặt phụ thuộc: `pip install -r backend/requirements.txt`
    2.  Chạy server: `uvicorn backend.server:app --reload --port 8000`

---

## 4. Frontend

-   **Ngôn ngữ**: JavaScript (JSX)
-   **Framework**: **React**. Dự án được khởi tạo từ `create-react-app` và được tùy chỉnh cấu hình bằng **CRACo** (`@craco/craco`).
-   **Giao diện người dùng (UI)**:
    -   **shadcn/ui**: Một bộ sưu tập các component UI có thể tái sử dụng. Các component này được xây dựng trên **Radix UI** (cho logic và khả năng truy cập) và **Tailwind CSS** (cho styling).
    -   **Tailwind CSS**: Framework CSS chính để tạo kiểu cho ứng dụng.
    -   `lucide-react`: Thư viện icon.
-   **Routing**: `react-router-dom` được sử dụng để quản lý điều hướng trong ứng dụng (ví dụ: `/login`, `/`).
-   **Quản lý trạng thái (State Management)**:
    -   **React Context API**: Được sử dụng cho việc quản lý trạng thái xác thực người dùng trên toàn ứng dụng.
    -   **Component State (`useState`, `useEffect`)**: Sử dụng cho các trạng thái cục bộ khác.
-   **Tương tác với API**: Thư viện `axios` được dùng để thực hiện các yêu cầu HTTP đến backend.
-   **Phụ thuộc chính (`package.json`)**:
    -   `react`, `react-dom`: Nền tảng React.
    -   `react-router-dom`: Routing.
    -   `axios`: HTTP client.
    -   `tailwindcss`: CSS framework.
    -   Các thư viện `@radix-ui/*`: Nền tảng cho component.
    -   `sonner`: Hiển thị thông báo (toast).
-   **Để chạy frontend**:
    1.  Cài đặt phụ thuộc: `npm install` (hoặc `yarn install`)
    2.  Chạy ứng dụng: `npm start` (hoặc `yarn start`)

---

## 5. Kiểm thử (Testing)

-   **Backend**: `backend_test.py` là một script kiểm thử tích hợp, sử dụng thư viện `requests` để gọi trực tiếp đến các API endpoint đang chạy và xác minh kết quả.
-   **Frontend**: Dự án có sẵn cấu hình để chạy test với `react-scripts test`, nhưng chưa có file test cụ thể nào được viết.

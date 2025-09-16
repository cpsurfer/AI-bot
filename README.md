# 🧠 My Personal AI Assistant

A private, custom AI assistant designed to answer questions and provide information about me, based on my personal documents.

---

## ✨ Features

- **Personalized Responses:** The bot provides answers tailored to your queries using information from your provided documents.
- **Secure & Private:** The assistant only accesses files you provide in the designated `me` folder, ensuring your data remains private and secure.
- **Easy to Use:** A simple, intuitive interface built with Streamlit for a seamless conversational experience.

---

## 🚀 Get Started

Follow these steps to set up and run the AI bot.

### ⚙️ Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
    cd your-repo-name
    ```

2.  **Add your API key:**
    Create a folder named `.streamlit` in the root directory. Inside it, create a file called `secrets.toml` and add your Gemini API key:
    ```toml
    GEMINI_API_KEY="your_api_key_here"
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### 📁 Add Your Documents

To make the assistant work, you need to create a folder and add your personal documents.

-   **Create a folder:** In the root directory of the project, create a new folder named `me`.
-   **Add your files:** Place your CV, professional summary, or any other relevant text documents (e.g., `my_cv.pdf`, `about_me.txt`) inside the `me` folder.

### 💻 Run the Bot

Launch the application from your terminal:
```bash
streamlit run main.py

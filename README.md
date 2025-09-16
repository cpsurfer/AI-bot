# 🧠 My Personal AI Assistant

A custom AI assistant designed to answer questions and provide information about me, based on my personal documents.

---

## ✨ Features

* **Personalized Responses:** The bot tailors answers to your queries using information from documents you provide.
* **Secure & Private:** The assistant only accesses files in the designated `me` folder, ensuring your data remains private and secure.
* **Easy to Use:** A simple, intuitive interface built with Streamlit offers a seamless conversational experience.

---

## 🚀 Get Started

Follow these steps to set up and run the AI bot.

### ⚙️ Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/cpsurfer/AI-bot.git](https://github.com/cpsurfer/AI-bot.git)
    cd AI-bot
    ```

2.  **Add your API key:**
    Create a folder named `.streamlit` in the project's root directory. Inside it, create a file named `secrets.toml` and add your **Google Gemini API key**:
    ```toml
    GEMINI_API_KEY="your_api_key_here"
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### 📁 Add Your Documents

To make the assistant work, you need to provide your personal documents.

* **Create a folder:** In the project's root directory, create a new folder called `me`.
* **Add your files:** Place your personal documents inside the `me` folder. The bot is ready to process files such as `linkedin.pdf`, `cv.pdf`, and `summary.txt`.

### 💻 Run the Bot

Launch the application from your terminal:
```bash
streamlit run main.py

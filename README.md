# ADA (Automated Directive Assistant)

```text
    ___    ____  ___ 
   /   |  / __ \/   |
  / /| | / / / / /| |
 / ___ |/ /_/ / ___ |
/_/  |_/_____/_/  |_|
```

**ADA** is a professional-grade, lightweight AI assistant designed for your terminal. It translates natural language queries into precise terminal commands, specifically tailored to your Operating System and Shell environment.

---

## 🚀 Key Features

-   **OS & Shell Aware**: Automatically detects if you are using PowerShell, CMD, Bash, or Zsh to provide compatible syntax.
-   **Smart Memory**: Remembers recent interactions for context-aware follow-up questions.
-   **Automatic Clipboard**: Your suggested commands are instantly copied to your clipboard for immediate use.
-   **Interactive Menu**: A sleek, arrow-key driven menu for easier management and querying.
-   **Customizable**: View and modify the system prompt to adjust ADA's personality or instructions.
-   **Secure**: Uses a local `.env` file for your Gemini API key and stores interaction history privately.

---

## 🛠 Installation

### The Easy Way (User)
Install directly from GitHub using `pip`:

```bash
pip install git+https://github.com/woodleyj/ada-assistant.git
```

### The Dev Way (Contributor)
If you want to modify the code or contribute:

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/woodleyj/ada-assistant.git
    cd ada-assistant
    ```
2.  **Install in editable mode**:
    ```bash
    pip install -e .
    ```

---

## 🏁 Getting Started

On your first run, ADA will guide you through a quick setup to securely save your **Gemini API Key**.

1.  Simply run:
    ```bash
    ada
    ```
2.  Follow the on-screen wizard to enter your key.

---

## 📖 Usage

### Command Line Mode
Pass your query directly to `ada`:

```powershell
# Commands are shell-aware!
ada "how do I find all python files recursively?"
```

### Interactive Mode
Run `ada` without arguments to open the interactive menu. Use your **arrow keys** to navigate:

-   **Ask a Question**: Direct chat or command generation.
-   **Manage Memory**: View or clear your interaction history.
-   **System Settings**: Configure the memory limit or edit the AI's system prompt.

### Management Commands
You can manage ADA settings directly from the terminal:

-   `ada /memories show` - View stored interaction history.
-   `ada /memories limit 10` - Change memory capacity (1-20).
-   `ada /prompt show` - View current AI instructions.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

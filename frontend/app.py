# frontend/app.py
import time
import gradio as gr
from frontend.client import client
from frontend.styles import CUSTOM_CSS

# --- HANDLER FUNCTIONS ---

def handle_login(u, p, auth_screen, app_screen, l_msg):
    """
    Handles login logic and UI switching.
    Yields dictionary updates to specific UI components.
    """
    # 1. Show Loading State
    yield {
        l_msg: "⏳ Logging in...", 
        auth_screen: gr.update(visible=True), 
        app_screen: gr.update(visible=False)
    }
    
    # 2. Perform Login
    success, msg = client.login(u, p)
    
    # 3. Update UI based on result
    if success:
        time.sleep(0.5) # Small delay for smooth transition
        yield {
            auth_screen: gr.update(visible=False), 
            app_screen: gr.update(visible=True), 
            l_msg: msg
        }
    else:
        yield {
            auth_screen: gr.update(visible=True), 
            app_screen: gr.update(visible=False), 
            l_msg: msg
        }

def handle_logout(auth_screen, app_screen, chatbot, l_user, l_pass, file_input, l_msg):
    """
    Clears session and resets UI to login screen.
    Returns a single dictionary update (not a generator).
    """
    client.token = None
    return {
        auth_screen: gr.update(visible=True), 
        app_screen: gr.update(visible=False), 
        chatbot: [], 
        l_user: "", 
        l_pass: "", 
        file_input: None, 
        l_msg: "👋 Logged out successfully."
    }

def handle_register(u, p):
    yield "⏳ Registering..."
    success, msg = client.register(u, p)
    yield msg

def handle_upload(file):
    yield "<span style='color: white;'>⏳ Uploading & Analyzing...</span>"
    result = client.upload_file(file)
    yield result

def respond(message, history):
    if not message: return history, ""
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": ""})
    yield history, ""
    
    # Stream response
    for partial in client.chat_stream(message):
        history[-1]["content"] = partial
        yield history, ""

# --- UI LAYOUT ---
with gr.Blocks(title="Legal AI Agent") as demo:
    gr.HTML(f"<style>{CUSTOM_CSS}</style>")
    
    # State variable for chat history
    chat_history_state = gr.State(value=[])

    # --- AUTH SCREEN ---
    with gr.Group(visible=True) as auth_screen:
        with gr.Column(elem_classes=["auth-box"]):
            gr.Markdown("# ⚖️ Legal AI Agent")
            gr.Markdown("### Secure Document Analysis")
            with gr.Tabs():
                with gr.Tab("Sign In"):
                    l_user = gr.Textbox(label="Username")
                    l_pass = gr.Textbox(label="Password", type="password")
                    l_btn = gr.Button("Login", variant="primary")
                    l_msg = gr.Markdown("Please login to continue.")
                with gr.Tab("Sign Up"):
                    r_user = gr.Textbox(label="Create Username")
                    r_pass = gr.Textbox(label="Create Password", type="password")
                    r_btn = gr.Button("Register", variant="secondary")
                    r_msg = gr.Markdown("Create a new account.")

    # --- MAIN APP SCREEN ---
    with gr.Row(visible=False) as app_screen:
        # Sidebar
        with gr.Column(scale=1, elem_classes=["sidebar"]):
            gr.Markdown("## ⚖️ Legal AI", elem_classes=["sidebar-title"])
            gr.Markdown("### 📄 Document Center")
            gr.Markdown("Upload documents or images.")
            
            file_input = gr.File(label="Upload PDF/Image", file_types=[".pdf", ".jpg", ".png", ".jpeg"])
            upload_status = gr.HTML("<span style='color: white;'>Waiting for upload...</span>", elem_classes=["status-msg"])
            
            gr.Markdown("---")
            logout_btn = gr.Button("🚪 Logout", variant="secondary")

        # Chat Area
        with gr.Column(scale=4):
            gr.Markdown("### 💬 Legal Assistant")
            chatbot = gr.Chatbot(elem_classes=["chat-window"], avatar_images=(None, "https://cdn-icons-png.flaticon.com/512/666/666162.png"))
            with gr.Row():
                msg_input = gr.Textbox(show_label=False, placeholder="Type your legal question here...", scale=8, container=False, autofocus=True)
                send_btn = gr.Button("➤", variant="primary", scale=1)

    # --- WIRING (EVENTS) ---
    
    # WRAPPERS: Defined here to capture the UI components securely
    # ------------------------------------------------------------
    
    # Wrapper for Login (Generator)
    def login_wrapper(u, p):
        yield from handle_login(u, p, auth_screen, app_screen, l_msg)

    # Wrapper for Logout (Regular Function)
    def logout_wrapper():
        return handle_logout(auth_screen, app_screen, chatbot, l_user, l_pass, file_input, l_msg)

    # ------------------------------------------------------------

    # Login Event
    l_btn.click(
        fn=login_wrapper, 
        inputs=[l_user, l_pass], 
        outputs=[auth_screen, app_screen, l_msg]
    )

    # Register Event
    r_btn.click(handle_register, [r_user, r_pass], r_msg)

    # Upload Event
    file_input.upload(handle_upload, inputs=[file_input], outputs=[upload_status])

    # Chat Events
    msg_input.submit(respond, [msg_input, chatbot], [chatbot, msg_input])
    send_btn.click(respond, [msg_input, chatbot], [chatbot, msg_input])

    # Logout Event
    logout_btn.click(
        fn=logout_wrapper, 
        outputs=[auth_screen, app_screen, chatbot, l_user, l_pass, file_input, l_msg]
    )

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())
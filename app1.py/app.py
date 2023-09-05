import json
from difflib import get_close_matches
import tkinter as tk
from tkinter import scrolledtext
import requests
import io
from threading import Thread
from flask import Flask, render_template, request, jsonify
from PIL import Image, ImageTk, ImageFilter

# Create a Flask app
app = Flask(__name__, template_folder='templates')

class ChatBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Bot")

        self.load_knowledge_base('kb.json')

        self.chat_text = scrolledtext.ScrolledText(self.root, state=tk.DISABLED)
        self.user_input_text = tk.Text(self.root, height=2)
        self.send_button = tk.Button(self.root, text="Send", command=self.send_message)
        self.get_image_button = tk.Button(self.root, text="Get Image", command=self.get_image)

        self.chat_text.pack(fill="both", expand=True)
        self.user_input_text.pack(fill="both", expand=True)
        self.send_button.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.get_image_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.last_question = None
        self.image_label = None  # To display the image

        self.root.mainloop()

    def load_knowledge_base(self, file_path: str):
        with open(file_path, 'r') as file:
            self.knowledge_base = json.load(file)

    def save_knowledge_base(self):
        with open('kb.json', 'w') as file:
            json.dump(self.knowledge_base, file, indent=2)

    def find_best_match(self, user_question: str) -> str | None:
        questions = [q["question"] for q in self.knowledge_base["questions"]]
        if user_question in questions:
            return user_question
        matches = get_close_matches(user_question, questions, n=1, cutoff=0.7)
        return matches[0] if matches else None

    def get_answer_for_question(self, question: str) -> str | None:
        for q in self.knowledge_base["questions"]:
            if q["question"] == question:
                return q["answer"]
        return None

    def save_and_thank(self):
        new_answer = self.user_input_text.get("1.0", "end-1c").strip()
        if new_answer.lower() != 'skip':
            self.knowledge_base["questions"].append({"question": self.last_question, "answer": new_answer})
            self.save_knowledge_base()
            self.add_bot_message("Thank you, response saved!")
            self.clear_inputs()

    def provide_correction(self):
        self.user_input_text.config(state=tk.NORMAL)
        self.send_button.config(state=tk.NORMAL)
        self.clear_inputs()
        self.add_bot_message("You are wrong. Please provide the correct answer:")

    def clear_inputs(self):
        self.user_input_text.delete("1.0", tk.END)
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete("end-2c", tk.END)
        self.chat_text.config(state=tk.DISABLED)
        self.user_input_text.config(state=tk.NORMAL)
        self.send_button.config(state=tk.NORMAL)

    def add_bot_message(self, message: str):
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, "Bot: " + message + "\n")
        self.chat_text.config(state=tk.DISABLED)

    def send_message(self):
        user_input = self.user_input_text.get("1.0", "end-1c").strip()
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, "You: " + user_input + "\n")
        self.chat_text.config(state=tk.DISABLED)

        if user_input.lower() == 'quit':
            self.root.destroy()
        else:
            if user_input.lower() == 'remove image':
                self.remove_image()
            else:
                best_match = self.find_best_match(user_input)

                if best_match:
                    answer = self.get_answer_for_question(best_match)
                    if answer:
                        self.add_bot_message(answer)
                    else:
                        self.add_bot_message("I have a similar question, but I don't have an answer yet.")
                        self.last_question = best_match
                        self.user_input_text.config(state=tk.NORMAL)
                        self.root.after(200, self.provide_correction)
                else:
                    if user_input.startswith("image:"):
                        search_query = user_input[6:].strip()
                        image_url = self.get_unsplash_image_url(search_query)
                        if image_url:
                            self.add_bot_message("Here is an image for your search:")
                            self.add_image_to_chat(image_url)
                        else:
                            self.add_bot_message("Sorry, I couldn't find an image for your search.")
                    else:
                        self.add_bot_message("I don't know the answer. Can you please teach me?")
                        self.last_question = user_input
                        self.user_input_text.config(state=tk.NORMAL)
                        self.root.after(200, self.provide_correction)

    def get_unsplash_image_url(self, query: str) -> str | None:
        access_key = "Q0D2l5K0MgW0mBVpQuDmcLGlyxF23jXA-h9gBORrXRk"
        url = f"https://api.unsplash.com/photos/random?query={query}&client_id={access_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data["urls"]["regular"]
        return None

    def add_image_to_chat(self, image_url: str):
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, f"Bot: [Image: {image_url}] \n")
        self.chat_text.config(state=tk.DISABLED)

    def get_image(self):
        user_input = self.user_input_text.get("1.0", "end-1c").strip()
        if user_input.startswith("image:"):
            search_query = user_input[6:].strip()
            image_url = self.get_unsplash_image_url(search_query)
            if image_url:
                image = self.load_image_from_url(image_url)
                self.show_image(image)
                self.add_bot_message("Here is an image for your search:")
            else:
                self.add_bot_message("Sorry, I couldn't find an image for your search.")
        else:
            self.add_bot_message("Please provide a valid image search query.")

    def load_image_from_url(self, url: str) -> Image.Image:
        response = requests.get(url)
        if response.status_code == 200:
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))
            return image
        raise ValueError("Failed to load image from URL")
    
    def show_image(self, image: Image.Image):
        if self.image_label:
            self.image_label.destroy()  # Remove the previous image label

        # Resize the image to a smaller size
        image = image.resize((300, 300), Image.LANCZOS)
        photo = ImageTk.PhotoImage(image)

        self.image_label = tk.Label(self.root, image=photo)
        self.image_label.image = photo  # Keep a reference to the PhotoImage

        # Place the image label in the center of the window
        self.image_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    def remove_image(self):
        if self.image_label:
            self.image_label.destroy()
            self.add_bot_message("Image removed.")
        else:
            self.add_bot_message("No image to remove.")

# ... (rest of the code)

##if __name__ == "__main__":
    #ChatBotApp()

def start_chatbot_app():
    root = tk.Tk()
    chatbot_app = ChatBotApp(root)
    root.mainloop()

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == "__main__":
    # Start the ChatBotApp in a separate thread
    chatbot_thread = Thread(target=start_chatbot_app)
    chatbot_thread.start()

    # Run the Flask app
    app.run(debug=True)

from datetime import datetime
import pickle
import os

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.camera import Camera
from kivy.core.window import Window

user_db = {}
temporary_fingerprint_data = None
DB_FILE = 'user_db.pkl'

class FingerprintApp(App):
    def build(self):
        self.load_user_db()

        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.title_label = Label(text="Fingerprint Authentication System", size_hint=(1, 0.1))
        self.layout.add_widget(self.title_label)

        self.register_button = Button(text="Register User", size_hint=(1, 0.1))
        self.register_button.bind(on_press=self.register_user)
        self.layout.add_widget(self.register_button)

        self.verify_button = Button(text="Verify Fingerprint", size_hint=(1, 0.1))
        self.verify_button.bind(on_press=self.verify_fingerprint)
        self.layout.add_widget(self.verify_button)

        return self.layout

    def load_user_db(self):
        global user_db
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'rb') as f:
                user_db = pickle.load(f)

    def save_user_db(self):
        with open(DB_FILE, 'wb') as f:
            pickle.dump(user_db, f)

    def save_user_details(self, name, phone, reg_no, photo_path, fingerprint_data):
        if reg_no in user_db:
            print("Fingerprint already registered!")
            return False
        user_db[reg_no] = {
            'name': name,
            'phone': phone,
            'photo': photo_path,
            'fingerprint': fingerprint_data,
            'verified': False,
            'registration_timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        print("User details saved successfully.")
        self.send_registration_message(name, reg_no, user_db[reg_no]['registration_timestamp'])
        self.save_user_db()
        return True

    def send_registration_message(self, name, reg_no, timestamp):
        message = f"User {name} with registration number {reg_no} registered successfully at {timestamp}."
        print("REGISTRATION SUCCESS MESSAGE:")
        print(message)

    def capture_fingerprint(self, reg_no):
        fingerprint_data = f"fingerprint_{reg_no}_data"
        return fingerprint_data

    def send_alert_to_admin(self, name, reg_no, time, registration_timestamp=None):
        if registration_timestamp:
            message = f"ALERT: User {name} with registration number {reg_no} tried to verify fingerprint again at {time}. Registration timestamp: {registration_timestamp}"
        else:
            message = f"ALERT: Unregistered fingerprint attempted! Name: {name}, Registration Number: {reg_no}, Time: {time}"

        print("ALERT SENT TO ADMIN:")
        print(message)

        screen_width = Window.width
        font_size = 12

        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        message_label = Label(text=message, size_hint=(1, None), height=100, font_size=font_size)
        popup_layout.add_widget(message_label)

        close_button = Button(text="Close", size_hint=(1, None), height=50)
        close_button.bind(on_press=self.close_alert_popup)
        popup_layout.add_widget(close_button)

        width_ratio = 0.8
        height_ratio = 0.4

        self.popup = Popup(
            title="Admin Alert",
            content=popup_layout,
            size_hint=(width_ratio, height_ratio),
            auto_dismiss=True
        )
        self.popup.open()

    def close_alert_popup(self, instance):
        if hasattr(self, 'popup') and self.popup:
            self.popup.dismiss()

    def check_fingerprint(self, fingerprint_data, reg_no):
        if reg_no not in user_db:
            print("Fingerprint does not exist in database!")
            self.send_alert_to_admin("Unknown User", reg_no, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            return False

        if user_db[reg_no]['verified']:
            print("ALERT: User has already verified their fingerprint.")
            self.send_alert_to_admin(user_db[reg_no]['name'], reg_no, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_db[reg_no]['registration_timestamp'])
            return False

        if fingerprint_data == user_db[reg_no]['fingerprint']:
            print("Fingerprint matched (registration check).")
            user_db[reg_no]['verified'] = True
            self.save_user_db()
            print(f"Fingerprint verified successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return True
        else:
            print("Fingerprint does not match in registration check!")
            self.send_alert_to_admin(user_db[reg_no]['name'], reg_no, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            return False

    def open_camera(self, name):
        self.camera_layout = BoxLayout(orientation='vertical')
        self.camera = Camera(play=True)
        self.camera.resolution = (640, 480)
        self.camera_layout.add_widget(self.camera)

        self.capture_button = Button(text="Capture Photo", size_hint=(1, 0.2))
        self.capture_button.bind(on_press=lambda x: self.capture_photo(name))
        self.camera_layout.add_widget(self.capture_button)

        self.camera_popup = Popup(title="Capture Photo", content=self.camera_layout, size_hint=(0.9, 0.9))
        self.camera_popup.open()

    def capture_photo(self, name):
        photo_path = f"{name}_photo.png"
        texture = self.camera.texture
        if texture:
            texture.save(photo_path)
            print(f"Photo of {name} saved as {photo_path}.")
        else:
            print("Failed to capture photo.")
        self.camera.play = False
        self.camera_popup.dismiss()
        self.photo_path = photo_path

    def register_user(self, instance):
        self.popup_register = BoxLayout(orientation='vertical', spacing=10)

        self.name_input = TextInput(hint_text="Enter your name", size_hint=(1, None), height=40)
        self.phone_input = TextInput(hint_text="Enter your phone number", size_hint=(1, None), height=40)
        self.reg_no_input = TextInput(hint_text="Enter your registration number", size_hint=(1, None), height=40)

        self.popup_register.add_widget(self.name_input)
        self.popup_register.add_widget(self.phone_input)
        self.popup_register.add_widget(self.reg_no_input)

        self.capture_button = Button(text="Open Camera to Register", size_hint=(1, None), height=50)
        self.capture_button.bind(on_press=self.capture_and_register)

        self.popup_register.add_widget(self.capture_button)

        self.popup = Popup(title="Register User", content=self.popup_register, size_hint=(0.8, 0.7))
        self.popup.open()

    def capture_and_register(self, instance):
        name = self.name_input.text
        phone = self.phone_input.text
        reg_no = self.reg_no_input.text

        if reg_no in user_db:
            self.show_popup_message("Error", "This registration number already exists. Please use another.")
            return

        self.popup.dismiss()
        self.open_camera(name)

        def after_photo_capture(instance):
            fingerprint_data = self.capture_fingerprint(reg_no)
            if self.save_user_details(name, phone, reg_no, self.photo_path, fingerprint_data):
                global temporary_fingerprint_data
                temporary_fingerprint_data = fingerprint_data
                self.show_popup_message("Success", f"User {name} registered successfully.")

        self.capture_button.bind(on_press=after_photo_capture)

    def verify_fingerprint(self, instance):
        self.popup_verify = BoxLayout(orientation='vertical', spacing=10)

        self.reg_no_verify_input = TextInput(hint_text="Enter registration number for verification", size_hint=(1, None), height=40)
        self.popup_verify.add_widget(self.reg_no_verify_input)

        self.verify_button = Button(text="Verify Fingerprint", size_hint=(1, None), height=50)
        self.verify_button.bind(on_press=self.perform_fingerprint_verification)
        self.popup_verify.add_widget(self.verify_button)

        self.popup_verify_message = Label(size_hint=(1, None), height=30)
        self.popup_verify.add_widget(self.popup_verify_message)

        self.popup = Popup(title="Verify Fingerprint", content=self.popup_verify, size_hint=(0.8, 0.7))
        self.popup.open()

    def perform_fingerprint_verification(self, instance):
        reg_no = self.reg_no_verify_input.text
        fingerprint_data = self.capture_fingerprint(reg_no)

        if self.check_fingerprint(fingerprint_data, reg_no):
            self.show_popup_message("Access Granted", "Fingerprint verified successfully!")
        else:
            self.show_popup_message("Access Denied", "Fingerprint verification failed.")

    def show_popup_message(self, title, message):
        popup_message = BoxLayout(orientation='vertical', padding=10)
        popup_message.add_widget(Label(text=message))
        close_button = Button(text="Close", size_hint=(1, None), height=50)
        close_button.bind(on_press=lambda x: self.popup.dismiss())
        popup_message.add_widget(close_button)

        self.popup = Popup(title=title, content=popup_message, size_hint=(0.7, 0.3))
        self.popup.open()

if __name__ == '__main__':
    FingerprintApp().run()

import json
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from Cryptodome.Cipher import Blowfish
from Cryptodome.Util.Padding import unpad


class VaultApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('KivyVault - CustomTkinter')
        self.geometry('520x420')
        self.resizable(False, False)

        self.show_password = False
        self.decrypted_password = ''

        self._create_widgets()

    def _create_widgets(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(self, text='KivyVault', font=ctk.CTkFont(size=28, weight='bold'))
        title.grid(row=0, column=0, pady=(20, 5), padx=24)

        username_frame = ctk.CTkFrame(self)
        username_frame.grid(row=1, column=0, sticky='nsew', padx=24, pady=5)
        username_frame.grid_columnconfigure(1, weight=1)

        username_label = ctk.CTkLabel(username_frame, text='Username', font=ctk.CTkFont(size=18))
        username_label.grid(row=0, column=0, sticky='w', padx=(10, 8), pady=12)

        self.username_entry = ctk.CTkEntry(username_frame, placeholder_text='Enter username', width=320)
        self.username_entry.grid(row=0, column=1, sticky='ew', padx=(0, 10), pady=12)

        self.status_label = ctk.CTkLabel(username_frame, text='', font=ctk.CTkFont(size=12), text_color='#e74c3c', anchor='w')
        self.status_label.grid(row=1, column=0, columnspan=2, sticky='w', padx=(10, 10), pady=(0, 8))

        password_frame = ctk.CTkFrame(self)
        password_frame.grid(row=2, column=0, sticky='nsew', padx=24, pady=5)
        password_frame.grid_columnconfigure(1, weight=1)

        password_label = ctk.CTkLabel(password_frame, text='Password', font=ctk.CTkFont(size=18))
        password_label.grid(row=0, column=0, sticky='w', padx=(10, 8), pady=12)

        self.password_display = ctk.CTkLabel(password_frame, text='', font=ctk.CTkFont(size=18), width=320, anchor='w')
        self.password_display.grid(row=0, column=1, sticky='ew', padx=(0, 10), pady=12)

        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=3, column=0, sticky='nsew', padx=24, pady=10)
        button_frame.grid_columnconfigure((0, 1, 2), weight=1)

        submit_button = ctk.CTkButton(button_frame, text='Submit', command=self.decrypt_password)
        submit_button.grid(row=0, column=0, padx=10, pady=10, sticky='ew')

        copy_button = ctk.CTkButton(button_frame, text='Copy', command=self.copy_to_clipboard)
        copy_button.grid(row=0, column=1, padx=10, pady=10, sticky='ew')

        toggle_button = ctk.CTkButton(button_frame, text='Show/Hide', command=self.toggle_password)
        toggle_button.grid(row=0, column=2, padx=10, pady=10, sticky='ew')

        clear_button = ctk.CTkButton(button_frame, text='Clear', command=self.clear_password)
        clear_button.grid(row=1, column=0, columnspan=3, padx=10, pady=(0, 10), sticky='ew')

        footer = ctk.CTkLabel(self, text='Enter a username and press Submit to decrypt the stored password.', font=ctk.CTkFont(size=12), text_color='#888888')
        footer.grid(row=4, column=0, pady=(0, 20), padx=24)

    def decrypt_password(self):
        username = self.username_entry.get().strip()
        self.status_label.configure(text='')

        if not username:
            self.status_label.configure(text='Please enter a username.')
            return

        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            messagebox.showerror('File Not Found', 'Could not find data.json.')
            return
        except json.JSONDecodeError:
            messagebox.showerror('Invalid Data', 'data.json is not valid JSON.')
            return

        if username not in data:
            self.status_label.configure(text='Invalid username')
            return

        try:
            self.decrypted_password = self._decrypt_password(data[username])
        except Exception as exc:
            messagebox.showerror('Decryption Error', f'Unable to decrypt password: {exc}')
            return

        self.show_password = False
        self._update_password_display()
        self.username_entry.delete(0, tk.END)

    def _decrypt_password(self, encrypted_password: str) -> str:
        secret_key = b'bitroid'
        bf = Blowfish.new(secret_key, Blowfish.MODE_ECB)
        cipher_text = bytes.fromhex(encrypted_password)
        decrypted_text = bf.decrypt(cipher_text)
        return unpad(decrypted_text, Blowfish.block_size).decode('utf-8')

    def toggle_password(self):
        if not self.decrypted_password:
            return
        self.show_password = not self.show_password
        self._update_password_display()

    def _update_password_display(self):
        if self.show_password:
            display_text = self.decrypted_password
        else:
            display_text = '*' * len(self.decrypted_password)
        self.password_display.configure(text=display_text)

    def copy_to_clipboard(self):
        if not self.decrypted_password:
            messagebox.showinfo('No Password', 'Decrypt a password first.')
            return
        self.clipboard_clear()
        self.clipboard_append(self.decrypted_password)

    def clear_password(self):
        self.decrypted_password = ''
        self.show_password = False
        self.password_display.configure(text='')
        self.status_label.configure(text='')


if __name__ == '__main__':
    ctk.set_appearance_mode('System')
    ctk.set_default_color_theme('blue')
    app = VaultApp()
    app.mainloop()

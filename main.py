import json
from tkinter import messagebox
import customtkinter as ctk
from Cryptodome.Cipher import Blowfish
from Cryptodome.Util.Padding import unpad

# Palette
APP_BG = '#eef2f8'
CARD_BG = '#ffffff'
FIELD_BG = '#ffffff'
OUTPUT_BG = '#f6f8fc'
BORDER = '#d6dde8'
BLUE = '#2563eb'
BLUE_HOVER = '#1d4ed8'
BLUE_TINT = '#e8effd'
TEXT = '#1f2937'
MUTED = '#6b7280'
ERROR = '#dc2626'
SUCCESS = '#16a34a'

FONT_FAMILY = 'Segoe UI'
FIELD_HEIGHT = 44


class VaultApp(ctk.CTk):
    def __init__(self):
        super().__init__(fg_color=APP_BG)
        self.title('KivyVault')
        self.geometry('460x520')
        self.resizable(False, False)

        self.show_password = False
        self.decrypted_password = ''
        self._status_job = None

        self._create_widgets()
        self._update_password_display()

    def _font(self, size, weight='normal', family=FONT_FAMILY):
        return ctk.CTkFont(family=family, size=size, weight=weight)

    def _create_widgets(self):
        card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=16, border_width=1, border_color=BORDER)
        card.pack(fill='both', expand=True, padx=24, pady=24)

        body = ctk.CTkFrame(card, fg_color='transparent')
        body.pack(fill='both', expand=True, padx=28, pady=24)

        # Header
        header = ctk.CTkFrame(body, fg_color='transparent')
        header.pack(fill='x')

        badge = ctk.CTkLabel(header, text='KV', width=44, height=44, corner_radius=12,
                             fg_color=BLUE, text_color='#ffffff', font=self._font(16, 'bold'))
        badge.pack(side='left')

        titles = ctk.CTkFrame(header, fg_color='transparent')
        titles.pack(side='left', padx=(12, 0))
        ctk.CTkLabel(titles, text='KivyVault', text_color=TEXT, font=self._font(22, 'bold'),
                     height=26, anchor='w').pack(anchor='w')
        ctk.CTkLabel(titles, text='Decrypt your stored passwords', text_color=MUTED,
                     font=self._font(13), height=18, anchor='w').pack(anchor='w')

        ctk.CTkFrame(body, height=1, fg_color=BORDER).pack(fill='x', pady=(20, 18))

        # Username
        self._field_label(body, 'USERNAME')
        self.username_entry = ctk.CTkComboBox(
            body, values=self._load_keys(), height=FIELD_HEIGHT, corner_radius=10,
            font=self._font(15), dropdown_font=self._font(14),
            fg_color=FIELD_BG, border_color=BORDER, border_width=1, text_color=TEXT,
            button_color=BLUE_TINT, button_hover_color='#d6e2fb',
            dropdown_fg_color=CARD_BG, dropdown_hover_color=BLUE_TINT, dropdown_text_color=TEXT,
        )
        self.username_entry.set('')
        self.username_entry.pack(fill='x')

        decrypt_button = ctk.CTkButton(
            body, text='Decrypt', command=self.decrypt_password, height=FIELD_HEIGHT,
            corner_radius=10, fg_color=BLUE, hover_color=BLUE_HOVER, text_color='#ffffff',
            font=self._font(15, 'bold'),
        )
        decrypt_button.pack(fill='x', pady=(14, 22))

        # Password output
        self._field_label(body, 'PASSWORD')
        output = ctk.CTkFrame(body, fg_color=OUTPUT_BG, corner_radius=10, border_width=1,
                              border_color=BORDER, height=FIELD_HEIGHT)
        output.pack(fill='x')
        output.pack_propagate(False)

        ghost = dict(width=58, height=30, corner_radius=8, fg_color='transparent',
                     hover_color=BLUE_TINT, text_color=BLUE, font=self._font(13, 'bold'))
        self.copy_button = ctk.CTkButton(output, text='Copy', command=self.copy_to_clipboard, **ghost)
        self.copy_button.pack(side='right', padx=(0, 7))
        self.toggle_button = ctk.CTkButton(output, text='Show', command=self.toggle_password, **ghost)
        self.toggle_button.pack(side='right', padx=(0, 2))

        self.password_display = ctk.CTkLabel(output, text='', anchor='w', fg_color='transparent',
                                             font=self._font(15, family='Consolas'))
        self.password_display.pack(side='left', fill='x', expand=True, padx=(14, 6), pady=6)

        self.status_label = ctk.CTkLabel(body, text='', height=22, anchor='w', font=self._font(12))
        self.status_label.pack(fill='x', pady=(6, 0))

        # Footer
        footer = ctk.CTkFrame(body, fg_color='transparent')
        footer.pack(fill='x', side='bottom')
        ctk.CTkLabel(footer, text='Select a username, then Decrypt.', text_color=MUTED,
                     font=self._font(12)).pack(side='left')
        ctk.CTkButton(footer, text='Clear', command=self.clear_password, width=70, height=30,
                      corner_radius=8, fg_color='transparent', hover_color='#f1f3f7',
                      border_width=1, border_color=BORDER, text_color=MUTED,
                      font=self._font(13)).pack(side='right')

    def _field_label(self, parent, text):
        ctk.CTkLabel(parent, text=text, text_color=MUTED, font=self._font(11, 'bold'),
                     height=16, anchor='w').pack(fill='x', pady=(0, 6))

    def _set_status(self, text, color=MUTED, timeout_ms=None):
        if self._status_job:
            self.after_cancel(self._status_job)
            self._status_job = None
        self.status_label.configure(text=text, text_color=color)
        if timeout_ms:
            self._status_job = self.after(timeout_ms, lambda: self._set_status(''))

    def decrypt_password(self):
        username = self.username_entry.get().strip()
        self._set_status('')

        if not username:
            self._set_status('Please select a username.', ERROR)
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

        self.username_entry.configure(values=sorted(data))

        if username not in data:
            self._set_status(f'No entry found for "{username}".', ERROR)
            return

        try:
            self.decrypted_password = self._decrypt_password(data[username])
        except Exception as exc:
            messagebox.showerror('Decryption Error', f'Unable to decrypt password: {exc}')
            return

        self.show_password = False
        self._update_password_display()
        self._set_status(f'Decrypted password for {username}.', SUCCESS, 3000)
        self.username_entry.set('')

    @staticmethod
    def _load_keys():
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                return sorted(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            return []

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
        if not self.decrypted_password:
            self.password_display.configure(text='Nothing decrypted yet', text_color=MUTED,
                                            font=self._font(14))
            self.toggle_button.configure(text='Show')
            return
        text = self.decrypted_password if self.show_password else '•' * len(self.decrypted_password)
        self.password_display.configure(text=text, text_color=TEXT,
                                        font=self._font(15, family='Consolas'))
        self.toggle_button.configure(text='Hide' if self.show_password else 'Show')

    def copy_to_clipboard(self):
        if not self.decrypted_password:
            self._set_status('Decrypt a password first.', ERROR, 3000)
            return
        self.clipboard_clear()
        self.clipboard_append(self.decrypted_password)
        self.copy_button.configure(text='Copied')
        self.after(1500, lambda: self.copy_button.configure(text='Copy'))
        self._set_status('Password copied to clipboard.', SUCCESS, 3000)

    def clear_password(self):
        self.decrypted_password = ''
        self.show_password = False
        self.username_entry.set('')
        self._update_password_display()
        self._set_status('')


if __name__ == '__main__':
    ctk.set_appearance_mode('light')
    app = VaultApp()
    app.mainloop()

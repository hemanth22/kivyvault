import json
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from Cryptodome.Cipher import Blowfish
from Cryptodome.Util.Padding import pad, unpad

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
CLIPBOARD_CLEAR_MS = 60_000  # wipe copied secrets from the clipboard after 60s

SECRET_KEY = b'bitroid'

MODE_VAULT = 'Vault'
MODE_TOOLS = 'Crypto Tools'
HINTS = {
    MODE_VAULT: 'Select a username, then Decrypt.',
    MODE_TOOLS: 'Encrypt, decrypt or round-trip test a value.',
}


def _cipher():
    return Blowfish.new(SECRET_KEY, Blowfish.MODE_ECB)


def encrypt_password(password: str) -> str:
    padded = pad(password.encode('utf-8'), Blowfish.block_size)
    return _cipher().encrypt(padded).hex()


def decrypt_password(encrypted_password: str) -> str:
    cipher_text = bytes.fromhex(encrypted_password)
    decrypted = _cipher().decrypt(cipher_text)
    return unpad(decrypted, Blowfish.block_size).decode('utf-8')


class VaultApp(ctk.CTk):
    def __init__(self):
        super().__init__(fg_color=APP_BG)
        self.title('KivyVault')
        self.geometry('460x600')
        self.resizable(False, False)

        self.show_password = False
        self.decrypted_password = ''
        self._status_job = None
        self._clipboard_job = None
        self._clipboard_value = None
        self.mode = MODE_VAULT
        self.protocol('WM_DELETE_WINDOW', self._on_close)

        self._create_widgets()
        self._update_password_display()

    def _font(self, size, weight='normal', family=FONT_FAMILY):
        return ctk.CTkFont(family=family, size=size, weight=weight)

    # ------------------------------------------------------------------ layout

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

        # Mode switcher
        self.mode_switch = ctk.CTkSegmentedButton(
            body, values=[MODE_VAULT, MODE_TOOLS], command=self._switch_mode, height=34,
            corner_radius=10, font=self._font(13, 'bold'),
            fg_color=OUTPUT_BG, unselected_color=OUTPUT_BG, unselected_hover_color=BLUE_TINT,
            selected_color=BLUE, selected_hover_color=BLUE_HOVER, text_color=TEXT,
        )
        self.mode_switch.set(MODE_VAULT)
        self.mode_switch.pack(fill='x', pady=(18, 18))

        # Footer (packed before content so it stays pinned to the bottom)
        footer = ctk.CTkFrame(body, fg_color='transparent')
        footer.pack(fill='x', side='bottom')
        self.hint_label = ctk.CTkLabel(footer, text=HINTS[MODE_VAULT], text_color=MUTED,
                                       font=self._font(12))
        self.hint_label.pack(side='left')
        ctk.CTkButton(footer, text='Clear', command=self.clear, width=70, height=30,
                      corner_radius=8, fg_color='transparent', hover_color='#f1f3f7',
                      border_width=1, border_color=BORDER, text_color=MUTED,
                      font=self._font(13)).pack(side='right')

        # Content area
        content = ctk.CTkFrame(body, fg_color='transparent')
        content.pack(fill='both', expand=True)

        self.vault_frame = ctk.CTkFrame(content, fg_color='transparent')
        self.tools_frame = ctk.CTkFrame(content, fg_color='transparent')
        self._build_vault(self.vault_frame)
        self._build_tools(self.tools_frame)
        self.vault_frame.pack(fill='both', expand=True)

        self.status_label = ctk.CTkLabel(content, text='', height=22, anchor='w', font=self._font(12))
        self.status_label.pack(fill='x', pady=(6, 0), side='bottom')

    def _ghost_button(self, parent, text, command):
        return ctk.CTkButton(parent, text=text, command=command, width=58, height=30,
                             corner_radius=8, fg_color='transparent', hover_color=BLUE_TINT,
                             text_color=BLUE, font=self._font(13, 'bold'))

    def _build_vault(self, parent):
        self._field_label(parent, 'USERNAME')
        self.username_entry = ctk.CTkComboBox(
            parent, values=self._load_keys(), height=FIELD_HEIGHT, corner_radius=10,
            font=self._font(15), dropdown_font=self._font(14),
            fg_color=FIELD_BG, border_color=BORDER, border_width=1, text_color=TEXT,
            button_color=BLUE_TINT, button_hover_color='#d6e2fb',
            dropdown_fg_color=CARD_BG, dropdown_hover_color=BLUE_TINT, dropdown_text_color=TEXT,
        )
        self.username_entry.set('')
        self.username_entry.pack(fill='x')

        ctk.CTkButton(
            parent, text='Decrypt', command=self.decrypt_selected, height=FIELD_HEIGHT,
            corner_radius=10, fg_color=BLUE, hover_color=BLUE_HOVER, text_color='#ffffff',
            font=self._font(15, 'bold'),
        ).pack(fill='x', pady=(14, 22))

        self._field_label(parent, 'PASSWORD')
        output = ctk.CTkFrame(parent, fg_color=OUTPUT_BG, corner_radius=10, border_width=1,
                              border_color=BORDER, height=FIELD_HEIGHT)
        output.pack(fill='x')
        output.pack_propagate(False)

        self.copy_button = self._ghost_button(output, 'Copy', self.copy_to_clipboard)
        self.copy_button.pack(side='right', padx=(0, 7))
        self.toggle_button = self._ghost_button(output, 'Show', self.toggle_password)
        self.toggle_button.pack(side='right', padx=(0, 2))

        self.password_display = ctk.CTkLabel(output, text='', anchor='w', fg_color='transparent',
                                             font=self._font(15, family='Consolas'))
        self.password_display.pack(side='left', fill='x', expand=True, padx=(14, 6), pady=6)

    def _build_tools(self, parent):
        self._field_label(parent, 'INPUT  (plain text or hex cipher text)')
        self.tool_input = ctk.CTkEntry(
            parent, height=FIELD_HEIGHT, corner_radius=10, font=self._font(15, family='Consolas'),
            fg_color=FIELD_BG, border_color=BORDER, border_width=1, text_color=TEXT,
            placeholder_text='Enter a value…', placeholder_text_color=MUTED,
        )
        self.tool_input.pack(fill='x')
        self.tool_input.bind('<Return>', lambda _e: self.tool_encrypt())

        actions = ctk.CTkFrame(parent, fg_color='transparent')
        actions.pack(fill='x', pady=(14, 22))
        actions.grid_columnconfigure((0, 1, 2), weight=1, uniform='actions')

        primary = dict(height=FIELD_HEIGHT, corner_radius=10, fg_color=BLUE, hover_color=BLUE_HOVER,
                       text_color='#ffffff', font=self._font(14, 'bold'))
        secondary = dict(height=FIELD_HEIGHT, corner_radius=10, fg_color=BLUE_TINT,
                         hover_color='#d6e2fb', text_color=BLUE, font=self._font(14, 'bold'))
        ctk.CTkButton(actions, text='Encrypt', command=self.tool_encrypt, **primary) \
            .grid(row=0, column=0, sticky='ew', padx=(0, 5))
        ctk.CTkButton(actions, text='Decrypt', command=self.tool_decrypt, **primary) \
            .grid(row=0, column=1, sticky='ew', padx=5)
        ctk.CTkButton(actions, text='Test', command=self.tool_test, **secondary) \
            .grid(row=0, column=2, sticky='ew', padx=(5, 0))

        self._field_label(parent, 'RESULT')
        output = ctk.CTkFrame(parent, fg_color=OUTPUT_BG, corner_radius=10, border_width=1,
                              border_color=BORDER, height=FIELD_HEIGHT)
        output.pack(fill='x')
        output.pack_propagate(False)

        self.tool_copy_button = self._ghost_button(output, 'Copy', self.copy_tool_result)
        self.tool_copy_button.pack(side='right', padx=(0, 7))

        # Read-only entry so long hex strings can be scrolled and selected.
        self.tool_output = ctk.CTkEntry(output, fg_color=OUTPUT_BG, border_width=0, text_color=TEXT,
                                        font=self._font(14, family='Consolas'))
        self.tool_output.pack(side='left', fill='x', expand=True, padx=(8, 6), pady=6)
        self._set_tool_output('')

    def _field_label(self, parent, text):
        ctk.CTkLabel(parent, text=text, text_color=MUTED, font=self._font(11, 'bold'),
                     height=16, anchor='w').pack(fill='x', pady=(0, 6))

    def _switch_mode(self, mode):
        self.mode = mode
        self.vault_frame.pack_forget()
        self.tools_frame.pack_forget()
        frame = self.vault_frame if mode == MODE_VAULT else self.tools_frame
        frame.pack(fill='both', expand=True)
        self.hint_label.configure(text=HINTS[mode])
        self._set_status('')

    def _set_status(self, text, color=MUTED, timeout_ms=None):
        if self._status_job:
            self.after_cancel(self._status_job)
            self._status_job = None
        self.status_label.configure(text=text, text_color=color)
        if timeout_ms:
            self._status_job = self.after(timeout_ms, lambda: self._set_status(''))

    # ------------------------------------------------------------------- vault

    def decrypt_selected(self):
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
            self.decrypted_password = decrypt_password(data[username])
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
        self._copy(self.decrypted_password, self.copy_button)
        self._set_status('Password copied — clipboard clears in 60s.', SUCCESS, 3000)

    # ------------------------------------------------------------ crypto tools

    def _tool_value(self):
        value = self.tool_input.get()
        if not value:
            self._set_status('Enter a value first.', ERROR)
        return value

    def _set_tool_output(self, text):
        self.tool_output.configure(state='normal')
        self.tool_output.delete(0, 'end')
        self.tool_output.insert(0, text)
        self.tool_output.configure(state='readonly')

    def tool_encrypt(self):
        value = self._tool_value()
        if not value:
            return
        self._set_tool_output(encrypt_password(value))
        self._set_status('Encrypted.', SUCCESS, 3000)

    def tool_decrypt(self):
        value = self._tool_value().strip()
        if not value:
            return
        try:
            result = decrypt_password(value)
        except ValueError as exc:
            self._set_tool_output('')
            self._set_status(f'Decryption failed: {exc}', ERROR)
            return
        except UnicodeDecodeError:
            self._set_tool_output('')
            self._set_status('Decryption failed: result is not valid UTF-8.', ERROR)
            return
        self._set_tool_output(result)
        self._set_status('Decrypted.', SUCCESS, 3000)

    def tool_test(self):
        """Round-trip check: encrypt the input, decrypt it back and compare."""
        value = self._tool_value()
        if not value:
            return
        try:
            cipher_text = encrypt_password(value)
            round_trip = decrypt_password(cipher_text)
        except Exception as exc:
            self._set_tool_output('')
            self._set_status(f'Test failed: {exc}', ERROR)
            return
        self._set_tool_output(cipher_text)
        if round_trip == value:
            self._set_status('Test passed: encrypt → decrypt round-trip matches.', SUCCESS)
        else:
            self._set_status('Test failed: decrypted value does not match input.', ERROR)

    def copy_tool_result(self):
        result = self.tool_output.get()
        if not result:
            self._set_status('Nothing to copy yet.', ERROR, 3000)
            return
        self._copy(result, self.tool_copy_button)
        self._set_status('Result copied to clipboard.', SUCCESS, 3000)

    # ------------------------------------------------------------------ shared

    def _copy(self, text, button):
        self.clipboard_clear()
        self.clipboard_append(text)
        button.configure(text='Copied')
        self.after(1500, lambda: button.configure(text='Copy'))
        self._schedule_clipboard_clear(text)

    def _schedule_clipboard_clear(self, text):
        """Wipe the copied value from the clipboard after CLIPBOARD_CLEAR_MS."""
        if self._clipboard_job is not None:
            self.after_cancel(self._clipboard_job)
        self._clipboard_value = text
        self._clipboard_job = self.after(CLIPBOARD_CLEAR_MS, self._clear_clipboard)

    def _clear_clipboard(self):
        """Clear the clipboard, but only if it still holds the value we copied."""
        self._clipboard_job = None
        if self._clipboard_value is None:
            return
        try:
            current = self.clipboard_get()
        except tk.TclError:
            current = None
        if current == self._clipboard_value:
            self.clipboard_clear()
            self.clipboard_append('')
            self.update()  # make sure the OS clipboard is updated
            self._set_status('Clipboard cleared.', MUTED, 3000)
        self._clipboard_value = None

    def _on_close(self):
        if self._clipboard_job is not None:
            self.after_cancel(self._clipboard_job)
            self._clear_clipboard()
        self.destroy()

    def clear(self):
        if self.mode == MODE_TOOLS:
            self.tool_input.delete(0, 'end')
            self._set_tool_output('')
        else:
            self.decrypted_password = ''
            self.show_password = False
            self.username_entry.set('')
            self._update_password_display()
        self._set_status('')


if __name__ == '__main__':
    ctk.set_appearance_mode('light')
    app = VaultApp()
    app.mainloop()

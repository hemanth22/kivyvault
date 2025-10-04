import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.core.clipboard import Clipboard
from kivy.lang import Builder
import json
from Cryptodome.Cipher import Blowfish
from Cryptodome.Util.Padding import pad, unpad
from base64 import b64encode, b64decode
from kivy.properties import BooleanProperty



Builder.load_file('hike.kv')

class MyGridLayout(Widget):

    oldsalary = ObjectProperty()
    show_password = BooleanProperty(False)


    def simpleiint(self):
        jdata = '{"hemanth": "0d4ba01661c2de80","priyadharshini": "20bc3aa6fbf6b2c0e9f622c36f5a20db"}'
        data = json.loads(jdata)

        secret_key = b'bitroid'
        bf = Blowfish.new(secret_key, Blowfish.MODE_ECB)

        def decrypt_password(encrypted_password: str):
            cipher_text = bytes.fromhex(encrypted_password)
            decrypted_text = bf.decrypt(cipher_text)
            unpadded_text = unpad(decrypted_text, Blowfish.block_size).decode('utf-8')
            return unpadded_text
        

        oldsalary = self.oldsalary.text
        #result = data.get(oldsalary)
        result = decrypt_password(data[oldsalary])
        #newsalary = self.newsalary.text
        #result_percent = round((((int(newsalary)-int(oldsalary)) / int(oldsalary)) * 100),2)
        #print('Your hike {0}%'.format(result_percent))
        self.decrypted_password = result
        #self.ids.name_label2.text = f'{result}'
        self.ids.name_label2.text = result if self.show_password else '*' * len(result)
        self.ids.oldsalary.text = ''

    def toggle_password(self):
        self.show_password = not self.show_password
        self.ids.name_label2.text = self.decrypted_password if self.show_password else '*' * len(self.decrypted_password)

    def copy_to_clipboard(self, instance):
        text_to_copy = self.decrypted_password
        Clipboard.copy(text_to_copy)

class hikeApp(App):
    def build(self):
        return MyGridLayout()

if __name__ == '__main__':
    hikeApp().run()

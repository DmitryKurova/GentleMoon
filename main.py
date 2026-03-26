from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.label import Label as RecycleLabel
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.switch import Switch
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.metrics import dp
import sqlite3
import json
import os
import hashlib
import random
import string
from datetime import datetime

DB_PATH = 'gentlemoon.db'
Window.size = (400, 700)

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            display_name TEXT,
            avatar TEXT,
            public_key TEXT,
            theme TEXT DEFAULT 'light'
        )''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            description TEXT,
            creator_id INTEGER,
            is_public INTEGER DEFAULT 1,
            join_key TEXT,
            avatar TEXT,
            created_at TEXT,
            FOREIGN KEY(creator_id) REFERENCES users(id)
        )''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS group_members (
            group_id INTEGER,
            user_id INTEGER,
            role TEXT DEFAULT 'member',
            joined_at TEXT,
            PRIMARY KEY (group_id, user_id),
            FOREIGN KEY(group_id) REFERENCES groups(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER,
            sender_id INTEGER,
            content TEXT,
            created_at TEXT,
            FOREIGN KEY(group_id) REFERENCES groups(id),
            FOREIGN KEY(sender_id) REFERENCES users(id)
        )''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS direct_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            recipient_id INTEGER,
            content TEXT,
            created_at TEXT,
            FOREIGN KEY(sender_id) REFERENCES users(id),
            FOREIGN KEY(recipient_id) REFERENCES users(id)
        )''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            content TEXT,
            created_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS reels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            video_path TEXT,
            caption TEXT,
            created_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )'')
        self.conn.commit()
    
    def close(self):
        self.conn.close()

db = Database()

class TOSScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        logo_layout = BoxLayout(size_hint_y=None, height=100)
        try:
            logo = Image(source='gentlemoonlogo.png', size_hint=(None, None), size=(80, 80))
            logo_layout.add_widget(logo)
        except:
            logo_layout.add_widget(Label(text="🌙", font_size=48))
        layout.add_widget(logo_layout)
        
        layout.add_widget(Label(text="GentleMoon", font_size=32, bold=True, size_hint_y=None, height=50))
        
        scroll = ScrollView()
        tos_text = Label(text="""
📜 TERMS OF SERVICE

By using GentleMoon, you agree:

1. You will NOT use this app for:
   • Illegal activities
   • Harassment or abuse
   • Spreading hate speech
   • Sharing illegal content
   • Impersonating others

2. You are responsible for:
   • Your account security
   • All content you post
   • Your interactions with others

3. We are NOT responsible for:
   • Data loss
   • User-generated content
   • Offline interactions
   • Device security

4. Privacy:
   • All data stays on YOUR device
   • No cloud storage
   • You control your keys

5. Changes to terms may occur

By clicking "I AGREE", you accept full responsibility for your use of this app.
        """, text_size=(Window.width - 40, None), size_hint_y=None)
        tos_text.bind(texture_size=tos_text.setter('size'))
        scroll.add_widget(tos_text)
        layout.add_widget(scroll)
        
        agree_btn = Button(text="I AGREE", size_hint_y=None, height=50, background_color=(0.3, 0.5, 0.7, 1))
        agree_btn.bind(on_press=self.accept_tos)
        layout.add_widget(agree_btn)
        
        self.add_widget(layout)
    
    def accept_tos(self, instance):
        with open('tos_accepted.txt', 'w') as f:
            f.write(datetime.now().isoformat())
        self.manager.current = 'login'

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)
        
        layout.add_widget(Label(text="🌙 GentleMoon", font_size=40, bold=True, size_hint_y=None, height=80))
        
        self.username = TextInput(hint_text="Username", multiline=False, size_hint_y=None, height=50)
        layout.add_widget(self.username)
        
        self.password = TextInput(hint_text="Password", password=True, multiline=False, size_hint_y=None, height=50)
        layout.add_widget(self.password)
        
        login_btn = Button(text="Login", size_hint_y=None, height=50, background_color=(0.4, 0.2, 0.6, 1))
        login_btn.bind(on_press=self.do_login)
        layout.add_widget(login_btn)
        
        register_btn = Button(text="Create Account", size_hint_y=None, height=50)
        register_btn.bind(on_press=self.go_register)
        layout.add_widget(register_btn)
        
        self.add_widget(layout)
    
    def do_login(self, instance):
        username = self.username.text.strip()
        password = self.password.text
        if not username or not password:
            self.show_popup("Error", "Enter username and password")
            return
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        db.cursor.execute("SELECT id, username FROM users WHERE username=? AND password_hash=?", (username, password_hash))
        user = db.cursor.fetchone()
        
        if user:
            App.get_running_app().current_user_id = user[0]
            App.get_running_app().current_username = user[1]
            theme = db.cursor.execute("SELECT theme FROM users WHERE id=?", (user[0],)).fetchone()[0]
            App.get_running_app().apply_theme(theme)
            self.manager.current = 'home'
        else:
            self.show_popup("Error", "Invalid username or password")
    
    def go_register(self, instance):
        self.manager.current = 'register'
    
    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.7, 0.4))
        popup.open()

class RegisterScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)
        
        layout.add_widget(Label(text="Create Account", font_size=28, size_hint_y=None, height=60))
        
        self.username = TextInput(hint_text="Username (unique)", multiline=False, size_hint_y=None, height=50)
        layout.add_widget(self.username)
        
        self.display_name = TextInput(hint_text="Display Name", multiline=False, size_hint_y=None, height=50)
        layout.add_widget(self.display_name)
        
        self.password = TextInput(hint_text="Password", password=True, multiline=False, size_hint_y=None, height=50)
        layout.add_widget(self.password)
        
        self.confirm = TextInput(hint_text="Confirm Password", password=True, multiline=False, size_hint_y=None, height=50)
        layout.add_widget(self.confirm)
        
        self.public_key = TextInput(hint_text="Your Personal Key (optional)", multiline=False, size_hint_y=None, height=50)
        layout.add_widget(self.public_key)
        
        register_btn = Button(text="Register", size_hint_y=None, height=50, background_color=(0.4, 0.2, 0.6, 1))
        register_btn.bind(on_press=self.do_register)
        layout.add_widget(register_btn)
        
        back_btn = Button(text="Back to Login", size_hint_y=None, height=50)
        back_btn.bind(on_press=self.go_back)
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
    
    def do_register(self, instance):
        username = self.username.text.strip()
        display = self.display_name.text.strip() or username
        password = self.password.text
        confirm = self.confirm.text
        pub_key = self.public_key.text.strip() or hashlib.sha256(os.urandom(32)).hexdigest()[:16]
        
        if not username or not password:
            self.show_popup("Error", "Username and password required")
            return
        
        if password != confirm:
            self.show_popup("Error", "Passwords don't match")
            return
        
        if len(username) < 3:
            self.show_popup("Error", "Username must be at least 3 characters")
            return
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            db.cursor.execute("INSERT INTO users (username, password_hash, display_name, public_key) VALUES (?, ?, ?, ?)",
                              (username, password_hash, display, pub_key))
            db.conn.commit()
            self.show_popup("Success", "Account created! Please login.")
            self.manager.current = 'login'
        except sqlite3.IntegrityError:
            self.show_popup("Error", "Username already taken")
    
    def go_back(self, instance):
        self.manager.current = 'login'
    
    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.7, 0.4))
        popup.open()

class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.clear_widgets()
        
        layout.add_widget(Label(text="⚙️ Settings", font_size=28, size_hint_y=None, height=50))
        
        theme_layout = BoxLayout(size_hint_y=None, height=50)
        theme_layout.add_widget(Label(text="Dark Mode:"))
        self.theme_switch = Switch(active=App.get_running_app().current_theme == 'dark')
        self.theme_switch.bind(active=self.toggle_theme)
        theme_layout.add_widget(self.theme_switch)
        layout.add_widget(theme_layout)
        
        layout.add_widget(Label(text="Account", font_size=20, bold=True, size_hint_y=None, height=40))
        
        self.username_display = Label(text=f"Username: {App.get_running_app().current_username}", size_hint_y=None, height=40)
        layout.add_widget(self.username_display)
        
        change_user_layout = BoxLayout(size_hint_y=None, height=50)
        self.new_username = TextInput(hint_text="New username", multiline=False)
        change_user_layout.add_widget(self.new_username)
        change_btn = Button(text="Change", size_hint_x=0.3)
        change_btn.bind(on_press=self.change_username)
        change_user_layout.add_widget(change_btn)
        layout.add_widget(change_user_layout)
        
        change_pass_layout = BoxLayout(size_hint_y=None, height=50)
        self.new_password = TextInput(hint_text="New password", password=True, multiline=False)
        change_pass_layout.add_widget(self.new_password)
        change_pass_btn = Button(text="Change Pass", size_hint_x=0.3)
        change_pass_btn.bind(on_press=self.change_password)
        change_pass_layout.add_widget(change_pass_btn)
        layout.add_widget(change_pass_layout)
        
        key_info = db.cursor.execute("SELECT public_key FROM users WHERE id=?", (App.get_running_app().current_user_id,)).fetchone()
        if key_info:
            layout.add_widget(Label(text=f"Your Key: {key_info[0][:12]}...", size_hint_y=None, height=40))
        
        layout.add_widget(Label(text="", size_hint_y=None, height=20))
        
        logout_btn = Button(text="Logout", size_hint_y=None, height=50, background_color=(0.8, 0.2, 0.2, 1))
        logout_btn.bind(on_press=self.logout)
        layout.add_widget(logout_btn)
        
        scroll = ScrollView()
        scroll.add_widget(layout)
        self.add_widget(scroll)
    
    def toggle_theme(self, instance, value):
        theme = 'dark' if value else 'light'
        App.get_running_app().apply_theme(theme)
        db.cursor.execute("UPDATE users SET theme=? WHERE id=?", (theme, App.get_running_app().current_user_id))
        db.conn.commit()
    
    def change_username(self, instance):
        new_name = self.new_username.text.strip()
        if not new_name:
            return
        try:
            db.cursor.execute("UPDATE users SET username=? WHERE id=?", (new_name, App.get_running_app().current_user_id))
            db.conn.commit()
            App.get_running_app().current_username = new_name
            self.username_display.text = f"Username: {new_name}"
            self.show_popup("Success", "Username changed")
        except sqlite3.IntegrityError:
            self.show_popup("Error", "Username already taken")
    
    def change_password(self, instance):
        new_pass = self.new_password.text.strip()
        if not new_pass:
            return
        password_hash = hashlib.sha256(new_pass.encode()).hexdigest()
        db.cursor.execute("UPDATE users SET password_hash=? WHERE id=?", (password_hash, App.get_running_app().current_user_id))
        db.conn.commit()
        self.show_popup("Success", "Password changed")
    
    def logout(self, instance):
        App.get_running_app().current_user_id = None
        App.get_running_app().current_username = None
        self.manager.current = 'login'
    
    def on_enter(self):
        self.build_ui()
    
    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.7, 0.4))
        popup.open()

class GroupListScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical')
        
        header = BoxLayout(size_hint_y=None, height=50, padding=10)
        header.add_widget(Label(text="👥 Groups & Channels", font_size=20))
        layout.add_widget(header)
        
        search_layout = BoxLayout(size_hint_y=None, height=50, padding=10)
        self.search_input = TextInput(hint_text="Search by name or @username", multiline=False)
        search_layout.add_widget(self.search_input)
        search_btn = Button(text="🔍", size_hint_x=0.2)
        search_btn.bind(on_press=self.search)
        search_layout.add_widget(search_btn)
        layout.add_widget(search_layout)
        
        btn_layout = BoxLayout(size_hint_y=None, height=50, padding=10, spacing=10)
        create_btn = Button(text="+ Create Group/Channel")
        create_btn.bind(on_press=self.create_group)
        btn_layout.add_widget(create_btn)
        join_btn = Button(text="🔑 Join with Key")
        join_btn.bind(on_press=self.join_with_key)
        btn_layout.add_widget(join_btn)
        layout.add_widget(btn_layout)
        
        self.groups_list = RecycleView()
        self.groups_list.viewclass = 'GroupItem'
        layout.add_widget(self.groups_list)
        
        self.add_widget(layout)
        self.load_groups()
    
    def load_groups(self, search_term=''):
        if search_term:
            query = '''SELECT g.id, g.name, g.description, g.is_public, u.username as creator 
                       FROM groups g JOIN users u ON g.creator_id = u.id 
                       WHERE g.name LIKE ? OR u.username LIKE ?'''
            params = (f'%{search_term}%', f'%{search_term}%')
        else:
            query = '''SELECT g.id, g.name, g.description, g.is_public, u.username as creator 
                       FROM groups g JOIN users u ON g.creator_id = u.id'''
            params = ()
        
        db.cursor.execute(query, params)
        groups = db.cursor.fetchall()
        
        data = []
        for group in groups:
            data.append({
                'text': f"{'🔓' if group[3] else '🔒'} {group[1]}\nby @{group[4]} • {group[2][:50]}",
                'group_id': group[0],
                'name': group[1],
                'is_public': group[3]
            })
        self.groups_list.data = data
    
    def search(self, instance):
        self.load_groups(self.search_input.text)
    
    def create_group(self, instance):
        self.manager.current = 'create_group'
    
    def join_with_key(self, instance):
        popup_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        key_input = TextInput(hint_text="Enter join key", multiline=False)
        popup_layout.add_widget(key_input)
        
        submit_btn = Button(text="Join")
        popup_layout.add_widget(submit_btn)
        
        popup = Popup(title="Join Private Group", content=popup_layout, size_hint=(0.8, 0.4))
        
        def do_join(instance):
            key = key_input.text.strip()
            if key:
                db.cursor.execute("SELECT id, name FROM groups WHERE join_key=? AND is_public=0", (key,))
                group = db.cursor.fetchone()
                if group:
                    db.cursor.execute("INSERT OR IGNORE INTO group_members (group_id, user_id, joined_at) VALUES (?, ?, ?)",
                                      (group[0], App.get_running_app().current_user_id, datetime.now().isoformat()))
                    db.conn.commit()
                    popup.dismiss()
                    self.show_popup("Success", f"Joined {group[1]}")
                    self.load_groups()
                else:
                    self.show_popup("Error", "Invalid key")
        submit_btn.bind(on_press=do_join)
        popup.open()
    
    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.7, 0.4))
        popup.open()
    
    def on_enter(self):
        self.load_groups()

class GroupItem(RecycleDataViewBehavior, BoxLayout):
    text = StringProperty()
    group_id = None
    name = ''
    is_public = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(70)
        self.padding = dp(10)
    
    def refresh_view_attrs(self, rv, index, data):
        self.text = data.get('text', '')
        self.group_id = data.get('group_id')
        self.name = data.get('name', '')
        self.is_public = data.get('is_public', False)
        return super().refresh_view_attrs(rv, index, data)
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            app = App.get_running_app()
            app.selected_group_id = self.group_id
            app.selected_group_name = self.name
            app.root.current = 'group_chat'
        return super().on_touch_down(touch)

class CreateGroupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        back_btn = Button(text="← Back", size_hint_y=None, height=50)
        back_btn.bind(on_press=self.go_back)
        layout.add_widget(back_btn)
        
        layout.add_widget(Label(text="Create Group/Channel", font_size=24, size_hint_y=None, height=50))
        
        self.name_input = TextInput(hint_text="Name", multiline=False, size_hint_y=None, height=50)
        layout.add_widget(self.name_input)
        
        self.desc_input = TextInput(hint_text="Description", multiline=True, size_hint_y=None, height=100)
        layout.add_widget(self.desc_input)
        
        public_layout = BoxLayout(size_hint_y=None, height=50)
        public_layout.add_widget(Label(text="Public (anyone can find)"))
        self.public_switch = Switch(active=True)
        public_layout.add_widget(self.public_switch)
        layout.add_widget(public_layout)
        
        self.key_input = TextInput(hint_text="Join key (for private groups)", multiline=False, size_hint_y=None, height=50)
        layout.add_widget(self.key_input)
        
        create_btn = Button(text="Create", size_hint_y=None, height=50, background_color=(0.4, 0.2, 0.6, 1))
        create_btn.bind(on_press=self.create)
        layout.add_widget(create_btn)
        
        self.add_widget(layout)
    
    def create(self, instance):
        name = self.name_input.text.strip()
        desc = self.desc_input.text.strip()
        is_public = 1 if self.public_switch.active else 0
        join_key = self.key_input.text.strip() if not is_public else None
        
        if not name:
            self.show_popup("Error", "Name required")
            return
        
        try:
            db.cursor.execute('''INSERT INTO groups (name, description, creator_id, is_public, join_key, created_at)
                                  VALUES (?, ?, ?, ?, ?, ?)''',
                              (name, desc, App.get_running_app().current_user_id, is_public, join_key, datetime.now().isoformat()))
            db.conn.commit()
            group_id = db.cursor.lastrowid
            db.cursor.execute("INSERT INTO group_members (group_id, user_id, role, joined_at) VALUES (?, ?, 'admin', ?)",
                              (group_id, App.get_running_app().current_user_id, datetime.now().isoformat()))
            db.conn.commit()
            self.show_popup("Success", f"Created {name}")
            self.manager.current = 'groups'
        except sqlite3.IntegrityError:
            self.show_popup("Error", "Name already taken")
    
    def go_back(self, instance):
        self.manager.current = 'groups'
    
    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.7, 0.4))
        popup.open()

class GroupChatScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        
        self.header = BoxLayout(size_hint_y=None, height=50, padding=10)
        back_btn = Button(text="←", size_hint_x=0.15)
        back_btn.bind(on_press=self.go_back)
        self.header.add_widget(back_btn)
        self.title_label = Label(text="", font_size=18)
        self.header.add_widget(self.title_label)
        layout.add_widget(self.header)
        
        self.messages_list = RecycleView()
        self.messages_list.viewclass = 'MessageItem'
        layout.add_widget(self.messages_list)
        
        input_layout = BoxLayout(size_hint_y=None, height=60, padding=10, spacing=10)
        self.message_input = TextInput(hint_text="Type message...", multiline=False)
        input_layout.add_widget(self.message_input)
        send_btn = Button(text="Send", size_hint_x=0.2)
        send_btn.bind(on_press=self.send_message)
        input_layout.add_widget(send_btn)
        layout.add_widget(input_layout)
        
        self.add_widget(layout)
        self.group_id = None
    
    def on_enter(self):
        app = App.get_running_app()
        self.group_id = app.selected_group_id
        db.cursor.execute("SELECT name FROM groups WHERE id=?", (self.group_id,))
        name = db.cursor.fetchone()[0]
        self.title_label.text = name
        self.load_messages()
        Clock.schedule_interval(self.refresh_messages, 2)
    
    def on_leave(self):
        Clock.unschedule(self.refresh_messages)
    
    def refresh_messages(self, dt):
        self.load_messages()
    
    def load_messages(self):
        db.cursor.execute('''SELECT m.id, m.content, m.created_at, u.display_name, u.username 
                              FROM messages m JOIN users u ON m.sender_id = u.id 
                              WHERE m.group_id=? ORDER BY m.created_at''', (self.group_id,))
        messages = db.cursor.fetchall()
        
        data = []
        for msg in messages:
            data.append({
                'text': f"{msg[3] or msg[4]}: {msg[1]}",
                'time': msg[2][:16],
                'is_own': msg[4] == App.get_running_app().current_username
            })
        self.messages_list.data = data
    
    def send_message(self, instance):
        content = self.message_input.text.strip()
        if content:
            db.cursor.execute("INSERT INTO messages (group_id, sender_id, content, created_at) VALUES (?, ?, ?, ?)",
                              (self.group_id, App.get_running_app().current_user_id, content, datetime.now().isoformat()))
            db.conn.commit()
            self.message_input.text = ''
            self.load_messages()
    
    def go_back(self, instance):
        self.manager.current = 'groups'

class MessageItem(RecycleDataViewBehavior, BoxLayout):
    text = StringProperty()
    time = StringProperty()
    is_own = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(50)
        self.padding = dp(5)
    
    def refresh_view_attrs(self, rv, index, data):
        self.text = data.get('text', '')
        self.is_own = data.get('is_own', False)
        self.clear_widgets()
        
        if self.is_own:
            self.add_widget(Widget(size_hint_x=0.3))
            msg = Label(text=self.text, size_hint_x=0.7, halign='right', valign='middle')
            msg.bind(size=msg.setter('text_size'))
            self.add_widget(msg)
        else:
            msg = Label(text=self.text, size_hint_x=0.7, halign='left', valign='middle')
            msg.bind(size=msg.setter('text_size'))
            self.add_widget(msg)
            self.add_widget(Widget(size_hint_x=0.3))
        return super().refresh_view_attrs(rv, index, data)

class UserSearchScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        back_btn = Button(text="← Back", size_hint_y=None, height=50)
        back_btn.bind(on_press=self.go_back)
        layout.add_widget(back_btn)
        
        layout.add_widget(Label(text="Find User", font_size=24, size_hint_y=None, height=50))
        
        search_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        self.username_input = TextInput(hint_text="@username", multiline=False)
        search_layout.add_widget(self.username_input)
        search_btn = Button(text="Search", size_hint_x=0.3)
        search_btn.bind(on_press=self.search)
        search_layout.add_widget(search_btn)
        layout.add_widget(search_layout)
        
        self.result_label = Label(text="", size_hint_y=None, height=50)
        layout.add_widget(self.result_label)
        
        self.chat_btn = Button(text="Start Chat", size_hint_y=None, height=50, disabled=True)
        self.chat_btn.bind(on_press=self.start_chat)
        layout.add_widget(self.chat_btn)
        
        self.add_widget(layout)
        self.found_user_id = None
    
    def search(self, instance):
        username = self.username_input.text.strip().lstrip('@')
        if not username:
            return
        
        db.cursor.execute("SELECT id, username, display_name FROM users WHERE username=?", (username,))
        user = db.cursor.fetchone()
        
        if user and user[0] != App.get_running_app().current_user_id:
            self.found_user_id = user[0]
            display = user[2] or user[1]
            self.result_label.text = f"Found: @{user[1]} ({display})"
            self.chat_btn.disabled = False
        elif user and user[0] == App.get_running_app().current_user_id:
            self.result_label.text = "That's you!"
            self.chat_btn.disabled = True
        else:
            self.result_label.text = "User not found"
            self.chat_btn.disabled = True
    
    def start_chat(self, instance):
        if self.found_user_id:
            App.get_running_app().selected_recipient_id = self.found_user_id
            self.manager.current = 'direct_chat'
    
    def go_back(self, instance):
        self.manager.current = 'home'

class DirectChatScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        
        self.header = BoxLayout(size_hint_y=None, height=50, padding=10)
        back_btn = Button(text="←", size_hint_x=0.15)
        back_btn.bind(on_press=self.go_back)
        self.header.add_widget(back_btn)
        self.title_label = Label(text="", font_size=18)
        self.header.add_widget(self.title_label)
        layout.add_widget(self.header)
        
        self.messages_list = RecycleView()
        self.messages_list.viewclass = 'DirectMessageItem'
        layout.add_widget(self.messages_list)
        
        input_layout = BoxLayout(size_hint_y=None, height=60, padding=10, spacing=10)
        self.message_input = TextInput(hint_text="Type message...", multiline=False)
        input_layout.add_widget(self.message_input)
        send_btn = Button(text="Send", size_hint_x=0.2)
        send_btn.bind(on_press=self.send_message)
        input_layout.add_widget(send_btn)
        layout.add_widget(input_layout)
        
        self.add_widget(layout)
        self.recipient_id = None
    
    def on_enter(self):
        app = App.get_running_app()
        self.recipient_id = app.selected_recipient_id
        db.cursor.execute("SELECT username, display_name FROM users WHERE id=?", (self.recipient_id,))
        user = db.cursor.fetchone()
        self.title_label.text = f"@{user[0]}"
        self.load_messages()
        Clock.schedule_interval(self.refresh_messages, 2)
    
    def on_leave(self):
        Clock.unschedule(self.refresh_messages)
    
    def refresh_messages(self, dt):
        self.load_messages()
    
    def load_messages(self):
        db.cursor.execute('''SELECT id, content, created_at, sender_id 
                              FROM direct_messages 
                              WHERE (sender_id=? AND recipient_id=?) OR (sender_id=? AND recipient_id=?)
                              ORDER BY created_at''', 
                          (App.get_running_app().current_user_id, self.recipient_id,
                           self.recipient_id, App.get_running_app().current_user_id))
        messages = db.cursor.fetchall()
        
        data = []
        for msg in messages:
            data.append({
                'text': msg[1],
                'time': msg[2][:16],
                'is_own': msg[3] == App.get_running_app().current_user_id
            })
        self.messages_list.data = data
    
    def send_message(self, instance):
        content = self.message_input.text.strip()
        if content:
            db.cursor.execute("INSERT INTO direct_messages (sender_id, recipient_id, content, created_at) VALUES (?, ?, ?, ?)",
                              (App.get_running_app().current_user_id, self.recipient_id, content, datetime.now().isoformat()))
            db.conn.commit()
            self.message_input.text = ''
            self.load_messages()
    
    def go_back(self, instance):
        self.manager.current = 'user_search'

class DirectMessageItem(RecycleDataViewBehavior, BoxLayout):
    text = StringProperty()
    time = StringProperty()
    is_own = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(50)
        self.padding = dp(5)
    
    def refresh_view_attrs(self, rv, index, data):
        self.text = data.get('text', '')
        self.is_own = data.get('is_own', False)
        self.clear_widgets()
        
        if self.is_own:
            self.add_widget(Widget(size_hint_x=0.3))
            msg = Label(text=self.text, size_hint_x=0.7, halign='right', valign='middle')
            msg.bind(size=msg.setter('text_size'))
            self.add_widget(msg)
        else:
            msg = Label(text=self.text, size_hint_x=0.7, halign='left', valign='middle')
            msg.bind(size=msg.setter('text_size'))
            self.add_widget(msg)
            self.add_widget(Widget(size_hint_x=0.3))
        return super().refresh_view_attrs(rv, index, data)

class ForumScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        
        header = BoxLayout(size_hint_y=None, height=50, padding=10)
        header.add_widget(Label(text="📝 Forum", font_size=20))
        layout.add_widget(header)
        
        self.posts_list = RecycleView()
        self.posts_list.viewclass = 'PostItem'
        layout.add_widget(self.posts_list)
        
        new_btn = Button(text="+ New Post", size_hint_y=None, height=50)
        new_btn.bind(on_press=self.new_post)
        layout.add_widget(new_btn)
        
        self.add_widget(layout)
        self.load_posts()
    
    def load_posts(self):
        db.cursor.execute('''SELECT p.id, p.content, p.created_at, u.username, u.display_name 
                              FROM posts p JOIN users u ON p.user_id = u.id 
                              ORDER BY p.created_at DESC''')
        posts = db.cursor.fetchall()
        
        data = []
        for post in posts:
            data.append({
                'text': f"{post[3]}: {post[1][:100]}",
                'time': post[2][:16],
                'post_id': post[0]
            })
        self.posts_list.data = data
    
    def new_post(self, instance):
        popup_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content_input = TextInput(hint_text="What's on your mind?", multiline=True, size_hint_y=None, height=200)
        popup_layout.add_widget(content_input)
        
        submit_btn = Button(text="Post", size_hint_y=None, height=50)
        popup_layout.add_widget(submit_btn)
        
        popup = Popup(title="New Post", content=popup_layout, size_hint=(0.9, 0.5))
        
        def submit(instance):
            if content_input.text.strip():
                db.cursor.execute("INSERT INTO posts (user_id, content, created_at) VALUES (?, ?, ?)",
                                  (App.get_running_app().current_user_id, content_input.text, datetime.now().isoformat()))
                db.conn.commit()
                self.load_posts()
                popup.dismiss()
        submit_btn.bind(on_press=submit)
        popup.open()

class PostItem(RecycleDataViewBehavior, BoxLayout):
    text = StringProperty()
    time = StringProperty()
    post_id = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(80)
        self.padding = dp(10)
    
    def refresh_view_attrs(self, rv, index, data):
        self.text = data.get('text', '')
        self.time = data.get('time', '')
        self.post_id = data.get('post_id')
        self.clear_widgets()
        
        self.add_widget(Label(text=self.text, size_hint_y=None, height=dp(50), text_size=(self.width, None)))
        self.add_widget(Label(text=self.time, size_hint_y=None, height=dp(20), font_size=10))
        return super().refresh_view_attrs(rv, index, data)

class ReelsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        
        header = BoxLayout(size_hint_y=None, height=50, padding=10)
        header.add_widget(Label(text="📱 Reels", font_size=20))
        layout.add_widget(header)
        
        self.reels_list = RecycleView()
        self.reels_list.viewclass = 'ReelItem'
        layout.add_widget(self.reels_list)
        
        new_btn = Button(text="+ Upload Reel", size_hint_y=None, height=50)
        new_btn.bind(on_press=self.new_reel)
        layout.add_widget(new_btn)
        
        self.add_widget(layout)
        self.load_reels()
    
    def load_reels(self):
        db.cursor.execute('''SELECT r.id, r.caption, r.created_at, u.username 
                              FROM reels r JOIN users u ON r.user_id = u.id 
                              ORDER BY r.created_at DESC''')
        reels = db.cursor.fetchall()
        
        data = []
        for reel in reels:
            data.append({
                'text': f"🎬 {reel[3]}: {reel[1] or 'No caption'}",
                'time': reel[2][:16]
            })
        self.reels_list.data = data
    
    def new_reel(self, instance):
        popup_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        path_input = TextInput(hint_text="Video file path", multiline=False)
        popup_layout.add_widget(path_input)
        
        caption_input = TextInput(hint_text="Caption", multiline=False)
        popup_layout.add_widget(caption_input)
        
        submit_btn = Button(text="Upload", size_hint_y=None, height=50)
        popup_layout.add_widget(submit_btn)
        
        popup = Popup(title="Add Reel", content=popup_layout, size_hint=(0.9, 0.4))
        
        def submit(instance):
            if path_input.text.strip():
                db.cursor.execute("INSERT INTO reels (user_id, video_path, caption, created_at) VALUES (?, ?, ?, ?)",
                                  (App.get_running_app().current_user_id, path_input.text, caption_input.text, datetime.now().isoformat()))
                db.conn.commit()
                self.load_reels()
                popup.dismiss()
        submit_btn.bind(on_press=submit)
        popup.open()

class ReelItem(RecycleDataViewBehavior, BoxLayout):
    text = StringProperty()
    time = StringProperty()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(70)
        self.padding = dp(10)
    
    def refresh_view_attrs(self, rv, index, data):
        self.text = data.get('text', '')
        self.time = data.get('time', '')
        self.clear_widgets()
        
        self.add_widget(Label(text=self.text, size_hint_y=None, height=dp(50)))
        self.add_widget(Label(text=self.time, size_hint_y=None, height=dp(20), font_size=10))
        return super().refresh_view_attrs(rv, index, data)

class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.sm = ScreenManager()
        
        self.sm.add_widget(GroupListScreen(name='groups'))
        self.sm.add_widget(CreateGroupScreen(name='create_group'))
        self.sm.add_widget(GroupChatScreen(name='group_chat'))
        self.sm.add_widget(UserSearchScreen(name='user_search'))
        self.sm.add_widget(DirectChatScreen(name='direct_chat'))
        self.sm.add_widget(ForumScreen(name='forum'))
        self.sm.add_widget(ReelsScreen(name='reels'))
        self.sm.add_widget(SettingsScreen(name='settings'))
        
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(self.sm)
        
        nav = BoxLayout(size_hint_y=None, height=60)
        btn_groups = Button(text="👥 Groups")
        btn_groups.bind(on_press=lambda x: setattr(self.sm, 'current', 'groups'))
        btn_chat = Button(text="💬 DM")
        btn_chat.bind(on_press=lambda x: setattr(self.sm, 'current', 'user_search'))
        btn_forum = Button(text="📝 Forum")
        btn_forum.bind(on_press=lambda x: setattr(self.sm, 'current', 'forum'))
        btn_reels = Button(text="📱 Reels")
        btn_reels.bind(on_press=lambda x: setattr(self.sm, 'current', 'reels'))
        btn_settings = Button(text="⚙️")
        btn_settings.bind(on_press=lambda x: setattr(self.sm, 'current', 'settings'))
        
        nav.add_widget(btn_groups)
        nav.add_widget(btn_chat)
        nav.add_widget(btn_forum)
        nav.add_widget(btn_reels)
        nav.add_widget(btn_settings)
        layout.add_widget(nav)
        
        self.add_widget(layout)

class GentleMoonApp(App):
    current_user_id = None
    current_username = None
    current_theme = 'light'
    selected_group_id = None
    selected_group_name = None
    selected_recipient_id = None
    
    def build(self):
        sm = ScreenManager()
        
        if not os.path.exists('tos_accepted.txt'):
            sm.add_widget(TOSScreen(name='tos'))
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(RegisterScreen(name='register'))
        sm.add_widget(HomeScreen(name='home'))
        
        if not os.path.exists('tos_accepted.txt'):
            sm.current = 'tos'
        else:
            sm.current = 'login'
        
        return sm
    
    def apply_theme(self, theme):
        self.current_theme = theme
        if theme == 'dark':
            from kivy.utils import get_color_from_hex
            Window.clearcolor = get_color_from_hex('#1e1e1e')
        else:
            Window.clearcolor = (0.95, 0.95, 0.95, 1)

if __name__ == '__main__':
    GentleMoonApp().run()
